import base64
import hashlib
import mimetypes
import os
import random
from pathlib import Path
from typing import Any, Dict

from azure.storage.blob import (
    BlobClient,
    BlobServiceClient,
    ContainerClient,
    ContentSettings,
)
from dotenv import load_dotenv
from pyaz.db_access_rosetta import PermanentIndexData, StorageParameterData, rosetta_db


def file_checksum(
    path: str | Path, algorithm: str = "md5", chunk_size: int = 8192
) -> Dict[str, Any]:
    """
    Compute checksum for a file.

    Returns a dict with:
      - hex: hex digest string
      - raw: raw digest bytes
      - base64: base64-encoded digest string
    """
    h = hashlib.new(algorithm)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            h.update(chunk)
    raw = h.digest()
    return {
        "raw": raw,
        "hex": raw.hex(),
        "base64": base64.b64encode(raw).decode("ascii"),
    }


def save_to_db(
    args,
    prefix_directory,
    storage_entity_type,
    stored_entity_id,
    version,
    blob_name,
    md5,
    file_size,
) -> None:
    sql = f"SELECT storage_id FROM {rosetta_db.schemaprefix}_SHR00.STORAGE_PARAMETER WHERE VALUE = '{prefix_directory}'"
    exist_storage_parameter = rosetta_db.query_first_row(sql)

    if exist_storage_parameter is None:
        sql = f"SELECT MAX(storage_id) FROM {rosetta_db.schemaprefix}_SHR00.STORAGE_PARAMETER"
        max_id_row = rosetta_db.query_first_row(sql)
        max_id = 0 if max_id_row is None or max_id_row[0] is None else max_id_row[0]

        storage_id = max_id + 1

        # Insert new storage parameter
        sp = StorageParameterData(
            key="DIR_ROOT",
            value=prefix_directory,
            storage_id=storage_id,
        )
        rosetta_db.insert_storage_parameter(sp)
    else:
        storage_id = exist_storage_parameter[0]

    # Remove the existing row
    sql = f"DELETE FROM {rosetta_db.schemaprefix}_PER00.PERMANENT_INDEX WHERE VERSION =(:version) AND STORAGE_ENTITY_TYPE = (:storage_entity_type) AND STORED_ENTITY_ID = (:stored_entity_id)"
    rosetta_db.execute_sql(
        sql,
        {
            "version": version,
            "storage_entity_type": storage_entity_type,
            "stored_entity_id": stored_entity_id,
        },
    )

    pi = PermanentIndexData(
        storage_id=storage_id,
        storage_entity_type=storage_entity_type,
        stored_entity_id=stored_entity_id,
        version=version,
        file_size=file_size,
        index_location=blob_name,
        check_sum_type="MD5",
        check_sum=md5,
        phys_check_sum=md5,
    )

    if args.flag_save_to_db:
        rosetta_db.insert_permanent_index(pi)

    sql = f"INSERT INTO {rosetta_db.schemaprefix}_PER00.PERMANENT_INDEX (STORAGE_ID, STORAGE_ENTITY_TYPE, STORED_ENTITY_ID, VERSION, FILE_SIZE, INDEX_LOCATION, CHECK_SUM_TYPE, CHECK_SUM, PHYS_CHECK_SUM) VALUES ({storage_id}, '{storage_entity_type}', '{stored_entity_id}', {version}, {file_size}, '{blob_name}', 'MD5', '{md5}', '{md5}');"

    if args.flag_generate_sql:
        print(sql)

    return sql


def upload_blob(args, container: ContainerClient, file_path: Path) -> None:
    if not file_path.is_file():
        raise ValueError(f"File not found: {file_path}")

    if not str(file_path).startswith(args.prefix_directory):
        raise ValueError(f"File does not start with prefix directory: {file_path}")

    try:
        len_prefix_directory = len(args.prefix_directory)

        file_name = file_path.name
        if file_name == "ie.xml":
            storage_entity_type = "IE"
            stored_entity_id = file_path.parent.name
        else:
            storage_entity_type = "FILE"
            idx = file_name.index("_")
            stored_entity_id = file_name[0:idx]

        version = random.randint(1, 11)
        blob_name = str(file_path)[len_prefix_directory:].replace(os.path.sep, "/")

        content_type, _ = mimetypes.guess_type(file_path)

        md5 = file_checksum(file_path)
        file_size = file_path.stat().st_size

        if args.flag_upload_blob_storage:
            cs = ContentSettings(content_type=content_type, content_md5=md5["raw"])
            with open(file_path, "rb") as data:
                container.upload_blob(
                    name=blob_name,
                    data=data,
                    overwrite=True,
                    content_settings=cs,
                )

        sql = save_to_db(
            args,
            args.prefix_directory,
            storage_entity_type,
            stored_entity_id,
            version,
            blob_name,
            md5["hex"],
            file_size,
        )

        return stored_entity_id, sql

    except Exception as e:
        print(e)
        raise RuntimeError(f"Failed to upload blob: {e}")
