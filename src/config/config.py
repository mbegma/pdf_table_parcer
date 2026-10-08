# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: pdf_table_parcer
# Name: config
# Filename: config.py
# Author: mbegma
# Create data: 09.02.2022
# Description: 
# Copyright: (c) Дата+, 2022 - 2026
# -----------------------------------------------------
from os import sep, path, makedirs
import configparser
from pathlib import Path
import json

ROOT_DIR = Path(__file__).parents[2]

config_file = ROOT_DIR / "settings" / "settings.ini"

config = configparser.ConfigParser()
if len(config.read(config_file, encoding="utf-8")) == 0:
    raise Exception(f"ini file is not present in script directory")


def create_dir(directory):
    if not Path(directory).exists():
        Path(directory).mkdir(parents=True)


class Config:
    # region CONST
    IS_DEBUG = config.getboolean("TOOL", "is_debug")
    IS_LOGGING = config.getboolean("TOOL", "is_logging")
    LOGGER_NAME = "app"
    # endregion

    # region DIR
    MAIN_DIR = config["WORKSPACE"]["main_dir"]
    create_dir(MAIN_DIR)

    LOG_DIR = config["WORKSPACE"]["log_dir_name"]
    create_dir(LOG_DIR)

    PDF_DIR = config.get("WORKSPACE", "pdf_dir", fallback=str(ROOT_DIR / "data" / "pdf"))
    create_dir(PDF_DIR)
    # endregion

    # region DB CONNECT
    DB_PATH = config.get("DB_CONNECT", "db_path", fallback=str(ROOT_DIR / "db" / "receipts.db"))
    create_dir(Path(DB_PATH).parent)

    IS_USE_DIRECTORY = config.getboolean("DB_CONNECT", "is_use_dir")
    if IS_USE_DIRECTORY:
        DB_CONNECTION_NAME = f'{config["DB_CONNECT"]["connection_dir"]}{sep}{config["DB_CONNECT"]["connection_name"]}'
    else:
        DB_CONNECTION_NAME = f'{config["DB_CONNECT"]["connection_name"]}'
    DB_SCHEMA_NAME = config["DB_CONNECT"]["schema_name"]
    # endregion

    def get_full_name(self, name, is_use_schema=True) -> str:
        prefix = Path(self.MAIN_DIR) / Path(self.DB_CONNECTION_NAME)
        if is_use_schema:
            postfix = Path(f"{self.DB_SCHEMA_NAME}.{name}")
        else:
            postfix = Path(name)
        return str(prefix / postfix)
