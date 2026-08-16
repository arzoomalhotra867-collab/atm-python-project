"""
atm_backend.py
---------------
Backend / data layer for the Python-Powered ATM Solution
(Chapter 3 of the project report: Login, Deposit, Withdraw,
Balance Inquiry, PIN Change and Mini Statement modules, backed
by a MySQL database with a customer table and a transactions table).

This module has no GUI code in it — atm_app.py imports ATMBackend
and calls these methods. Keeping the two separate is what the report
calls the project's "modular architecture" (section 3.1 / 3.10).
"""

import random
from datetime import datetime

import mysql.connector
from mysql.connector import Error

from db_config import DB_CONFIG, DATABASE_NAME


class ATMBackend:
    """Handles every database interaction the ATM needs."""

    def __init__(self):
        self.conn = None
        self._connect_and_prepare()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _connect_and_prepare(self):
        """Connect to MySQL, create the database/tables if missing."""
        try:
            # First connect without selecting a database, so we can create it.
            bootstrap_conn = mysql.connector.connect(**DB_CONFIG)
            cursor = bootstrap_conn.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
            )
            cursor.close()
            bootstrap_conn.close()

            self.conn = mysql.connector.connect(
                database=DATABASE_NAME, **DB_CONFIG
            )
        except Error as e:
            raise ConnectionError(
                "Could not connect to MySQL.\n"
                f"Details: {e}\n\n"
                "Check db_config.py (host / user / password) and make sure "
                "the MySQL server is running."
            )
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # Customer table — matches Table 3.7 "Customer Table" in the report,
        # extended with dob/contact/email captured at Registration.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customer (
                account_no BIGINT PRIMARY KEY,
                name       VARCHAR(50)  NOT NULL,
                dob        DATE,
                contact    VARCHAR(10),
                email      VARCHAR(100),
                pin        VARCHAR(4)   NOT NULL,
                balance    DECIMAL(12,2) NOT NULL DEFAULT 0
            )
            """
        )
        # Transaction table — matches the report's "Transaction Table".
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
                account_no       BIGINT NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                amount           DECIMAL(12,2) NOT NULL,
                balance_after    DECIMAL(12,2) NOT NULL,
                txn_date         DATETIME NOT NULL,
                FOREIGN KEY (account_no) REFERENCES customer(account_no)
            )
            """
        )
        self.conn.commit()
        cursor.close()

    # ------------------------------------------------------------------
    # Validation helpers (mirrors section 3.11 "Security Features" /
    # the original validate_* methods, but returns booleans instead of
    # printing, so both the GUI and any future CLI can reuse them).
    # ------------------------------------------------------------------
    @staticmethod
    def validate_name(name: str) -> bool:
        return name.isalpha() and 0 < len(name) <= 25

    @staticmethod
    def validate_contact(contact: str) -> bool:
        return contact.isdigit() and len(contact) == 10

    @staticmethod
    def validate_email(email: str) -> bool:
        return email.count("@") == 1 and "." in email.split("@")[-1]

    @staticmethod
    def validate_pin(pin: str) -> bool:
        return pin.isdigit() and len(pin) == 4

    @staticmethod
    def validate_amount(amount_str: str) -> bool:
        try:
            return float(amount_str) > 0
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def account_number_exists(self, account_no) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM customer WHERE account_no=%s", (account_no,)
        )
        found = cursor.fetchone() is not None
        cursor.close()
        return found

    def generate_account_number(self) -> int:
        """Random unique 10-digit account number, issued to the customer
        automatically (a real bank assigns this — it isn't typed in)."""
        while True:
            acc_no = random.randint(1_000_000_000, 9_999_999_999)
            if not self.account_number_exists(acc_no):
                return acc_no

    def register_customer(self, name, dob, contact, email, pin) -> int:
        """Creates a new customer row with an opening balance of 0.
        Returns the newly issued account number."""
        account_no = self.generate_account_number()
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO customer
               (account_no, name, dob, contact, email, pin, balance)
               VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (account_no, name.title(), dob, contact, email, pin, 0),
        )
        self.conn.commit()
        cursor.close()
        return account_no

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def authenticate(self, account_no, pin):
        """Returns (customer_row_dict, None) on success or
        (None, error_message) on failure."""
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM customer WHERE account_no=%s", (account_no,)
        )
        row = cursor.fetchone()
        cursor.close()
        if row is None:
            return None, "Account not found."
        if str(row["pin"]) != str(pin):
            return None, "Incorrect PIN."
        return row, None

    # ------------------------------------------------------------------
    # Balance inquiry
    # ------------------------------------------------------------------
    def get_customer(self, account_no):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM customer WHERE account_no=%s", (account_no,)
        )
        row = cursor.fetchone()
        cursor.close()
        return row

    def get_balance(self, account_no) -> float:
        row = self.get_customer(account_no)
        return float(row["balance"]) if row else None

    # ------------------------------------------------------------------
    # Deposit
    # ------------------------------------------------------------------
    def deposit(self, account_no, amount: float):
        if amount <= 0:
            return False, "Amount must be greater than zero.", None
        balance = self.get_balance(account_no)
        new_balance = round(balance + amount, 2)
        self._update_balance(account_no, new_balance)
        self._record_transaction(account_no, "Deposit", amount, new_balance)
        return True, "Deposit successful.", new_balance

    # ------------------------------------------------------------------
    # Withdraw
    # ------------------------------------------------------------------
    def withdraw(self, account_no, amount: float):
        if amount <= 0:
            return False, "Amount must be greater than zero.", None
        balance = self.get_balance(account_no)
        if amount > balance:
            return False, "Insufficient balance.", balance
        new_balance = round(balance - amount, 2)
        self._update_balance(account_no, new_balance)
        self._record_transaction(account_no, "Withdraw", amount, new_balance)
        return True, "Withdrawal successful.", new_balance

    def _update_balance(self, account_no, new_balance):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE customer SET balance=%s WHERE account_no=%s",
            (new_balance, account_no),
        )
        self.conn.commit()
        cursor.close()

    # ------------------------------------------------------------------
    # PIN change
    # ------------------------------------------------------------------
    def change_pin(self, account_no, old_pin, new_pin):
        _, error = self.authenticate(account_no, old_pin)
        if error:
            return False, error
        if not self.validate_pin(new_pin):
            return False, "New PIN must be exactly 4 digits."
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE customer SET pin=%s WHERE account_no=%s",
            (new_pin, account_no),
        )
        self.conn.commit()
        cursor.close()
        return True, "PIN changed successfully."

    # ------------------------------------------------------------------
    # Mini statement / transaction history
    # ------------------------------------------------------------------
    def get_mini_statement(self, account_no, limit=10):
        cursor = self.conn.cursor(dictionary=True)
        cursor.execute(
            """SELECT transaction_type, amount, balance_after, txn_date
               FROM transactions
               WHERE account_no=%s
               ORDER BY txn_date DESC
               LIMIT %s""",
            (account_no, limit),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def _record_transaction(self, account_no, txn_type, amount, balance_after):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO transactions
               (account_no, transaction_type, amount, balance_after, txn_date)
               VALUES (%s,%s,%s,%s,%s)""",
            (account_no, txn_type, amount, balance_after, datetime.now()),
        )
        self.conn.commit()
        cursor.close()

    # ------------------------------------------------------------------
    def close(self):
        if self.conn and self.conn.is_connected():
            self.conn.close()
