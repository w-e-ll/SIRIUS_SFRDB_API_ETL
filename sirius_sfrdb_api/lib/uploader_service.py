#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

from bics_sirius_sfrdb_api.lib.uploader_utils import (
    discover_latest_date_folder,
    discover_input_files_from_folder,
    load_one_table,
)
from bics_sirius_sfrdb_api.lib.uploader_db import OracleClient


logger = logging.getLogger('uploader_service')


def run_uploader(cfg):

    logger.info(
        f"INPUT_DIR={cfg.input_dir} | DB_LIST={cfg.db_list} | "
        f"TRUNCATE={cfg.truncate} | BATCH_SIZE={cfg.batch_size}"
    )

    latest_folder = discover_latest_date_folder(cfg.input_dir)
    logger.info(f"Using latest daily folder: {latest_folder}")

    files = discover_input_files_from_folder(latest_folder)
    for k, v in files.items():
        logger.info(f"Using CSV for {k}: {v}")

    for name in cfg.db_list:
        db_cfg = cfg.dbs.get(name)
        if not db_cfg:
            logger.error(f"Database {name} missing in YAML config, skipping")
            continue

        try:  # I need to pass here correct set of credentials by db from the db list by name probably
            with OracleClient(db_cfg, arraysize=cfg.batch_size) as ora:
                for domain in ("countries", "cities", "accounts"):
                    if domain not in files:
                        logger.warning(f"[{name}] No file for {domain}, skipping")
                        continue

                    load_one_table(
                        ora,
                        domain,
                        files[domain],
                        cfg.truncate,
                        cfg.batch_size,
                    )

        except Exception as exc:
            logger.exception(f"[{name}] Upload failure: {exc}")
            continue
