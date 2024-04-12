CREATE TABLE IF NOT EXISTS users
(
    user_id         INTEGER PRIMARY KEY,
    user_name       TEXT,
    date_created    TEXT,
    status          INTEGER,
    is_admin        INTEGER
);
CREATE TABLE IF NOT EXISTS chats
(
    chat_id         INTEGER PRIMARY KEY,
    date_joined     TEXT,
    memer_count     INTEGER,
    status          INTEGER
);
CREATE TABLE IF NOT EXISTS connections
(
    connection_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id         INTEGER,
    user_id         INTEGER,
    date_creation   TEXT,
    date_updated    TEXT,
    status          INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
    FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
);
