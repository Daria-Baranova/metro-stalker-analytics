import io
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
EXPORT_DIR = ROOT / "superset" / "export"
CONTAINER_ZIP = "/tmp/dashboard.zip"

load_dotenv(ROOT / ".env")


def superset(*args, **kwargs):
    return subprocess.run(
        ["docker", "compose", "exec", "-T", "superset", *args],
        cwd=ROOT, check=True, **kwargs,
    )


def database_uri():
    user = os.environ["POSTGRES_USER"]
    password = quote(os.environ["POSTGRES_PASSWORD"], safe="")
    database = os.environ["POSTGRES_DB"]
    return f"postgresql://{user}:{password}@postgres:5432/{database}"


def export_dashboard():
    superset("superset", "export-dashboards", "-f", CONTAINER_ZIP)
    data = superset("cat", CONTAINER_ZIP, capture_output=True).stdout
    superset("rm", CONTAINER_ZIP)
    shutil.rmtree(EXPORT_DIR, ignore_errors=True)
    with zipfile.ZipFile(io.BytesIO(data)) as bundle:
        for name in bundle.namelist():
            target = EXPORT_DIR / Path(*Path(name).parts[1:])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bundle.read(name))


def import_dashboard():
    superset("superset", "db", "upgrade")
    superset("sh", "-c", 'superset fab create-admin --username admin --firstname Admin --lastname Metro --email admin@example.com --password "$SUPERSET_ADMIN_PASSWORD"')
    superset("superset", "init")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as bundle:
        for file in EXPORT_DIR.rglob("*.yaml"):
            text = file.read_text(encoding="utf-8")
            if file.parent.name == "databases":
                text = re.sub(r"^sqlalchemy_uri: .*$", f"sqlalchemy_uri: {database_uri()}", text, flags=re.MULTILINE)
            bundle.writestr(f"dashboard/{file.relative_to(EXPORT_DIR).as_posix()}", text)
    superset("sh", "-c", f"cat > {CONTAINER_ZIP}", input=buffer.getvalue())
    try:
        superset("superset", "import-dashboards", "-p", CONTAINER_ZIP, "-u", "admin")
    finally:
        superset("rm", CONTAINER_ZIP)


if __name__ == "__main__":
    {"export": export_dashboard, "import": import_dashboard}[sys.argv[1]]()