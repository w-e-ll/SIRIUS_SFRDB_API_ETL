#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import uuid

from datetime import datetime, timezone


from sirius_sfrdb_api.fetcher_token_manager import auth_get


PAGE_SIZE = max(1, min(int(os.getenv("PAGE_SIZE", "200")), 1000))
ONLY_ACTIVE = os.getenv("ONLY_ACTIVE", "false").lower() == "true"


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch_entity(name, api_url, flattener, logger):
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

            r = auth_get(api_url, params=params)
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
