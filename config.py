import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

INSTANCE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "chave-temporaria-agendamento-rg-uaua"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL"
    )

    if DATABASE_URL:

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:

        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{INSTANCE_DIR / 'agendamento.db'}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False