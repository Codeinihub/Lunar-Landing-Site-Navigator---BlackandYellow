
import sqlite3
import json
import time
import hashlib

from pathlib import Path
from typing import Any, Callable

DB_PATH = Path(__file__).resolve().parent / "power_cache.db"


def initialize_cache():

    with sqlite3.connect(DB_PATH) as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                saved_at REAL NOT NULL
            )
        """)


def generate_cache_key(namespace: str, parameters: dict) -> str:

    key_data = {
        "namespace": namespace,
        "parameters": parameters
    }

    serialized = json.dumps(
        key_data,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        serialized.encode()
    ).hexdigest()


def get_cached_data(cache_key: str, max_age=604800):

    with sqlite3.connect(DB_PATH) as connection:

        row = connection.execute(
            "SELECT data, saved_at FROM cache WHERE cache_key = ?",
            (cache_key,)
        ).fetchone()

        if row is None:
            return None

        data, saved_at = row

        if time.time() - saved_at > max_age:

            connection.execute(
                "DELETE FROM cache WHERE cache_key = ?",
                (cache_key,)
            )

            return None

        return json.loads(data)


def save_cached_data(cache_key: str, data: Any):

    with sqlite3.connect(DB_PATH) as connection:

        connection.execute("""
            INSERT OR REPLACE INTO cache
            (cache_key, data, saved_at)
            VALUES (?, ?, ?)
        """, (
            cache_key,
            json.dumps(data),
            time.time()
        ))


def get_or_fetch_data(
    namespace: str,
    parameters: dict,
    fetch_function: Callable[[], Any],
    max_age=604800
):

    cache_key = generate_cache_key(
        namespace,
        parameters
    )

    cached_data = get_cached_data(
        cache_key,
        max_age
    )

    if cached_data is not None:

        print(f"Cache hit: {namespace}")

        return cached_data

    print(f"Cache miss: {namespace}")

    data = fetch_function()

    save_cached_data(cache_key, data)

    return data
