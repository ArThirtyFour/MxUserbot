
# import re


from mautrix.util.formatter import parse_html


from mautrix.types import EventID, Format, MessageType, RelatesTo, RoomID, TextMessageEventContent


def get_commands(cls):
    cmds = {}
    for attr_name in dir(cls):
        method = getattr(cls, attr_name)
        if callable(method) and getattr(method, 'is_command', False):
            cmds[method.command_name] = method
    return cmds

# def is_owner(event):
#     return event.sender in owners


# from loguru import logger
# навайбкожено, переписать
from mautrix.types import (
    RoomID, EventID, MessageType, RelatesTo, 
    TextMessageEventContent, Format, RelationType
)
from mautrix.util.formatter import parse_html

async def answer(
    mx,
    room_id: RoomID,
    text: str,
    html: bool = True,
    msgtype: MessageType = MessageType.TEXT,
    relates_to: RelatesTo | None = None,
    edit_id: EventID | None = None,
    **kwargs,
) -> EventID:
    # 1. Готовим текст без тегов для уведомлений
    plain_text = await parse_html(text) if html else text

    if edit_id:
        # --- ЛОГИКА РЕДАКТИРОВАНИЯ ---
        content = TextMessageEventContent(
            msgtype=msgtype,
            body=f" * {plain_text}" # Звездочка для старых клиентов
        )
        if html:
            content.format = Format.HTML
            content.formatted_body = text

        # Указываем, ЧТО мы редактируем
        content.relates_to = RelatesTo(
            rel_type=RelationType.REPLACE,
            event_id=edit_id
        )

        # Создаем объект нового контента (обязательно для Matrix)
        new_content = TextMessageEventContent(
            msgtype=msgtype,
            body=plain_text
        )
        if html:
            new_content.format = Format.HTML
            new_content.formatted_body = text

        # ПРАВИЛЬНОЕ ПРИСВОЕНИЕ (через атрибут, а не в __init__)
        content.new_content = new_content
    else:
        # --- ОБЫЧНАЯ ОТПРАВКА ---
        content = TextMessageEventContent(
            msgtype=msgtype,
            body=plain_text
        )
        if html:
            content.format = Format.HTML
            content.formatted_body = text

        if relates_to:
            content.relates_to = relates_to
        
    # Отправляем. Если mx — это интерфейс, он вызовет send_message у клиента.
    # Если mx — это клиент, он вызовет свой метод.
    if hasattr(mx, "send_message"):
        return await mx.send_message(room_id, content, **kwargs)
    return await mx.client.send_message(room_id, content, **kwargs)



def get_args(message):
    import shlex
    """
    Get arguments from message
    :param message: Message or string to get arguments from
    :return: List of arguments
    """
    if not (message := getattr(message, "message", message)):
        return False

    if len(message := message.split(maxsplit=1)) <= 1:
        return []

    message = message[1]

    try:
        split = shlex.split(message)
    except ValueError:
        return message  # Cannot split, let's assume that it's just one long message



    return list(filter(lambda x: len(x) > 0, split))


import os
def get_args_raw(message) -> str:
    """
    Get the parameters to the command as a raw string (not split)
    :param message: Message or string to get arguments from
    :return: Raw string of arguments
    """
    if not (message := getattr(message, "message", message)):
        return False

    return args[1] if len(args := message.split(maxsplit=1)) > 1 else ""




def escape_html(text: str, /) -> str:  # sourcery skip
    """
    Pass all untrusted/potentially corrupt input here
    :param text: Text to escape
    :return: Escaped text
    """
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def escape_quotes(text: str, /) -> str:
    """
    Escape quotes to html quotes
    :param text: Text to escape
    :return: Escaped text
    """
    return escape_html(text).replace('"', "&quot;")


def get_base_dir() -> str:
    """
    Get directory of this file
    :return: Directory of this file
    """
    return get_dir(__file__)


def get_dir(mod: str) -> str:
    """
    Get directory of given module
    :param mod: Module's `__file__` to get directory of
    :return: Directory of given module
    """
    return os.path.abspath(os.path.dirname(os.path.abspath(mod)))





# # Throws exception if event sender is not a room admin
# def must_be_admin(self, room, event, power_level=50):
#     if not self.is_admin(room, event, power_level=power_level):
#         raise CommandRequiresAdmin


# # Throws exception if event sender is not a bot owner
# def must_be_owner(self, event):
#     if not is_owner(event):
#         raise CommandRequiresOwner


# # Returns true if event's sender has PL50 or more in the room event was sent in,
# # or is bot owner
# def is_admin(self, room, event, power_level=50):
#     if is_owner(event):
#         return True
#     if event.sender not in room.power_levels.users:
#         return False
#     return room.power_levels.users[event.sender] >= power_level


# # Checks if this event should be ignored by bot, including custom property
# def should_ignore_event(self, event):
#     return "org.vranki.hemppa.ignore" in event.source['content']





# def clear_modules(self):
#     self.modules = dict()
