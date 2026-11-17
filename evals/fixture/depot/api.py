# ABOUTME: JSON shapes served to the mobile app and the web client.
# ABOUTME: The mobile app switches on the status strings; see README.
from depot.orders import get_order


def order_json(conn, order_id):
    order = get_order(conn, order_id)
    return {
        "id": order["id"],
        "status": order["status"],
        "total_cents": order["total_cents"],
        "can_cancel": order["status"] in ("pending", "paid"),
    }
