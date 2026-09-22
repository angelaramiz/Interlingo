import json
import sqlite3
import sys


def main() -> None:
    if len(sys.argv) != 6:
        print("Uso: set_version.py <db_path> <clave> <versionCode> <versionName> <apkUrl>")
        sys.exit(2)
    db_path, clave, code, name, apk_url = sys.argv[1:6]
    valor = json.dumps(
        {"versionCode": int(code), "versionName": name, "apkUrl": apk_url}
    )
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS app_versions "
            "(clave TEXT PRIMARY KEY, valor TEXT NOT NULL)"
        )
        conn.execute(
            "INSERT INTO app_versions (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
            (clave, valor),
        )
        conn.commit()
    finally:
        conn.close()
    print(f"OK {clave} = {valor}")


if __name__ == "__main__":
    main()
