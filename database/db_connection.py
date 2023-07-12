import psycopg2
from decouple import config


def connect():
    try:
        db = psycopg2.connect(
            host=config("DB_HOST"),
            database=config("DB_NAME"),
            user=config("DB_USER"),
            password=config("DB_PASS")
        )
        cur = db.cursor()
        return db, cur
    except psycopg2.Error:
        db = psycopg2.connect(
            host=config("DB_HOST"),
            database=config("DB_NAME"),
            user=config("DB_USER"),
            password=config("DB_PASS")
        )
        cur = db.cursor()
        return db, cur
