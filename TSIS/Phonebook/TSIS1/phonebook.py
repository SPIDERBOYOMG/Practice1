"""
phonebook.py — TSIS1 PhoneBook Console Application
Extends Practice 7-8 menu with new features.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from connect import (
    setup_schema,
    insert_from_console,
    get_all,
    get_all_paginated,
    update_contact,
    add_phone_console,
    list_groups,
    move_to_group_console,
    filter_by_group,
    search_all,
    search_by_email,
    connect_csv_to_postgres_in_moment,
    export_to_json,
    import_from_json,
)


# ─────────────────────────────────────────────
# Display helpers
# ─────────────────────────────────────────────

HEADER = f"{'ID':<5} {'Name':<20} {'Email':<25} {'Birthday':<12} {'Group':<10} {'Phones'}"
SEP    = "─" * 90


def _print_rows(rows):
    if not rows:
        print("  (no results)")
        return
    print(SEP)
    print(HEADER)
    print(SEP)
    for row in rows:
        cid, name, email, bday, grp, phones = row
        print(f"{str(cid):<5} {str(name):<20} {str(email or ''):<25} "
              f"{str(bday or ''):<12} {str(grp or ''):<10} {phones or ''}")
    print(SEP)


# ─────────────────────────────────────────────
# Paginated browse loop
# ─────────────────────────────────────────────

def paginated_browse():
    PAGE_SIZE = 5
    order_by  = "username"
    print("\nSort by: (1) name  (2) birthday  (3) date added")
    s = input("Choice [1]: ").strip()
    if s == "2":
        order_by = "birthday"
    elif s == "3":
        order_by = "created_at"

    page = 1
    while True:
        rows, total = get_all_paginated(page, PAGE_SIZE, order_by)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        print(f"\n── Page {page}/{total_pages} (total {total} contacts) ──")
        _print_rows(rows)
        print("  [n]ext  [p]rev  [q]uit")
        cmd = input(">> ").strip().lower()
        if cmd == "n" and page < total_pages:
            page += 1
        elif cmd == "p" and page > 1:
            page -= 1
        elif cmd == "q":
            break


# ─────────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════╗
║        PhoneBook  TSIS1              ║
╠══════════════════════════════════════╣
║  SETUP                               ║
║   1. Init / update schema & procs    ║
╠══════════════════════════════════════╣
║  CONTACTS                            ║
║   2. Add contact                     ║
║   3. Show all (sorted)               ║
║   4. Browse with pagination          ║
║   5. Update contact                  ║
╠══════════════════════════════════════╣
║  PHONES & GROUPS                     ║
║   6. Add phone to contact            ║
║   7. Move contact to group           ║
║   8. Filter contacts by group        ║
╠══════════════════════════════════════╣
║  SEARCH                              ║
║   9. Search (name / email / phone)   ║
║  10. Search by email                 ║
╠══════════════════════════════════════╣
║  IMPORT / EXPORT                     ║
║  11. Import from CSV                 ║
║  12. Export to JSON                  ║
║  13. Import from JSON                ║
╠══════════════════════════════════════╣
║   0. Exit                            ║
╚══════════════════════════════════════╝
"""


def main():
    while True:
        print(MENU)
        choice = input("Choose: ").strip()

        if choice == "1":
            setup_schema()

        elif choice == "2":
            insert_from_console()

        elif choice == "3":
            print("\nSort by: (1) name  (2) birthday  (3) date added")
            s = input("Choice [1]: ").strip()
            order = {"2": "birthday", "3": "created_at"}.get(s, "username")
            _print_rows(get_all(order_by=order))

        elif choice == "4":
            paginated_browse()

        elif choice == "5":
            name = input("Enter username to update: ").strip()
            update_contact(name)

        elif choice == "6":
            add_phone_console()

        elif choice == "7":
            move_to_group_console()

        elif choice == "8":
            rows = filter_by_group()
            _print_rows(rows)

        elif choice == "9":
            q = input("Search query: ").strip()
            results = search_all(q)
            if not results:
                print("  (no results)")
            else:
                print(SEP)
                print(f"{'ID':<5} {'Name':<20} {'Email':<25} {'Birthday':<12} {'Group':<10} {'Phone':<15} {'Type'}")
                print(SEP)
                for row in results:
                    cid, name, email, bday, grp, phone, ptype = row
                    print(f"{str(cid):<5} {str(name):<20} {str(email or ''):<25} "
                          f"{str(bday or ''):<12} {str(grp or ''):<10} "
                          f"{str(phone or ''):<15} {ptype or ''}")
                print(SEP)

        elif choice == "10":
            q = input("Email query: ").strip()
            results = search_by_email(q)
            if not results:
                print("  (no results)")
            else:
                print(SEP)
                print(f"{'ID':<5} {'Name':<20} {'Email':<25} {'Birthday':<12} {'Group'}")
                print(SEP)
                for row in results:
                    print(f"{str(row[0]):<5} {str(row[1]):<20} {str(row[2] or ''):<25} "
                          f"{str(row[3] or ''):<12} {str(row[4] or '')}")
                print(SEP)

        elif choice == "11":
            fname = input("CSV filename [contacts.csv]: ").strip() or "contacts.csv"
            connect_csv_to_postgres_in_moment(fname)

        elif choice == "12":
            fname = input("Output filename [contacts_export.json]: ").strip() or "contacts_export.json"
            export_to_json(fname)

        elif choice == "13":
            fname = input("JSON filename [contacts_export.json]: ").strip() or "contacts_export.json"
            import_from_json(fname)

        elif choice == "0":
            print("Goodbye!")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
