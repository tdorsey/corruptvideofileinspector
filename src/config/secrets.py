import logging
from pathlib import Path


def read_docker_secret(secret_name: str, secrets_dir: str = "/run/secrets") -> str | None:
    """
    Read a Docker secret from the specified secrets directory.

    Args:
        secret_name: The name of the secret file to read.
        secrets_dir: The directory where Docker secrets are mounted (default: /run/secrets).

    Returns:
        The secret value as a string, or None if not found or unreadable.
    """
    secret_path = Path(secrets_dir) / secret_name

    # For local development, also try with .txt extension
    if not secret_path.exists():
        secret_path_with_txt = Path(secrets_dir) / f"{secret_name}.txt"
        if secret_path_with_txt.exists():
            secret_path = secret_path_with_txt

    try:
        with secret_path.open("r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logging.getLogger(__name__).warning(
            f"Docker secret '{secret_name}' not found at {secret_path}"
        )
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error reading Docker secret '{secret_name}': {e}")
    return None
