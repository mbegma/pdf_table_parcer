# -*- coding:utf-8 -*-
# -----------------------------------------------------
# Project Name: pdf_table_parcer
# Name: receipt_parser
# Filename: receipt_parser.py
# Author: mbegma
# Description: PDF parser for MosOblEIRC receipts (ЕПД)
# -----------------------------------------------------

import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import pdfplumber

from src.classes.base import BaseClass


MONTHS_RU = {
    "январь": 1, "января": 1,
    "февраль": 2, "февраля": 2,
    "март": 3, "марта": 3,
    "апрель": 4, "апреля": 4,
    "май": 5, "мая": 5,
    "июнь": 6, "июня": 6,
    "июль": 7, "июля": 7,
    "август": 8, "августа": 8,
    "сентябрь": 9, "сентября": 9,
    "октябрь": 10, "октября": 10,
    "ноябрь": 11, "ноября": 11,
    "декабрь": 12, "декабря": 12,
}


def parse_float(val: Any) -> float:
    """Безопасное преобразование строкового числа из квитанции в float."""
    if val is None:
        return 0.0
    s = str(val).replace(" ", "").replace("\xa0", "").replace(",", ".")
    match = re.search(r"[-+]?\d*\.?\d+", s)
    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return 0.0
    return 0.0


class ReceiptParser(BaseClass):
    _ver = "1.0.0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def parse_file(self, pdf_path: str) -> Dict[str, Any]:
        """
        Извлекает данные из одной PDF-квитанции:
        - Лицевой счет, период, ФИО, адрес, общую сумму (без учета добровольного страхования)
        - Список начислений по жилищным, коммунальным и иным услугам.
        """
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.set_info(f"Parsing receipt file: {path.name}")

        with pdfplumber.open(path) as pdf:
            if not pdf.pages:
                raise ValueError(f"Empty PDF document: {pdf_path}")

            page = pdf.pages[0]
            page_text = page.extract_text() or ""

            # 1. Извлечение метаданных квитанции
            account_number = self._extract_account_number(page_text)
            period_name, year, month_num = self._extract_period(page_text)
            payer_name = self._extract_payer_name(page_text)
            address = self._extract_address(page_text)

            period_date = f"{year:04d}-{month_num:02d}-01"
            period_str = f"{period_name} {year}"

            # 2. Извлечение таблицы начислений (РАСЧЕТ РАЗМЕРА ПЛАТЫ...)
            services, total_to_pay = self._extract_charges_table(page)

            # Если итоговая сумма не найдена в таблице, ищем в тексте шапки
            if total_to_pay == 0.0:
                total_to_pay = self._extract_total_from_text(page_text)

            result = {
                "source_file": path.name,
                "account_number": account_number,
                "period": period_str,
                "period_date": period_date,
                "year": year,
                "month": month_num,
                "payer_name": payer_name,
                "address": address,
                "total_to_pay": total_to_pay,
                "services": services,
            }

            self.set_info(
                f"Successfully parsed {path.name}: "
                f"Account={account_number}, Period={period_str}, "
                f"Total={total_to_pay:.2f} руб., Services count={len(services)}"
            )
            return result

    def _extract_account_number(self, text: str) -> str:
        match = re.search(r"Лицевой\s+счет:\s*([0-9\s\-]+?)(?:Просим|ФИО|\n|$)", text)
        if match:
            return match.group(1).replace(" ", "").strip()
        # Альтернативный поиск по шаблону номера счета (напр. 32546-580 или 32546580 в начале документа)
        first_num = re.search(r"(\d{5,8})", text)
        return first_num.group(1) if first_num else "UNKNOWN"

    def _extract_period(self, text: str):
        match = re.search(
            r"ЖИЛИЩНО-КОММУНАЛЬНЫЕ И ИНЫЕ УСЛУГИ ЗА\s+([а-яА-ЯёЁ]+)\s+(\d{4})",
            text,
            re.IGNORECASE,
        )
        if match:
            month_str = match.group(1).lower().strip()
            year = int(match.group(2))
            month_num = MONTHS_RU.get(month_str, 1)
            return month_str, year, month_num

        # Запасной вариант поиска периода в заголовке таблицы
        match_tbl = re.search(r"УСЛУГИ ЗА\s+([а-яА-ЯёЁ]+)\s+(\d{4})", text, re.IGNORECASE)
        if match_tbl:
            month_str = match_tbl.group(1).lower().strip()
            year = int(match_tbl.group(2))
            month_num = MONTHS_RU.get(month_str, 1)
            return month_str, year, month_num

        return "неизвестно", 2026, 1

    def _extract_payer_name(self, text: str) -> Optional[str]:
        match = re.search(r"ФИО:\s*([^\n]+)", text)
        return match.group(1).strip() if match else None

    def _extract_address(self, text: str) -> Optional[str]:
        match = re.search(r"Адрес:\s*([^\n]+)", text)
        return match.group(1).strip() if match else None

    def _extract_total_from_text(self, text: str) -> float:
        match = re.search(
            r"БЕЗ\s+УЧЕТА\s+ДОБРОВОЛЬНОГО\s+СТРАХОВАНИЯ\s*\n?\s*(\d[\d\s]*\s*руб\.\s*\d+\s*коп\.)",
            text,
            re.IGNORECASE,
        )
        if match:
            return parse_float(match.group(1))
        return 0.0

    def _extract_charges_table(self, page) -> (List[Dict[str, Any]], float):
        """Парсинг строк начислений с явной калибровкой вертикальных линий."""
        # Область таблицы начислений (обычно y от 215 до 460)
        crop = page.crop((28.0, 215.0, 547.0, 460.0))
        vlines = sorted(list(set([round(l["x0"], 1) for l in crop.lines if l["width"] < 1])))

        # В квитанциях МосОблЕИРЦ бывает 9 вертикальных линий (8 колонок, без перерасчетов)
        # либо 10 линий (9 колонок, колонка перерасчетов включена)
        table = crop.extract_table(
            table_settings={
                "explicit_vertical_lines": vlines,
                "vertical_strategy": "explicit",
                "horizontal_strategy": "lines",
            }
        )

        if not table:
            return [], 0.0

        has_recalculation = len(vlines) == 10
        current_category = "Жилищные услуги"
        services = []
        total_without_insurance = 0.0

        for row in table:
            row_str = "".join([str(c or "") for c in row])
            norm = re.sub(r"\s+", "", row_str).lower()

            # Смена категории
            if "жилищн" in norm and "начислен" in norm:
                current_category = "Жилищные услуги"
                continue
            elif "коммунал" in norm and "начислен" in norm:
                current_category = "Коммунальные услуги"
                continue
            elif "иные" in norm and "начислен" in norm:
                current_category = "Иные услуги"
                continue

            # Игнорируем добровольное страхование
            if "добровольноестрахование" in norm:
                continue

            # Извлечение итоговой суммы без добровольного страхования
            if ("всегоза" in norm or "итогокоплате" in norm) and "безучетадобровольногострахования" in norm:
                total_without_insurance = parse_float(row[-1])
                continue

            # Пропуск строк заголовков и служебных итогов
            if (
                "видыуслуг" in norm
                or "всегоза" in norm
                or "итого" in norm
                or "расчетразмера" in norm
            ):
                continue

            service_name = (row[0] or "").replace("\n", " ").strip()
            service_name = re.sub(r"\s+", " ", service_name)
            if not service_name:
                continue

            volume = parse_float(row[1])
            unit = (row[2] or "").replace("\n", " ").strip()
            tariff = parse_float(row[3])
            billed_amount = parse_float(row[4])

            if has_recalculation:
                recalculation = parse_float(row[5])
                debt_or_overpayment = parse_float(row[6])
                paid_amount = parse_float(row[7])
                total_amount = parse_float(row[8])
            else:
                recalculation = 0.0
                debt_or_overpayment = parse_float(row[5])
                paid_amount = parse_float(row[6])
                total_amount = parse_float(row[7])

            services.append({
                "category": current_category,
                "name": service_name,
                "volume": volume,
                "unit": unit,
                "tariff": tariff,
                "billed_amount": billed_amount,
                "recalculation": recalculation,
                "debt_or_overpayment": debt_or_overpayment,
                "paid_amount": paid_amount,
                "total_amount": total_amount,
            })

        return services, total_without_insurance
