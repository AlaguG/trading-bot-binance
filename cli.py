"""
cli.py
Command-line entry point for the trading bot.

Examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000

API credentials can be passed via --api-key/--api-secret, or (recommended)
set as environment variables BINANCE_API_KEY / BINANCE_API_SECRET.
"""

import argparse
import os
import sys

from bot.client import BasicBot, BinanceAPIError, BinanceNetworkError
from bot.orders import execute_order
from bot.validators import ValidationError, validate_order_input
from bot.logging_config import get_logger

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Simplified trading bot for Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"], help="Order side")
    parser.add_argument(
        "--type", dest="order_type", required=True,
        choices=["MARKET", "LIMIT", "market", "limit"], help="Order type"
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", required=False, default=None, help="Price (required for LIMIT orders)")
    parser.add_argument(
        "--api-key", dest="api_key", default=os.environ.get("BINANCE_API_KEY"),
        help="Binance Testnet API key (or set BINANCE_API_KEY env var)"
    )
    parser.add_argument(
        "--api-secret", dest="api_secret", default=os.environ.get("BINANCE_API_SECRET"),
        help="Binance Testnet API secret (or set BINANCE_API_SECRET env var)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Validate input before touching the network at all
    try:
        validated = validate_order_input(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValidationError as exc:
        logger.error("Validation failed: %s", exc)
        print(f"INVALID INPUT: {exc}")
        sys.exit(1)

    # 2. Build the API client
    try:
        bot = BasicBot(api_key=args.api_key, api_secret=args.api_secret)
    except ValueError as exc:
        logger.error("Client init failed: %s", exc)
        print(f"CONFIG ERROR: {exc}")
        sys.exit(1)

    # 3. Place the order, handling API/network failures without a raw traceback
    try:
        execute_order(bot, validated)
    except (BinanceAPIError, BinanceNetworkError):
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - final safety net, always log unexpected errors
        logger.exception("Unexpected error while placing order")
        print(f"UNEXPECTED ERROR: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
