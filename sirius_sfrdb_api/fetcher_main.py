#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import uuid
import urllib3

from datetime import datetime, timezone

from dotenv import load_dotenv

from bics_sirius_sfrdb_api.lib.fetcher_utils import cleaning_saved_today_records, write_csv
from bics_sirius_sfrdb_api.lib.shared_logger import setup_logger
from bics_sirius_sfrdb_api.lib.fetcher_flats import flat_account, flat_city, flat_country
from bics_sirius_sfrdb_api.lib.fetcher_config import load_yaml_config
from bics_sirius_sfrdb_api.lib.fetcher_to_csv import write_csv
from bics_sirius_sfrdb_api.lib.fetcher_token_manager import TokenManager, auth_get


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

ENV = os.getenv("SFRDB_ENV", "ITT").upper()
PAGE_SIZE = max(1, min(int(os.getenv("PAGE_SIZE", "200")), 1000))
ONLY_ACTIVE = os.getenv("ONLY_ACTIVE", "false").lower() == "true"
CONFIG_ENV = {
    "ITT":  {"token_url": "https://idmuat-int-auth.dmzint.bics/auth/realms/gentes-itt/protocol/openid-connect/token",
             "api_base":  "https://sfrdb-itt.bics.bc/api/v1"},
    "UAT":  {"token_url": "https://idmuat-int-auth.dmzint.bics/auth/realms/gentes-uat/protocol/openid-connect/token",
             "api_base":  "https://sfrdb-uat.bics.bc/api/v1"},
    "PROD": {"token_url": "https://idm-int-auth.dmzint.bics/auth/realms/gentes/protocol/openid-connect/token",
             "api_base":  "https://sfrdb.bics.bc/api/v1"},
}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_entity(name, api_url, flattener, logger, tm):
    """Fetch paginated entity from SFRDB."""
    logger.info(f"Fetching [{name}] from {api_url}")

    batch_id = str(uuid.uuid4())
    extracted_at = now_iso()

    all_rows = []
    page = 1
    try:
        while True:
            params = {"page": page, "size": PAGE_SIZE}
            if ONLY_ACTIVE:
                params["onlyActive"] = "active"

            r = auth_get(tm, api_url, params=params)
            data = r.json()

            recs, meta = data.get("records") or [], data.get("_metadata") or {}
            page_count = meta.get("pageCount")

            for rec in recs:
                all_rows.append(flattener(rec, batch_id, extracted_at))

            if not recs:
                break

            if page_count is not None and page >= page_count:
                break

            page += 1
    except Exception as e:
        logger.error(f"Failed to fetch for {flattener}: {e}")

    logger.info(f"Fetched {len(all_rows)} rows for {name}.\nExtracted At: {extracted_at}")
    return all_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", required=True)
    args = parser.parse_args()

    cfg = load_yaml_config(args.config_dir)
    api_env_endpoints = CONFIG_ENV[ENV]

    logfile = os.path.join(cfg.log_dir, "fetcher.log")
    logger = setup_logger(logfile)

    tm = TokenManager(api_env_endpoints)

    logger.info(f"=== SFRDB Fetcher started (ENV={ENV}) ===")

    today = datetime.now().strftime("%Y-%m-%d")
    input_dir = os.path.join(cfg.input_dir, today)
    os.makedirs(input_dir, exist_ok=True)

    cleaning_saved_today_records(input_dir)

    # Entity endpoints
    api_accounts = f"{api_env_endpoints['api_base']}/accounts"
    api_cities = f"{api_env_endpoints['api_base']}/cities"
    api_countries = f"{api_env_endpoints['api_base']}/countries"

    # Fetch all 3 domains
    accounts = fetch_entity("accounts", api_accounts, flat_account, logger, tm)
    cities = fetch_entity("cities", api_cities, flat_city, logger, tm)
    countries = fetch_entity("countries", api_countries, flat_country, logger, tm)

    # Write all CSVs under same date folder
    write_csv(os.path.join(input_dir, f"accounts_{today}.csv"), accounts)
    write_csv(os.path.join(input_dir, f"cities_{today}.csv"), cities)
    write_csv(os.path.join(input_dir, f"countries_{today}.csv"), countries)

    logger.info("=== SFRDB Fetcher finished ===")


if __name__ == "__main__":
    main()

