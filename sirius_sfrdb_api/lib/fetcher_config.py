#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import yaml
import logging

from dataclasses import dataclass

logger = logging.getLogger('fetcher_config')


@dataclass
class AppConfig:
    base_dir: str
    log_dir: str
    input_dir: str


def expand(value: str, base_dir: str) -> str:
    return value.replace("${base_dir}", base_dir)


def load_yaml_config(config_dir: str) -> AppConfig:
    path = os.path.join(config_dir, "sfrdb_config.yml")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Config not found: {path}")

    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    base_dir = cfg["paths"]["base_dir"]

    return AppConfig(
        base_dir=base_dir,
        log_dir=expand(cfg["paths"]["log_dir"], base_dir),
        input_dir=expand(cfg["paths"]["input_dir"], base_dir),
    )
