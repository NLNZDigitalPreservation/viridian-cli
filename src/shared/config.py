import os
import re
from argparse import ArgumentParser
from pathlib import Path


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


class Parser(ArgumentParser):
    """An easy way to make flags also configurable from env variables"""

    def add_env_argument(self, *args, **kwargs):
        if len(args) != 1:
            raise ValueError("Provide exactly one flag name")

        flag_name = args[0]

        # Prioritize environment variables over the normal default
        environment_default = os.environ.get(_to_env_var_name(flag_name), None)
        if environment_default is not None:
            # If a type is specified such as 'int' or 'float' or 'str', convert
            # the environment variable using the callback
            type_callback = kwargs.get("type", None)
            if type_callback:
                environment_default = type_callback(environment_default)

            kwargs["default"] = environment_default

        # Mark the flag as not required if it's supplied as an env variable
        no_env_variable_set = _to_env_var_name(flag_name) not in os.environ
        marked_required = kwargs.get("required", False)
        kwargs["required"] = marked_required and no_env_variable_set

        super().add_argument(flag_name, **kwargs)

    def add_log_level(self):
        self.add_env_argument(
            "--log-level",
            default="INFO",
            help="The log level of logging",
        )

    def add_dbms_arguments(self):
        """Adds arguments required for any service that connects to the DBMS"""
        self.add_env_argument(
            "--dbms-hostname",
            default="localhost",
            help="The hostname of the DBMS",
        )
        self.add_env_argument(
            "--dbms-port",
            default=5432,
            help="The hostname of the DBMS",
        )
        self.add_env_argument(
            "--dbms-username",
            default="fixity",
            help="The username to connect to the DBMS with",
        )
        self.add_env_argument(
            "--dbms-password",
            default="fixity",
            help="The password to connect to the DBMS with",
        )
        self.add_env_argument(
            "--db-name",
            default="db_fixity",
            help="The name of the database in the DBMS to connect to",
        )
        self.add_env_argument(
            "--optional_db_tables",
            required=False,
            help="enable or disable OPTIONAL DB TABLES",
        )

    def add_rosetta_arguments(self):
        """Adds arguments required for any service that connects to the DBMS"""
        self.add_env_argument(
            "--rosetta-db-hostname",
            default="localhost",
            help="The hostname of the DBMS",
        )
        self.add_env_argument(
            "--rosetta-db-port",
            default=1521,
            help="The hostname of the DBMS",
        )
        self.add_env_argument(
            "--rosetta-db-username",
            default="fixity",
            help="The username to connect to the DBMS with",
        )
        self.add_env_argument(
            "--rosetta-db-password",
            default="fixity",
            help="The password to connect to the DBMS with",
        )
        self.add_env_argument(
            "--rosetta-db-sid",
            default=None,
            help="The name of the database in the DBMS to connect to",
        )
        self.add_env_argument(
            "--rosetta-db-service-name",
            default=None,
            help="The name of the database in the DBMS to connect to",
        )
        self.add_env_argument(
            "--rosetta-db-schemaprefix",
            required=None,
            help="enable or disable OPTIONAL DB TABLES",
        )
        self.add_env_argument(
            "--file-translate-from",
            default="/mnt/e/data/fixity",
            help="The root directory of the permanent storage",
        )
        self.add_env_argument(
            "--file-translate-to",
            default="Y:/ndha/dps_export_test/leefr/export/Fixity",
            help="The target directory of the permanent storage",
        )

    def add_broker_arguments(self):
        """Adds arguments that are required for any service that connects to the message
        broker
        """
        self.add_env_argument(
            "--broker-hostname",
            default="localhost",
            help="The hostname of the RabbitMQ broker",
        )
        self.add_env_argument(
            "--broker-username",
            default="fixity",
            help="The username to access the broker with",
        )
        self.add_env_argument(
            "--broker-password",
            default="fixity",
            help="The password to access the broker with",
        )

    def add_blob_storage_arguments(self):
        self.add_env_argument(
            "--storage-dir",
            type=Path,
            default=Path("storage"),
            help="The directory where data from the data storage API is stored",
        )

        self.add_env_argument(
            "--account-name",
            default="devstoreaccount1",
            help="The the credential connect to blob storage",
        )

        self.add_env_argument(
            "--account-key",
            default="Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==",
            help="The the credential connect to blob storage",
        )

        self.add_env_argument(
            "--connection-string",
            default=None,
            help="The connection configuration to blob storage",
        )

        self.add_env_argument(
            "--container-name",
            default="fixity-dev",
            help="The name of the storage container",
        )

    def add_app_arguments(self, api_port, base_dir):
        self.add_env_argument(
            "--version",
            default="2.0.0",
            help="The version number of Fixity Tool",
        )
        self.add_env_argument(
            "--test-mode",
            default=False,
            type=bool,
            help="The flag for testing purpose",
        )

        self.add_env_argument(
            "--expire-interval",
            default=1800,
            type=int,
            help="The expire timeslot for the sessions",
        )

        self.add_env_argument(
            "--rosetta-pds-url",
            default="https://slbpdstest.natlib.govt.nz/pds",
            help="The authorization url of pds client",
        )

        self.add_env_argument(
            "--bootstrap-password",
            default="password",
            help="The password for bootstrap user",
        )

        self.add_env_argument(
            "--api-port",
            type=int,
            default=api_port,
            help="The port where API requests for are served from",
        )

        self.add_env_argument(
            "--fixity-worker-url",
            default="http://localhost:7071",
            help="The api for workers",
        )
        self.add_env_argument(
            "--fixity-ssl-verify",
            default=True,
            type=str2bool,
            help="Enable TLS certificate verification for fixity HTTPS calls",
        )
        self.add_env_argument(
            "--fixity-ca-bundle",
            default=os.path.join(base_dir, "fixity.cert"),
            help="Optional CA bundle file path for fixity HTTPS calls",
        )

        self.add_env_argument(
            "--max-workers",
            default=10,
            type=int,
            help="The maximum threads to call workers",
        )

        self.add_env_argument(
            "--batch-size",
            default=10000,
            type=int,
            help="The maximum jobs for a batch",
        )

        self.add_env_argument(
            "--content-read-buffer-size",
            default=10485760,
            type=int,
            help="The maximum size for each downloading round from the blob storage. The default is 10M",
        )

        self.add_env_argument(
            "--max-running-millions",
            default=180000,
            type=int,
            help="The maximum million seconds for the activity of the durable functions. The default is 2Minutes",
        )

        self.add_env_argument(
            "--enable-blob-storage-event",
            default=True,
            type=bool,
            help="If allow the blob storage events from the event grid API",
        )
        self.add_env_argument(
            "--max-worker-timeout-hours",
            default=24,
            type=int,
            help="The maximum hours for a worker to run the durable function",
        )
        self.add_env_argument(
            "--persistent-storage",
            default="/persistent/master-node",
            help="The persistent directory for master node storage",
        )
        self.add_env_argument(
            "--blob-url-prefix",
            default="http://localhost:10000/devstoreaccount1/fixity-dev",
            help="The prefix string of the blob url",
        )
        self.add_env_argument(
            "--if-read-from-disk",
            default=False,
            type=bool,
            help="If read the files from blob storage or local disk",
        )

    def add_pyaz_arguments(self):
        self.add_env_argument(
            "--source-file",
            default="",
            help="The path of the file",
        )

        self.add_env_argument(
            "--blob-name",
            default="",
            help="The name of the blob",
        )

        self.add_env_argument(
            "--source-directory",
            default="",
            help="The path of the directory",
        )

        self.add_env_argument(
            "--prefix-directory",
            default="",
            help="The prefix directory to import",
        )

        self.add_env_argument(
            "--if-upload-to-blob-storage",
            default=True,
            type=bool,
            help="If upload the files to the blob storage",
        )

    @staticmethod
    def parse_duration(duration: str) -> int:
        """Parses a duration string in the format XdXhXm to seconds."""

        # Convert the journal max age to seconds
        match = re.match(r"^(\d+)d(\d+)h(\d+)m$", duration)
        if match is None:
            raise ValueError(
                "Invalid duration format, must be in the format XdXhXm. "
                f"Instead, {duration} was given."
            )
        duration_seconds = int(match[1]) * 86400  # Convert days to seconds
        duration_seconds += int(match[2]) * 3600  # Convert hours to seconds
        duration_seconds += int(match[3]) * 60  # Convert minutes to seconds

        return duration_seconds

    @staticmethod
    def str_to_bool(string: str) -> bool:
        return str2bool(string)


def _to_env_var_name(flag_name: str) -> str:
    """Converts a flag to an idiomatic environment variable name"""
    return flag_name.replace("--", "").replace("-", "_").upper()
