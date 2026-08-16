"""
db_config.example.py
---------------------
Template for db_config.py — this file IS safe to commit to Git.

Copy this file to db_config.py (which is gitignored) and fill in
your own MySQL credentials there. Never put real passwords in this
example file or in db_config.py once it's committed anywhere public.
"""

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "port": 3306,
    # If your MySQL account uses the newer caching_sha2_password plugin,
    # use_pure=True is usually enough. If it uses mysql_native_password
    # instead, uncomment the line below.
    "use_pure": True,
    # "auth_plugin": "mysql_native_password",
}

DATABASE_NAME = "atm_db"
