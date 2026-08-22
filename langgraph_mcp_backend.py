import os
import asyncio
import threading
import requests
import aiosqlite

from typing import TypedDict, Annotated

from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.tools import tool, BaseTool

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun

from langchain_mcp_adapters.client import MultiServerMCPClient

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")


# ============================================================
# DEDICATED ASYNC LOOP
# ============================================================

_ASYNC_LOOP = asyncio.new_event_loop()

_ASYNC_THREAD = threading.Thread(
    target=_ASYNC_LOOP.run_forever,
    daemon=True
)

_ASYNC_THREAD.start()


def _submit_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)


def run_async(coro):
    return _submit_async(coro).result()


def submit_async_task(coro):
    return _submit_async(coro)


# ============================================================
# LLM
# ============================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)


# ============================================================
# SEARCH TOOL
# ============================================================

search_tool = DuckDuckGoSearchRun(region="us-en")


# ============================================================
# STOCK TOOL
# ============================================================

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Get the latest available stock price for ONE company.

    Use only one stock symbol per tool call.

    Examples:
    Google -> GOOG
    Apple -> AAPL
    Tesla -> TSLA
    Microsoft -> MSFT
    Amazon -> AMZN
    TCS -> TCS.BSE
    Reliance -> RELIANCE.BSE
    Infosys -> INFY.BSE
    """

    if not ALPHA_VANTAGE_API_KEY:
        return {
            "success": False,
            "error": "ALPHA_VANTAGE_API_KEY is missing."
        }

    symbol = symbol.strip().upper()

    aliases = {
        "GOOGLE": "GOOG",
        "ALPHABET": "GOOG",
        "APPLE": "AAPL",
        "TESLA": "TSLA",
        "MICROSOFT": "MSFT",
        "AMAZON": "AMZN",
        "NVIDIA": "NVDA",
        "META": "META",
        "NETFLIX": "NFLX",
        "TCS": "TCS.BSE",
        "TATA CONSULTANCY SERVICES": "TCS.BSE",
        "RELIANCE": "RELIANCE.BSE",
        "RELIANCE INDUSTRIES": "RELIANCE.BSE",
        "INFOSYS": "INFY.BSE",
        "INFY": "INFY.BSE",
        "HDFC BANK": "HDFCBANK.BSE",
        "ICICI BANK": "ICICIBANK.BSE",
    }

    symbol = aliases.get(symbol, symbol)

    try:
        response = requests.get(
            "https://www.alphavantage.co/query",
            params={
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": ALPHA_VANTAGE_API_KEY,
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

    except requests.RequestException as e:
        return {
            "success": False,
            "symbol": symbol,
            "error": str(e)
        }

    if "Note" in data:
        return {
            "success": False,
            "symbol": symbol,
            "error": "Alpha Vantage rate limit reached."
        }

    if "Information" in data:
        return {
            "success": False,
            "symbol": symbol,
            "error": data["Information"]
        }

    if "Error Message" in data:
        return {
            "success": False,
            "symbol": symbol,
            "error": data["Error Message"]
        }

    quote = data.get("Global Quote", {})

    if not quote:
        return {
            "success": False,
            "symbol": symbol,
            "error": "No stock data found."
        }

    price = quote.get("05. price")

    if not price:
        return {
            "success": False,
            "symbol": symbol,
            "error": "Price unavailable."
        }

    currency = "INR" if symbol.endswith(".BSE") else "USD"

    return {
        "success": True,
        "symbol": symbol,
        "price": float(price),
        "currency": currency,
        "latest_trading_day": quote.get("07. latest trading day"),
        "source": "Alpha Vantage"
    }


# ============================================================
# WEATHER TOOL
# ============================================================

@tool
def get_weather(city: str) -> dict:
    """
    Get current weather for a city using Open-Meteo.
    """

    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={
                "name": city,
                "count": 1
            },
            timeout=10,
        )

        geo.raise_for_status()
        geo_data = geo.json()

        if not geo_data.get("results"):
            return {
                "success": False,
                "error": f"City '{city}' not found."
            }

        location = geo_data["results"][0]

        weather = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current_weather": "true"
            },
            timeout=10,
        )

        weather.raise_for_status()
        weather_data = weather.json()

        current = weather_data.get("current_weather", {})

        return {
            "success": True,
            "city": location["name"],
            "country": location.get("country"),
            "temperature_c": current.get("temperature"),
            "wind_speed_kmh": current.get("windspeed"),
            "weather_code": current.get("weathercode"),
            "source": "Open-Meteo"
        }

    except requests.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================
# MCP CLIENT
# ============================================================

client = MultiServerMCPClient(
    {
        "expense": {
            "transport": "streamable_http",
            "url": "https://splendid-gold-dingo.fastmcp.app/mcp",
        }
    }
)


def load_mcp_tools() -> list[BaseTool]:

    try:
        loaded_tools = run_async(client.get_tools())

        print("\nLoaded MCP tools:")

        for tool_obj in loaded_tools:
            print("-", tool_obj.name)

        return loaded_tools

    except Exception as e:
        print("Failed to load MCP tools:", e)
        return []


mcp_tools = load_mcp_tools()


# ============================================================
# COMBINE TOOLS
# ============================================================

tools = [
    search_tool,
    get_stock_price,
    get_weather,
    *mcp_tools
]

llm_with_tools = llm.bind_tools(tools)


# ============================================================
# STATE
# ============================================================

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ============================================================
# CHAT NODE
# ============================================================

async def chat_node(state: ChatState):

    system_message = SystemMessage(
        content="""
You are a helpful AI assistant with access to tools.

Tool usage rules:

STOCKS:
- Use get_stock_price.
- Make only ONE stock tool call for one company.
- Google/Alphabet -> GOOG.
- TCS -> TCS.BSE.
- Do not query multiple share classes unless explicitly asked.

WEATHER:
- Use get_weather for current weather questions.

NEWS:
- Use DuckDuckGo search for latest news or current events.

EXPENSES:
- Use the available MCP expense tools when the user asks about expenses.

GENERAL:
- Never invent live data.
- If a tool returns an error, explain the error clearly.
- Give concise, natural answers after using tools.
"""
    )

    response = await llm_with_tools.ainvoke(
        [system_message] + state["messages"]
    )

    return {
        "messages": [response]
    }


# ============================================================
# TOOL NODE
# ============================================================

tool_node = ToolNode(tools)


# ============================================================
# CHECKPOINTER
# ============================================================

async def _init_checkpointer():

    conn = await aiosqlite.connect("chatbot.db")

    return AsyncSqliteSaver(conn)


checkpointer = run_async(_init_checkpointer())


# ============================================================
# GRAPH
# ============================================================

graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges(
    "chat_node",
    tools_condition
)

graph.add_edge("tools", "chat_node")

chatbot = graph.compile(
    checkpointer=checkpointer
)


# ============================================================
# THREAD HELPERS
# ============================================================

async def _alist_threads():

    thread_ids = set()

    async for checkpoint in checkpointer.alist(None):

        thread_ids.add(
            checkpoint.config["configurable"]["thread_id"]
        )

    return list(thread_ids)


def retrieve_all_threads():

    return run_async(_alist_threads())