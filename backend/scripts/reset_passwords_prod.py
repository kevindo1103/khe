"""One-shot admin script: reset all active TenantUser passwords to random values.

Usage (on prod VPS):
    cd /opt/khe/backend
    python scripts/reset_passwords_prod.py

Prints a plaintext table of username / tenant / new_password BEFORE writing to DB.
Confirm the print-out, then the script commits. Output is printed to stdout only —
NOT logged to any file. Deliver credentials securely (do not paste in chat/email).
"""
import secrets
import string
import sqlite3
from pathlib import Path
from tabulate import tabulate  # pip install tabulate if needed; fallback below

DB_PATH = Path(__file__).resolve().parents[1] / "master.db"

# Password alphabet: alphanumeric + safe specials (no ambiguous chars)
ALPHABET = string.ascii_letters + string.digits + "!@#$%^&*"
PASSWORD_LENGTH = 16


def _random_password() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(PASSWORD_LENGTH))


def _hash_password(plain: str) -> str:
    import bcrypt  # direct bcrypt — never passlib (see CLAUDE.md bug pattern)
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"master.db not found at {DB_PATH}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT id, tenant_id, username FROM tenant_users WHERE is_active = 1"
    ).fetchall()

    if not rows:
        print("No active users found.")
        conn.close()
        return

    # Generate new credentials
    entries = []
    for row in rows:
        new_pw = _random_password()
        entries.append({
            "id": row["id"],
            "tenant_id": row["tenant_id"],
            "username": row["username"],
            "new_password": new_pw,
            "new_hash": _hash_password(new_pw),
        })

    # Print table BEFORE writing — confirm visually
    print("\n" + "=" * 60)
    print("NEW CREDENTIALS — deliver securely, do NOT share via chat")
    print("=" * 60)
    try:
        print(tabulate(
            [[e["tenant_id"], e["username"], e["new_password"]] for e in entries],
            headers=["tenant_id", "username", "new_password"],
            tablefmt="grid",
        ))
    except ImportError:
        # Fallback if tabulate not installed
        print(f"{'tenant_id':<30} {'username':<20} {'new_password':<20}")
        print("-" * 72)
        for e in entries:
            print(f"{e['tenant_id']:<30} {e['username']:<20} {e['new_password']:<20}")

    print("=" * 60)
    print(f"\nTotal: {len(entries)} active account(s) will be updated.\n")

    confirm = input("Type YES to commit password changes to DB: ").strip()
    if confirm != "YES":
        print("Aborted — no changes written.")
        conn.close()
        return

    # Commit
    for e in entries:
        cur.execute(
            "UPDATE tenant_users SET hashed_password = ? WHERE id = ?",
            (e["new_hash"], e["id"]),
        )
    conn.commit()
    conn.close()

    print(f"\nDone. {len(entries)} password(s) updated in master.db.")
    print("Re-print the table above and deliver credentials now.")


if __name__ == "__main__":
    main()
