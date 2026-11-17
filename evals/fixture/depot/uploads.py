# ABOUTME: Chunked upload of product images. Parts arrive in any order, then get assembled.
# ABOUTME: The assembled file lands in the spool directory as <upload_id>.bin.
import os


def begin(conn, expected_parts):
    cur = conn.execute("INSERT INTO uploads (expected_parts) VALUES (?)", (expected_parts,))
    conn.commit()
    return cur.lastrowid


def add_part(conn, upload_id, n, body):
    conn.execute(
        "INSERT INTO upload_parts (upload_id, n, body) VALUES (?, ?, ?)", (upload_id, n, body)
    )
    conn.commit()


def status(conn, spool, upload_id):
    if os.path.exists(os.path.join(spool, f"{upload_id}.lock")):
        return "assembling"
    if os.path.exists(os.path.join(spool, f"{upload_id}.bin")):
        return "ready"
    upload = conn.execute("SELECT * FROM uploads WHERE id = ?", (upload_id,)).fetchone()
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM upload_parts WHERE upload_id = ?", (upload_id,)
    ).fetchone()["c"]
    if count == upload["expected_parts"]:
        return "complete"
    return "uploading"


def assemble(conn, spool, upload_id):
    if status(conn, spool, upload_id) != "complete":
        raise ValueError("upload not complete")
    lock = os.path.join(spool, f"{upload_id}.lock")
    open(lock, "w").close()
    parts = conn.execute(
        "SELECT body FROM upload_parts WHERE upload_id = ? ORDER BY n", (upload_id,)
    ).fetchall()
    with open(os.path.join(spool, f"{upload_id}.bin"), "wb") as out:
        for part in parts:
            out.write(part["body"])
    os.remove(lock)
