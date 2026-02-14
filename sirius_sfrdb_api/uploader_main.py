#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os

from dotenv import load_dotenv

from sirius_sfrdb_api.lib.shared_logger import setup_logger
from sirius_sfrdb_api.lib.uploader_config import load_yaml_config
from sirius_sfrdb_api.lib.uploader_service import run_uploader

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="SFRDB CSV → Oracle uploader")
    parser.add_argument("--config-dir", required=True)
    args = parser.parse_args()

    cfg = load_yaml_config(args.config_dir)

    logfile = os.path.join(cfg.log_dir, "uploader.log")
    logger = setup_logger(logfile)

    logger.info(f"=== SFRDB Uploader started | ENV={cfg.env} ===")

    run_uploader(cfg)

    logger.info("=== SFRDB Uploader finished ===")


if __name__ == "__main__":
    main()
