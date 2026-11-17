# ABOUTME: Support ticket lifecycle.
# ABOUTME: Every state change goes through transition(), which checks the table below.
from enum import Enum


class TicketState(str, Enum):
    OPEN = "open"
    WAITING = "waiting"
    RESOLVED = "resolved"
    CLOSED = "closed"


TRANSITIONS = {
    TicketState.OPEN: {TicketState.WAITING, TicketState.RESOLVED},
    TicketState.WAITING: {TicketState.OPEN, TicketState.RESOLVED},
    TicketState.RESOLVED: {TicketState.OPEN, TicketState.CLOSED},
    TicketState.CLOSED: set(),
}


class IllegalTransition(Exception):
    pass


def open_ticket(conn):
    cur = conn.execute("INSERT INTO tickets DEFAULT VALUES")
    conn.commit()
    return cur.lastrowid


def get_state(conn, ticket_id):
    row = conn.execute("SELECT state FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return TicketState(row["state"])


def transition(conn, ticket_id, to):
    current = get_state(conn, ticket_id)
    if to not in TRANSITIONS[current]:
        raise IllegalTransition(f"ticket {ticket_id}: {current.value} -> {to.value} is not allowed")
    conn.execute("UPDATE tickets SET state = ? WHERE id = ?", (to.value, ticket_id))
    conn.commit()
