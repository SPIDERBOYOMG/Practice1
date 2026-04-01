import psycopg2

DB_CONFIG = {
  #я вам так и покажу
}


def create_table():
    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    phone VARCHAR(100) NOT NULL
                )
            """)
        connect.commit()


def insert_from_console():
    username = input("Name: ")
    phone = input("Phone: ")

    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            cur.execute("""
                INSERT INTO contacts (username, phone)
                VALUES (%s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, phone))
        connect.commit()


def get_all():
    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            cur.execute("SELECT * FROM contacts")
            for row in cur.fetchall():
                print(row)


def search_by_name(name):
    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            cur.execute("""
                SELECT * FROM contacts
                WHERE username ILIKE %s
            """, (f"%{name}%",))
            print(cur.fetchall())


def search_by_phone_prefix(phone):
    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            cur.execute("""
                SELECT * FROM contacts
                WHERE phone LIKE %s
            """, (f"{phone}%",))
            print(cur.fetchall())


def update_contact(username):
    choice = input("Update (1)name or (2)phone: ")

    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            if choice == "1":
                new_name = input("New name: ")
                cur.execute("""
                    UPDATE contacts
                    SET username = %s
                    WHERE username = %s
                """, (new_name, username))
                print("name updated")

            elif choice == "2":
                new_phone = input("New phone: ")
                cur.execute("""
                    UPDATE contacts
                    SET phone = %s
                    WHERE username = %s
                """, (new_phone, username))
                print("phone updated")

            else:
                print("operation does not exist")
        connect.commit()


def delete_contact():
    choice = input("Delete by (1)name or (2)phone: ")

    with psycopg2.connect(**DB_CONFIG) as connect:
        with connect.cursor() as cur:
            if choice == "1":
                name = input("Enter name: ")
                cur.execute("DELETE FROM contacts WHERE username = %s", (name,))
            elif choice == "2":
                phone = input("Enter phone: ")
                cur.execute("DELETE FROM contacts WHERE phone = %s", (phone,))
            else:
                print("operation does not exist")
        connect.commit()
