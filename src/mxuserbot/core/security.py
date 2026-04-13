import sys
import os
import inspect
from pathlib import Path
from functools import wraps
from loguru import logger

class SekaiSecurity:
    def __init__(self, bot):
        self.bot = bot
        self._db = bot._db
        self.owners = set()

        self.root_path = Path(__file__).resolve().parents[2] # Корень бота
        self.core_path = self.root_path / "mxuserbot" / "modules" / "core"
        self.community_path = self.root_path / "mxuserbot" / "modules" / "community"

    async def init_security(self):
        """Инициализация с гарантированным владельцем и песочницей"""

        my_id = None
        resp = await self.bot.client.whoami()
        if hasattr(resp, "user_id"):
            my_id = resp.user_id

        if not my_id:
            logger.critical("CANNOT DETERMINE OWNER ID! Shutting down for security reasons.")
            sys.exit(1)

        self.owners.add(my_id)

        raw_data = await self._db.get("core", "owners")
        db_owners = raw_data.value if hasattr(raw_data, 'value') else raw_data

        if isinstance(db_owners, list):
            for owner in db_owners:
                if owner and isinstance(owner, str):
                    self.owners.add(owner)

        await self._db.set("core", "owners", list(self.owners))
        logger.success(f"Security active. Owners: {self.owners}")

        self._enable_fs_firewall()


    def _is_community_caller(self) -> bool:
            """Вспомогательный метод для определения, откуда идет вызов"""
            for frame_info in inspect.stack():
                if "modules/community" in frame_info.filename.replace("\\", "/"):
                    return True
            return False

    def _enable_fs_firewall(self):
        def fs_audit_hook(event, args):
            try:
                if event == "open":
                    path, mode, flags = args
                    if hasattr(mode, "count") and ("w" in mode or "a" in mode or "+" in mode or "x" in mode):
                        self._check_file_access(path, "write")
                elif event in ("os.remove", "os.unlink", "os.rmdir"):
                    self._check_file_access(args[0], "delete")
                elif event == "os.rename":
                    self._check_file_access(args[0], "rename_from")
                    self._check_file_access(args[1], "rename_to")


                elif event == "import":
                    module_name = args[0]
                    if module_name and "mxuserbot.modules.core" in module_name:
                        allowed = [
                            "src.mxuserbot.modules.core.loader", 
                            "src.mxuserbot.modules.core.utils",
                            "src.mxuserbot.modules.core.types"
                        ]
                        
                        is_allowed = any(module_name == a or module_name.startswith(a + ".") for a in allowed)
                        
                        if not is_allowed and self._is_community_caller():
                            logger.critical(f"[SECURITY BLOCK] Попытка импорта ядра: {module_name}")
                            raise PermissionError(f"Security: Import of core module '{module_name}' is forbidden.")

                elif event.startswith("ctypes"):
                    if self._is_community_caller():
                        logger.critical("[SECURITY BLOCK] Попытка использования ctypes!")
                        raise PermissionError("Security: C-level memory access is forbidden.")

            except PermissionError as e:
                raise e
            except Exception:
                pass

        sys.addaudithook(fs_audit_hook)
        logger.success("Security Firewall (FS + Memory) is ACTIVE.")


    def _check_file_access(self, target_filepath, action):
        """Проверяет, имеет ли вызывающий код право на действие"""
        path = Path(target_filepath).resolve()
        
        caller_file = None
        is_community_caller = False

        for frame_info in inspect.stack():
            fname = frame_info.filename
            if "modules/community" in fname.replace("\\", "/"):
                caller_file = Path(fname)
                is_community_caller = True
                break

        if not is_community_caller:
            return

        if path.suffix == ".py":
            logger.critical(f"[SECURITY BLOCK] Модуль '{caller_file.name}' попытался изменить/удалить код: {path.name}")
            raise PermissionError(f"Security Exception: Community modules are NOT allowed to modify .py files!")

        if self.core_path in path.parents:
            logger.critical(f"[SECURITY BLOCK] Модуль '{caller_file.name}' попытался влезть в CORE: {path.name}")
            raise PermissionError("Security Exception: Access denied to core system files!")


    def is_owner(self, sender_id: str) -> bool:
        return sender_id in self.owners

    def gate(self, func):
        @wraps(func)
        async def wrapper(event):
            sender = getattr(event, "sender", None)
            if not sender or self.is_owner(sender):
                return await func(event)
            return 
        return wrapper