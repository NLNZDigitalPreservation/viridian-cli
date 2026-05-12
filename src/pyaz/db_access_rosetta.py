import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

import oracledb
from typing_extensions import Tuple


@dataclass
class PermanentIndexData:
    id: Optional[int] = None
    file_size: Optional[int] = None
    version: Optional[int] = None
    status: Optional[int] = None
    stored_entity_id: Optional[str] = None
    check_sum_type: Optional[str] = None
    storage_id: Optional[int] = None
    update_date: Optional[datetime] = None
    storage_entity_type: Optional[str] = None
    index_location: Optional[str] = None
    check_sum: Optional[str] = None
    update_check_sum: Optional[bool] = None
    phys_check_sum: Optional[str] = None
    phys_check_sum_type: Optional[str] = None
    xsd_versions: Optional[str] = None
    created_by: Optional[str] = None
    title: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class StorageParameterData:
    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[str] = None
    storage_id: Optional[int] = None

    def to_dict(self):
        return asdict(self)


def is_empty_string(var):
    return var is None or len(var.strip()) == 0


class RosettaDatabaseHandler:
    def __init__(self):
        self.hostname = None
        self.port = None
        self.username = None
        self.password = None
        self.sid = None
        self.service_name = None
        self.schemaprefix = None
        self.rosetta_db_dsn = None
        self.pool = None

    def initialize(self, args):
        assert args.rosetta_db_schemaprefix is not None
        assert args.rosetta_db_hostname is not None
        assert args.rosetta_db_port is not None
        assert args.rosetta_db_username is not None
        assert args.rosetta_db_password is not None
        assert not is_empty_string(args.rosetta_db_sid) or not is_empty_string(
            args.rosetta_db_service_name
        )

        self.hostname = args.rosetta_db_hostname
        self.port = args.rosetta_db_port
        self.username = args.rosetta_db_username
        self.password = args.rosetta_db_password
        self.sid = args.rosetta_db_sid
        self.service_name = args.rosetta_db_service_name
        self.schemaprefix = args.rosetta_db_schemaprefix

        if not is_empty_string(self.sid):
            self.rosetta_db_dsn = oracledb.makedsn(
                host=self.hostname,
                port=int(self.port),
                sid=self.sid,
            )
        else:
            self.rosetta_db_dsn = oracledb.makedsn(
                host=self.hostname,
                port=int(self.port),
                service_name=self.service_name,
            )
        self.pool = oracledb.create_pool(
            user=self.username,
            password=self.password,
            dsn=self.rosetta_db_dsn,
            min=3,
            max=20,
        )

    def close(self):
        pass

    # def create_connection(self):
    #     conn = oracledb.connect(
    #         user=self.username,
    #         password=self.password,
    #         dsn=self.rosetta_db_dsn,
    #     )
    #     logging.debug(f"Created a connection: {self.rosetta_db_dsn}")
    #     return conn

    # def close_connection(self, conn: oracledb.Connection):
    #     if conn is not None:
    #         conn.close()
    #         logging.debug(f"Closed the connection: {self.rosetta_db_dsn}")

    def get_count(self, sql_query):
        with self.pool.acquire() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    row = cursor.fetchone()
                    return row[0]
            except Exception as ex:
                logging.error(f"Failed to execute sql: {ex}")
                raise RuntimeError(str(ex))

    def get_max_id(self, table_name):
        sql_query = f"SELECT MAX(ID) FROM {table_name}"
        with self.pool.acquire() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    row = cursor.fetchone()
                    return row[0]
            except Exception as ex:
                logging.error(f"Failed to execute sql: {ex}")
                raise RuntimeError(str(ex))

    def execute_sql(self, sql_query, binds):
        with self.pool.acquire() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query, binds)
                conn.commit()
            except Exception as ex:
                conn.rollback()
                logging.error(f"Failed to execute sql: {ex}")
                logging.exception(ex)
                raise RuntimeError(str(ex))

    def query_first_row(self, sql_query):
        with self.pool.acquire() as conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    return cursor.fetchone()
            except Exception as ex:
                logging.error(f"Failed to execute sql: {ex}")
                raise RuntimeError(str(ex))

    def build_insert_permanent_index(
        self,
        pi: PermanentIndexData,
        use_sequence: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build INSERT SQL and binds for a PermanentIndexData instance.

        - use_sequence: optional sequence name (e.g. "MYSEQ") - if provided and pi.id is None,
        the ID value will be set to MYSEQ.NEXTVAL in the VALUES clause (no bind for id).
        Returns: (sql, binds)
        """
        table = f"{self.schemaprefix}_PER00.PERMANENT_INDEX"
        data = pi.__dict__
        cols = []
        vals = []
        binds: Dict[str, Any] = {}

        for attr, value in data.items():
            if value is None:
                continue
            col = attr.upper()
            if attr == "id" and use_sequence and pi.id is None:
                cols.append(col)
                vals.append(f"{use_sequence}.NEXTVAL")
                continue
            cols.append(col)
            bind_name = attr  # keep simple names for binds
            vals.append(f":{bind_name}")
            binds[bind_name] = value

        if not cols:
            raise ValueError("No values present on PermanentIndexData to insert")

        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)})"
        return sql, binds

    def build_insert_storage_parameter(
        self,
        sp: StorageParameterData,
        use_sequence: Optional[str] = None,
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Build INSERT SQL and binds for a StorageParameterData instance.
        - use_sequence: optional sequence name for the ID column.
        """
        table = f"{self.schemaprefix}_SHR00.STORAGE_PARAMETER"
        data = sp.__dict__
        cols = []
        vals = []
        binds: Dict[str, Any] = {}

        for attr, value in data.items():
            if value is None:
                continue
            col = attr.upper()
            if attr == "id" and use_sequence and sp.id is None:
                cols.append(col)
                vals.append(f"{use_sequence}.NEXTVAL")
                continue
            cols.append(col)
            bind_name = attr
            vals.append(f":{bind_name}")
            binds[bind_name] = value

        if not cols:
            raise ValueError("No values present on StorageParameterData to insert")

        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(vals)})"
        return sql, binds

    def insert_permanent_index(self, pi: PermanentIndexData):
        sql, binds = self.build_insert_permanent_index(pi)
        self.execute_sql(sql, binds)

    def insert_storage_parameter(self, sp: StorageParameterData):
        sql, binds = self.build_insert_storage_parameter(sp)
        self.execute_sql(sql, binds)


rosetta_db = RosettaDatabaseHandler()
