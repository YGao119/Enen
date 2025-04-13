from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, ToolMessage
from typing import Any, Dict, AsyncIterable, Literal
from pydantic import BaseModel
from tools import get_account_info, get_holdings, get_stock_price, get_crypto_best_bid_ask, place_order

memory = MemorySaver()


class ResponseFormat(BaseModel):
    """Respond to the user in this format."""
    status: Literal["input_required", "completed", "error"] = "input_required"
    message: str

class StockAgent:

    SYSTEM_INSTRUCTION = (
        "You are a specialized assistant for stock and crypto market information. "
        "You have access to the following tools: "
        "- get_stock_price: Get current stock price and basic information."
        "- get_holdings: Get current crypto holdings."
        "- get_account_info: Get current account information."
        "- get_best_bid_ask: Get current best bid and ask prices for crypto currencies."
        "- place_order: Place a crypto order."
        "Always use the tools to answer the user's questions."
    )
     
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.tools = [get_stock_price, get_holdings, get_account_info, get_crypto_best_bid_ask, place_order]

        self.graph = create_react_agent(
            self.model, tools=self.tools, checkpointer=memory, prompt = self.SYSTEM_INSTRUCTION, response_format=ResponseFormat
        )

    def invoke(self, query, sessionId) -> str:
        config = {"configurable": {"thread_id": sessionId}}
        self.graph.invoke({"messages": [("user", query)]}, config)        
        return self.get_agent_response(config)

    async def stream(self, query, sessionId) -> AsyncIterable[Dict[str, Any]]:
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": sessionId}}

        for item in self.graph.stream(inputs, config, stream_mode="values"):
            message = item["messages"][-1]
            if (
                isinstance(message, AIMessage)
                and message.tool_calls
                and len(message.tool_calls) > 0
            ):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Looking up the stock price...",
                }
            elif isinstance(message, ToolMessage):
                yield {
                    "is_task_complete": False,
                    "require_user_input": False,
                    "content": "Processing the stock price..",
                }            
        
        yield self.get_agent_response(config)

        
    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)        
        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(structured_response, ResponseFormat): 
            if structured_response.status == "input_required":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "error":
                return {
                    "is_task_complete": False,
                    "require_user_input": True,
                    "content": structured_response.message
                }
            elif structured_response.status == "completed":
                return {
                    "is_task_complete": True,
                    "require_user_input": False,
                    "content": structured_response.message
                }

        return {
            "is_task_complete": False,
            "require_user_input": True,
            "content": "We are unable to process your request at the moment. Please try again.",
        }

    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]
