from a2a.server import A2AServer
from a2a.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from a2a.utils.push_notification_auth import PushNotificationSenderAuth
from task_manager import AgentTaskManager
from agent import StockAgent
import click
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=8080)
def main(host, port):
    """Starts the Currency Agent server."""
    try:
        if not os.getenv("GOOGLE_API_KEY"):
            raise MissingAPIKeyError("GOOGLE_API_KEY environment variable not set.")

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skills = [
            AgentSkill(
                id="get_stock_price",
                name="Stock Price Tool",
                description="Helps with stock prices and basic stock information",
                tags=["stock price", "stock information"],
                examples=["What is the stock price of AAPL?"],
            ),
            AgentSkill(
                id="get_holdings",
                name="Holdings Tool",
                description="Helps with crypto holdings and basic crypto information",
                tags=["holdings", "crypto"],
                examples=["What are my current crypto holdings?"],
            ),
            AgentSkill(
                id="get_account_info",
                name="Account Info Tool",
                description="Helps with account information and basic account details",
                tags=["account info", "account details"],
                examples=["What is my account information?"],
            ),
            AgentSkill(
                id="get_best_bid_ask",
                name="Best Bid Ask Tool",
                description="Helps with getting current best bid and ask prices for crypto currencies",
                tags=["best bid ask", "price"],
                examples=["What is the best bid and ask for BTC-USD?"],
            ),
            AgentSkill(
                id="place_order",
                name="Place Order Tool",
                description="Helps with placing crypto orders",
                tags=["place order", "order placement"],
                examples=["Place a market order for 1 BTC"],
            ),
        ]
        agent_card = AgentCard(
            name="StockAgent",
            description="Helps with account information, stock prices, crypto best bid ask prices, crypto holdings, and crypto order placement",
            url=f"http://{host}:{port}/",
            version="1.0.0",
            defaultInputModes=StockAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=StockAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=skills,
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=StockAgent(), notification_sender_auth=notification_sender_auth),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"]
        )

        logger.info(f"Starting server on {host}:{port}")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
