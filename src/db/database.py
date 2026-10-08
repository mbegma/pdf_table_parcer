# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: pdf_table_parcer
# Name: database
# Filename: database.py
# Author: mbegma
# Description: SQLite database manager for storing digitized receipts and service charges
# -----------------------------------------------------

import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from src.config import config

logger = logging.getLogger(config.LOGGER_NAME)


class ReceiptsDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_schema(self) -> None:
        """Создает таблицы и индексы в SQLite, если они еще не существуют."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Таблица лицевых счетов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_number TEXT PRIMARY KEY,
                    payer_name TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Таблица квитанций / периодов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_number TEXT NOT NULL,
                    period TEXT NOT NULL,
                    period_date TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    month INTEGER NOT NULL,
                    total_to_pay REAL,
                    source_file TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(account_number, year, month),
                    FOREIGN KEY(account_number) REFERENCES accounts(account_number) ON DELETE CASCADE
                );
            """)

            # Таблица начислений по ЖКХ и иным услугам
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS service_charges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    account_number TEXT NOT NULL,
                    service_category TEXT NOT NULL,
                    service_name TEXT NOT NULL,
                    volume REAL DEFAULT 0.0,
                    unit TEXT,
                    tariff REAL DEFAULT 0.0,
                    billed_amount REAL DEFAULT 0.0,
                    recalculation REAL DEFAULT 0.0,
                    debt_or_overpayment REAL DEFAULT 0.0,
                    paid_amount REAL DEFAULT 0.0,
                    total_amount REAL DEFAULT 0.0,
                    FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE,
                    FOREIGN KEY(account_number) REFERENCES accounts(account_number) ON DELETE CASCADE
                );
            """)

            # Индексы для быстрого поиска и аналитических выборок / графиков
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_receipts_acc_date 
                ON receipts(account_number, period_date);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_charges_receipt_id 
                ON service_charges(receipt_id);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_charges_acc_srv 
                ON service_charges(account_number, service_name);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_charges_category 
                ON service_charges(service_category);
            """)

            conn.commit()
            logger.debug(f"Database schema initialized at {self.db_path}")

    def save_receipt(self, receipt_data: Dict[str, Any]) -> int:
        """
        Сохраняет квитанцию и начисления в БД в единой транзакции (идемпотентно).
        Возвращает id сохраненной квитанции.
        """
        account_number = receipt_data["account_number"]
        payer_name = receipt_data.get("payer_name")
        address = receipt_data.get("address")
        period = receipt_data["period"]
        period_date = receipt_data["period_date"]
        year = receipt_data["year"]
        month = receipt_data["month"]
        total_to_pay = receipt_data.get("total_to_pay", 0.0)
        source_file = receipt_data.get("source_file", "")
        services = receipt_data.get("services", [])

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Сохраняем/обновляем лицевой счет
            cursor.execute("""
                INSERT INTO accounts (account_number, payer_name, address)
                VALUES (?, ?, ?)
                ON CONFLICT(account_number) DO UPDATE SET
                    payer_name = COALESCE(excluded.payer_name, accounts.payer_name),
                    address = COALESCE(excluded.address, accounts.address);
            """, (account_number, payer_name, address))

            # 2. Проверяем, существует ли уже квитанция за этот период
            cursor.execute("""
                SELECT id FROM receipts 
                WHERE account_number = ? AND year = ? AND month = ?;
            """, (account_number, year, month))
            row = cursor.fetchone()

            if row:
                receipt_id = row["id"]
                # Обновляем метаданные квитанции
                cursor.execute("""
                    UPDATE receipts SET
                        period = ?,
                        period_date = ?,
                        total_to_pay = ?,
                        source_file = ?
                    WHERE id = ?;
                """, (period, period_date, total_to_pay, source_file, receipt_id))
                # Удаляем старые начисления для чистой перезаписи
                cursor.execute("DELETE FROM service_charges WHERE receipt_id = ?;", (receipt_id,))
                logger.info(f"Overwriting existing receipt id={receipt_id} for {account_number} ({period})")
            else:
                cursor.execute("""
                    INSERT INTO receipts (
                        account_number, period, period_date, year, month, total_to_pay, source_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (account_number, period, period_date, year, month, total_to_pay, source_file))
                receipt_id = cursor.lastrowid
                logger.info(f"Inserted new receipt id={receipt_id} for {account_number} ({period})")

            # 3. Вставляем строки начислений
            charge_rows = []
            for s in services:
                charge_rows.append((
                    receipt_id,
                    account_number,
                    s["category"],
                    s["name"],
                    s.get("volume", 0.0),
                    s.get("unit", ""),
                    s.get("tariff", 0.0),
                    s.get("billed_amount", 0.0),
                    s.get("recalculation", 0.0),
                    s.get("debt_or_overpayment", 0.0),
                    s.get("paid_amount", 0.0),
                    s.get("total_amount", 0.0),
                ))

            if charge_rows:
                cursor.executemany("""
                    INSERT INTO service_charges (
                        receipt_id, account_number, service_category, service_name,
                        volume, unit, tariff, billed_amount, recalculation,
                        debt_or_overpayment, paid_amount, total_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, charge_rows)

            conn.commit()
            return receipt_id

    def get_summary(self) -> Dict[str, Any]:
        """Возвращает краткую статистику по сохраненным данным."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            acc_count = cursor.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
            rec_count = cursor.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
            chg_count = cursor.execute("SELECT COUNT(*) FROM service_charges").fetchone()[0]
            periods = [r[0] for r in cursor.execute("SELECT DISTINCT period_date FROM receipts ORDER BY period_date").fetchall()]
            return {
                "accounts_count": acc_count,
                "receipts_count": rec_count,
                "charges_count": chg_count,
                "periods": periods
            }
