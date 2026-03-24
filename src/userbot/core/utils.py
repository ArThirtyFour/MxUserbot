
# import re



# def starts_with_command(body):
#     """Checks if body starts with ! and has one or more letters after it"""
#     return re.match(r"^!\w.*", body) is not None

# def is_owner(event):
#     return event.sender in owners



# from loguru import logger




# def reload_modules(self):
#     for modulename in self.modules:
#         logger.info(f'Reloading {modulename} ..')
#         self.modules[modulename] = Loader().register_module(modulename)

#         load_settings(get_account_data())




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
