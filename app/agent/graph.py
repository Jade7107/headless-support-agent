from typing import Annotated, Sequence, TypedDict
import operator
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.postgres import PostgresSaver
from app.core.config import get_settings

settings = get_settings()

# We swap 'operator.add' for LangGraph's native 'add_messages' reducer
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
@tool
def check_refund_status(transaction_id: str) -> str:
    """Use this tool to check the refund status of a specific transaction."""
    return f"Refund for transaction {transaction_id} is currently processing and will clear in 2-3 business days."
@tool
def check_inventory(product_sku: str) -> str:
    """Use this tool to check if a specific product SKU is currently in stock."""
    # Simulating a database lookup
    if "PROD" in product_sku:
        return f"Product {product_sku} is in stock. We have 45 units available."
    return f"Product {product_sku} is currently out of stock."

tools = [check_refund_status, check_inventory]

llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.3-70b-versatile", 
    api_key=settings.groq_api_key
)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    """This node asks the LLM to process the conversation history and decide what to do."""
    
    # 1. Define the Agent's identity and rules
    system_prompt = SystemMessage(
        content="""You are a highly efficient, professional technical support agent. 
        Your job is to assist users with their accounts, refunds, and inventory checks.
        Never break character. If you do not have a tool to answer a question, apologize and say you cannot help."""
    )
    
    # 2. Prepend the system prompt to the current conversation history
    # We do this on the fly so we don't permanently pollute the state's memory log
    messages = [system_prompt] + list(state["messages"])
    
    # 3. Ask the LLM to think
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

tool_node = ToolNode(tools)

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "action"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("action", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"action": "action", END: END})
workflow.add_edge("action", "agent")

# ---------------------------------------------------------
# 7. Permanent Database Memory (Async PostgresSaver)
# ---------------------------------------------------------
import os
import psycopg

# MAGIC UPGRADE: If Render provides a DATABASE_URL, use it (Cloud). Otherwise, build the local Docker one.
DB_URI = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{settings.database.username}:{settings.database.password.get_secret_value()}@{settings.database.hostname}:{settings.database.port}/{settings.database.db}"
)

# We use the sync connection JUST ONCE to safely build the tables on startup
with psycopg.connect(DB_URI, autocommit=True) as setup_conn:
    PostgresSaver(setup_conn).setup()

# MAGIC UPGRADE: We create an Asynchronous Connection Pool for high-concurrency traffic
async_pool = AsyncConnectionPool(conninfo=DB_URI, max_size=20)

# Initialize the ASYNC Postgres checkpointer
memory = AsyncPostgresSaver(async_pool)

# Compile the graph with the async memory
support_agent = workflow.compile(checkpointer=memory)