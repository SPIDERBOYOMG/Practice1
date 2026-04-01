from config import *
from connect import *


while True:
    print("""
1. Create table
2. Import from CSV
3. Add contact
4. Show all
5. Search by name
6. Search by phone
7. Update contact
8. Delete contact
0. Exit
""")

    choice = input("Choose: ")

    if choice == "1":
        create_table()

    elif choice == "2":
        connect_csv_to_postgres_in_moment("contacts.csv")

    elif choice == "3":
        insert_from_console()

    elif choice == "4":
        get_all()

    elif choice == "5":
        name = input("Enter name: ")
        search_by_name(name)

    elif choice == "6":
        phone = input("Enter phone prefix: ")
        search_by_phone_prefix(phone)

    elif choice == "7":
        username = input("Enter username: ")
        update_contact(username)

    elif choice == "8":
        delete_contact()

    elif choice == "0":
        print("Goodbye!")
        break

    else:
        print("Invalid choice")
