#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import csv
import logging

logger = logging.getLogger('fetcher_to_csv')


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
