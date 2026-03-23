__all__ = [
    "Module"
]



import os
import sys
import shutil
import importlib
import importlib.util
from pathlib import Path
from loguru import logger
import inspect
import hashlib
import typing
import logging
from abc import ABC, abstractmethod


class ModuleCannotBeDisabled(Exception):
    pass

class Module(ABC):
    __origin__ = "<unknown>"
    __module_hash__ = "unknown"
    __source__ = ""
    
    def _internal_init(self, name):
        """Скрытый метод инициализации. Лоадер вызовет его сам!"""
        self.name = name
        self.enabled = True
        self.logger = logging.getLogger("module " + self.name)

    def matrix_start(self, bot):
        self.logger.info('Starting..')

    @abstractmethod
    async def matrix_message(self, bot, room, event):
        pass

    def matrix_stop(self, bot):
        self.logger.info('Stopping..')

    async def matrix_poll(self, bot, pollcount):
        pass

    @abstractmethod
    def help(self):
        return 'A cool hemppa module'

    def long_help(self, bot=None, room=None, event=None, args=None):
        return self.help()

    def get_settings(self):
        return {'enabled': getattr(self, "enabled", True)}

    def set_settings(self, data):
        if data.get('enabled') is not None:
            self.enabled = data['enabled']

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False