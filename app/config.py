"""
Configuration for Medical Laboratory Management System.

Handles the split between:
  - Application files  (read-only, inside the PyInstaller bundle)
  - User data           (writable, lives in %PROGRAMDATA% on Windows)

This module works both when run normally with `python run.py` (for
development) and when frozen into an .exe with PyInstaller.
"""

import os
import sys
import platform


def is_frozen() -> bool:
    """True when running as a PyInstaller-built executable."""
    return getattr(sys, "frozen", False)


def get_app_dir() -> str:
    """
    Directory containing the bundled application (read-only at runtime).
    In a PyInstaller onefile build this is the temporary extraction dir
    (sys._MEIPASS); in dev mode it's this file's parent's parent.
    """
    if is_frozen():
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir() -> str:
    """
    Writable per-machine data directory for the database, backups,
    uploads, generated reports, and license info.

    Windows:  C:\\ProgramData\\MedicalLaboratoryManagementSystem\\
    macOS:    ~/Library/Application Support/MedicalLaboratoryManagementSystem/
    Linux:    ~/.local/share/MedicalLaboratoryManagementSystem/  (dev/testing)

    MEDLAB_DATA_DIR, if set, overrides all of the above on any platform —
    used by the test suite to fully isolate each test's data instead of
    sharing one real on-disk directory across every run.
    """
    app_name = "MedicalLaboratoryManagementSystem"

    override = os.environ.get("MEDLAB_DATA_DIR")
    if override:
        data_dir = override
    elif platform.system() == "Windows":
        base = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        data_dir = os.path.join(base, app_name)
    elif platform.system() == "Darwin":
        data_dir = os.path.join(
            os.path.expanduser("~/Library/Application Support"), app_name
        )
    else:
        # Linux — used during development/testing in this sandbox
        data_dir = os.path.join(os.path.expanduser("~/.local/share"), app_name)

    os.makedirs(data_dir, exist_ok=True)
    return data_dir


class Config:
    APP_NAME = "Medical Laboratory Management System"
    APP_DIR = get_app_dir()
    DATA_DIR = get_data_dir()

    # Subdirectories under the writable data dir
    DB_DIR = os.path.join(DATA_DIR, "database")
    BACKUP_DIR = os.path.join(DATA_DIR, "backups")
    UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
    REPORTS_DIR = os.path.join(DATA_DIR, "reports")
    LICENSE_DIR = os.path.join(DATA_DIR, "license")
    LOG_DIR = os.path.join(DATA_DIR, "logs")

    for _d in (DB_DIR, BACKUP_DIR, UPLOAD_DIR, REPORTS_DIR, LICENSE_DIR, LOG_DIR):
        os.makedirs(_d, exist_ok=True)

    DB_PATH = os.path.join(DB_DIR, "medlab.db")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get("MEDLAB_SECRET_KEY", "dev-key-change-in-production-please")

    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB upload limit

    LICENSE_FILE = os.path.join(LICENSE_DIR, "license.json")

    # Desktop server settings
    SERVER_HOST = "127.0.0.1"
    SERVER_PORT_RANGE = (5000, 5050)  # will scan for a free port in this range
