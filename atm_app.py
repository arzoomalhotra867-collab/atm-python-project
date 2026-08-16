"""
atm_app.py
-----------
Main entry point / GUI for the Python-Powered ATM Solution.

Redesigned to match the screenshots in Chapter 4 of the project report:
    Figure 4.2  Login Screen
    Figure 4.3  Deposit Window
    Figure 4.4  Withdrawal Window
    Figure 4.5  Balance Inquiry
    Figure 4.7  Mini Statement
Each banking function opens as its own window (like the report figures),
launched from an ATM Dashboard menu after login.

Run with:
    python atm_app.py

Requires:
    pip install mysql-connector-python
    a running MySQL server, configured in db_config.py
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from atm_backend import ATMBackend

# ---------------------------------------------------------------------
# Shared styling — matches the navy/blue "ATM SYSTEM" look used
# throughout Chapter 4 of the report.
# ---------------------------------------------------------------------
BG_DARK = "#10264B"
BG_LIGHT = "#F4F4F4"
FG_LIGHT = "#FFFFFF"
GREEN = "#2E8B57"
RED = "#C0392B"
BLUE = "#2255A4"
GOLD = "#FFD700"

FONT_TITLE = ("Arial", 20, "bold")
FONT_HEADING = ("Arial", 15, "bold")
FONT_LABEL = ("Arial", 11, "bold")
FONT_ENTRY = ("Arial", 11)
FONT_BTN = ("Arial", 11, "bold")
FONT_VALUE = ("Arial", 11)


def styled_button(parent, text, command, bg=BLUE, width=14):
    return tk.Button(
        parent, text=text, command=command, bg=bg, fg="white", font=FONT_BTN,
        width=width, relief="flat", cursor="hand2",
        activebackground=bg, activeforeground="white",
    )


def info_row(parent, row, label_text, value_text, bg, value_fg="black"):
    """One 'Label:  [ value ]' line, styled like the Account Number /
    Current Balance rows shown in the report's Deposit/Withdraw figures."""
    tk.Label(parent, text=label_text, font=FONT_LABEL, bg=bg) \
        .grid(row=row, column=0, sticky="e", padx=(10, 4), pady=4)
    val = tk.Label(parent, text=value_text, font=FONT_VALUE, fg=value_fg, bg="white",
                    relief="solid", bd=1, width=18, anchor="w", padx=6)
    val.grid(row=row, column=1, sticky="w", padx=(0, 10), pady=4)
    return val


# =======================================================================
# LOGIN WINDOW  (Figure 4.2 — window title "ATM Login")
# =======================================================================
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ATM Login")
        self.geometry("360x480")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)

        try:
            self.backend = ATMBackend()
        except ConnectionError as e:
            messagebox.showerror("Database Error", str(e))
            self.destroy()
            raise SystemExit

        self.dashboard = None

        tk.Label(self, text="\U0001F3E6", font=("Arial", 42), bg=BG_DARK,
                 fg=FG_LIGHT).pack(pady=(35, 0))
        tk.Label(self, text="ATM SYSTEM", font=FONT_TITLE, bg=BG_DARK,
                 fg=FG_LIGHT).pack(pady=(0, 25))

        form = tk.Frame(self, bg=BG_DARK)
        form.pack()
        tk.Label(form, text="Account Number :", bg=BG_DARK, fg=FG_LIGHT,
                 font=FONT_LABEL).grid(row=0, column=0, pady=8, sticky="e")
        self.acc_entry = tk.Entry(form, font=FONT_ENTRY, width=16)
        self.acc_entry.grid(row=0, column=1, pady=8, padx=8)

        tk.Label(form, text="PIN :", bg=BG_DARK, fg=FG_LIGHT,
                 font=FONT_LABEL).grid(row=1, column=0, pady=8, sticky="e")
        self.pin_entry = tk.Entry(form, font=FONT_ENTRY, width=16, show="*")
        self.pin_entry.grid(row=1, column=1, pady=8, padx=8)

        self.status_label = tk.Label(self, text="", bg=BG_DARK, fg="#FF6B6B",
                                      font=("Arial", 10), wraplength=300)
        self.status_label.pack(pady=6)

        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(pady=10)
        styled_button(btn_frame, "LOGIN", self.login, bg=GREEN, width=12) \
            .grid(row=0, column=0, padx=6)
        styled_button(btn_frame, "CLEAR", self.clear, bg=RED, width=12) \
            .grid(row=0, column=1, padx=6)

        tk.Button(self, text="New customer? Register here", command=self.open_register,
                  bg=BG_DARK, fg="#8FB8FF", font=("Arial", 9, "underline"),
                  relief="flat", cursor="hand2", bd=0,
                  activebackground=BG_DARK, activeforeground="#B7D3FF") \
            .pack(pady=(6, 0))

        tk.Label(self, text="Welcome to Secure Banking", font=("Arial", 10, "italic"),
                 bg=BG_DARK, fg=GOLD).pack(side="bottom", pady=20)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def clear(self):
        self.acc_entry.delete(0, tk.END)
        self.pin_entry.delete(0, tk.END)
        self.status_label.config(text="")

    def login(self):
        acc_str = self.acc_entry.get().strip()
        pin = self.pin_entry.get().strip()

        if not acc_str.isdigit():
            self.status_label.config(text="Account number must be numeric.")
            return
        if not self.backend.validate_pin(pin):
            self.status_label.config(text="PIN must be exactly 4 digits.")
            return

        row, error = self.backend.authenticate(int(acc_str), pin)
        if error:
            self.status_label.config(text=error)
            return

        self.clear()
        self.withdraw()  # hide the login window while dashboard is open
        self.dashboard = DashboardWindow(self, row["account_no"])

    def open_register(self):
        RegisterWindow(self)

    def show_again(self):
        self.deiconify()

    def on_close(self):
        try:
            self.backend.close()
        finally:
            self.destroy()


# =======================================================================
# DASHBOARD  (mirrors the module menu described in Chapter 3.10)
# =======================================================================
class DashboardWindow(tk.Toplevel):
    def __init__(self, login_window: LoginWindow, account_no):
        super().__init__(login_window)
        self.login_window = login_window
        self.backend = login_window.backend
        self.account_no = account_no

        self.title("ATM Dashboard")
        self.geometry("330x430")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        customer = self.backend.get_customer(account_no)
        tk.Label(self, text=f"Welcome, {customer['name']}", font=("Arial", 13, "bold"),
                 bg=BG_LIGHT, fg=BLUE).pack(pady=(18, 2))
        tk.Label(self, text=f"Account No: {account_no}", font=("Arial", 9),
                 bg=BG_LIGHT, fg="#555555").pack(pady=(0, 12))
        tk.Label(self, text="Choose an option:", bg=BG_LIGHT,
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))

        grid = tk.Frame(self, bg=BG_LIGHT)
        grid.pack()
        buttons = [
            ("DEPOSIT", self.open_deposit),
            ("WITHDRAWAL", self.open_withdraw),
            ("BALANCE INQUIRY", self.open_balance),
            ("CHANGE PIN", self.open_pin_change),
            ("MINI STATEMENT", self.open_mini_statement),
        ]
        for i, (text, cmd) in enumerate(buttons):
            styled_button(grid, text, cmd, bg=BLUE, width=18) \
                .grid(row=i // 2, column=i % 2, padx=6, pady=8)

        styled_button(self, "LOGOUT", self.logout, bg=RED, width=18).pack(pady=20)

        self.protocol("WM_DELETE_WINDOW", self.logout)

    def open_deposit(self):
        DepositWindow(self, self.backend, self.account_no)

    def open_withdraw(self):
        WithdrawWindow(self, self.backend, self.account_no)

    def open_balance(self):
        BalanceInquiryWindow(self, self.backend, self.account_no)

    def open_pin_change(self):
        PinChangeWindow(self, self.backend, self.account_no)

    def open_mini_statement(self):
        MiniStatementWindow(self, self.backend, self.account_no)

    def logout(self):
        self.destroy()
        self.login_window.show_again()


# =======================================================================
# DEPOSIT  (Figure 4.3 — window title "Deposit")
# =======================================================================
class DepositWindow(tk.Toplevel):
    def __init__(self, parent, backend, account_no):
        super().__init__(parent)
        self.backend = backend
        self.account_no = account_no

        self.title("Deposit")
        self.geometry("330x360")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        tk.Label(self, text="DEPOSIT MONEY", font=FONT_HEADING, bg=BG_LIGHT,
                 fg=BLUE).pack(pady=(18, 12))

        info = tk.Frame(self, bg=BG_LIGHT)
        info.pack()
        info_row(info, 0, "Account Number :", str(account_no), BG_LIGHT)
        balance = backend.get_balance(account_no)
        self.balance_value = info_row(info, 1, "Current Balance :",
                                       f"\u20B9 {balance:,.2f}", BG_LIGHT, value_fg=GREEN)

        tk.Label(self, text="Enter Amount to Deposit :", bg=BG_LIGHT,
                 font=FONT_LABEL).pack(pady=(16, 3))
        self.amount_entry = tk.Entry(self, font=FONT_ENTRY, width=20)
        self.amount_entry.pack()

        btn_frame = tk.Frame(self, bg=BG_LIGHT)
        btn_frame.pack(pady=14)
        styled_button(btn_frame, "DEPOSIT", self.do_deposit, bg=GREEN, width=11) \
            .grid(row=0, column=0, padx=5)
        styled_button(btn_frame, "CANCEL", self.destroy, bg=RED, width=11) \
            .grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(self, text="", bg=BG_LIGHT, fg=GREEN,
                                      font=("Arial", 10, "bold"), wraplength=290,
                                      justify="center")
        self.status_label.pack(pady=6)

    def do_deposit(self):
        amount_str = self.amount_entry.get().strip()
        if not self.backend.validate_amount(amount_str):
            self.status_label.config(fg=RED, text="Enter a valid amount greater than zero.")
            return
        ok, msg, new_balance = self.backend.deposit(self.account_no, float(amount_str))
        if ok:
            self.status_label.config(
                fg=GREEN,
                text=f"\u20B9{float(amount_str):,.2f} Deposited Successfully!\n"
                     f"New Balance : \u20B9{new_balance:,.2f}"
            )
            self.balance_value.config(text=f"\u20B9 {new_balance:,.2f}")
            self.amount_entry.delete(0, tk.END)
        else:
            self.status_label.config(fg=RED, text=msg)


# =======================================================================
# WITHDRAWAL  (Figure 4.4 — window title "Withdraw")
# =======================================================================
class WithdrawWindow(tk.Toplevel):
    def __init__(self, parent, backend, account_no):
        super().__init__(parent)
        self.backend = backend
        self.account_no = account_no

        self.title("Withdraw")
        self.geometry("330x360")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        tk.Label(self, text="WITHDRAW MONEY", font=FONT_HEADING, bg=BG_LIGHT,
                 fg=BLUE).pack(pady=(18, 12))

        info = tk.Frame(self, bg=BG_LIGHT)
        info.pack()
        info_row(info, 0, "Account Number :", str(account_no), BG_LIGHT)
        balance = backend.get_balance(account_no)
        self.balance_value = info_row(info, 1, "Current Balance :",
                                       f"\u20B9 {balance:,.2f}", BG_LIGHT, value_fg=GREEN)

        tk.Label(self, text="Enter Amount to Withdraw :", bg=BG_LIGHT,
                 font=FONT_LABEL).pack(pady=(16, 3))
        self.amount_entry = tk.Entry(self, font=FONT_ENTRY, width=20)
        self.amount_entry.pack()

        btn_frame = tk.Frame(self, bg=BG_LIGHT)
        btn_frame.pack(pady=14)
        styled_button(btn_frame, "WITHDRAW", self.do_withdraw, bg=GREEN, width=11) \
            .grid(row=0, column=0, padx=5)
        styled_button(btn_frame, "CANCEL", self.destroy, bg=RED, width=11) \
            .grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(self, text="", bg=BG_LIGHT, fg=GREEN,
                                      font=("Arial", 10, "bold"), wraplength=290,
                                      justify="center")
        self.status_label.pack(pady=6)

    def do_withdraw(self):
        amount_str = self.amount_entry.get().strip()
        if not self.backend.validate_amount(amount_str):
            self.status_label.config(fg=RED, text="Enter a valid amount greater than zero.")
            return
        ok, msg, result = self.backend.withdraw(self.account_no, float(amount_str))
        if ok:
            self.status_label.config(
                fg=GREEN,
                text=f"\u20B9{float(amount_str):,.2f} Withdrawn Successfully!\n"
                     f"New Balance : \u20B9{result:,.2f}"
            )
            self.balance_value.config(text=f"\u20B9 {result:,.2f}")
            self.amount_entry.delete(0, tk.END)
        else:
            self.status_label.config(fg=RED, text=f"{msg} (Available: \u20B9{result:,.2f})")


# =======================================================================
# BALANCE INQUIRY  (Figure 4.5 — window title "Balance Inquiry")
# =======================================================================
class BalanceInquiryWindow(tk.Toplevel):
    def __init__(self, parent, backend, account_no):
        super().__init__(parent)
        self.title("Balance Inquiry")
        self.geometry("330x340")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        tk.Label(self, text="BALANCE INQUIRY", font=FONT_HEADING, bg=BG_LIGHT,
                 fg=BLUE).pack(pady=(18, 12))

        customer = backend.get_customer(account_no)
        info = tk.Frame(self, bg=BG_LIGHT)
        info.pack()
        info_row(info, 0, "Account Number :", str(account_no), BG_LIGHT)
        info_row(info, 1, "Account Holder :", customer["name"], BG_LIGHT)

        box = tk.Frame(self, bg="white", relief="solid", bd=1)
        box.pack(pady=22, padx=30, fill="x")
        tk.Label(box, text="Available Balance", bg="white", font=FONT_LABEL) \
            .pack(pady=(12, 2))
        tk.Label(box, text=f"\u20B9 {float(customer['balance']):,.2f}", bg="white",
                 fg=GREEN, font=("Arial", 20, "bold")).pack(pady=(0, 12))

        styled_button(self, "BACK", self.destroy, bg=BLUE, width=12).pack(pady=6)


# =======================================================================
# PIN CHANGE
# =======================================================================
class PinChangeWindow(tk.Toplevel):
    def __init__(self, parent, backend, account_no):
        super().__init__(parent)
        self.backend = backend
        self.account_no = account_no

        self.title("Change PIN")
        self.geometry("330x400")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        tk.Label(self, text="CHANGE PIN", font=FONT_HEADING, bg=BG_LIGHT,
                 fg=BLUE).pack(pady=(18, 12))

        customer = backend.get_customer(account_no)
        info = tk.Frame(self, bg=BG_LIGHT)
        info.pack()
        info_row(info, 0, "Account Number :", str(account_no), BG_LIGHT)
        info_row(info, 1, "Account Holder :", customer["name"], BG_LIGHT)

        form = tk.Frame(self, bg=BG_LIGHT)
        form.pack(pady=14)
        tk.Label(form, text="Current PIN :", bg=BG_LIGHT, font=FONT_LABEL) \
            .grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.old_pin = tk.Entry(form, font=FONT_ENTRY, width=14, show="*")
        self.old_pin.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="New PIN :", bg=BG_LIGHT, font=FONT_LABEL) \
            .grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.new_pin = tk.Entry(form, font=FONT_ENTRY, width=14, show="*")
        self.new_pin.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="Confirm New PIN :", bg=BG_LIGHT, font=FONT_LABEL) \
            .grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.confirm_pin = tk.Entry(form, font=FONT_ENTRY, width=14, show="*")
        self.confirm_pin.grid(row=2, column=1, padx=5, pady=5)

        btn_frame = tk.Frame(self, bg=BG_LIGHT)
        btn_frame.pack(pady=8)
        styled_button(btn_frame, "UPDATE PIN", self.do_change, bg=GREEN, width=12) \
            .grid(row=0, column=0, padx=5)
        styled_button(btn_frame, "BACK", self.destroy, bg=BLUE, width=12) \
            .grid(row=0, column=1, padx=5)

        self.status_label = tk.Label(self, text="", bg=BG_LIGHT, fg=GREEN,
                                      font=("Arial", 10, "bold"), wraplength=290,
                                      justify="center")
        self.status_label.pack(pady=6)

    def do_change(self):
        old_pin = self.old_pin.get().strip()
        new_pin = self.new_pin.get().strip()
        confirm = self.confirm_pin.get().strip()

        if new_pin != confirm:
            self.status_label.config(fg=RED, text="New PIN and confirmation do not match.")
            return

        ok, msg = self.backend.change_pin(self.account_no, old_pin, new_pin)
        self.status_label.config(fg=GREEN if ok else RED, text=msg)
        if ok:
            for e in (self.old_pin, self.new_pin, self.confirm_pin):
                e.delete(0, tk.END)


# =======================================================================
# MINI STATEMENT  (Figure 4.7 — window title "Mini Statement")
# =======================================================================
class MiniStatementWindow(tk.Toplevel):
    def __init__(self, parent, backend, account_no):
        super().__init__(parent)
        self.backend = backend
        self.account_no = account_no

        self.title("Mini Statement")
        self.geometry("480x400")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        tk.Label(self, text="MINI STATEMENT", font=FONT_HEADING, bg=BG_LIGHT,
                 fg=BLUE).pack(pady=(16, 10))

        customer = backend.get_customer(account_no)
        info = tk.Frame(self, bg=BG_LIGHT)
        info.pack()
        tk.Label(info, text="Account Number :", font=FONT_LABEL, bg=BG_LIGHT) \
            .grid(row=0, column=0, sticky="e", padx=4)
        tk.Label(info, text=str(account_no), font=FONT_VALUE, bg=BG_LIGHT) \
            .grid(row=0, column=1, sticky="w", padx=4)
        tk.Label(info, text="Account Holder :", font=FONT_LABEL, bg=BG_LIGHT) \
            .grid(row=1, column=0, sticky="e", padx=4)
        tk.Label(info, text=customer["name"], font=FONT_VALUE, bg=BG_LIGHT) \
            .grid(row=1, column=1, sticky="w", padx=4)

        columns = ("date", "time", "type", "amount", "balance")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=8)
        headings = {"date": "Date", "time": "Time", "type": "Type",
                    "amount": "Amount (\u20B9)", "balance": "Balance (\u20B9)"}
        widths = {"date": 90, "time": 70, "type": 80, "amount": 90, "balance": 90}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col],
                              anchor="center" if col in ("date", "time", "type") else "e")
        self.tree.pack(pady=10, padx=12, fill="x")

        rows = backend.get_mini_statement(account_no)
        for r in rows:
            self.tree.insert("", "end", values=(
                r["txn_date"].strftime("%d-%m-%Y"),
                r["txn_date"].strftime("%H:%M:%S"),
                r["transaction_type"],
                f"{float(r['amount']):,.2f}",
                f"{float(r['balance_after']):,.2f}",
            ))
        if not rows:
            tk.Label(self, text="No transactions yet.", bg=BG_LIGHT, fg="#777777") \
                .pack()

        btn_frame = tk.Frame(self, bg=BG_LIGHT)
        btn_frame.pack(pady=12)
        styled_button(btn_frame, "BACK", self.destroy, bg=BLUE, width=12) \
            .grid(row=0, column=0, padx=6)
        styled_button(btn_frame, "PRINT", self.print_receipt, bg=GREEN, width=12) \
            .grid(row=0, column=1, padx=6)

    def print_receipt(self):
        """Saves a plain-text receipt, since there's no physical printer —
        this is the 'Receipt' module referenced in the report's module list."""
        customer = self.backend.get_customer(self.account_no)
        rows = self.backend.get_mini_statement(self.account_no)

        lines = [
            "========== ATM MINI STATEMENT ==========",
            f"Account Number : {self.account_no}",
            f"Account Holder : {customer['name']}",
            f"Generated On   : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            "-----------------------------------------",
        ]
        for r in rows:
            lines.append(
                f"{r['txn_date'].strftime('%d-%m-%Y %H:%M:%S')}  "
                f"{r['transaction_type']:<10} "
                f"Amt: {float(r['amount']):>10,.2f}  "
                f"Bal: {float(r['balance_after']):>10,.2f}"
            )
        lines.append("-----------------------------------------")
        lines.append(f"Current Balance : \u20B9 {float(customer['balance']):,.2f}")
        lines.append("==========================================")

        os.makedirs("receipts", exist_ok=True)
        filename = f"receipts/receipt_{self.account_no}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        messagebox.showinfo("Receipt Saved", f"Receipt saved to:\n{os.path.abspath(filename)}")


# =======================================================================
# REGISTRATION
# =======================================================================
class RegisterWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Registration")
        self.geometry("330x430")
        self.resizable(False, False)
        self.configure(bg=BG_LIGHT)

        tk.Label(self, text="REGISTRATION", font=FONT_HEADING, bg=BG_LIGHT,
                 fg=BLUE).grid(row=0, column=0, columnspan=2, pady=(18, 14))

        labels = ["Name", "DOB (DD/MM/YYYY)", "Contact No.", "Email",
                  "Create 4-digit PIN", "Confirm PIN"]
        self.entries = {}
        for i, text in enumerate(labels, start=1):
            tk.Label(self, text=text, bg=BG_LIGHT, font=FONT_LABEL) \
                .grid(row=i, column=0, sticky="w", padx=15, pady=6)
            show = "*" if "PIN" in text else None
            entry = tk.Entry(self, font=FONT_ENTRY, width=18, show=show)
            entry.grid(row=i, column=1, padx=10, pady=6)
            self.entries[text] = entry

        self.status_label = tk.Label(self, text="", bg=BG_LIGHT, fg=RED,
                                      font=("Arial", 9), wraplength=300, justify="left")
        self.status_label.grid(row=8, column=0, columnspan=2, padx=15)

        btn_frame = tk.Frame(self, bg=BG_LIGHT)
        btn_frame.grid(row=9, column=0, columnspan=2, pady=14)
        styled_button(btn_frame, "SUBMIT", self.submit, bg=GREEN, width=12) \
            .grid(row=0, column=0, padx=5)
        styled_button(btn_frame, "CANCEL", self.destroy, bg=RED, width=12) \
            .grid(row=0, column=1, padx=5)

    def submit(self):
        backend = self.parent.backend
        name = self.entries["Name"].get().strip()
        dob_str = self.entries["DOB (DD/MM/YYYY)"].get().strip()
        contact = self.entries["Contact No."].get().strip()
        email = self.entries["Email"].get().strip()
        pin = self.entries["Create 4-digit PIN"].get().strip()
        confirm_pin = self.entries["Confirm PIN"].get().strip()

        if not backend.validate_name(name):
            return self._error("Name must contain only letters (max 25 characters).")
        try:
            dob = datetime.strptime(dob_str, "%d/%m/%Y").date()
        except ValueError:
            return self._error("DOB must be a valid date in DD/MM/YYYY format.")
        if not backend.validate_contact(contact):
            return self._error("Contact number must be exactly 10 digits.")
        if not backend.validate_email(email):
            return self._error("Please enter a valid email address.")
        if not backend.validate_pin(pin):
            return self._error("PIN must be exactly 4 digits.")
        if pin != confirm_pin:
            return self._error("PIN and Confirm PIN do not match.")

        try:
            account_no = backend.register_customer(name, dob, contact, email, pin)
        except Exception as e:
            return self._error(f"Registration failed: {e}")

        messagebox.showinfo(
            "Registration Successful",
            f"Welcome, {name.title()}!\n\n"
            f"Your Account Number is:\n{account_no}\n\n"
            "Please note it down — you'll need it to log in."
        )
        self.destroy()

    def _error(self, msg):
        self.status_label.config(text=msg)


# =======================================================================
if __name__ == "__main__":
    LoginWindow().mainloop()
