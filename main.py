# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: pdf_table_parcer
# Name: main
# Filename: main.py
# Author: mbegma
# Create data: 16.12.2024
# Description: Парсер и загрузчик квитанций ЕПД МосОблЕИРЦ в SQLite
# Copyright: (c) mbegma, 2024-2026
# -----------------------------------------------------

import sys
from pathlib import Path

# Добавляем корневую директорию и папку src в sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
for p in (PROJECT_ROOT, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import logging
from typing import Optional, List

from src.config import config
from src.common import create_logger_ext, get_log_filename
from src.common import LOG_HDL_CNSL, LOG_HDL_FILE
from src.classes import BaseClass, ReceiptParser
from src.db.database import ReceiptsDB

log = create_logger_ext(
    logger_name=config.LOGGER_NAME,
    logger_file_name=get_log_filename(config.LOG_DIR),
    logger_handler_type_dict={
        LOG_HDL_FILE: {"level": logging.DEBUG, "format": "extra_1"},
        LOG_HDL_CNSL: {"level": logging.INFO, "format": "detailed"},
    },
)


class MainClass(BaseClass):
    _ver = "1.0.0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pdf_file = kwargs.get("pdf_file", None)
        self.pdf_dir = Path(kwargs.get("pdf_dir", config.PDF_DIR))
        self.db = ReceiptsDB(db_path=kwargs.get("db_path", config.DB_PATH))
        self.parser = ReceiptParser(class_logger=self.log)

    def execute(self) -> None:
        self.set_info("Starting receipt parsing and database ingestion...")

        # Определяем список файлов для обработки
        pdf_paths: List[Path] = []
        if self.pdf_file:
            target_path = Path(self.pdf_file)
            if target_path.exists():
                pdf_paths = [target_path]
            else:
                self.set_error(f"Specified PDF file does not exist: {self.pdf_file}")
                return
        else:
            if self.pdf_dir.exists():
                pdf_paths = sorted(list(self.pdf_dir.glob("*.pdf")))
            else:
                self.set_error(f"PDF directory does not exist: {self.pdf_dir}")
                return

        if not pdf_paths:
            self.set_warning("No PDF files found to process.")
            return

        self.set_info(f"Found {len(pdf_paths)} PDF receipt(s) to process.")

        processed_count = 0
        error_count = 0

        for file_path in pdf_paths:
            try:
                # 1. Извлекаем данные из квитанции
                receipt_data = self.parser.parse_file(str(file_path))

                # 2. Сохраняем данные в БД SQLite
                receipt_id = self.db.save_receipt(receipt_data)
                self.set_info(
                    f"[{file_path.name}] -> Saved receipt ID {receipt_id} for "
                    f"account {receipt_data['account_number']} ({receipt_data['period']}) "
                    f"with {len(receipt_data['services'])} services."
                )
                processed_count += 1
            except Exception as e:
                self.set_error(f"Failed to process {file_path.name}: {e}")
                self.log.exception(e)
                error_count += 1

        # Вывод статистики
        summary = self.db.get_summary()
        self.set_info(
            f"Finished processing! Success: {processed_count}, Errors: {error_count}.\n"
            f"Database summary: {summary['accounts_count']} account(s), "
            f"{summary['receipts_count']} receipt(s), {summary['charges_count']} charges records.\n"
            f"Available periods: {', '.join(summary['periods'])}"
        )


def main():
    log.info(f"Main directory: {config.MAIN_DIR}")
    log.info(f"Database path:  {config.DB_PATH}")
    log.info(f"PDF directory:  {config.PDF_DIR}")

    # Запуск обработки всех квитанций в папке data/pdf
    processor = MainClass(class_logger=log)
    processor.execute()


if __name__ == "__main__":
    main()
