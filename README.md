# SIRIUS_SFRDB_API_ETL

### SFRDB ETL — Fetch → Transform → Load into Oracle (XXX)

This project implements a production-grade ETL pipeline for synchronizing reference datasets from SFRDB API into Oracle (SFRDB_SCHEMA).
The ETL runs every 2 hours and provides guaranteed reproducible daily snapshots.

---------------------------------------------

## Project Structure

```
sirius_sfrdb_api_etl/
│
├── bash_files/
│   ├── cleanup_folders.sh
│   └── run_workflow.sh
│
├── sirius_sfrdb_api/
│   ├── lib/
│   │   ├── fetcher_config.py
│   │   ├── fetcher_entity.py
│   │   ├── fetcher_flats.py
│   │   ├── fetcher_to_csv.py
│   │   ├── fetcher_utils.py
│   │   ├── fetcher_token_manager.py
│   │   ├── uploader_config.py
│   │   ├── uploader_db.py
│   │   ├── uploader_service.py
│   │   ├── uploader_utils.py
│   │   └── shared_logger.py
│   │
│   ├── fetcher_main.py
│   └── uploader_main.py
│
├── etc/
│   └── sfrdb_config.yml
│
├── var/
│   ├── data/
│   │   └── YYYY-MM-DD/
│   │       ├── accounts_YYYY-MM-DD.csv
│   │       ├── cities_YYYY-MM-DD.csv
│   │       └── countries_YYYY-MM-DD.csv
│   │
│   └── log/
│       ├── fetcher.log
│       └── uploader.log
│
├── .env
├── setup.py
├── README.md
└── requirements.txt
```

---

### Configuration

#### 2.1 Environment variables (.env)

``` 
SFRDB_ENV=UAT
SFRDB_CLIENT_SECRET=xxxxxxxxxxxxx

BBPDB01I_user=SFRDB_SCHEMA
BBPDB01I_pass=xxxxxxx

BBPDB01U_user=SFRDB_SCHEMA
BBPDB01U_pass=xxxxxxx
```

These variables are loaded automatically via dotenv.

```  
export SFRDB_ENV=UAT
export SFRDB_CLIENT_SECRET=xxxxxx
```

#### 2.2 YAML configuration (etc/sfrdb_config.yml)

``` 
env: UAT

paths:
  base_dir: /home/<id>/apps/sirius_sfrdb_api_etl
  data_dir: "${base_dir}/var/data"
  log_dir:  "${base_dir}/var/log"

fetch:
  base_url: "https://sfrdb-uat.xxx.bc/api/v1"
  save_prefix: "sfrdb"

load:
  db_list: [XXX, XXX]
  batch_size: 2000
  truncate: true     # or false

databases:
  XXX:
    host: XXX.bc    # 127.0.0.1
    port: 1540
    sid:  XXX
  XXX:
    host: XXX.bc    # 127.0.0.1
    port: 1540
    sid:  XXX
```

---

### 3. ETL Workflow Overview

#### 3.1 Fetcher (fetcher_main.py)

Responsible for downloading API data and producing CSV snapshots.

#### Duties:

- OAuth2 token retrieval (via fetcher_token_manager.py)
- Fetching: /accounts, /cities, /countries
- Pagination handling
- Flattening JSON responses
- Rewriting same-day results
- Logging to var/log/sfrdb_fetcher.log

Output folder example:
  ``` 
  var/data/2026-01-13/
              │── accounts_2026-01-13.csv
              │── cities_2026-01-13.csv
              └── countries_2026-01-13.csv
  ```

#### 3.2 Uploader (uploader_main.py)

Loads the latest date folder into Oracle.

#### Duties:

- Detect latest folder under var/data/
- Validate CSV against schema
- Truncate Oracle tables
- Bulk-insert with batching
- Log to var/log/sfrdb_uploader.log

Oracle tables populated:
- T_ACCOUNT_INFORMATION
- T_CITY
- T_COUNTRY

---

### 4. Automation Scripts
#### 4.1 run_workflow.sh

- Executes the entire pipeline
- Used by cron (every 2 hours).

---

#### 4.2 cleanup_folders.sh

Deletes old folders and logs:
- keeps latest 4 folders in var/data/
- removes logs older than 14 days

Retention policy is now fully automated.

---

## Environments & Endpoints

| ENV | API Base URL |
|-----|--------------|
| ITT | https://sfrdb-itt.xxx.bc/api/ |
| UAT | https://sfrdb-uat.xxx.bc/api/ |
| PROD | https://sfrdb.xxx.bc/api/ |

Endpoints used:

- `/v1/accounts`
- `/v1/cities`
- `/v1/countries`

Authentication:
- OAuth2 Client Credentials  
- Keycloak token endpoint (per environment)

---

### 5. Cron Configuration (Production)

Open editor:

```  
crontab -e
```

Run ETL every 2 hours

```  
0 */2 * * * /home/<id>/apps/sirius_sfrdb_api_etl/bash_files/run_workflow.sh > /dev/null 2>&1
```

Daily cleanup at 03:00

```  
0 3 * * * /home/<id>/apps/sirius_sfrdb_api_etl/bash_files/cleanup_folders.sh > /dev/null 2>&1
```

---

### 6. How to Run Manually
#### Fetcher:
```
python -m sirius_sfrdb_api.fetcher_main --config-dir ./etc
```
#### Uploader:
```
python -m sirius_sfrdb_api.uploader_main --config-dir ./etc
```

#### Workflow:
```
bash bash_files/run_workflow.sh
```

---

### 7. Logging
Logs stored under:

```
var/log/
    │── fetcher.log
    └── uploader.log
```

---

### 8. Developer Notes
- Logging is centralized using shared_logger.py
- All business logic resides in lib/
- fetcher_main.py and uploader_main.py only orchestrate execution
- Configuration is fully externalized (YAML + .env)
- The entire ETL is production-grade.

---

### Contacts

#### Developer:
Valentin Sheboldaev / valentin.sheboldaev.ext@w-e-ll.com