"""
orders.py
Order placement logic - sits between the CLI and the API client.
Builds a clean order summary, calls the client, and normalizes the result
for display, regardless of whether the order is MARKET or LIMIT.
"""

from bot.client import BasicBot, BinanceAPIError, BinanceNetworkError
from bot.logging_config import get_logger

logger = get_logger(__name__)


def build_order_summary(order: dict) -> str:
    lines = [
        "Order Request Summary",
        "-" * 40,
        f"Symbol   : {order['symbol']}",
        f"Side     : {order['side']}",
        f"Type     : {order['order_type']}",
        f"Quantity : {order['quantity']}",
    ]
    if order["order_type"] == "LIMIT":
        lines.append(f"Price    : {order['price']}")
    return "\n".join(lines)


def build_response_summary(response: dict) -> str:
    lines = [
        "Order Response",
        "-" * 40,
        f"Order ID     : {response.get('orderId')}",
        f"Status       : {response.get('status')}",
        f"Executed Qty : {response.get('executedQty')}",
    ]
    avg_price = response.get("avgPrice")
    if avg_price is not None:
        lines.append(f"Avg Price    : {avg_price}")
    return "\n".join(lines)


def execute_order(bot: BasicBot, validated_order: dict) -> dict:
    """
    Place the order and print/log a clean summary.
    Returns the raw Binance response dict on success, raises on failure.
    """
    print(build_order_summary(validated_order))
    print()

    try:
        response = bot.place_order(
            symbol=validated_order["symbol"],
            side=validated_order["side"],
            order_type=validated_order["order_type"],
            quantity=validated_order["quantity"],
            price=validated_order["price"],
        )
    except BinanceAPIError as exc:
        logger.error("Order failed (API error): %s", exc)
        print(f"FAILED: {exc}")
        raise
    except BinanceNetworkError as exc:
        logger.error("Order failed (network error): %s", exc)
        print(f"FAILED: {exc}")
        raise

    print(build_response_summary(response))
    print()
    print("SUCCESS: order placed.")
    logger.info("Order placed successfully: %s", response)
    return response
