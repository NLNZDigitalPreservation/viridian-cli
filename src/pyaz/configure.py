import argparse
import os

DEFAULT_CONN_STR = "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://localhost:10000/devstoreaccount1;QueueEndpoint=http://localhost:10001/devstoreaccount1;TableEndpoint=http://localhost:10002/devstoreaccount1;"


def str2bool(value):
    true_values = {"true", "1", "yes", "y", "t", "on"}
    false_values = {"false", "0", "no", "n", "f", "off"}

    value = value.strip().lower()
    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        raise ValueError(f"Invalid truth value: {value}")


def parse_args():
    parser = argparse.ArgumentParser(
        prog="pyaz", description="pyaz: manage the blob storage in the Azurite"
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["cc", "dc", "lc", "lb", "id", "if", "db", "ied"],
        default=os.getenv("PYAZ_COMMAND", "id"),
        help="command to run",
    )

    parser.add_argument(
        "--connection-string",
        default=os.getenv("CONNECTION_STRING", DEFAULT_CONN_STR),
        help="The connection configuration to blob storage",
    )

    parser.add_argument(
        "--container-name",
        default=os.getenv("CONTAINER_NAME", "fixity-dev"),
        help="The name of the storage container",
    )

    parser.add_argument(
        "--prefix-directory",
        type=str,
        default=os.getenv("PREFIX_DIRECTORY", "/persistent/fixity/testdata/"),
        help="The prefix directory to import",
    )

    parser.add_argument(
        "--source-directory",
        type=str,
        default=os.getenv("SOURCE_DIRECTORY", "/persistent/fixity/testdata/"),
        help="The source directory to import",
    )

    parser.add_argument(
        "--source-file",
        type=str,
        default=os.getenv("SOURCE_FILE", None),
        help="The source file to import",
    )

    parser.add_argument(
        "--blob-name",
        type=str,
        default=os.getenv("BLOB_NAME", None),
        help="The name of the blob to import",
    )

    parser.add_argument(
        "--flag-upload-blob-storage",
        type=str2bool,
        default=True,
        help="Flag to indicate whether to upload the blob to storage",
    )

    parser.add_argument(
        "--flag-save-to-db",
        type=str2bool,
        default=True,
        help="Flag to indicate whether to save the blob metadata to the database",
    )

    parser.add_argument(
        "--flag-generate-sql",
        type=str2bool,
        default=True,
        help="Flag to indicate whether to generate SQL for the blob metadata",
    )

    """Adds arguments required for any service that connects to the DBMS"""
    parser.add_argument(
        "--rosetta-db-hostname",
        default=os.getenv("ROSETTA_DB_HOSTNAME", "localhost"),
        help="The hostname of the DBMS",
    )

    parser.add_argument(
        "--rosetta-db-port",
        type=int,
        default=int(os.getenv("ROSETTA_DB_PORT", "1521")),
        help="The port of the DBMS",
    )
    parser.add_argument(
        "--rosetta-db-username",
        default=os.getenv("ROSETTA_DB_USERNAME", "system"),
        help="The username to connect to the DBMS with",
    )
    parser.add_argument(
        "--rosetta-db-password",
        default=os.getenv("ROSETTA_DB_PASSWORD", "Pass123Word"),
        help="The password to connect to the DBMS with",
    )
    parser.add_argument(
        "--rosetta-db-sid",
        default=os.getenv("ROSETTA_DB_SID", None),
        help="The SID of the database to connect to",
    )
    parser.add_argument(
        "--rosetta-db-service-name",
        default=os.getenv("ROSETTA_DB_SERVICE_NAME", "FREEPDB1"),
        help="The service name of the database to connect to",
    )
    parser.add_argument(
        "--rosetta-db-schemaprefix",
        default=os.getenv("ROSETTA_DB_SCHEMAPREFIX", "V2PN"),
        help="enable or disable OPTIONAL DB TABLES",
    )

    args = parser.parse_args()
    return args
