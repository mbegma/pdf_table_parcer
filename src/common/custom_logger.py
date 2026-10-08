# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: custom_logger
# Author: mbegma
# Create data: 15.07.2020
# Description: Вспомогательный модуль, для реализации стандартного логирования библиотекой logging
# Copyright: (c) mbegma, 2024
# -----------------------------------------------------
import datetime
import logging
import logging.handlers
import random
import string
from os import path, sep, makedirs
from pathlib import Path
from typing import Union, Dict

LOG_HDL_FILE = 0
LOG_HDL_ROT_FILE = 1
LOG_HDL_CNSL = 2
LOG_FMT = {
    'standard': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    # 'detailed': '%(levelname)s - %(asctime)s - %(name)s | [%(filename)s:%(lineno)d]: %(message)s',
    'detailed': '%(levelname)s\t%(asctime)s.%(msecs)03d\t[%(name)s] - [%(filename)s:%(lineno)d -> %(funcName)s()]:\t%(message)s',
    'extra_1': '%(levelname)s | %(asctime)s.%(msecs)d [%(name)s (%(module)s:%(lineno)d)] >> %(message)s',
    'extra_2': '%(levelname)s | [%(asctime)s.%(msecs)03d]\t<%(module)s:%(lineno)d>\t%(message)s',
    'extra_3': '%(asctime)s | %(levelname)s | [%(filename)s:%(lineno)d -> %(funcName)s()] | %(message)s'
}


def random_string(size: int = 8, chars: str = string.ascii_lowercase) -> str:
    """
    Функция генерирует случайную строку длинной size из chars
    :param size: длинна сгенерированной строки;
    :param chars: последовательность символов из которых происходит генерация;
    :return: строка
    """
    return ''.join(random.choice(chars) for _ in range(size))


def get_logger_random_name(basename):
    """
    Функция генерирует имя со случайными символами в конце
    :param basename: основное имя
    :return: случайное имя в формате basename_XYZW
    """
    return f"{basename}_{random_string(4)}"


def get_log_filename(log_dir: str, log_sub_dir: Union[str, None]=None) -> str:
    """
    Функция генерирует случайное имя лог файлу
    :param log_dir: основная директория лог файлов
    :param log_sub_dir: поддиректория, если необходимо, если нет, то None
    :return: полный путь к логу файлу.
    """
    log_file_name = f"log_{datetime.datetime.today().strftime('%Y_%m_%d_%H_%M_%S')}_{random_string(4)}.log"
    if log_sub_dir is None:
        log_full_file_name = Path(log_dir) / Path(log_file_name)
        # log_full_file_name = f"{log_dir}{sep}{log_file_name}"
    else:
        log_full_file_name = Path(log_dir) / Path(log_sub_dir) / Path(log_file_name)
        # log_full_file_name = f"{log_dir}{sep}{log_sub_dir}{sep}{log_file_name}"
    return str(log_full_file_name)


def reset_logging():
    manager = logging.root.manager
    manager.disabled = logging.NOTSET
    for logger in manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(logging.NOTSET)
            logger.propagate = True
            logger.disabled = False
            logger.filters = []
            # logger.filters.clear()
            handlers = list(logger.handlers)
            # handlers = logger.handlers.copy()
            for handler in handlers:
                # Copied from `logging.shutdown`.
                try:
                    handler.acquire()
                    handler.flush()
                    handler.close()
                except (OSError, ValueError):
                    pass
                finally:
                    handler.release()
                logger.removeHandler(handler)


def create_logger_ext(logger_name: Union[str, None] = None,
                      logger_file_name: Union[str, None] = None,
                      logger_handler_type_dict: Union[Dict[int, Dict], None] = None) -> logging.Logger:
    """
    Функция создает логгер по параметрам в словаре.
    :param logger_name: Имя
    :param logger_file_name: название файла
    :param logger_handler_type_dict: {<тип>: {"level": logging.<уровень>, "формат": LOG_FMT[<значение>]}}
    :return:
    """
    reset_logging()
    log = logging.getLogger(logger_name) if logger_name is not None else logging.getLogger()
    log.setLevel(logging.DEBUG)

    if logger_handler_type_dict is None:
        return log

    _date_fmt = "%Y-%m-%d %H:%M:%S"

    for handle_type in logger_handler_type_dict:
        if handle_type == LOG_HDL_FILE:
            if logger_file_name is not None:
                if not Path(logger_file_name).parent.exists():
                    Path(logger_file_name).parent.mkdir(parents=True)
                _log_handler = logging.FileHandler(
                    filename=str(logger_file_name),
                    mode='a',
                    encoding='utf8'
                )
            else:
                _log_handler = None
        elif handle_type == LOG_HDL_ROT_FILE:
            if logger_file_name is not None:
                if not Path(logger_file_name).parent.exists():
                    Path(logger_file_name).parent.mkdir(parents=True)
                _log_handler = logging.handlers.RotatingFileHandler(
                    filename=str(logger_file_name),
                    maxBytes=10485760,  # 10MB
                    backupCount=5
                )
            else:
                _log_handler = None
        elif handle_type == LOG_HDL_CNSL:
            _log_handler = logging.StreamHandler()
        else:
            _log_handler = None
        if _log_handler is not None:
            _log_formatter = logging.Formatter(LOG_FMT.get(logger_handler_type_dict[handle_type]['format'],
                                                           LOG_FMT['standard']), _date_fmt)
            _log_handler.setFormatter(_log_formatter)
            _log_handler.setLevel(logger_handler_type_dict[handle_type]['level'])
            log.addHandler(_log_handler)
    return log





