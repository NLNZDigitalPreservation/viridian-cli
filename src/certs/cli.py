import argparse
from pathlib import Path
import shutil
import subprocess
import os

from certs.sort_fullchain import sort_certificates_in_chain

SOURCE_ROOT_DIR = "/data/certs"
DEST_ROOT_DIR = "/data/viridian/conf/proxy/ssl"


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
        prog="dps-cert",
        description="""dps-cert: deploy the certificates to the correct location based on the environment:
          def  - DEV environment
          uat  - UAT environment
          prd  - PRD environment
          """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["dev", "uat", "prd"],
        default="dev",
        help="command to run",
    )

    parser.add_argument(
        "--flag-replace-existing",
        type=str2bool,
        default=True,
        help="Flag to indicate whether to replace existing certificates (true/false). Default is true.",
    )

    parser.add_argument(
        "--source-dir",
        type=str,
        default=SOURCE_ROOT_DIR,
        help="Source directory for certificates. Default is /data/certs.",
    )
    parser.add_argument(
        "--dest-dir",
        type=str,
        default=DEST_ROOT_DIR,
        help="Destination directory for certificates. Default is /data/viridian/conf/proxy/ssl.",
    )

    args = parser.parse_args()
    return args


def copy_files(src_file: str, dest_file: str, replace: bool = False):
    if not os.path.isfile(src_file):
        raise ValueError(f"Source file not found: {src_file}")

    if os.path.isfile(dest_file) and not replace:
        raise ValueError(f"Destination file already exists: {dest_file}")

    shutil.copy2(src_file, dest_file)

    # Change the permissions of the destination file to 644 (rw-r--r--)
    os.chmod(dest_file, 0o644)


def verify_certificates(cert_file: str, privkey_file: str):
    cert_check = subprocess.run(
        ["openssl", "x509", "-in", cert_file, "-noout"],
        capture_output=True,
        text=True,
    )
    if cert_check.returncode != 0:
        raise ValueError(f"Invalid certificate: {cert_file}")

    key_check = subprocess.run(
        ["openssl", "pkey", "-in", privkey_file, "-noout"],
        capture_output=True,
        text=True,
    )
    if key_check.returncode != 0:
        raise ValueError(f"Invalid private key: {privkey_file}")

    print("Certificate and private key are both valid.")
    print()

    print("Certificate information:")
    cert_info = subprocess.run(
        [
            "openssl",
            "x509",
            "-in",
            cert_file,
            "-noout",
            "-subject",
            "-issuer",
            "-dates",
        ],
        capture_output=True,
        text=True,
    )
    if cert_info.returncode != 0:
        raise ValueError(f"Invalid certificate: {cert_file}")
    print(cert_info.stdout.strip())
    print()

    cert_hash = subprocess.run(
        [
            "openssl",
            "x509",
            "-in",
            cert_file,
            "-pubkey",
            "-noout",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if cert_hash.returncode != 0:
        raise ValueError(f"Invalid certificate: {cert_file}")

    cert_hash = subprocess.run(
        ["openssl", "pkey", "-pubin", "-outform", "DER"],
        input=cert_hash.stdout,
        capture_output=True,
        text=False,
        check=False,
    )
    if cert_hash.returncode != 0:
        raise ValueError(f"Invalid certificate: {cert_file}")

    cert_hash = subprocess.run(
        ["openssl", "sha256"],
        input=cert_hash.stdout,
        capture_output=True,
        text=False,
        check=False,
    )
    if cert_hash.returncode != 0:
        raise ValueError(f"Invalid certificate: {cert_file}")
    cert_hash = cert_hash.stdout.decode("utf-8", errors="replace").strip().split()[-1]

    key_hash = subprocess.run(
        ["openssl", "pkey", "-in", privkey_file, "-pubout", "-outform", "DER"],
        capture_output=True,
        text=False,
        check=False,
    )
    if key_hash.returncode != 0:
        raise ValueError(f"Invalid private key: {privkey_file}")

    key_hash = subprocess.run(
        ["openssl", "sha256"],
        input=key_hash.stdout,
        capture_output=True,
        text=False,
        check=False,
    )
    if key_hash.returncode != 0:
        raise ValueError(f"Invalid private key: {privkey_file}")
    key_hash = key_hash.stdout.decode("utf-8", errors="replace").strip().split()[-1]

    print("Certificate public key SHA256:")
    print(cert_hash)
    print()

    print("Private key public key SHA256:")
    print(key_hash)
    print()

    if cert_hash == key_hash:
        print("========================================")
        print("OK: Certificate and private key MATCH.")
        print("========================================")
        return True

    print("========================================")
    print("ERROR: Certificate and private key DO NOT MATCH!")
    print("========================================")
    raise ValueError("Certificate and private key do not match.")


def resolve_certificates(args):
    env_name = args.command

    cert_file_name = f"cert-wildcard-{env_name}-natlib-govt-nz_fullchain.pem"
    src_cert_file = (
        f"{args.source_dir}/cert-wildcard-{env_name}-natlib-govt-nz/{cert_file_name}"
    )
    dest_cert_file = (
        f"{args.dest_dir}/cert-wildcard-{env_name}-natlib-govt-nz/{cert_file_name}"
    )

    privkey_file_name = f"cert-wildcard-{env_name}-natlib-govt-nz_privkey.pem"
    src_privkey_file = (
        f"{args.source_dir}/cert-wildcard-{env_name}-natlib-govt-nz/{privkey_file_name}"
    )
    dest_privkey_file = (
        f"{args.dest_dir}/cert-wildcard-{env_name}-natlib-govt-nz/{privkey_file_name}"
    )

    sort_certificates_in_chain(
        certs_path=Path(src_cert_file),
        key_path=Path(src_privkey_file),
        cert_out=Path(dest_cert_file),
        key_out=Path(dest_privkey_file),
    )
    # verify_certificates(dest_cert_file, dest_privkey_file)


def main():
    args = parse_args()

    try:
        env_name = args.command
        if not env_name:
            raise ValueError("ENV_NAME environment variable is not set.")

        replace_existing = os.environ.get("REPLACE_EXISTING", "false").lower() == "true"
        resolve_certificates(args)
        print(f"Certificates copied successfully for environment: {env_name}")
        exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        exit(2 if "do not match" in str(e).lower() else 1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
