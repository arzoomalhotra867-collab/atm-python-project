-- database_setup.sql
-- Matches the "Customer Table" / "Transaction Table" design in
-- Chapter 3.7 (Database Design) of the project report.
--
-- This is optional: atm_backend.py creates the database and tables
-- automatically the first time you run atm_app.py. Run this manually
-- only if you'd rather set things up yourself first.

CREATE DATABASE IF NOT EXISTS atm_db;
USE atm_db;

CREATE TABLE IF NOT EXISTS customer (
    account_no BIGINT PRIMARY KEY,
    name       VARCHAR(50)  NOT NULL,
    dob        DATE,
    contact    VARCHAR(10),
    email      VARCHAR(100),
    pin        VARCHAR(4)   NOT NULL,
    balance    DECIMAL(12,2) NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id   INT AUTO_INCREMENT PRIMARY KEY,
    account_no       BIGINT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    amount           DECIMAL(12,2) NOT NULL,
    balance_after    DECIMAL(12,2) NOT NULL,
    txn_date         DATETIME NOT NULL,
    FOREIGN KEY (account_no) REFERENCES customer(account_no)
);
