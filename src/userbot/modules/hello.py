from ..core import loader


@loader.tds
class MatrixModule(loader.Module):
    strings = {
        "name": "HelloModule",
        "_cls_doc": "выводит приветственное сообщение"
    }

    @loader.command()
    async def hello(self, bot, room, event, args):
        """Отправляет приветственное сообщение"""
        await bot.send_text(room, "Привет")
