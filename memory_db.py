import aiosqlite
import json

DB_NAME = "users.db"


# ---------------- INIT ----------------
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            history TEXT DEFAULT '[]'
        )
        """)
        await db.commit()


# ---------------- GET USER ----------------
async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT history FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return []

        try:
            return json.loads(row[0])
        except:
            return []


# ---------------- SAVE USER ----------------
async def save_user(user_id: int, history: list):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT OR REPLACE INTO users (user_id, history)
        VALUES (?, ?)
        """, (user_id, json.dumps(history)))
        await db.commit()


# ---------------- CLEAR USER ----------------
async def clear_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM users WHERE user_id = ?",
            (user_id,)
        )
        await db.commit()

