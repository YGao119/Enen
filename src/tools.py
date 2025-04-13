
from robinhood import RobinhoodClient
from langchain_core.tools import tool
import httpx
import os
from typing import Any
import logging

logger = logging.getLogger(__name__)
robinhood_client = RobinhoodClient()

@tool
def get_account_info():
    """Use this to get current account information.
    
    Returns:
        A dictionary containing the account data, or an error message if the request fails.
    """
    logger.info("Getting account info...")
    try:

        account = robinhood_client.get_account()
        logger.info("Account info retrieved successfully.")
        return account
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return {"error": str(e)}

@tool
def get_holdings(*asset_codes: str | None):
    """Use this to get current holdings.
    
    Args:
        asset_codes: A list of asset codes to look up (e.g., "BTC", "ETH").
        If no asset codes are provided, all crypto holdings will be returned.
        
    Returns:
        A dictionary containing the holdings data, or an error message if the request fails.
    """
    logger.info("Getting holdings...")
    try:
        holdings = robinhood_client.get_holdings(*asset_codes)
        logger.info("Holdings retrieved successfully.")
        return holdings
    except Exception as e:
        logger.error(f"Error getting holdings: {e}")
        return {"error": str(e)}

@tool
def get_crypto_best_bid_ask(symbols: list[str]):
    """Use this to get current best bid and ask prices.
    
    Args:
        symbols: A list of currency pair symbols to look up (e.g., "BTC-USD", "ETH-USD").
        
    Returns:
        A dictionary containing the best bid and ask prices, or an error message if the request fails.
    """
    logger.info("Getting best bid and ask prices...")
    try:
        best_bid_ask = robinhood_client.get_best_bid_ask(*symbols)
        logger.info("Best bid and ask prices retrieved successfully.")
        return best_bid_ask
    except Exception as e:
        logger.error(f"Error getting best bid and ask prices: {e}")
        return {"error": str(e)}

@tool
def place_order(
    client_order_id: str,
    side: str,
    order_type: str,
    symbol: str,
    order_config: dict[str, str],
) -> Any:
    """
    Args:
        client_order_id: A unique identifier for the order.
        side: The side of the order ("buy" or "sell").
        order_type: The type of order ("limit", "market", "stop_limit", "stop_loss").
        symbol: The currency pair symbol (e.g., "BTC-USD").
        order_config: A dictionary containing the order configuration.

    Returns:
        A dictionary containing the order data, or an error message if the request fails.
    """
    logger.info("Placing order...")
    try:
        order = robinhood_client.place_order(client_order_id, side, order_type, symbol, order_config)
        logger.info("Order placed successfully.")
        return order
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        return {"error": str(e)}


@tool
def get_stock_price(symbol: str):
    """Use this to get current stock price and basic information.

    Args:
        symbol: The stock symbol to look up (e.g., "AAPL").

    Returns:
        A dictionary containing the stock data, or an error message if the request fails.
    """    
    logger.info("Getting stock price...")
    try:
        response = httpx.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": os.getenv("ALPHA_VANTAGE_API_KEY")
            }
        )
        response.raise_for_status()
        data = response.json()
        if "Global Quote" not in data:
            return {"error": "Invalid API response format or symbol not found."}
        logger.info("Stock price retrieved successfully.")
        return data["Global Quote"]
    except httpx.HTTPError as e:
        logger.error(f"Error getting stock price: {e}")
        return {"error": f"API request failed: {e}"}
    except ValueError:
        logger.error("Invalid JSON response from API.")
        return {"error": "Invalid JSON response from API."}
