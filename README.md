# Simplified Trading Bot — Binance Futures Testnet (USDT-M)

A small, structured CLI application that places MARKET and LIMIT orders
(BUY/SELL) on the Binance Futures Testnet, with input validation, logging,
and error handling.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py           # Binance REST API wrapper (signing, requests, error handling)
    orders.py            # Order building + placement logic
    validators.py         # CLI input validation
    logging_config.py      # Logging setup (writes to trading_bot.log)
  cli.py                  # CLI entry point
  requirements.txt
  README.md
  trading_bot.log          # created on first run
```

## Setup

1. **Create a Binance Futures Demo Trading API key**
   (Note: the old GitHub-login testnet site at `testnet.binancefuture.com`
   was retired by Binance in 2025 in favor of a unified Demo Trading mode
   on the main site.)
   - Log in to a normal Binance account at https://www.binance.com
   - Go to https://demo.binance.com/en/futures and click **Start demo trading**
   - Click the account icon (top right) → **Demo Trading API**
   - Click **Create API** → choose **System generated** → give it a label
   - Copy the **API Key** and **Secret Key** immediately (the secret is
     shown only once)

2. **Install dependencies** (Python 3.8+)
   ```bash
   cd trading_bot
   pip install -r requirements.txt
   ```

3. **Set your API credentials** as environment variables (recommended,
   keeps keys out of shell history):
   ```bash
   export BINANCE_API_KEY="your_api_key_here"
   export BINANCE_API_SECRET="your_api_secret_here"
   ```
   On Windows (PowerShell):
   ```powershell
   $env:BINANCE_API_KEY="your_api_key_here"
   $env:BINANCE_API_SECRET="your_api_secret_here"
   ```

   Alternatively, pass them directly on each command with `--api-key` and
   `--api-secret`.

## How to Run

**Market order (BUY):**
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

**Limit order (SELL):**
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
```

Each run prints:
- the order request summary (symbol, side, type, quantity, price)
- the order response from Binance (orderId, status, executedQty, avgPrice)
- a clear SUCCESS or FAILED message

All requests, responses, and errors are also written to `trading_bot.log`
in the project root.

## Assumptions

- Binance Demo Trading USDT-M Futures endpoint
  (`https://demo-fapi.binance.com`) is used for all calls. This replaces
  the older `testnet.binancefuture.com`, which Binance retired in 2025.
- Direct REST calls via `requests` (with manual HMAC-SHA256 signing) are
  used instead of the `python-binance` library, to keep the dependency
  footprint minimal and the signing logic visible/auditable.
- The account placing orders must already have testnet USDT futures
  balance (the testnet UI provides free test funds) and the symbol must
  be a valid USDT-M perpetual pair (e.g. BTCUSDT).
- `timeInForce` for LIMIT orders defaults to `GTC` (Good-Til-Canceled),
  since the task did not specify a different policy.
- Basic quantity/price validation (must be positive numbers) happens
  client-side before any network call; exchange-specific rules like
  minimum notional or lot size are enforced by Binance itself and
  surfaced back to the user as an API error.

## Error Handling

- **Invalid input** (bad symbol format, missing price for LIMIT, etc.) is
  caught before any API call and reported clearly, exiting with a
  non-zero status.
- **API errors** (e.g. insufficient balance, invalid symbol) are caught,
  logged with the Binance error code/message, and printed to the user.
- **Network errors** (timeouts, connection failures) are caught
  separately and reported without a raw stack trace.

## Bonus Ideas (not implemented by default)

The structure is set up so a third order type (e.g. STOP-LIMIT) could be
added as a new branch in `bot/client.py` (`place_order`) and
`bot/validators.py`, without touching the CLI layer.
