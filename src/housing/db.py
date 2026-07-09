"""Helpers de conexión para MongoDB y PostgreSQL."""
from contextlib import contextmanager

import psycopg
from pymongo import MongoClient
from pymongo.database import Database

from .config import settings


def get_mongo_client() -> MongoClient:
    return MongoClient(settings.mongo_uri)


def get_mongo_db(name: str = "housing") -> Database:
    return get_mongo_client()[name]


@contextmanager
def get_postgres():
    conn = psycopg.connect(settings.postgres_uri)
    try:
        yield conn
    finally:
        conn.close()
