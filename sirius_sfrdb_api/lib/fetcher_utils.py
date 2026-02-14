#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import os
import logging


logger = logging.getLogger('fetcher_utils')


def cleaning_saved_today_records(out_dir):
    if os.path.exists(out_dir):
        logger.info(f"Cleaning existing folder for today: {out_dir}")
        for filename in os.listdir(out_dir):
            file_path = os.path.join(out_dir, filename)
            try:
                os.remove(file_path)
                logger.info(f"Removed old file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove old file {file_path}: {e}")
    else:
        os.makedirs(out_dir, exist_ok=True)


def write_csv(path, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        logger.error(f"Failed to write to {path}: {e}")