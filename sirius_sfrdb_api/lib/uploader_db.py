# uploader_db.py
import oracledb
import logging

from typing import Optional, List, Tuple

from sirius_sfrdb_api.lib.uploader_config import DBConfig

logger = logging.getLogger('uploader_db')


class OracleClient:
    def __init__(self, cfg: DBConfig, arraysize: int = 1000):
        self.cfg = cfg
        self.arraysize = arraysize
        self.conn: Optional[oracledb.Connection] = None

    def connect(self):
        dsn = oracledb.makedsn(self.cfg.host, self.cfg.port, sid=self.cfg.sid)
        try:
            self.conn = oracledb.connect(user=self.cfg.user, password=self.cfg.password, dsn=dsn)
            self.conn.autocommit = False
            logger.info("[%s] Connected (sid=%s)", self.cfg.name, self.cfg.sid)
        except Exception as e:
            logger.exception("[%s] DB connect failed: %s", self.cfg.name, e)
            raise

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            logger.warning("[%s] error on close (ignored)", self.cfg.name)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.conn:
            if exc is None:
                try:
                    self.conn.commit()
                    logger.info("[%s] COMMIT", self.cfg.name)
                except Exception as e:
                    logger.exception("[%s] Commit failed: %s", self.cfg.name, e)
                    try:
                        self.conn.rollback()
                    except Exception:
                        pass
                    raise
            else:
                try:
                    self.conn.rollback()
                    logger.info("[%s] ROLLBACK", self.cfg.name)
                except Exception:
                    pass
        self.close()

    def table_exists(self, owner: str, table: str) -> bool:
        sql = """SELECT 1 FROM ALL_TABLES WHERE OWNER=:o AND TABLE_NAME=:t"""
        with self.conn.cursor() as cur:
            cur.execute(sql, dict(o=owner.upper(), t=table.upper()))
            return cur.fetchone() is not None

    def get_columns(self, owner: str, table: str) -> List[str]:
        sql = """
        SELECT COLUMN_NAME
        FROM ALL_TAB_COLUMNS
        WHERE OWNER=:o AND TABLE_NAME=:t
        ORDER BY COLUMN_ID
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, dict(o=owner.upper(), t=table.upper()))
            return [r[0] for r in cur.fetchall()]

    def truncate(self, owner: str, table: str):
        sql = f"TRUNCATE TABLE {owner}.{table}"
        with self.conn.cursor() as cur:
            cur.execute(sql)
        logger.info("[%s] Truncated %s.%s", self.cfg.name, owner, table)

    def insert_many(self, owner: str, table: str, cols: List[str], rows: List[Tuple]):
        if not rows:
            logger.info("[%s] %s.%s – nothing to insert", self.cfg.name, owner, table)
            return

        # quick client-side validation
        ncols = len(cols)
        bad = next((i for i, r in enumerate(rows) if len(r) != ncols), None)
        if bad is not None:
            raise ValueError(f"{owner}.{table}: row {bad} has {len(rows[bad])} values, expected {ncols}")

        placeholders = ",".join([f":{i + 1}" for i in range(ncols)])
        collist = ",".join(cols)
        sql = f"INSERT /*+ APPEND */ INTO {owner}.{table} ({collist}) VALUES ({placeholders})"

        with self.conn.cursor() as cur:
            cur.setinputsizes(None)

            try:
                cur.executemany(
                    sql,
                    rows,
                    batcherrors=True,
                    arraydmlrowcounts=True,
                )
            except oracledb.Error as e:
                # executemany itself failed (e.g., ORA-00942, ORA-00904, ORA-12899…)
                logger.exception(
                    "[%s] executemany failed for %s.%s (cols=%d, rows=%d): %s",
                    self.cfg.name, owner, table, ncols, len(rows), e
                )
                raise

            # Only reach here if executemany succeeded
            errs = cur.getbatcherrors()
            if errs:
                # show a small sample—fail fast so we don't commit partial unknown state
                for e in errs[:25]:
                    logger.error("[%s] %s.%s row %d failed: %s", self.cfg.name, owner, table, e.offset, str(e).strip())
                raise oracledb.DatabaseError(f"{len(errs)} row error(s) while inserting into {owner}.{table}")

            counts = cur.getarraydmlrowcounts()
            inserted = sum(1 for c in counts if c > 0)
            logger.info("[%s] Inserted %d/%d rows into %s.%s", self.cfg.name, inserted, len(rows), owner, table)
