# This agent is built on top of the previous agent-lab-0*.py. It incorpoated with learnings from the respective labs

#lab 01
# ensure that you the knowledge base on aws set up first
#lab 02
# ensure that you have the memory manager set up first and get the memory_id
# lab 03
# ensure that you have the gateway created and the tools set up

# Import libraries
from boto3.session import Session

from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

from tools.retrieval import get_technical_support, get_product_info
from tools.web_search import web_search
from tools.return_policy import get_return_policy

import uuid

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from bedrock_agentcore.runtime import (
    BedrockAgentCoreApp,
)

from libraries.aws import get_or_create_cognito_pool

# # Enable detailed debug logs for the Strands SDK
# import logging
# logging.getLogger("strands").setLevel(logging.DEBUG)

# # Configure the log handler to stream to stderr
# logging.basicConfig(
#     format="%(levelname)s | %(name)s | %(message)s",
#     handlers=[logging.StreamHandler()]
# )

# ------------------------------------------------------------------
# Common Utilities
# ------------------------------------------------------------------
boto_session = Session()
region = boto_session.region_name

# ------------------------------------------------------------------
# Memory Setup
# ------------------------------------------------------------------
memory_id = "CustomerSupportMemory-UeB3D6Ahia" # global level memory resource database
ACTOR_ID = "customer_001" # user level. helps to distinguish memory between different users
session_id = uuid.uuid4() # session level. helps to distinguish memory between different sessions. 1 actor could have multiple sessions.
# Memory > Actor > Session


memory_config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=str(session_id),
        actor_id=ACTOR_ID,
        retrieval_config={
            "support/customer/{actorId}/semantic": RetrievalConfig(top_k=3, relevance_score=0.2),
            "support/customer/{actorId}/preferences": RetrievalConfig(top_k=3, relevance_score=0.2)
        }
    )

# ------------------------------------------------------------------
# Agentcore Tool Connection
# ------------------------------------------------------------------
gateway_url = "https://customersupport-gw-mnyzzral2q.gateway.bedrock-agentcore.ap-southeast-1.amazonaws.com/mcp"
try:
    cognito_config = get_or_create_cognito_pool(refresh_token=True)
    print(cognito_config)
    mcp_client = MCPClient(
        lambda: streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {cognito_config['bearer_token']}"},
        )
    )
except Exception as e:
    print(f"❌ Error getting cognito config: {str(e)}")
    exit(1)

# ------------------------------------------------------------------
# Agentcore Runtime App Setup
# ------------------------------------------------------------------
SYSTEM_PROMPT = """You are a helpful and professional customer support assistant for an electronics e-commerce company.
Your role is to:
- Provide accurate information using the tools available to you
- Support the customer with technical information and product specifications, and maintenance questions
- Be friendly, patient, and understanding with customers
- Always offer additional help after answering questions
- If you can't help with something, direct customers to the appropriate contact

You have access to the following tools:
1. get_return_policy() - For warranty and return policy questions
2. get_product_info() - To get information about a specific product
3. get_technical_support() - For troubleshooting issues, setup guides, maintenance tips, and detailed technical assistance
4. web_search() - To access current technical documentation, or for updated information.
5. check_warranty_status() - To check the warranty status of a product using its serial number and optionally verify via email 
For any technical problems, setup questions, or maintenance concerns, always use the get_technical_support() tool as it contains our comprehensive technical documentation and step-by-step guides.

Always use the appropriate tool to get accurate, up-to-date information rather than making assumptions about electronic products or specifications."""

# Initialize the Bedrock model (Anthropic Claude 3.7 Sonnet)
model = BedrockModel(
    model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0",
    temperature=0.3,
    region_name=region,
)

# Create the customer support agent with all tools from directory
# agent = Agent(
#     model=model,
#     load_tools_from_directory=True,
#     system_prompt=SYSTEM_PROMPT,
#     # callback_handler = None # to disable console output
# )

# Module import approach
# agent = Agent(
#     model=model,
#     session_manager=AgentCoreMemorySessionManager(memory_config, region),
#     tools=[
#         get_product_info,  # Tool 1: Simple product information lookup
#         get_return_policy,  # Tool 2: Simple return policy lookup
#         web_search,  # Tool 3: Access the web for updated information
#         get_technical_support,  # Tool 4: Technical support & troubleshooting
#     ],
#     system_prompt=SYSTEM_PROMPT,
#     # callback_handler = None # to disable console output
# )

# # MCP Client approach with local agent
# def create_agent(prompt):
#     try:
#         with mcp_client:
#             tools = [
#                 get_product_info,
#                 get_return_policy,
#                 get_technical_support,
#             ] + mcp_client.list_tools_sync()

#             # Create the customer support agent
#             agent = Agent(
#                 model=model,
#                 session_manager=AgentCoreMemorySessionManager(memory_config, region),
#                 tools=tools,
#                 system_prompt=SYSTEM_PROMPT,
#             )
#             print("Loaded tools:", agent.tool_names)
#             # print("Tools configs:", agent.tool_registry.get_all_tools_config())
#             response = agent(prompt)
#             return response
#     except Exception as e:
#         raise e

# Entire agent to be hosted on agentcore runtime
app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload, context=None):
    """AgentCore Runtime entrypoint function"""
    user_input = payload.get("prompt", "")

    # Access request headers - handle None case
    request_headers = context.request_headers or {}

    # Get Client JTW token (aka bearer token or access token)
    auth_header = request_headers.get("Authorization", "")

    print(f"Auth header: {auth_header}")

    if gateway_url and auth_header:
        try:
            with mcp_client:
                tools = [
                    get_product_info,
                    get_return_policy,
                    get_technical_support,
                ] + mcp_client.list_tools_sync()

                # Create the customer support agent
                agent = Agent(
                    model=model,
                    session_manager=AgentCoreMemorySessionManager(memory_config, region),
                    tools=tools,
                    system_prompt=SYSTEM_PROMPT,
                )
                print("Loaded tools:", agent.tool_names)
                
                # Stream the response
                stream = agent.stream_async(user_input)
                async for event in stream:
                    if "data" in event:
                        yield event["data"] # Stream data chunks
                    elif "message" in event:
                        yield event["message"] # Stream message parts
                        
        except Exception as e:
                print(f"MCP client error: {str(e)}")
                yield f"Error: {str(e)}"



if __name__ == "__main__":
    # - Note that for this to work properly, you can only run `python -m agents.agent` from within myagents parent folder
    # - If agent.py is outside and within myagents parent folder (ie not within a agents folder), you can run `python agent.py`
    # - All these is so that the python file within each sub folders (e.g. tools/return_policy.py can reference to libraries.debug_tools)
    app.run()