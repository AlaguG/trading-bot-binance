"""
validators.py
Input validation for CLI arguments before they are sent to Binance.
Keeping validation separate from the API layer means bad input never
reaches the network call, and errors are easy to test on their own.
"""

import re

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


class ValidationError(Exception):
    """Raised when user-supplied input fails validation."""


def validate_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"Invalid symbol '{symbol}'. Expected something like 'BTCUSDT' "
            "(letters/numbers only, 5-20 characters)."
        )
    return symbol


def validate_side(side: str) -> str:
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Invalid side '{side}'. Must be one of {sorted(VALID_SIDES)}.")
    return side


def validate_order_type(order_type: str) -> str:
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of {sorted(VALID_ORDER_TYPES)}."
        )
    return order_type


def validate_quantity(quantity: float) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")
    if quantity <= 0:
        raise ValidationError(f"Quantity must be greater than 0, got {quantity}.")
    return quantity


def validate_price(price, order_type: str):
    """Price is required for LIMIT orders, ignored/optional for MARKET."""
    if order_type == "LIMIT":
        if price is None:
            raise ValidationError("Price is required for LIMIT orders.")
        try:
            price = float(price)
        except (TypeError, ValueError):
            raise ValidationError(f"Price must be a number, got '{price}'.")
        if price <= 0:
            raise ValidationError(f"Price must be greater than 0, got {price}.")
        return price
    return None


def validate_order_input(symbol: str, side: str, order_type: str, quantity, price=None) -> dict:
    """Run all validators and return a clean dict of validated values."""
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_quantity = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_type,
        "quantity": clean_quantity,
        "price": clean_price,
    }
