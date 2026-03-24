


import re
import sys
import datetime
from loguru import logger

# from .starts_with_command import starts_with_command
from .exceptions import CommandRequiresAdmin, CommandRequiresOwner



import datetime
from loguru import logger
from nio import InviteEvent, JoinError, MatrixRoom

from ...settings import config


invite_whitelist = {}
join_on_invite = True

class CallBack:
    def __init__(self, bot):
        self.bot = bot


    async def invite_cb(self, room, event):
        if event.server_timestamp < self.bot.start_time:
            return
        room: MatrixRoom
        event: InviteEvent

        if len(invite_whitelist) > 0 and not await self.bot.on_invite_whitelist(event.sender):
            logger.error(f'Cannot join room {room.display_name}, as {event.sender} is not whitelisted for invites!')
            return

        if join_on_invite or await self.bot.is_owner(event):
            for attempt in range(3):
                jointime = datetime.datetime.now()
                result = await self.bot.join(room.room_id)
                if type(result) == JoinError:
                    logger.error(f"Error joining room %s (attempt %d): %s", room.room_id, attempt, result.message)
                else:
                    logger.info(f"joining room '{room.display_name}'({room.room_id}) invited by '{event.sender}'")
                    return
        else:
            logger.warning(f'Received invite event, but not joining as sender is not owner or bot not configured to join on invite. {event}')

    async def memberevent_cb(
            self,
            room,
            event
    ):
        # Automatically leaves rooms where bot is alone.
        if room.member_count == 1 and event.membership=='leave' and event.sender != config.matrix_config.owner:
            logger.info(f"Membership event in {room.display_name} ({room.room_id}) with {room.member_count} members by '{event.sender}' (I am OWNER)- leaving room as i don't want to be left alone!")
            await self.bot.room_leave(room.room_id)

    async def message_cb(self, room, event):
        if event.server_timestamp < self.bot.start_time:
            return
        # Ignore if asked to ignore
        # if should_ignore_event(event):
        #     if debug:
        #         logger.debug('Ignoring event!')
        #     return

        body = event.body
        # # Figure out the command
        # if not starts_with_command(body):
        #     return

        # if owners_only and not is_owner(event):
        #     logger.info(f"Ignoring {event.sender}, because they're not an owner")
        #     await send_text(room, "Sorry, only bot owner can run commands.", event=event)
        #     return
        jointime = None

        # HACK to ignore messages for some time after joining.
        if jointime:
            if (datetime.datetime.now() - jointime).seconds < 5:
                logger.info(f"Waiting for join delay, ignoring message: {body}")
                return
            jointime = None

        command = body.split().pop(0)

        command = re.sub(r'\W+', '', command)



        moduleobject = self.bot.active_modules.get(command) or self.bot.active_modules.get(self.bot.active_modules.get(command))
        logger.debug(self.bot.active_modules.get(command))
        logger.debug(moduleobject)

        if moduleobject is not None:
            if moduleobject.enabled:
                try:
                    await moduleobject.matrix_message(self.bot, room, event)
                except CommandRequiresAdmin:
                    await self.bot.send_text(room, f'Sorry, you need admin power level in this room to run that command.', event=event)
                except CommandRequiresOwner:
                    await self.bot.send_text(room, f'Sorry, only bot owner can run that command.', event=event)
                except Exception:
                    await self.bot.send_text(room, f'Module {command} experienced difficulty: {sys.exc_info()[0]} - see log for details', event=event)
                    logger.exception(f'unhandled exception in !{command}')
        else:
            logger.error(f"Unknown command: {command}")
            # TODO Make this configurable
            # await send_text(room,
            #                     f"Sorry. I don't know what to do. Execute !help to get a list of available commands.")



