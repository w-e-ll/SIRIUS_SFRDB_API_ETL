#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import csv
import glob
import logging

import oracledb

from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from bics_sirius_sfrdb_api.lib.uploader_db import OracleClient


logger = logging.getLogger('uploader_utils')


OWNER = "SFRDB_SCHEMA"

TABLES = {
    "accounts":  ("T_ACCOUNT_INFORMATION", [
        "ACCOUNT_ID", "COUNTRY_ID", "COUNTRY_ISO3", "COUNTRY_NAME",
        "SHORT_CODE", "NAME", "LEGAL_NAME", "COMMERCIAL_NAME", "COMMERCIAL_REGION",
        "CARRIER_ID", "NEW_CARRIER_ID", "SAP_CODE", "START_DATE", "END_DATE",  # "END_DATE", it is always NULL? "START_DATE" - sometimes empty and sometimes not? need to check whY?
        "ULTIMATE_PARENT_ACCOUNT_ID", "PARENT_ACCOUNT_ID", "IDENTIFIER_NUMBER",
        "TRADE_REGISTER_NUMBER", "VAT_NUMBER", "HQ_STREET", "HQ_STREET_NUMBER",
        "HQ_CITY", "HQ_POSTAL_CODE", "HQ_COUNTRY_ID", "HQ_COUNTRY_ISO3",
        "HQ_COUNTRY_NAME", "HQ_STATE", "HQ_RESIDENCE", "HQ_FLOOR",
        "ACCOUNT_TYPE_COMMERCIAL_CUSTOMER", "ACCOUNT_TYPE_COMMERCIAL_SUPPLIER",
        "ACCOUNT_TYPE_PARTNER", "ACCOUNT_TYPE_ELIGIBLE_CUSTOMER_PROSPECTS",
        "ACCOUNT_TYPE_CAPACITY_BUYING_SUPPLIER", "ACCOUNT_TYPE_NUMBERING_PLAN",
        "ACCOUNT_TYPE_EASY_CONNECT", "COMMERCIAL_TIER", "COMMERCIAL_SEGMENT",
        "COMMERCIAL_SUBSEGMENT", "SRC_EXTRACTED_AT", "SRC_BATCH_ID"
    ]),
    "cities":    ("T_CITY", [
        "COUNTRY_ID", "CITY_ID", "CITY_ABBREVIATION", "CITY_NAME", "NORMALIZED_NAME",
        "CITY_ALIAS", "SRC_EXTRACTED_AT", "SRC_BATCH_ID",
    ]),
    "countries": ("T_COUNTRY", [
        "COUNTRY_ID", "COUNTRY_ISO2", "COUNTRY_ISO3", "NAME",
        "GEOGRAPHICAL_REGION", "COMMERCIAL_REGION", "PHONE_CODE", "MCC",
        "SRC_EXTRACTED_AT", "SRC_BATCH_ID"
    ]),
}

ACCOUNTS_RENAME = {
    "account_id": "ACCOUNT_ID",
    "country_id": "COUNTRY_ID",
    "country_iso3": "COUNTRY_ISO3",
    "country_name": "COUNTRY_NAME",
    "short_code": "SHORT_CODE",
    "name": "NAME",
    "legal_name": "LEGAL_NAME",
    "commercial_name": "COMMERCIAL_NAME",
    "commercial_region": "COMMERCIAL_REGION",
    "carrier_id": "CARRIER_ID",
    "new_carrier_id": "NEW_CARRIER_ID",
    "sap_code": "SAP_CODE",
    "start_date": "START_DATE",
    "end_date": "END_DATE",
    "ultimate_parent_account_id": "ULTIMATE_PARENT_ACCOUNT_ID",
    "parent_account_id": "PARENT_ACCOUNT_ID",
    "identifier_number": "IDENTIFIER_NUMBER",
    "trade_register_number": "TRADE_REGISTER_NUMBER",
    "vat_number": "VAT_NUMBER",
    "hq_street": "HQ_STREET",
    "hq_street_number": "HQ_STREET_NUMBER",
    "hq_city": "HQ_CITY",
    "hq_postal_code": "HQ_POSTAL_CODE",
    "hq_country_id": "HQ_COUNTRY_ID",
    "hq_country_iso3": "HQ_COUNTRY_ISO3",
    "hq_country_name": "HQ_COUNTRY_NAME",
    "hq_state": "HQ_STATE",
    "hq_residence": "HQ_RESIDENCE",
    "hq_floor": "HQ_FLOOR",
    "account_type_commercial_customer": "ACCOUNT_TYPE_COMMERCIAL_CUSTOMER",
    "account_type_commercial_supplier": "ACCOUNT_TYPE_COMMERCIAL_SUPPLIER",
    "account_type_partner": "ACCOUNT_TYPE_PARTNER",
    "account_type_eligible_customer_prospects": "ACCOUNT_TYPE_ELIGIBLE_CUSTOMER_PROSPECTS",
    "account_type_capacity_buying_supplier": "ACCOUNT_TYPE_CAPACITY_BUYING_SUPPLIER",
    "account_type_numbering_plan": "ACCOUNT_TYPE_NUMBERING_PLAN",
    "account_type_easy_connect": "ACCOUNT_TYPE_EASY_CONNECT",
    "commercial_tier": "COMMERCIAL_TIER",
    "commercial_segment": "COMMERCIAL_SEGMENT",
    "commercial_subsegment": "COMMERCIAL_SUBSEGMENT",
}

CITIES_RENAME = {
    "country_id": "COUNTRY_ID",
    "city_id": "CITY_ID",
    "city_abbreviation": "CITY_ABBREVIATION",
    "city_name": "CITY_NAME",
    "normalized_name": "NORMALIZED_NAME",
    "city_alias": "CITY_ALIAS",
}

COUNTRIES_RENAME = {
    "country_id": "COUNTRY_ID",
    "country_iso2": "COUNTRY_ISO2",
    "country_iso3": "COUNTRY_ISO3",
    "name": "NAME",
    "geographical_region": "GEOGRAPHICAL_REGION",
    "commercial_region": "COMMERCIAL_REGION",
    "phone_code": "PHONE_CODE",
    "mcc": "MCC",
    "src_extracted_at": "SRC_EXTRACTED_AT",
    "src_batch_id": "SRC_BATCH_ID",
}

RENAME = {"accounts": ACCOUNTS_RENAME, "cities": CITIES_RENAME, "countries": COUNTRIES_RENAME}


def newest(pattern: str) -> Optional[str]:
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load_csv(path: str) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append({k: (v) for k, v in r.items()})
        return rows
    except Exception as e:
        logger.exception("Failed reading CSV %s: %s", path, e)
        raise


def to_oracle_datetime(v: str | None):
    if not v:
        return None
    s = str(v).strip()
    # cx_Oracle/oracledb understands datetime objects; normalize ISO strings
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(s)   # handles 'YYYY-MM-DD' and '...T...+00:00'
    except ValueError:
        # Fallbacks for common CSV formats
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s[:10], fmt)
            except ValueError:
                pass
        return None  # or raise if you want to fail-hard


def y_or_n(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    vv = str(v).strip().upper()
    if vv in ("Y", "N"):
        return vv
    if vv in ("TRUE", "1"):
        return "Y"
    if vv in ("FALSE", "0"):
        return "N"
    return None


def transform(records: List[Dict[str, object]], domain: str, batch_id: str) -> Tuple[List[str], List[Tuple]]:
    table, cols = TABLES[domain]
    rename = RENAME[domain]

    out_rows: List[Tuple] = []
    now_ts = datetime.now(timezone.utc)

    for rec in records:
        row: Dict[str, object] = {}

        # rename
        for src_key, db_col in rename.items():
            val = rec.get(src_key)
            if domain == "accounts" and db_col in ("START_DATE", "END_DATE"):
                val = to_oracle_datetime(val)
            if domain == "accounts" and db_col.startswith("ACCOUNT_TYPE_"):
                val = y_or_n(val)
            row[db_col] = val

        # ensure all target cols present
        for c in cols:
            if c not in row:
                row[c] = None

        row["SRC_EXTRACTED_AT"] = now_ts
        row["SRC_BATCH_ID"] = batch_id

        out_rows.append(tuple(row[c] for c in cols))

    return cols, out_rows


def validate_against_db(ora: OracleClient, table: str, cols: List[str]):
    if not ora.table_exists(OWNER, table):
        raise RuntimeError(f"Table {OWNER}.{table} does not exist")
    db_cols = [c.upper() for c in ora.get_columns(OWNER, table)]
    missing = [c for c in cols if c.upper() not in db_cols]
    if missing:
        raise RuntimeError(f"Target table {OWNER}.{table} missing columns: {missing}")


def parse_batch_id_from_filename(path: str) -> str:
    base = os.path.basename(path)
    try:
        for prefix in ("accounts_", "cities_", "countries_"):
            if base.startswith(prefix):
                return os.path.splitext(base[len(prefix):])[0]
        return os.path.splitext(base)[0]
    except Exception:
        return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")


def discover_input_files_from_folder(folder: str) -> Dict[str, str]:
    """
    Given a folder like var/data/csv/2025-01-12/, find:
        accounts_*.csv
        cities_*.csv
        countries_*.csv
    """
    files: Dict[str, str] = {}

    def pick_one(domain):
        pattern = os.path.join(folder, f"{domain}_{os.path.basename(folder)}.csv")
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
        return None

    acc = pick_one("accounts")
    city = pick_one("cities")
    country = pick_one("countries")

    if acc:
        files["accounts"] = acc
    if city:
        files["cities"] = city
    if country:
        files["countries"] = country

    if not files:
        raise FileNotFoundError(f"No domain CSV files found in folder {folder}")

    return files


def discover_latest_date_folder(base_dir: str) -> str:
    """
    Finds the newest date folder under base_dir.
    base_dir typically = var/data/csv/
    """
    if not os.path.isdir(base_dir):
        raise FileNotFoundError(f"Input directory does not exist: {base_dir}")

    candidates = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
    ]

    if not candidates:
        raise FileNotFoundError(f"No dated folders found under {base_dir}")

    # keep only valid YYYY-MM-DD
    valid = []
    for d in candidates:
        try:
            datetime.strptime(d, "%Y-%m-%d")
            valid.append(d)
        except ValueError:
            pass

    if not valid:
        raise FileNotFoundError(f"No valid date folders found under {base_dir}")

    latest = max(valid)
    return os.path.join(base_dir, latest)


def load_one_table(ora: OracleClient, domain: str, path: str, truncate: bool, batch_size: int):
    table, _ = TABLES[domain]
    logger.info("[%s] [%s] Source file: %s", ora.cfg.name, table, path)

    records = load_csv(path)
    logger.info("[%s] [%s] Read %d rows", ora.cfg.name, table, len(records))

    batch_id = parse_batch_id_from_filename(path)
    cols, rows = transform(records, domain, batch_id)

    validate_against_db(ora, table, cols)

    if truncate:
        ora.truncate(OWNER, table)

    total = len(rows)
    start = 0
    while start < total:
        end = min(start + batch_size, total)
        chunk = rows[start:end]
        try:
            ora.insert_many(OWNER, table, cols, chunk)
        except oracledb.DatabaseError as e:
            logger.exception("[%s] [%s] Insert failed at rows %d..%d: %s", ora.cfg.name, table, start, end, e)
            raise
        start = end

    logger.info("[%s] [%s] Done. Inserted %d rows.", ora.cfg.name, table, total)
