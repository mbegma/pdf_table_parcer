# -*- coding:utf-8 -*-
# ----------------------------------------------------------------------------------------------------------------------
# Project Name: _template
# Name: base
# Filename: base.py
# Author: mbegma
# Create data: 14.07.2026
# Description: 
#            
# Copyright: (c) mbegma, 2026
# History: 
#        - 14.07.2026: start of development
# ----------------------------------------------------------------------------------------------------------------------
import sys
import logging
from src.config import config


class BaseClass:
    _ver = '0.0.0'
    def __init__(self, **kwargs):
        self.log = kwargs.get('class_logger', logging.getLogger(config.LOGGER_NAME))
        self.log.info(f"Hello, from {self.__class__.__name__} version: {self._ver}")
        self.error = None

    def set_info(self, message):
        if sys.version_info >= (3, 8):
            self.log.info(message, stacklevel=2)
        else:
            classname = self.__class__.__name__
            self.log.info(f'[{classname}] : {message}')
        # u_ags.add_message(data)

    def set_warning(self, message):
        if sys.version_info >= (3, 8):
            self.log.warning(message, stacklevel=2)
        else:
            classname = self.__class__.__name__
            self.log.warning(f'[{classname}] : {message}')
        # u_ags.add_message(data)

    def set_error(self, message):
        if sys.version_info >= (3, 8):
            self.log.error(message, stacklevel=2)
        else:
            classname = self.__class__.__name__
            self.log.error(f'[{classname}] : {message}')
        # u_ags.add_message(data)

    def get_last_error(self):
        return self.error

def main():
    pass


if __name__ == "__main__":
    main()
