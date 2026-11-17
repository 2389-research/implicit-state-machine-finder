# ABOUTME: Tests for the support ticket lifecycle.
# ABOUTME: Run with: python3 -m unittest discover -s tests
import unittest

from depot import db, tickets
from depot.tickets import TicketState


class TicketTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()

    def test_resolve_then_close(self):
        ticket_id = tickets.open_ticket(self.conn)
        tickets.transition(self.conn, ticket_id, TicketState.RESOLVED)
        tickets.transition(self.conn, ticket_id, TicketState.CLOSED)
        self.assertEqual(tickets.get_state(self.conn, ticket_id), TicketState.CLOSED)

    def test_closed_ticket_cannot_reopen(self):
        ticket_id = tickets.open_ticket(self.conn)
        tickets.transition(self.conn, ticket_id, TicketState.RESOLVED)
        tickets.transition(self.conn, ticket_id, TicketState.CLOSED)
        with self.assertRaises(tickets.IllegalTransition):
            tickets.transition(self.conn, ticket_id, TicketState.OPEN)


if __name__ == "__main__":
    unittest.main()
