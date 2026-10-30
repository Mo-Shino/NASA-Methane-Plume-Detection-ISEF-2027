"""
setup_earthdata.py
Automated NASA Earthdata Login & Token Configuration Tool.

Configures NASA Earthdata authentication credentials for EMIT data access:
    - Creates ~/.netrc and ~/_netrc formatted for urs.earthdata.nasa.gov
    - Supports Earthdata JWT tokens via EARTHDATA_TOKEN (.env)
    - Verifies authentication directly with NASA CMR / LP DAAC Cloud

Author: SpectraPlume Research Team (ISEF 2027)
"""

import os
import sys
from pathlib import Path

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

import earthaccess


def configure_token(token: str) -> bool:
    """Configures and tests NASA Earthdata Bearer Token."""
    os.environ["EARTHDATA_TOKEN"] = token
    env_file = Path.cwd() / ".env"
    env_file.write_text(f"EARTHDATA_TOKEN={token}\n", encoding="utf-8")
    print(f"[OK] Saved token to local environment: {env_file}")

    print("\nVerifying authentication with NASA Earthdata...")
    try:
        auth = earthaccess.login(strategy="environment")
        if auth.authenticated:
            print("[SUCCESS] Officially authenticated with NASA Earthdata!")
            print("[SUCCESS] Verified for NASA LP DAAC & EMIT data access.")
            return True
        else:
            print("[FAILED] Token authentication was unsuccessful.")
            return False
    except Exception as e:
        print(f"[ERROR] Error during authentication: {e}")
        return False


def configure_credentials(username: str, password: str) -> bool:
    """Writes credentials to .netrc and tests login."""
    home = Path.home()
    netrc_content = f"machine urs.earthdata.nasa.gov\n    login {username}\n    password {password}\n"

    for filename in [".netrc", "_netrc"]:
        netrc_file = home / filename
        netrc_file.write_text(netrc_content, encoding="utf-8")
        print(f"[OK] Saved NASA credentials to: {netrc_file}")

    try:
        auth = earthaccess.login(strategy="netrc")
        if auth.authenticated:
            print(f"[SUCCESS] User '{username}' logged in successfully.")
            return True
        else:
            print("[FAILED] Login failed. Check credentials.")
            return False
    except Exception as e:
        print(f"[ERROR] netrc authentication error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("   NASA Earthdata Authentication & Token Setup (SpectraPlume)")
    print("=" * 70)

    # Check if .env has token
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.startswith("EARTHDATA_TOKEN="):
                saved_tok = line.split("=", 1)[1].strip()
                if saved_tok:
                    print(f"Found saved token in .env, verifying...")
                    if configure_token(saved_tok):
                        sys.exit(0)

    if len(sys.argv) >= 2:
        arg = sys.argv[1]
        if len(arg) > 50:  # Token string
            configure_token(arg)
        elif len(sys.argv) >= 3:
            configure_credentials(sys.argv[1], sys.argv[2])
    else:
        print("Provide token as argument: python setup_earthdata.py <TOKEN>")
