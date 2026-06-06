"""
Location : gym_app/database/schema.py
Purpose  : Simplified Data Architecture Definition - Single Table Setup.
"""

SCHEMA = """
-- 1. users Table Layout
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'receptionist')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. members Table Layout (Collapsed Single-Table Design)
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_code TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    whatsapp TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
    age INTEGER CHECK(age >= 10 AND age <= 100),
    address TEXT,
    plan_name TEXT NOT NULL,
    join_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS message_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    sent_date DATE,
    FOREIGN KEY(member_id) REFERENCES members(id)
);
-- 3. Optimization Strategy Structural Indexes
CREATE INDEX IF NOT EXISTS idx_members_code ON members(member_code);
CREATE INDEX IF NOT EXISTS idx_members_name ON members(full_name);
CREATE INDEX IF NOT EXISTS idx_members_phone ON members(phone);
CREATE INDEX IF NOT EXISTS idx_members_expiry ON members(expiry_date);
"""