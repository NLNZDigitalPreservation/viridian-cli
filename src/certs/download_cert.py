import base64
from pathlib import Path
from azure.identity import ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient


def download_cert(client_id, key_vault_name, cert_path, env_name="dev"):
    """Download a certificate from Azure Key Vault using managed identity.

    Args:
        client_id: The managed identity client ID.
        key_vault_name: The name of the Key Vault.
        cert_path: The local directory path to save the downloaded certificate.
        env_name: The environment name (default is "dev").
    """

    pfx_name = f"cert-wildcard-{env_name}-natlib-govt-nz"
    pfx_path = Path(
        f"{cert_path}/cert-wildcard-{env_name}-natlib-govt-nz/{pfx_name}.pfx"
    )
    pfx_path.parent.mkdir(parents=True, exist_ok=True)

    credential = ManagedIdentityCredential(client_id=client_id)
    vault_url = f"https://{key_vault_name}.vault.azure.net"
    client = SecretClient(vault_url=vault_url, credential=credential)

    secret = client.get_secret(pfx_name)
    cert_bytes = base64.b64decode(secret.value)

    with open(str(pfx_path), "wb") as f:
        f.write(cert_bytes)
