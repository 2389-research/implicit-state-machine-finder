# ABOUTME: Background job runner for label printing and the nightly export.
# ABOUTME: Workers call next_job, then start, then complete or fail; operators can retry or cancel.
MAX_ATTEMPTS = 3


def enqueue(conn, kind):
    cur = conn.execute("INSERT INTO jobs (kind) VALUES (?)", (kind,))
    conn.commit()
    return cur.lastrowid


def next_job(conn):
    return conn.execute(
        "SELECT * FROM jobs WHERE running = 0 AND done = 0 AND failed = 0 ORDER BY id LIMIT 1"
    ).fetchone()


def start(conn, job_id):
    conn.execute("UPDATE jobs SET running = 1, attempts = attempts + 1 WHERE id = ?", (job_id,))
    conn.commit()


def complete(conn, job_id):
    conn.execute("UPDATE jobs SET running = 0, done = 1 WHERE id = ?", (job_id,))
    conn.commit()


def fail(conn, job_id, error):
    conn.execute(
        "UPDATE jobs SET running = 0, failed = 1, last_error = ? WHERE id = ?",
        (error, job_id),
    )
    conn.commit()


def retry(conn, job_id):
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job["attempts"] >= MAX_ATTEMPTS:
        raise ValueError("out of attempts")
    conn.execute("UPDATE jobs SET running = 1, attempts = attempts + 1 WHERE id = ?", (job_id,))
    conn.commit()


def cancel(conn, job_id):
    conn.execute("UPDATE jobs SET running = 0 WHERE id = ?", (job_id,))
    conn.commit()


def summary(conn):
    row = conn.execute(
        "SELECT SUM(running) AS running, SUM(failed) AS failed, SUM(done) AS done FROM jobs"
    ).fetchone()
    return {"running": row["running"] or 0, "failed": row["failed"] or 0, "done": row["done"] or 0}
