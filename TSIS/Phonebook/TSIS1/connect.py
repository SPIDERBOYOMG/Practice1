"""
connect.py — Database helpers for TSIS1 PhoneBook
Extends Practice 7-8 connect.py with new schema support.
"""

import os
import psycopg2
import csv
import json
from config import DB_CONFIG

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_path(path):
    return path if os.path.isabs(path) else os.path.join(BASE_DIR, path)


# ─────────────────────────────────────────────
# Internal helper
# ─────────────────────────────────────────────

def _conn():
    """Return a new psycopg2 connection."""
    return psycopg2.connect(**DB_CONFIG)


def _run_sql_file(path):
    """Execute a .sql file against the DB."""
    path = _resolve_path(path)
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute(sql)
        con.commit()
    print(f"Executed {path}")


# ─────────────────────────────────────────────
# Schema setup
# ─────────────────────────────────────────────

def setup_schema():
    """Apply schema.sql and procedures.sql."""
    _run_sql_file("schema.sql")
    _run_sql_file("procedures.sql")
    print("Schema and procedures ready.")


# ─────────────────────────────────────────────
# CRUD — contacts
# ─────────────────────────────────────────────

def insert_from_console():
    username = input("Name: ").strip()
    phone    = input("Primary phone: ").strip()
    email    = input("Email (leave blank to skip): ").strip() or None
    bday     = input("Birthday YYYY-MM-DD (leave blank to skip): ").strip() or None

    groups   = list_groups()
    print("Groups:", ", ".join(f"{g[0]}.{g[1]}" for g in groups))
    gid_str  = input("Group id (leave blank to skip): ").strip()
    if gid_str:
        try:
            group_id = int(gid_str)
        except ValueError:
            print("Invalid group id entered, skipping group assignment.")
            group_id = None
    else:
        group_id = None

    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                INSERT INTO contacts (username, phone, email, birthday, group_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, (username, phone, email, bday, group_id))
        con.commit()
    print(f"Contact '{username}' added.")


def get_all(order_by="username"):
    """Fetch all contacts with their group and phones."""
    allowed = {"username", "birthday", "created_at"}
    if order_by not in allowed:
        order_by = "username"

    with _conn() as con:
        with con.cursor() as cur:
            cur.execute(f"""
                SELECT c.id, c.username, c.email, c.birthday, g.name AS grp,
                STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ') AS phones
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                GROUP BY c.id, c.username, c.email, c.birthday, g.name
                ORDER BY c.{order_by} NULLS LAST
            """)
            return cur.fetchall()


def get_all_paginated(page=1, page_size=5, order_by="username"):
    """Paginated contacts using the Practice-8 DB function."""
    allowed = {"username", "birthday", "created_at"}
    if order_by not in allowed:
        order_by = "username"

    offset = (page - 1) * page_size
    with _conn() as con:
        with con.cursor() as cur:
            # Use the existing paginated function; order_by applied in wrapper
            cur.execute(f"""
                SELECT c.id, c.username, c.email, c.birthday, g.name AS grp,
                STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ') AS phones
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                GROUP BY c.id, c.username, c.email, c.birthday, g.name
                ORDER BY c.{order_by} NULLS LAST
                LIMIT %s OFFSET %s
            """, (page_size, offset))
            rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM contacts")
            total = cur.fetchone()[0]
    return rows, total


def update_contact(username):
    choice = input("Update: (1)name  (2)email  (3)birthday  (4)group: ").strip()
    with _conn() as con:
        with con.cursor() as cur:
            if choice == "1":
                val = input("New name: ").strip()
                cur.execute("UPDATE contacts SET username=%s WHERE username=%s", (val, username))
            elif choice == "2":
                val = input("New email: ").strip()
                cur.execute("UPDATE contacts SET email=%s WHERE username=%s", (val, username))
            elif choice == "3":
                val = input("New birthday YYYY-MM-DD: ").strip()
                cur.execute("UPDATE contacts SET birthday=%s WHERE username=%s", (val, username))
            elif choice == "4":
                groups = list_groups()
                print("Groups:", ", ".join(f"{g[0]}.{g[1]}" for g in groups))
                gid = int(input("Group id: ").strip())
                cur.execute("UPDATE contacts SET group_id=%s WHERE username=%s", (gid, username))
            else:
                print("Invalid choice.")
                return
        con.commit()
    print("Updated.")


# ─────────────────────────────────────────────
# Phones
# ─────────────────────────────────────────────

def add_phone_console():
    name  = input("Contact name: ").strip()
    phone = input("Phone number: ").strip()
    ptype = input("Type (home/work/mobile): ").strip()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
        con.commit()
    print("Phone added.")


# ─────────────────────────────────────────────
# Groups
# ─────────────────────────────────────────────

def list_groups():
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT id, name FROM groups ORDER BY name")
            return cur.fetchall()


def move_to_group_console():
    name  = input("Contact name: ").strip()
    group = input("Group name: ").strip()
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("CALL move_to_group(%s, %s)", (name, group))
        con.commit()
    print(f"Moved '{name}' to group '{group}'.")


def filter_by_group():
    groups = list_groups()
    print("Available groups:")
    for gid, gname in groups:
        print(f"  {gid}. {gname}")
    gid = int(input("Enter group id: ").strip())

    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.username, c.email, c.birthday, g.name,
                STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')', ', ')
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                LEFT JOIN phones p ON p.contact_id = c.id
                WHERE c.group_id = %s
                GROUP BY c.id, c.username, c.email, c.birthday, g.name
                ORDER BY c.username
            """, (gid,))
            return cur.fetchall()


# ─────────────────────────────────────────────
# Search
# ─────────────────────────────────────────────

def search_all(query):
    """Uses the search_contacts DB function (name + email + all phones)."""
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (query,))
            return cur.fetchall()


def search_by_email(query):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.username, c.email, c.birthday, g.name
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                WHERE c.email ILIKE %s
                ORDER BY c.username
            """, (f"%{query}%",))
            return cur.fetchall()


# ─────────────────────────────────────────────
# CSV Import (extended from Practice 7)
# ─────────────────────────────────────────────

def connect_csv_to_postgres_in_moment(filename):
    """
    Extended CSV importer.
    Expected columns: username, phone, type, email, birthday, group
    Falls back gracefully if new columns are absent.
    """
    imported = skipped = 0
    filename = _resolve_path(filename)
    with _conn() as con:
        with con.cursor() as cur:
            with open(filename, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    username = row.get("username", "").strip()
                    phone    = row.get("phone", "").strip()
                    ptype    = row.get("type", "mobile").strip() or "mobile"
                    email    = row.get("email", "").strip() or None
                    birthday = row.get("birthday", "").strip() or None
                    group    = row.get("group", "").strip() or None

                    if not username or not phone:
                        skipped += 1
                        continue

                    # Resolve group_id
                    group_id = None
                    if group:
                        cur.execute("""
                            INSERT INTO groups (name) VALUES (%s)
                            ON CONFLICT (name) DO NOTHING;
                            SELECT id FROM groups WHERE name=%s
                        """, (group, group))
                        # psycopg2 only executes one statement; do two calls:
                        cur.execute("INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (group,))
                        cur.execute("SELECT id FROM groups WHERE name=%s", (group,))
                        row_g = cur.fetchone()
                        group_id = row_g[0] if row_g else None

                    # Upsert contact
                    cur.execute("""
                        INSERT INTO contacts (username, phone, email, birthday, group_id)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (username) DO NOTHING
                        RETURNING id
                    """, (username, phone, email, birthday, group_id))
                    result = cur.fetchone()
                    if result:
                        contact_id = result[0]
                        cur.execute("""
                            INSERT INTO phones (contact_id, phone, type)
                            VALUES (%s, %s, %s)
                        """, (contact_id, phone, ptype))
                        imported += 1
                    else:
                        skipped += 1
        con.commit()
    print(f"CSV import: {imported} inserted, {skipped} skipped.")


# ─────────────────────────────────────────────
# JSON Export / Import
# ─────────────────────────────────────────────

def export_to_json(filename="contacts_export.json"):
    with _conn() as con:
        with con.cursor() as cur:
            cur.execute("""
                SELECT c.id, c.username, c.email,
                c.birthday::TEXT, g.name AS group_name,
                c.created_at::TEXT
                FROM contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                ORDER BY c.username
            """)
            contacts_raw = cur.fetchall()

            data = []
            for cid, username, email, birthday, group_name, created_at in contacts_raw:
                cur.execute("""
                    SELECT phone, type FROM phones
                    WHERE contact_id = %s
                    ORDER BY id
                """, (cid,))
                phones = [{"phone": r[0], "type": r[1]} for r in cur.fetchall()]
                data.append({
                    "username":   username,
                    "email":      email,
                    "birthday":   birthday,
                    "group":      group_name,
                    "phones":     phones,
                    "created_at": created_at,
                })

    filename = _resolve_path(filename)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Exported {len(data)} contacts to '{filename}'.")


def import_from_json(filename="contacts_export.json"):
    filename = _resolve_path(filename)
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    imported = skipped = overwritten = 0
    with _conn() as con:
        with con.cursor() as cur:
            for entry in data:
                username = entry.get("username", "").strip()
                if not username:
                    skipped += 1
                    continue

                # Check duplicate
                cur.execute("SELECT id FROM contacts WHERE username=%s", (username,))
                existing = cur.fetchone()

                if existing:
                    ans = input(f"  '{username}' already exists. (s)kip or (o)verwrite? ").strip().lower()
                    if ans != "o":
                        skipped += 1
                        continue
                    # Delete old phones, update contact
                    cur.execute("DELETE FROM phones WHERE contact_id=%s", (existing[0],))
                    contact_id = existing[0]
                    overwritten += 1
                else:
                    # Resolve group
                    group_id = None
                    if entry.get("group"):
                        cur.execute("INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (entry["group"],))
                        cur.execute("SELECT id FROM groups WHERE name=%s", (entry["group"],))
                        row_g = cur.fetchone()
                        group_id = row_g[0] if row_g else None

                    primary_phone = entry["phones"][0]["phone"] if entry.get("phones") else ""
                    cur.execute("""
                        INSERT INTO contacts (username, phone, email, birthday, group_id)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (username, primary_phone, entry.get("email"), entry.get("birthday"), group_id))
                    contact_id = cur.fetchone()[0]
                    imported += 1

                # Insert phones
                for ph in entry.get("phones", []):
                    cur.execute("""
                        INSERT INTO phones (contact_id, phone, type)
                        VALUES (%s, %s, %s)
                    """, (contact_id, ph.get("phone"), ph.get("type")))

        con.commit()
    print(f"JSON import: {imported} inserted, {overwritten} overwritten, {skipped} skipped.")
