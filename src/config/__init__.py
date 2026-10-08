# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name:
# Name: __init__.py
# Filename: __init__.py
# Author: mbegma
# Create data: 17.12.2024
# Description: idea from https://github.com/Afaneor/fastapi-docker-boilerplate/tree/main/%7B%7Bcookiecutter.project_name%7D%7D/app/config
# Copyright: (c) mbegma, 2024
# History: 
#        - 17.12.2024: start of development
# -----------------------------------------------------
from src.config.config import Config

def get_settings() -> Config:
    return Config()


config = get_settings()