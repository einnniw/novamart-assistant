"""Fictional order lookup module for NovaMart Assistant.

ALL DATA IN THIS MODULE IS STRICTLY FICTIONAL AND CREATED SOLELY FOR
EDUCATIONAL AND PORTFOLIO DEMONSTRATION PURPOSES.
"""

from typing import Any, Dict

# Fixed dictionary of fictional mock orders for demonstration.
FICTIONAL_ORDERS: Dict[str, Dict[str, Any]] = {
    "NM-1001": {
        "order_id": "NM-1001",
        "customer_name": "Jordan Lee",
        "status": "Shipped",
        "carrier": "NovaExpress",
        "tracking_number": "TRK-98234-NM",
        "estimated_delivery": "Within 2 business days",
        "items": [
            {"name": "Wireless Noise-Canceling Headphones", "quantity": 1, "price": 89.99}
        ],
        "total_amount": 89.99
    },
    "NM-1002": {
        "order_id": "NM-1002",
        "customer_name": "Alex Mercer",
        "status": "Processing",
        "carrier": "Pending Assignment",
        "tracking_number": None,
        "estimated_delivery": "Estimated 3-5 business days",
        "items": [
            {"name": "Ergonomic Office Chair Cushion", "quantity": 2, "price": 34.50}
        ],
        "total_amount": 69.00
    },
    "NM-1003": {
        "order_id": "NM-1003",
        "customer_name": "Samira Patel",
        "status": "Delivered",
        "carrier": "NovaExpress",
        "tracking_number": "TRK-44129-NM",
        "estimated_delivery": "Delivered on October 15",
        "items": [
            {"name": "Organic Cotton Bed Sheet Set", "quantity": 1, "price": 49.99}
        ],
        "total_amount": 49.99
    }
}


def lookup_order(order_id: str) -> Dict[str, Any]:
    """Look up a fictional order by its ID.
    
    Validates the order ID format and returns order details if found,
    or a clear 'not_found' status without inventing a status.
    """
    # Validate argument type and presence
    if not isinstance(order_id, str) or not order_id.strip():
        return {
            "status": "error",
            "fictional_notice": "Fictional order service for portfolio demo.",
            "message": "Invalid order ID format. Please provide a non-empty string identifier (e.g. 'NM-1001')."
        }

    normalized_id = order_id.strip().upper()
    order = FICTIONAL_ORDERS.get(normalized_id)

    if order:
        return {
            "status": "found",
            "fictional_notice": "Fictional order record for portfolio demonstration only.",
            "order": order
        }

    return {
        "status": "not_found",
        "fictional_notice": "Fictional order record for portfolio demonstration only.",
        "message": f"Order '{normalized_id}' was not found in NovaMart's order records."
    }
