# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: error_classes
# Author: mbegma
# Create data: 16.12.2024
# Description: 
# Copyright: (c) mbegma, 2024
# -----------------------------------------------------


class Error(Exception):
    """Базовый класс для всех исключений в этом модуле."""
    pass


class InputDataError(Error):
    """Исключение порождается при некорректных или отсутствующих входных данных.
     Атрибуты:
        message -- описание ошибки
    """
    def __init__(self, message):
        if message[:1] == '!':
            self.message = message
        else:
            self.message = '!InputDataError: {0}'.format(message)


class ProcessDataError(Error):
    """Исключение порождается при отсутствии расчетных данных или ошибках в процессе выполнения.
     Атрибуты:
        message -- описание ошибки
    """
    def __init__(self, message):
        if message[:1] == '!':
            self.message = message
        else:
            self.message = '!ProcessDataError: {0}'.format(message)
