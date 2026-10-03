#!/usr/bin/env python3

"""
Extract a private key and build a correctly ordered fullchain from a PFX file.

Features:
  - Supports RSA and EC certificates/private keys.
  - Identifies the leaf certificate by matching its public key to the private key.
  - Places the leaf certificate first in fullchain.pem.
  - Orders intermediate certificates using issuer/subject relationships.
  - Omits self-signed root certificates from the fullchain.
  - Preserves Bag Attributes, subject, and issuer metadata.
  - Verifies that the private key matches the leaf certificate.
  - Prompts for the PFX password securely.

Requirements:
  - Python 3.8+
  - OpenSSL installed and available on PATH

Example:
  python3 build_fullchain.py certificate.pfx

  python3 build_fullchain.py certificate.pfx \
      --cert-out /etc/nginx/ssl/fullchain.pem \
      --key-out /etc/nginx/ssl/privkey.pem
"""

import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CERT_PATTERN = re.compile(
    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----",
    re.DOTALL,
)


def run_openssl(args, input_data=None, text=False):
    """Run OpenSSL and raise an informative error on failure."""

    command = ["openssl"] + args

    result = subprocess.run(
        command,
        input=input_data,
        capture_output=True,
        text=text,
    )

    if result.returncode != 0:
        stderr = result.stderr

        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

        raise RuntimeError(
            f"OpenSSL command failed:\n" f"  {' '.join(command)}\n" f"{stderr.strip()}"
        )

    return result.stdout


def split_certificates(pem_data):
    """
    Split a PEM bundle into individual certificates.

    Preserve the text preceding each certificate, including:
      - Bag Attributes
      - friendlyName
      - localKeyID
      - subject
      - issuer

    Each result contains:
      {
          "metadata": "...",
          "certificate": "-----BEGIN CERTIFICATE-----..."
      }
    """

    if isinstance(pem_data, bytes):
        pem_data = pem_data.decode("utf-8", errors="replace")

    matches = list(CERT_PATTERN.finditer(pem_data))

    if not matches:
        raise RuntimeError("No certificates were found in the PFX file.")

    certificates = []

    for index, match in enumerate(matches):

        # Capture the metadata between the previous certificate
        # and the current certificate.
        start = 0 if index == 0 else matches[index - 1].end()

        metadata = pem_data[start : match.start()].strip()
        certificate = match.group(0).strip()

        certificates.append(
            {
                "metadata": metadata,
                "certificate": certificate + "\n",
            }
        )

    return certificates


def certificate_public_key_hash(cert_path):
    """Return SHA-256 hash of the certificate's DER public key."""

    public_key_pem = run_openssl(
        [
            "x509",
            "-in",
            str(cert_path),
            "-pubkey",
            "-noout",
        ],
        text=True,
    )

    public_key_der = run_openssl(
        [
            "pkey",
            "-pubin",
            "-outform",
            "DER",
        ],
        input_data=public_key_pem.encode("utf-8"),
    )

    return hashlib.sha256(public_key_der).hexdigest()


def private_key_public_key_hash(key_path):
    """Return SHA-256 hash of the public component of a private key."""

    public_key_der = run_openssl(
        [
            "pkey",
            "-in",
            str(key_path),
            "-pubout",
            "-outform",
            "DER",
        ],
    )

    return hashlib.sha256(public_key_der).hexdigest()


def certificate_subject_issuer(cert_path):
    """Return the subject and issuer distinguished names."""

    output = run_openssl(
        [
            "x509",
            "-in",
            str(cert_path),
            "-noout",
            "-subject",
            "-issuer",
            "-nameopt",
            "RFC2253",
        ],
        text=True,
    )

    subject = None
    issuer = None

    for line in output.splitlines():

        line = line.strip()

        if line.startswith("subject="):
            subject = line[len("subject=") :].strip()

        elif line.startswith("issuer="):
            issuer = line[len("issuer=") :].strip()

    if not subject or not issuer:
        raise RuntimeError(f"Could not determine subject/issuer for {cert_path}")

    return subject, issuer


def is_self_signed(cert_path):
    """Check whether subject and issuer names are identical."""

    subject, issuer = certificate_subject_issuer(cert_path)

    return subject == issuer


def order_certificates(cert_paths, leaf_path):
    """
    Order certificates as leaf followed by its intermediate chain.

    Uses issuer/subject name matching. This is not a full cryptographic
    certificate-chain validation procedure.
    """

    remaining = [
        path for path in cert_paths if path != leaf_path and not is_self_signed(path)
    ]

    ordered = [leaf_path]
    current = leaf_path

    while remaining:

        _, current_issuer = certificate_subject_issuer(current)

        matches = []

        for candidate in remaining:

            candidate_subject, _ = certificate_subject_issuer(candidate)

            if candidate_subject == current_issuer:
                matches.append(candidate)

        if not matches:
            break

        # If multiple certificates match, choose the first one found
        # in the original PFX bundle.
        next_cert = matches[0]

        ordered.append(next_cert)
        remaining.remove(next_cert)

        current = next_cert

    return ordered, remaining


def write_fullchain(cert_out, ordered, cert_metadata):
    """
    Write the fullchain with the leaf first.

    Metadata is preserved as comments so that the PEM certificate
    blocks remain readable and usable by Nginx.
    """

    cert_out.parent.mkdir(parents=True, exist_ok=True)

    with cert_out.open("w", encoding="utf-8") as output:

        for cert_path in ordered:

            metadata = cert_metadata.get(cert_path, "").strip()

            if metadata:

                for line in metadata.splitlines():
                    output.write(f"# {line}\n")

            output.write(cert_path.read_text(encoding="utf-8").rstrip())

            output.write("\n")


def sort_certificates_in_chain(
    certs_path: Path, key_path: Path, cert_out: Path, key_out: Path
) -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="pfx-fullchain-") as tmp:

            temp_dir = Path(tmp)

            # Split the certificate bundle while preserving metadata.
            cert_entries = split_certificates(certs_path.read_bytes())

            cert_paths = []
            cert_metadata = {}

            for index, entry in enumerate(cert_entries):

                cert_path = temp_dir / f"certificate_{index:03d}.pem"

                cert_path.write_text(
                    entry["certificate"],
                    encoding="utf-8",
                )

                cert_paths.append(cert_path)

                # Keep metadata associated with its original certificate.
                cert_metadata[cert_path] = entry["metadata"]

            print(f"Found {len(cert_paths)} certificate(s).")

            # Identify the leaf by comparing its public key with the key.
            key_hash = private_key_public_key_hash(key_path)

            leaf_path = None

            for cert_path in cert_paths:

                cert_hash = certificate_public_key_hash(cert_path)

                if cert_hash == key_hash:
                    leaf_path = cert_path
                    break

            if leaf_path is None:
                raise RuntimeError(
                    "No certificate matches the extracted private key. "
                    "Check that the PFX contains the correct key and "
                    "certificate."
                )

            print("Matching leaf certificate found.")

            # Order the leaf and intermediate certificates.
            ordered, unlinked = order_certificates(
                cert_paths,
                leaf_path,
            )

            if unlinked:

                print(
                    f"WARNING: {len(unlinked)} certificate(s) could "
                    "not be linked to the leaf chain."
                )

                for cert_path in unlinked:

                    subject, issuer = certificate_subject_issuer(cert_path)

                    print(f"  Subject: {subject}")
                    print(f"  Issuer:  {issuer}")

                print("These certificates will not be included in " "fullchain.pem.")

            # Write fullchain with metadata preserved.
            write_fullchain(
                cert_out,
                ordered,
                cert_metadata,
            )

            # Write private key and restrict permissions.
            key_out.parent.mkdir(parents=True, exist_ok=True)

            key_out.write_bytes(key_path.read_bytes())
            key_out.chmod(0o600)

            # Verify the final output certificate matches the key.
            final_cert_hash = certificate_public_key_hash(leaf_path)

            final_key_hash = private_key_public_key_hash(key_out)

            if final_cert_hash != final_key_hash:
                raise RuntimeError(
                    "Final verification failed: certificate and key "
                    "public keys do not match."
                )

            print("\nSUCCESS")
            print(f"Fullchain: {cert_out}")
            print(f"Private key: {key_out}")
            print(f"Certificates in fullchain: {len(ordered)}")
            print("Certificate metadata preserved.")
            print("Private key matches the leaf certificate.")
            print("Private key permissions set to 600.")
            return 0

    except Exception as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1
