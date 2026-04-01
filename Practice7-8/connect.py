import psycopg2
import csv
from config import DB_CONFIG


def connect_csv_to_postgres_in_moment(filename):
    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            with open(filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)

                for row in reader:
                    username, phone = row
                    cur.execute("""
                        INSERT INTO contacts (username, phone)
                        VALUES (%s, %s)
                        ON CONFLICT (username) DO NOTHING
                    """, (username, phone))
        connect.commit()
