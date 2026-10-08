# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: pdf_table_parcer
# Name: __init__.py
# Filename: __init__.py
# Author: mbegma
# Create data: 15.05.2024
# Description: 
# Copyright: (c) mbegma, 2024-2026
# -----------------------------------------------------
from src.classes.error_classes import InputDataError, ProcessDataError
from src.classes.base import BaseClass
from src.classes.receipt_parser import ReceiptParser

__all__ = ["BaseClass", "ReceiptParser", "InputDataError", "ProcessDataError"]
