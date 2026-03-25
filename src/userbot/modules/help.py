from ..core.types import Module, command, tds

@tds
class MatrixModule(Module):
    strings = {
        "name": "Помощь",
        "_cls_doc": "Отображает список всех доступных команд и информацию о модулях.",
        "info_text": "Привет! Сын хорошего человека!\nКак дела?"
    }

    @command(name="help")
    async def help_cmd(self, bot, room, event, args):
        """[команда] - Показать список команд или справку"""

        if not args:
            msg = f"<b>💠 {self.friendly_name}</b>\n"
            msg += f"<i>{self.help()}</i>\n\n"
            
            msg += "<b>Доступные модули:</b>\n"
            for mod in bot.all_modules.active_modules.values():
                msg += f"▫️ <code>{mod.friendly_name}</code> — {mod.help()}\n"
            
            info = self.strings.get("info_text", "")
            if info:
                msg += f"\n<i>{info}</i>"
                
            return await bot.send_text(room, msg)

        cmd_name = args.lower()
        for mod in bot.all_modules.active_modules.values():
            if cmd_name in mod.commands:
                doc = mod.strings.get(f"_cmd_doc_{cmd_name}", "Описание отсутствует")
                return await bot.send_text(
                    room, 
                    f"<b>Команда:</b> <code>!{cmd_name}</code>\n"
                    f"<b>Описание:</b> {doc}"
                )
        
        await bot.send_text(room, f"❌ Команда <code>!{cmd_name}</code> не найдена.")