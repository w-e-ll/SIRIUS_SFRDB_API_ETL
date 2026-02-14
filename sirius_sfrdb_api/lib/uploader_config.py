# uploader_config.py
import os
import yaml


class DBConfig:
    def __init__(self, name, host, port, sid, user, password):
        self.name = name
        self.host = host
        self.port = port
        self.sid = sid
        self.user = user
        self.password = password


class AppConfig:
    def __init__(self, input_dir, log_dir, db_list, truncate, batch_size, dbs, env):
        self.input_dir = input_dir
        self.log_dir = log_dir
        self.db_list = db_list
        self.truncate = truncate
        self.batch_size = batch_size
        self.dbs = dbs
        self.env = env


def load_yaml_config(config_dir: str):
    path = os.path.join(config_dir, "sfrdb_config.yml")
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)

    # Compute absolute project root
    base = cfg["paths"]["base_dir"]

    # --- FIX: Resolve ${base_dir} in INPUT DIR ---
    env = cfg["env"]
    raw_input_dir = cfg["paths"]["input_dir"]
    raw_log_dir = cfg["paths"]["log_dir"]
    input_dir = raw_input_dir.replace("${base_dir}", base)
    log_dir = raw_log_dir.replace("${base_dir}", base)

    # --- Resolve DB configs ---
    dbs = {}
    for name, dbc in cfg["databases"].items():

        host = dbc["host"]
        port = dbc["port"]
        sid = dbc["sid"]

        # credentials coming from .env
        user = os.getenv(f"{name}_user")
        password = os.getenv(f"{name}_pass")

        dbs[name] = DBConfig(name, host, port, sid, user, password)

    return AppConfig(
        input_dir=input_dir,
        log_dir=log_dir,
        db_list=cfg["load"]["db_list"],
        truncate=cfg["load"]["truncate"],
        batch_size=cfg["load"]["batch_size"],
        dbs=dbs,
        env=env,
    )
