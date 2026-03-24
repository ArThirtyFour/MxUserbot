import os
import sys
import asyncio
from loguru import logger
from nio import AsyncClient

from ...settings import config


_client_instance = None

class ClientManager:
    """Менеджер Matrix-клиента. Работает через обертку БД."""
    
    def __init__(self, db_wrapper, config):
        self._db = db_wrapper
        self._config = config
        self._client = None

    def get_client(self):
        global _client_instance
        
        if _client_instance is not None:
            return _client_instance

        base_url = self._config.matrix_config.base_url
        bot_owner = self._config.matrix_config.owner
        access_token = self._config.matrix_config.access_token.get_secret_value()

        join_on_invite = os.getenv('JOIN_ON_INVITE', 'False').lower() == 'true'
        invite_whitelist = os.getenv('INVITE_WHITELIST', '').split(',')
        if invite_whitelist == ['']: invite_whitelist = []

        if base_url and bot_owner and access_token:
            logger.info(f"Initializing Matrix Client for {bot_owner}...")
            
            client = AsyncClient(
                base_url, 
                bot_owner, 
                ssl=base_url.startswith("https://")
            )
            client.access_token = access_token
            


            join_on_invite = self._db.get("core", "join_on_invite", False)
            invite_whitelist = self._db.get("core", "invite_whitelist", [])
            
            current_owners = self._db.get("core", "owners", [])
            if bot_owner not in current_owners:
                current_owners.append(bot_owner)
                self._db.set("core", "owners", current_owners)


            _client_instance = client

            from .loader import Loader
            loader = Loader()
            asyncio.run(loader.register_all_modules())

            return _client_instance

        else:
            logger.error("Mandatory config missing: check MATRIX_SERVER, OWNER, and ACCESS_TOKEN")
            sys.exit(1)

