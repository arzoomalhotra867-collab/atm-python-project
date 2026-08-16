# Python-Powered ATM Solution

A complete, working implementation of the ATM system described in the
project report — Login, Registration, Deposit, Withdrawal, Balance
Inquiry, PIN Change and Mini Statement, backed by a MySQL database.

## Files

| File                  | Purpose                                                        |
|------------------------|-----------------------------------------------------------------|
| `atm_app.py`           | Main program — Tkinter GUI, run this file                      |
| `atm_backend.py`       | Database layer — validation, MySQL queries, business logic     |
| `db_config.py`         | Your MySQL host/user/password go here                          |
| `database_setup.sql`   | Optional manual schema (tables are also auto-created)          |
| `requirements.txt`     | Python packages needed                                         |

## Setup

1. **Install MySQL** if you don't already have it running locally, and
   make sure the server is started.

2. **Install the Python dependency:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Edit `db_config.py`** and set your MySQL username/password:
   ```python
   DB_CONFIG = {
       "host": "localhost",
       "user": "root",
       "password": "your_mysql_password",
       "port": 3306,
   }
   ```
   You don't need to create the `atm_db` database or its tables by hand —
   `atm_backend.py` creates them automatically the first time it connects.
   (If you'd rather set it up manually, `database_setup.sql` has the
   same schema — run it with `mysql -u root -p < database_setup.sql`.)

4. **Run the app:**
   ```bash
   python atm_app.py
   ```

## How it works

- **Register** → fill in Name, DOB, Contact, Email and choose a 4-digit
  PIN. The system assigns you a 10-digit account number automatically
  (shown once at the end, like a bank issuing a card) — write it down.
- **Login** → enter that account number and PIN to reach the dashboard.
- From the dashboard you can **Deposit**, **Withdraw**, check your
  **Balance**, **Change PIN**, or view a **Mini Statement** of your
  last 10 transactions. Every deposit/withdrawal is written to the
  `transactions` table with a timestamp, which is what powers the
  mini statement.

## What changed from the original files you uploaded

Your three original files (`atm_backend.py`, `atm_frontend.py`,
`atm_registration.py`) were three disconnected pieces: a console-only
backend with a login bug (it compared a PIN string against the whole
customer dictionary, so login could never actually succeed), a Tkinter
window whose buttons didn't do anything, and a registration form that
validated input but never saved it anywhere or talked to the backend.

This version merges them into one connected application: the GUI calls
straight into `ATMBackend`, which persists everything in MySQL so data
survives between runs, and every module your report documents in
Chapter 3 (Table 3.3 "Functional Requirements") is actually implemented
and wired up — not just described.
