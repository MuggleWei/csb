import logging
import logging.handlers
import os


class LogHandle(object):
    """simple log handle"""

    @staticmethod
    def init_log(filename, console_level=logging.WARNING, file_level=logging.DEBUG, use_rotate=False, mode="a"):
        """
        init log
        :param filename: log output file path
        :param console_level: console log level
        :param file_level: file log level
        :param use_rotate: whether or not use rotating log
        :param mode: log file open mode
        :return:
        """
        folder = os.path.dirname(filename)
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        formatter = LogHandle.get_formatter()

        ch = LogHandle.get_console_handler(console_level)
        if use_rotate is True:
            fh = LogHandle.get_rotating_handler(level=file_level, filename=filename, mode=mode)
        else:
            fh = LogHandle.get_file_handler(level=file_level, filename=filename, mode=mode)

        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(ch)
        logger.addHandler(fh)

    @staticmethod
    def get_formatter():
        """
        log formatter
        """
        return logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(filename)s:%(lineno)s - %(message)s")

    @staticmethod
    def get_console_handler(level):
        """
        get console log handler
        :param level: log level
        :return: console log handler
        """
        handler = logging.StreamHandler()
        handler.setLevel(level)
        return handler

    @staticmethod
    def get_file_handler(level, filename, mode="a"):
        """
        get file log handler
        :param level: log level
        :param filename: log output file path
        :param mode: file open mode
        :return: file log handler
        """
        handler = logging.FileHandler(filename=filename, mode=mode)
        handler.setLevel(level)
        return handler

    @staticmethod
    def get_rotating_handler(level, filename, mode="a", maxBytes=20 * 1024 * 1024, backupCount=10):
        """
        get rotation log handler
        :param level: log level
        :param filename: log output file path
        :param mode: file open mode
        :param maxBytes: max size of single file
        :param backupCount: max number of file reserved
        :return: rotating file log handler
        """
        handler = logging.handlers.RotatingFileHandler(
            filename=filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount)
        handler.setLevel(level)
        return handler

    @staticmethod
    def log_level(str_level: str):
        """
        convert string to log level enum
        :param str_level: log level string
        :return: log level enum
        """
        if str_level.lower() == "debug":
            return logging.DEBUG
        elif str_level.lower() == "info":
            return logging.INFO
        elif str_level.lower() == "warning":
            return logging.WARNING
        elif str_level.lower() == "error":
            return logging.ERROR
        elif str_level.lower() == "fatal":
            return logging.FATAL
        else:
            return logging.INFO
