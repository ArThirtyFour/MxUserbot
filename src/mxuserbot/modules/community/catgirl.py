import aiohttp
# Добавляем импорт ImageInfo
from mautrix.types import MessageEvent, ImageInfo 
from ...core import loader
from mautrix.client import Client

@loader.tds
class MatrixModule(loader.Module):
    strings = {
        "name": "CatGirlModule",
        "_cls_doc": "Скидывает милых catgirl",
        "error_api": "Api умерло",
        "error_image": "Не удалось скачать/загрузить изображение на сервер"
    }

    @loader.command()
    async def catgirl(self, mx: Client, event: MessageEvent):
        """Отправляет фото кошко-девочки через API."""
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.nekosia.cat/api/v1/images/catgirl") as r:
                if r.status != 200:
                    return await mx.send_text(
                        room_id=event.room_id, 
                        content=self.strings["error_api"]
                    )
                
                data = await r.json()
                url = data["image"]["original"]["url"]
                filename = url.split("/")[-1] or "catgirl.png"

                async with s.get(url) as img:
                    if img.status != 200:
                        return await mx.send_text(
                            room_id=event.room_id, 
                            content=self.strings["error_image"]
                        )
                    image_bytes = await img.read()

                    mxc = await mx.client.upload_media(
                        data=image_bytes,
                        mime_type="image/png",
                        filename=filename
                    )

                    image_info = ImageInfo(
                        mimetype="image/png",
                        size=len(image_bytes)
                    )

            await mx.client.send_image(
                room_id=event.room_id,
                url=mxc,
                info=image_info,
                file_name=filename
            )