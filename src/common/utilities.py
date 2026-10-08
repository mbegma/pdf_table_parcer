# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: utilities
# Filename: utilities.py
# Author: mbegma
# Create data: 09.02.2022
# Description: 
# Copyright: (c) mbegma, 2024
# -----------------------------------------------------
import random
import string
import math
from os import sep, path, makedirs
from uuid import uuid4
import logging



local_log = logging.getLogger(__name__)


def tab(n):
    return "\t" * n


def random_string(size=8, chars=string.ascii_lowercase):
    """
    Функция генерирует случайную строку длинной size из chars
    :param size: длинна сгенерированной строки
    :param chars: последовательность символов из которых происходит генерация
    :return: строка
    """
    return ''.join(random.choice(chars) for _ in range(size))


def get_guid_format(upper_format=True):
    """
    Функция формирует строку GUID со скобками
    :param upper_format: признак генерации в upper case
    :return: '{GUID}'
    """
    return f'{{{str(uuid4()).upper()}}}' if upper_format else f'{{{uuid4()}}}'

def save_to_file(file_name, data) -> bool:
    try:
        with open(file_name, 'w') as f:
            if isinstance(data, list):
                for item in data:
                    f.write('{0}\n'.format(item))
            else:
                f.write('{0}\n'.format(data))
        return True
    except Exception as e:
        logging.error(str(e.args))
        return False


def main():
    pass


if __name__ == "__main__":
    main()
