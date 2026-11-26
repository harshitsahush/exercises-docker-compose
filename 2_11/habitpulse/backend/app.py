import os
from datetime import date
from flask import Flask, jsonify, request
import psycopg
from psycopg.rows import dict_row
import redis

app = Flask(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_NAME = os.getenv("POSTGRES_DB", "habitpulse")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
APP_PORT = int(os.getenv("PORT", "5000"))

cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_db_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        row_factory=dict_row,
    )


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS habits (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    completed_on DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
        conn.commit()


@app.get("/health")
def health():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        cache.ping()
        return jsonify({"status": "healthy", "db": DB_HOST, "redis": REDIS_HOST}), 200
    except Exception as exc:
        return jsonify({"status": "unhealthy", "error": str(exc)}), 500


@app.get("/habits")
def list_habits():
    init_db()
    cache.incr("habits_list_requests")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, completed_on FROM habits ORDER BY id ASC;")
            rows = cur.fetchall()

    today_str = date.today().isoformat()
    habits = [
        {
            "id": row["id"],
            "name": row["name"],
            "completed_today": row["completed_on"].isoformat() == today_str
            if row["completed_on"]
            else False,
        }
        for row in rows
    ]
    return jsonify(
        {
            "habits": habits,
            "list_requests_count": int(cache.get("habits_list_requests") or 0),
        }
    )


@app.post("/habits")
def create_habit():
    init_db()
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Habit name is required"}), 400

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO habits (name) VALUES (%s) RETURNING id, name, completed_on;",
                (name,),
            )
            row = cur.fetchone()
        conn.commit()

    return jsonify({"id": row["id"], "name": row["name"], "completed_today": False}), 201


@app.post("/habits/<int:habit_id>/toggle")
def toggle_habit(habit_id: int):
    init_db()
    today = date.today()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, completed_on FROM habits WHERE id = %s;", (habit_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Habit not found"}), 404

            new_date = None if row["completed_on"] == today else today
            cur.execute(
                "UPDATE habits SET completed_on = %s WHERE id = %s RETURNING id, name, completed_on;",
                (new_date, habit_id),
            )
            updated = cur.fetchone()
        conn.commit()

    return jsonify(
        {
            "id": updated["id"],
            "name": updated["name"],
            "completed_today": updated["completed_on"] == today,
        }
    )


@app.delete("/habits/<int:habit_id>")
def delete_habit(habit_id: int):
    init_db()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM habits WHERE id = %s RETURNING id;", (habit_id,))
            deleted = cur.fetchone()
        conn.commit()

    if not deleted:
        return jsonify({"error": "Habit not found"}), 404
    return jsonify({"deleted": habit_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
