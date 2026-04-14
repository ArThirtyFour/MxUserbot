


from ...core import utils, loader
from mautrix.client import Client
from mautrix.types import MessageEvent, TrustState

class Meta:
    name = "VerifierModule"
    _cls_doc = "Управление доверием устройств"

@loader.tds
class VerifierModule(loader.Module):

    @loader.command()
    async def verif(self, mx: Client, event: MessageEvent):
        """Начать верификацию. Бот не будет трогать уже верифицированные устройства."""

        await utils.answer(mx, "🔍 Проверяю статусы устройств...")
        
        devices_resp = await mx.client.api.request("GET", "/_matrix/client/v3/devices")
        my_devices = devices_resp.get("devices", [])
        
        unverified = []
        for dev in my_devices:
            d_id = dev['device_id']
            if d_id == mx.client.device_id: continue
            
            identity = await mx.client.crypto.crypto_store.get_device(mx.client.mxid, d_id)
            
            if not identity:
                identity = await mx.client.crypto.get_or_fetch_device(mx.client.mxid, d_id)
            
            if not identity or identity.trust < TrustState.VERIFIED:
                unverified.append(dev)

        if not unverified:
            return await utils.answer(mx, "✅ Все устройства в локальной базе бота уже верифицированы!")

        target = unverified[-1]
        await mx.sas_verifier.start_verification(mx.client.mxid, target['device_id'], event.room_id)
        await utils.answer(mx, f"🛡 Инициация верификации: <code>{target['device_id']}</code>\n⏳ Жми «Принять» на телефоне.")