import os
import shutil
import importlib
import importlib.util
from pathlib import Path
from loguru import logger
import inspect
import hashlib
import typing

from .types import Module

def _calc_module_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8", errors="ignore")).hexdigest()


_MODULE_NAME_BY_HASH: typing.Dict[str, str] = {}


class Loader:
    def __init__(self, db_wrapper):
        self.db = db_wrapper 
        self.active_modules: typing.Dict[str, object] = {}
        
        self.module_path = Path(__file__).resolve().parents[2] / 'userbot' / 'modules'
        self.uv_path = shutil.which(cmd="uv")

    async def register_all(self) -> None:
        print(self.module_path)
        """Загрузить все модули из папки extra"""
        if not os.path.exists(self.module_path):
            os.makedirs(self.module_path)

        modulefiles = [
            str(self.module_path / mod) 
            for mod in os.listdir(self.module_path) 
            if mod.endswith(".py") and not mod.startswith("_")
        ]
        
        for mod_path in modulefiles:
            logger.info(f'Loading: {mod_path}')
            stem = Path(mod_path).stem
            module_name = f'src.userbot.modules.{stem}'
            
            spec = importlib.util.spec_from_file_location(module_name, mod_path)
            if spec:
                await self.register_module(spec, module_name)

    def _apply_metadata(self, instance, spec):
        """Запись исходника и хэша"""
        try:
            with open(spec.origin, 'r', encoding='utf-8') as f:
                source = f.read()
            instance.__source__ = source
            instance.__module_hash__ = _calc_module_hash(source)
            instance.__origin__ = spec.origin
            _MODULE_NAME_BY_HASH[instance.__module_hash__] = instance.__class__.__name__
        except Exception:
            instance.__module_hash__ = "unknown"

    async def register_module(self, spec, module_name):
        """Регистрация одиночного модуля"""
        try: 
            module = importlib.util.module_from_spec(spec)
            if "." in module_name:
                module.__package__ = module_name.rsplit('.', 1)[0]

            spec.loader.exec_module(module)
            
            if not hasattr(module, 'MatrixModule'):
                return None

            cls = getattr(module, 'MatrixModule')
            short_name = module_name.split('.')[-1]
            
            try:
                instance = cls() 
            except TypeError:
                instance = cls(short_name)

            if hasattr(instance, '_internal_init'):
                instance._internal_init(short_name, self.db, self)

            self._apply_metadata(instance, spec)
            
            self.active_modules[short_name] = instance
            
            logger.success(f"Модуль {short_name} загружен. Hash: {instance.__module_hash__[:8]}")
            return instance

        except Exception as e:
            logger.exception(f"Ошибка в модуле {module_name}: {e}")
            return None
