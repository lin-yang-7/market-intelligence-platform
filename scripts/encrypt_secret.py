import argparse
import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON_PATH = ROOT / "backend" / "common"
if str(COMMON_PATH) not in sys.path:
    sys.path.insert(0, str(COMMON_PATH))

from mip_common.secrets import encrypt_secret  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Encrypt a secret for env var usage.")
    parser.add_argument("--value", default="", help="Secret value. Prompts when omitted.")
    parser.add_argument(
        "--key",
        default=os.getenv("SECRET_ENCRYPTION_KEY", ""),
        help="Encryption key. Defaults to SECRET_ENCRYPTION_KEY.",
    )
    args = parser.parse_args()
    value = args.value or getpass.getpass("Secret value: ")
    print(encrypt_secret(value, args.key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
