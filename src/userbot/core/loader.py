import os
import typing
import shutil
import inspect
import hashlib
import asyncio
import importlib.util
from functools import wraps
from pathlib import Path
from loguru import logger

from . import utils
from .types import Module 
_MODULE_NAME_BY_HASH: typing.Dict[str, str] = {}


def _calc_module_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8", errors="ignore")).hexdigest()


def command(name=None):
    def decorator(func):
        func.is_command = True
        func.command_name = (name or func.__name__).lower()
        return func
    return decorator


def tds(cls):
    """Decorator that makes triple-quote docstrings translatable"""
    if not hasattr(cls, 'strings'):
        cls.strings = {}

    @wraps(cls._internal_init)
    async def _internal_init(self, *args, **kwargs):
        def proccess_decorators(mark: str, obj: str):
            nonlocal self
            for attr in dir(func_):
                if (
                    attr.endswith("_doc")
                    and len(attr) == 6
                    and isinstance(getattr(func_, attr), str)
                ):
                    var = f"strings_{attr.split('_')[0]}"
                    if not hasattr(self, var):
                        setattr(self, var, {})

                    getattr(self, var).setdefault(f"{mark}{obj}", getattr(func_, attr))

        for command_, func_ in utils.get_commands(cls).items():
            proccess_decorators("_cmd_doc_", command_)
            try:
                func_.__doc__ = self.strings[f"_cmd_doc_{command_}"]
            except AttributeError:
                func_.__func__.__doc__ = self.strings[f"_cmd_doc_{command_}"]

        # self.__doc__ = self.strings.get("_cls_doc", self.__doc__)
        self.__class__.__doc__ = self.strings.get("_cls_doc", self.__class__.__doc__)

        return await self._internal_init._old_(self, *args, **kwargs)

    _internal_init._old_ = cls._internal_init
    cls._internal_init = _internal_init

    for command_, func in utils.get_commands(cls).items():
        cmd_doc = func.__doc__
        if cmd_doc:
            cls.strings.setdefault(f"_cmd_doc_{command_}", inspect.cleandoc(cmd_doc))

    cls_doc = cls.__dict__.get('__doc__') # Обходим наследование от ABC
    if cls_doc:
        cls.strings.setdefault("_cls_doc", inspect.cleandoc(cls_doc))

    def _require(key: str, error_msg: str):
        """Проверяет наличие и непустоту ключа в словаре strings"""
        if not str(cls.strings.get(key, "")).strip():
            raise ValueError(f"❌ {error_msg}")

    _require("name", f"Модуль '{cls.__name__}' ОБЯЗАН иметь ключ 'name' в strings!")
    _require("_cls_doc", f"Модуль '{cls.__name__}' ОБЯЗАН иметь docstring или ключ '_cls_doc' в strings!")

    for cmd_name in utils.get_commands(cls).keys():
        _require(f"_cmd_doc_{cmd_name}", f"Команда '!{cmd_name}' ОБЯЗАНА иметь docstring!")

    return cls



class Loader:
    def __init__(self, db_wrapper):
        self.db = db_wrapper 
        self.active_modules: typing.Dict[str, object] = {}
        self.module_path = Path(__file__).resolve().parents[2] / 'userbot' / 'modules'
        
        self._background_tasks: typing.Set[asyncio.Task] = set()


    async def register_all(self, bot) -> None:
        """Сканирует папку и запускает регистрацию модулей"""
        if not self.module_path.exists():
            self.module_path.mkdir(parents=True, exist_ok=True)

        module_files = [
            f for f in self.module_path.iterdir() 
            if f.suffix == ".py" and not f.name.startswith("_")
        ]

        if not module_files:
            logger.warning("Папка модулей пуста.")
            return

        import_tasks = [
            self.register_module(path, bot) 
            for path in module_files
        ]
        
        await asyncio.gather(*import_tasks, return_exceptions=True)
        logger.info(f"Загружено модулей: {len(self.active_modules)}. Ожидание фоновой активации...")

    async def register_module(self, path: Path, bot):
        """Низкоуровневый импорт файла и создание инстанса"""
        module_name = f"src.userbot.modules.{path.stem}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, str(path))
            if not spec or not spec.loader:
                return

            module = importlib.util.module_from_spec(spec)
            if "." in module_name:
                module.__package__ = module_name.rsplit('.', 1)[0]
            
            spec.loader.exec_module(module)

            if not hasattr(module, 'MatrixModule'):
                return

            cls = getattr(module, 'MatrixModule')
            short_name = path.stem
            
            try:
                instance = cls()
            except TypeError:
                instance = cls(short_name)
            
            instance._is_ready = False


            if hasattr(instance, '_internal_init'):
                await instance._internal_init(short_name, self.db, self)

            self._apply_metadata(instance, spec)
            self.active_modules[short_name] = instance

            startup_task = asyncio.create_task(self._finalize_module_startup(instance, bot, short_name))
            self._background_tasks.add(startup_task)
            startup_task.add_done_callback(self._background_tasks.discard)

            logger.debug(f"Импортирован файл модуля: {short_name}")

        except Exception:
            logger.exception(f"Ошибка при импорте файла {path.name}")


    async def _finalize_module_startup(self, instance, bot, name):
        """Фоновый метод: загрузка настроек и запуск _matrix_start"""
        try:
            # Загрузка конфига из БД
            if hasattr(instance, "set_settings"):
                saved_settings = await self.db.get(name, "__config__")
                if saved_settings:
                    instance.set_settings(saved_settings)

            if getattr(instance, "enabled", True) and hasattr(instance, "_matrix_start"):
                await instance._matrix_start(bot)
            
            instance._is_ready = True
            
            logger.success(f"Модуль {name} успешно запущен в фоне.")
        except Exception:
            logger.exception(f"Ошибка при запуске модуля {name}")


    def _apply_metadata(self, instance, spec):
        """Запись метаданных (исходник, хэш)"""
        try:
            with open(spec.origin, 'r', encoding='utf-8') as f:
                source = f.read()
            instance.__source__ = source
            instance.__module_hash__ = _calc_module_hash(source)
            instance.__origin__ = spec.origin
            _MODULE_NAME_BY_HASH[instance.__module_hash__] = instance.__class__.__name__
        except Exception:
            instance.__module_hash__ = "unknown"