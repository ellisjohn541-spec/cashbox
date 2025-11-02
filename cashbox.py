# Cashbox V.1
# Created by John Ellis
# Command line program designed for tracking monthly direct debits, savings and investments
# Please read the text document for instructions and more details on how to yse the program

# License information:
# This project is open source for educational and portfolio use
# You are more than welcome to enjoy using, or modify the program

# I plan on upgrading cashbox with a GUI using Tkinter as a future project

import sqlite3
from datetime import datetime

DB_NAME = "finance.db"
DB_SAVINGS = "savings.db"
DB_INVEST = "investments.db"

#----------------------------
#Database(s) Setup / Utility
#----------------------------

def connect_db():
    '''Connect to SQLite database (creates if it does not exist).'''
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    return conn, cursor

def setup_tables():
    '''Create database tables if they don't exist'''
    conn, cursor = connect_db()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS direct_debits (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   amount REAL NOT NULL,
                   due_day INTEGER,
                   active INTEGER DEFAULT 1)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   debit_id INTEGER,
                   month TEXT,
                   date TEXT DEFAULT CURRENT_DATE,
                   note TEXT)""")
    
    
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   amount REAL NOT NULL,
                   date TEXT DEFAULT CURRENT_DATE,
                   note TEXT)""")
    
    conn.commit()
    conn.close()

def savings_db():
    '''Connect to savings SQLite database (creates if it does not exist).'''
    conn = sqlite3.connect(DB_SAVINGS)
    cursor = conn.cursor()
    return conn, cursor

def setup_tables_savings():
    '''Creates the database tables if they don't exist'''

    conn, cursor = savings_db()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS savings (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   account_name TEXT NOT NULL,
                   balance REAL NOT NULL,
                   interest_rate REAL NOT NULL,
                   last_update TEXT DEFAULT CURRENT_DATE)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS contributions (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   savings_id INTEGER,
                   amount REAL NOT NULL,
                   date TEXT DEFAULT CURRENT_DATE,
                   FOREIGN KEY(savings_id) REFERENCES savings(id))""")
    
    conn.commit()
    conn.close()

def connect_invest_db():
    '''connect to the investments database (creates if missing)'''
    conn = sqlite3.connect(DB_INVEST)
    cursor = conn.cursor()
    return conn, cursor

def setup_invest_tables():
    '''create investment related tables if not already created'''
    conn, cursor = connect_invest_db()

    cursor.execute("""CREATE TABLE IF NOT EXISTS portfolios (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)""")

    cursor.execute("""CREATE TABLE IF NOT EXISTS contributions (id INTEGER PRIMARY KEY AUTOINCREMENT, portfolio_id INTEGER, amount REAL NOT NULL, date TEXT DEFAULT CURRENT_DATE, FOREIGN KEY (portfolio_id) REFERENCES portfolios(id))""")

    conn.commit()
    conn.close()

    
#Core features monthly module

def add_income():
    '''record new income entry'''
    conn, cursor = connect_db()
    try:
        amount = float(input("Enter Income Amount: £"))
        note = input("Enter Notes: ")
        cursor.execute("INSERT INTO income (amount, note) VALUES (?,?)", (amount, note))
        conn.commit()
        print(f"Income of £{amount:.2f} recorded succesfully.\n")
    except ValueError:
        print("Invalid input. Please enter a numerical value.")
    finally:
        conn.close()
        
def view_direct_debit():
    '''Display all direct debits'''
    conn, cursor = connect_db()
    cursor.execute("SELECT id, name, amount, due_day, active FROM direct_debits")
    debits = cursor.fetchall()
    conn.close()
    
    if not debits:
        print("No direct debits found.\n")
        return
    
    print("\n---Direct Debits---")
    for d in debits:
        status = "Active" if d[4] else "Inactive"
        print (f"[{d[0]}] {d[1]} - £{d[2]:.2f} (Due: {d[3]}) [{status}]")
    print()
    
def add_direct_debit():
    '''Add a new recurring direct debit'''
    conn, cursor = connect_db()
    try:
        name = input("Enter name: ")
        amount = float(input("Enter amount: £"))
        due_day = int(input("Enter due date (1-31): "))
        cursor.execute("INSERT INTO direct_debits (name, amount, due_day) VALUES (?, ?, ?)", (name, amount, due_day), )
        conn.commit()
        print(f"Added {name} (£{amount:2f}) successfully.\n")
    except ValueError:
        print("Invalid input. Please try again.")
    finally:
        conn.close()
        
def calculate_remaining():
    '''Show how much spending money is left'''
    conn, cursor = connect_db()
    #get total income
    cursor.execute("SELECT SUM(amount) FROM income")
    income_total = cursor.fetchone()[0] or 0

    #Get total outgoings

    cursor.execute("SELECT SUM(amount) FROM direct_debits WHERE active=1")
    outgoing_total = cursor.fetchone()[0] or 0
    
    remaining = income_total - outgoing_total

    print("\n--Summery--")
    print(f"Total Income: £{income_total:.2f}")
    print(f"Total Outgoings: £{outgoing_total:.2f}")
    print(f"Spending Money Left: £{remaining:.2f}\n")

    conn.close()
    
def debit_paid():
    '''show all direct debits'''
    conn, cursor = connect_db()
    cursor.execute("SELECT id, name, amount FROM direct_debits WHERE active = 1")
    rows = cursor.fetchall()
    
    if not rows:
        print("No active direct debits found")
        conn.close()
        return
    
    print("\nActive Direct Debits:")
    for row in rows:
        print(f"{row[0]}. {row[1]} - £{row[2]:.2f}")
          
    try:
        debit_id = int(input("\nEnter the ID of the debit to mark as paid: "))
    except ValueError:
        print("Invalid Input")
        return
    
    month = input("Enter Month (e.g October 2025): ")
    note = input("Add a note: ")
    
    cursor.execute("INSERT INTO payments (debit_id, month, note) VALUES (?, ?, ?)", (debit_id, month, note))
    
    conn.commit()
    conn.close()
    print("Payment Recorded Successfully.")

#core features savings module

def add_savings_account():

    conn, cursor = savings_db()
    name = input("Enter Account Name: ")
    balance = float(input("Enter current balance: £"))
    rate = float(input("Enter annual interest rate(in %): "))
    cursor.execute("INSERT INTO savings (account_name, balance, interest_rate) VALUES(?,?,?)", (name, balance, rate))
    conn.commit()
    conn.close()
    print(f"Savings account '{name}' added succesfully.\n")

def add_monthly_contribution():
    
    conn, cursor = savings_db()
    cursor.execute("SELECT id, account_name FROM savings")
    accounts = cursor.fetchall()

    if not accounts:
        print("No savings account found.\n")
        conn.close()
        return

    print("\nSavings Accounts:")
    for acc in accounts:
        print(f"[{acc[0]}] {acc[1]}")

    try:
        acc_id = int(input("Enter account ID to update: "))
        amount = float(input("Enter contribution ammount: £"))
    except ValueError:
        print("Invalid Input.\n")
        conn.close()
        return

    cursor.execute("INSERT INTO contributions(savings_id, amount) VALUES (?,?)", (acc_id, amount))
    cursor.execute("UPDATE savings SET balance=balance + ?WHEREid = ?",(amount, acc_id))
    conn.commit()
    conn.close()
    print("Contribution added successfuly./n")

def show_projection():
    '''display balance projections based on interest rate (1-10 years)'''
    conn,cursor=savings_db()
    cursor.execute("SELECT account_name, balance, interest_rate FROM savings")
    accounts = cursor.fetchall()
    conn.close()

    if not accounts:
        print("No savings accounts to show.\n")
        return

    for acc in accounts:
        name,balance,rate = acc
        print(f"\n{name} - Current Balance: £{balance:.2f}, Rate: {rate:.2f}%")
        for year in range(1,11):
            projected = balance*((1 + (rate/100))** year)
            print(f"Year {year}: £{projected:.2f}")
        print()

#core features for the investments module

def add_portfolio():
    '''Add a new investment portfolio'''
    conn,cursor = connect_invest_db()
    name = input("Enter Portfolio Name: ").strip()
    if not name:
        print("Portfolio name cannot be empty.\n")
        return
    cursor.execute("INSERT INTO portfolios (name) VALUES (?)", (name,))
    conn.commit()
    conn.close()
    print(f"Portfolio '{name}' added successfully.\n")

def add_contribution():
    '''adds a new contribution to the portfolio'''
    conn,cursor = connect_invest_db()
    cursor.execute("SELECT id, name FROM portfolios")
    portfolios = cursor.fetchall()

    if not portfolios:
        print("No portfolios found. Please create one first. \n")
        conn.close()
        return
    
    print("\nAvailable Portfolios:")
    for p in portfolios:
        print(f"[{p[0]}] {p[1]}")

    try:
        pid = int(input("Enter Portfolio ID: "))
        amount = float(input("Enter contribution amount (£): "))
    except ValueError:
        print("Invalid input.\n")
        conn.close()
        return
    
    cursor.execute("INSERT INTO contributions (portfolio_id, amount) VALUES (?,?)",(pid, amount))
    conn.commit()
    conn.close()
    print("Contribution added successfully.\n")

def calculate_projections():
    '''Calculate 1 to 10 year growth projections (Bad, Good, Average).'''
    conn,cursor = connect_invest_db()
    cursor.execute("SELECT id, name FROM portfolios")
    portfolios = cursor.fetchall()
    conn.close()

    if not portfolios:
        print("No portfolios to calculate. \n")
        return
    
    current_balance = float(input("Enter Your Current Balance: (£) "))
    growth_rates = {"Bad Market": 0.03, "Average Market": 0.05, "Good Market": 0.07}
    for p in portfolios:
        print(f"\n--- {p[1]} ---")
        for label, rate in growth_rates.items():
            balance = current_balance
            print(f"{label}:")
            for year in range(1, 11): # 1 to 10 years
                balance = balance * (1 + rate) # compound annually
                print(f"Year {year}: £{balance:.2f}")
        print("-"*40)


def main_menu():

    setup_tables() #ensure database and tables exist
    setup_tables_savings() #ensure the savings databse and tables exist
    setup_invest_tables() #ensure the investment database and tables exist

    while True:
        
            
        RESET = "\033[0m"
        BOLD = "\033[1m"
        UNDERLINE = "\033[4m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"

        print("\n"+"="*45)
        print(f"{BOLD} {CYAN} {UNDERLINE} =====CASHBOX FINANCE SUITE====={RESET}")
        print("="*45)
        print(f"Session: {datetime.now().strftime('%d-%m-%y %H:%M:%S')}")
        print(f"\n{BOLD} {GREEN} {UNDERLINE} =====MONTHLY====={RESET}")
        print("\n1. Enter Income")
        print("2. View Direct Debits")
        print("3. Add New Direct Debit")
        print("4. Calculate Remaining Balance")
        print("5. Add Direct Debit Paid")
        print(f"\n{BOLD} {YELLOW} {UNDERLINE} =====SAVINGS====={RESET}")
        print("\n6. Add New Savings Account")
        print("7. Add Monthly Contribution")
        print("8. View Growth Projection")
        print(f"\n{BOLD} {BLUE} {UNDERLINE} =====STOCKS====={RESET}")
        print("\n9.  Add New Portfolio")
        print("10. Add Contribution")
        print("11. Projections")
        print(f"\n{BOLD}{RED}12. Exit")
     
        choice = input(f"\n{BOLD}{WHITE}Select an option (1-12): ").strip()
     
        if choice =="1":
            add_income()
        elif choice =="2":
            view_direct_debit()
        elif choice =="3":
            add_direct_debit()
        elif choice =="4":
            calculate_remaining()
        elif choice =="5":
            debit_paid()
        elif choice == "6":
            add_savings_account()
        elif choice == "7":
            add_monthly_contribution()
        elif choice == "8":
            show_projection()
        elif choice == "9":
            add_portfolio()
        elif choice == "10":
            add_contribution()
        elif choice == "11":
            calculate_projections()
        elif choice =="12":
            print("Goodbye!")
            break
        else:
            print("Invalid option, please try again. \n")
        
#entry point

if __name__== "__main__":

    main_menu()
        