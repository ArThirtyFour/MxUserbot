from ..core.types import Module, command

class MatrixModule(Module):
    """Модуль помощи"""

    config = {
        "msg_users": False,
        "info_text": "сын проститутки <h>"
    }

    @command(name="help")
    async def help_cmd(self, bot, room, event, args):
        """[module] - Показать помощь"""
        
        # Общая помощь
        msg = "<b>Список команд:</b>\n"
        for name, mod in bot.all_modules.active_modules.items():
            msg += f"▫️ <code>!{name}</code> - {mod.help()}\n"
        
        msg += f"\n<i>{self.config['info_text']}</i>"


        await bot.send_text(room, msg)


    def help(self):
        return "Помощь по всем командам"