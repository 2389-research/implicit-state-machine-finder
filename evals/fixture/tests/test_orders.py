# ABOUTME: Tests for the order path: create, pay, ship, and the JSON served to clients.
# ABOUTME: Run with: python3 -m unittest discover -s tests
import unittest

from depot import api, db, fulfilment, orders, webhooks


class OrderPathTest(unittest.TestCase):
    def setUp(self):
        self.conn = db.connect()

    def test_new_order_is_pending(self):
        order_id = orders.create_order(self.conn, 2500)
        self.assertEqual(api.order_json(self.conn, order_id)["status"], "pending")

    def test_paid_order_ships(self):
        order_id = orders.create_order(self.conn, 2500)
        webhooks.payment_succeeded(self.conn, order_id)
        self.assertEqual(fulfilment.ship_ready_orders(self.conn), [order_id])
        self.assertEqual(api.order_json(self.conn, order_id)["status"], "shipped")

    def test_unpaid_order_does_not_ship(self):
        orders.create_order(self.conn, 2500)
        self.assertEqual(fulfilment.ship_ready_orders(self.conn), [])

    def test_order_json_shape(self):
        order_id = orders.create_order(self.conn, 2500)
        self.assertEqual(
            api.order_json(self.conn, order_id),
            {"id": order_id, "status": "pending", "total_cents": 2500, "can_cancel": True},
        )


if __name__ == "__main__":
    unittest.main()
