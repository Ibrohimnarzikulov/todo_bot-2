from datetime import time as dt_time

import asyncpg
from app.config import DATABASE_URL, DEFAULT_REMINDER_TIME

_pool: asyncpg.Pool | None = None


async def init_db():
    """Pool yaratish va jadvallarni tayyorlash (agar mavjud bo'lmasa)."""
    global _pool
    _pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=5)

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                full_name TEXT,
                reminder_time TIME NOT NULL DEFAULT '09:00',
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                task_text TEXT NOT NULL,
                is_done BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            );
            """
        )
    return _pool


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("DB pool hali ishga tushmagan. Avval init_db() chaqiring.")
    return _pool


async def close_db():
    if _pool:
        await _pool.close()


# ---------- USERS ----------

async def upsert_user(user_id: int, chat_id: int, full_name: str):
    pool = get_pool()
    hh, mm = map(int, DEFAULT_REMINDER_TIME.split(":"))
    default_time = dt_time(hour=hh, minute=mm)
    await pool.execute(
        """
        INSERT INTO users (user_id, chat_id, full_name, reminder_time)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (user_id) DO UPDATE
        SET chat_id = EXCLUDED.chat_id, full_name = EXCLUDED.full_name;
        """,
        user_id, chat_id, full_name, default_time,
    )


async def set_reminder_time(user_id: int, time_str: str):
    pool = get_pool()
    hh, mm = map(int, time_str.split(":"))
    new_time = dt_time(hour=hh, minute=mm)
    await pool.execute(
        "UPDATE users SET reminder_time = $1 WHERE user_id = $2;",
        new_time, user_id,
    )


async def get_all_users():
    pool = get_pool()
    return await pool.fetch("SELECT user_id, chat_id, reminder_time FROM users;")


# ---------- TASKS ----------

async def add_task(user_id: int, task_text: str):
    pool = get_pool()
    return await pool.fetchrow(
        "INSERT INTO tasks (user_id, task_text) VALUES ($1, $2) RETURNING id;",
        user_id, task_text,
    )


async def get_tasks(user_id: int, only_pending: bool = False):
    pool = get_pool()
    if only_pending:
        return await pool.fetch(
            "SELECT id, task_text, is_done FROM tasks WHERE user_id = $1 AND is_done = FALSE ORDER BY id;",
            user_id,
        )
    return await pool.fetch(
        "SELECT id, task_text, is_done FROM tasks WHERE user_id = $1 ORDER BY id;",
        user_id,
    )


async def mark_done(user_id: int, task_id: int) -> bool:
    pool = get_pool()
    result = await pool.execute(
        "UPDATE tasks SET is_done = TRUE WHERE id = $1 AND user_id = $2;",
        task_id, user_id,
    )
    return result.endswith("1")


async def delete_task(user_id: int, task_id: int) -> bool:
    pool = get_pool()
    result = await pool.execute(
        "DELETE FROM tasks WHERE id = $1 AND user_id = $2;",
        task_id, user_id,
    )
    return result.endswith("1")


async def clear_done(user_id: int):
    pool = get_pool()
    await pool.execute(
        "DELETE FROM tasks WHERE user_id = $1 AND is_done = TRUE;",
        user_id,
    )
