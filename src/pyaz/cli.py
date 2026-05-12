#!/usr/bin/env -S .venv/bin/python3
from datetime import datetime
import time
import os
from pathlib import Path

from azure.storage.blob import BlobClient, BlobServiceClient, ContainerClient
from pyaz.blob_upload import upload_blob
from pyaz.configure import parse_args
from pyaz.db_access_rosetta import rosetta_db

API_VERSION = "2020-04-08"  # "2026-02-06"


def _get_service_client(connection_string: str) -> BlobServiceClient:
    return BlobServiceClient.from_connection_string(
        connection_string, api_version=API_VERSION
    )


def create_container(args):
    svc = _get_service_client(args.connection_string)
    try:
        svc.create_container(args.container_name)
        return f"Created container: {args.container_name}"
    except Exception as e:
        raise RuntimeError(f"Failed to create container: {e}")


def delete_container(args):
    svc = _get_service_client(args.connection_string)
    try:
        svc.delete_container(args.container_name)
        return f"Deleted container: {args.container_name}"
    except Exception as e:
        raise RuntimeError(f"Failed to delete container: {e}")


def list_containers(args):
    svc = _get_service_client(args.connection_string)
    try:
        names = [
            c["name"] if isinstance(c, dict) else c.name for c in svc.list_containers()
        ]
        return "\n".join(names)
    except Exception as e:
        raise RuntimeError(f"Failed to list containers: {e}")


def list_blobs(args):
    svc = _get_service_client(args.connection_string)
    try:
        container = svc.get_container_client(args.container_name)
        blobs = [b.name for b in container.list_blobs()]
        return "\n".join(blobs)
    except Exception as e:
        raise RuntimeError(f"Failed to list blobs: {e}")


def import_directory(args):
    svc = _get_service_client(args.connection_string)
    container = svc.get_container_client(args.container_name)
    if not os.path.isdir(args.source_directory):
        raise ValueError(f"Source directory not found: {args.source_directory}")

    uploaded_stored_entity_id = []
    insert_sql_list = []
    for root, _, files in os.walk(args.source_directory):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, args.source_directory)
            blob_name = rel_path.replace(os.path.sep, "/")
            try:
                stored_entity_id, sql = upload_blob(args, container, Path(full_path))
                uploaded_stored_entity_id.append(f"'{stored_entity_id}'")
                insert_sql_list.append(sql)
                print(f"Uploaded {full_path} -> {blob_name}")
            except Exception as e:
                raise RuntimeError(f"Failed to upload {full_path}: {e}")

    if args.flag_generate_sql:
        time.sleep(1)  #
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        export_file = f"insert_{timestamp}.sql"

        stored_entity_ids = ",".join(uploaded_stored_entity_id)
        delete_sql = f"DELETE FROM {rosetta_db.schemaprefix}_PER00.PERMANENT_INDEX WHERE STORED_ENTITY_ID IN ({stored_entity_ids});"

        with open(export_file, "w") as fp:
            fp.write(delete_sql + "\n")
            fp.write("\n".join(insert_sql_list))

    return "\n".join(uploaded_stored_entity_id)


def import_file(args):
    svc = _get_service_client(args.connection_string)
    container = svc.get_container_client(args.container_name)

    # if not args.blob_name:
    #     print("Blob name not specified.")
    #     return "Blob name must be specified for file import."

    if not args.source_file:
        print("Source file not specified.")
        return "Source file must be specified for file import."

    if not os.path.isfile(args.source_file):
        raise ValueError(f"Source file not found: {args.source_file}")

    try:
        stored_entity_id, sql = upload_blob(args, container, Path(args.source_file))
        if args.flag_generate_sql:
            delete_sql = f"DELETE FROM {rosetta_db.schemaprefix}_PER00.PERMANENT_INDEX WHERE STORED_ENTITY_ID='{stored_entity_id}';"

            time.sleep(1)  #
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            export_file = f"insert_{timestamp}.sql"

            with open(export_file, "w") as fp:
                fp.write(delete_sql + "\n")
                fp.write(sql)

        return f"Uploaded {args.source_file} -> {args.container_name}"
    except Exception as e:
        raise RuntimeError(f"Failed to upload file: {e}")


def delete_blob(args):
    svc = _get_service_client(args.connection_string)
    container = svc.get_container_client(args.container_name)

    if not args.blob_name:
        raise ValueError("Blob name must be specified for deletion.")

    try:
        container.delete_blob(args.blob_name)
        return f"Deleted blob: {args.blob_name}"
    except Exception as e:
        raise RuntimeError(f"Failed to delete blob: {e}")


def main():
    args = parse_args()
    print(args)

    commands = {
        "cc": create_container,
        "dc": delete_container,
        "lc": list_containers,
        "lb": list_blobs,
        "id": import_directory,
        "if": import_file,
        "db": delete_blob,
    }

    rosetta_db.initialize(args)
    ret = commands[args.command](args)
    print(ret)


if __name__ == "__main__":
    main()
