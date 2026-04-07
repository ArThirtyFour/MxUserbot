import traceback


from loguru import logger

from . import MXUserBot

if __name__ == "__main__":
    try:
        bot = MXUserBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Работа бота завершена пользователем (Ctrl+C).")
    except Exception:
        traceback.print_exc(file=sys.stderr)