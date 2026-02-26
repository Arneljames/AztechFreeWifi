-- SQLite Schema for Aztech Free WiFi Captive Portal

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    date_used DATE NOT NULL,
    session_start DATETIME NOT NULL,
    session_end DATETIME NOT NULL
);

-- Index for faster daily MAC lookup
CREATE INDEX IF NOT EXISTS idx_users_mac_date ON users (mac_address, date_used);
