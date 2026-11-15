
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "chave-temporaria-agendamento-rg-uaua"
    )

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:

        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql+psycopg://",
                1
            )

        elif DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:

        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{INSTANCE_DIR / 'agendamento.db'}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
