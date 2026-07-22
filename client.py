"""
client.py
Thin wrapper around the Binance Futures Testnet REST API.

Uses direct REST calls (requests) with HMAC-SHA256 request signing, as
described in Binance's API docs, rather than the python-binance library,
to keep dependencies minimal and the signing logic transparent.

As of the 2025 Binance Demo Trading revamp, the old GitHub-login testnet
site (testnet.binancefuture.com) was retired. API keys are now created
from a normal Binance account while in "Demo Trading" mode
(https://demo.binance.com/en/futures), and the REST base URL changed to
demo-fapi.binance.com.

Docs: https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info
Base URL: https://demo-fapi.binance.com
"""

import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests

from bot.logging_config import get_logger

logger = get_logger(__name__)

BASE_URL = "https://demo-fapi.binance.com"


class BinanceAPIError(Exception):
    """Raised when Binance returns an error response."""


class BinanceNetworkError(Exception):
    """Raised when the request to Binance fails at the network level."""


class BasicBot:
    """
    Minimal Binance Futures Testnet client.

    Handles request signing, sending, logging, and error translation.
    Order-building logic lives in orders.py; this class only knows how
    to talk to the API.
    """

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL, timeout: int = 10):
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must be provided (env vars or --api-key/--api-secret).")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        # Offset (ms) between Binance server time and local system time.
        # Populated lazily on first signed request via _sync_server_time().
        # This protects against "-1021/-2015" signature errors caused by an
        # out-of-sync local clock (common on locked-down/corporate networks
        # where Windows can't reach an NTP server).
        self._server_time_offset_ms = None

    def _sync_server_time(self) -> None:
        """
        Fetch Binance server time and compute the offset from local time,
        so signed request timestamps line up with Binance's clock even if
        the local OS clock is not NTP-synced.
        """
        try:
            response = self.session.get(f"{self.base_url}/fapi/v1/time", timeout=self.timeout)
            response.raise_for_status()
            server_time_ms = response.json()["serverTime"]
            local_time_ms = int(time.time() * 1000)
            self._server_time_offset_ms = server_time_ms - local_time_ms
            logger.info("Synced server time. Offset from local clock: %sms", self._server_time_offset_ms)
        except Exception as exc:  # noqa: BLE001 - non-fatal, we fall back to local time
            logger.warning("Could not sync server time, falling back to local clock: %s", exc)
            self._server_time_offset_ms = 0

    def _sign(self, params: dict) -> dict:
        """Attach timestamp + HMAC-SHA256 signature required for signed endpoints."""
        if self._server_time_offset_ms is None:
            self._sync_server_time()

        params = dict(params)
        params["timestamp"] = int(time.time() * 1000) + self._server_time_offset_ms
        params.setdefault("recvWindow", 10000)  # generous window to absorb residual clock drift
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(self, method: str, path: str, params: dict, signed: bool = True) -> dict:
        url = f"{self.base_url}{path}"
        request_params = self._sign(params) if signed else params

        logger.info("REQUEST %s %s | params=%s", method, url, {k: v for k, v in params.items()})

        try:
            response = self.session.request(method, url, params=request_params, timeout=self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("NETWORK ERROR %s %s | %s", method, url, exc)
            raise BinanceNetworkError(f"Network error while calling {path}: {exc}") from exc

        logger.info("RESPONSE %s %s | status=%s | body=%s", method, url, response.status_code, response.text)

        try:
            data = response.json()
        except ValueError:
            logger.error("Non-JSON response from %s: %s", url, response.text)
            raise BinanceAPIError(f"Non-JSON response from {path}: {response.text}")

        if response.status_code != 200:
            code = data.get("code")
            msg = data.get("msg", response.text)
            logger.error("API ERROR %s %s | code=%s msg=%s", method, url, code, msg)
            raise BinanceAPIError(f"Binance API error (code {code}): {msg}")

        return data

    def ping(self) -> dict:
        """Unsigned connectivity check."""
        return self._request("GET", "/fapi/v1/ping", {}, signed=False)

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price: float = None) -> dict:
        """
        Place a MARKET or LIMIT order on USDT-M Futures Testnet.
        POST /fapi/v1/order
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = "GTC"  # Good-Til-Canceled, required for LIMIT orders

        return self._request("POST", "/fapi/v1/order", params, signed=True)

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """GET /fapi/v1/order - useful to poll a MARKET order's fill details."""
        params = {"symbol": symbol, "orderId": order_id}
        return self._request("GET", "/fapi/v1/order", params, signed=True)
