# This agent is built on top of the previous agent-lab-0*.py. It incorpoated with learnings from the respective labs

#lab 01
# ensure that you the knowledge base on aws set up first
#lab 02
# ensure that you have the memory manager set up first and get the memory_id

# Import libraries
from boto3.session import Session

from strands import Agent
from strands.models import BedrockModel

from tools.retrieval import get_technical_support, get_product_info
from tools.web_search import web_search
from tools.return_policy import get_return_policy

import uuid

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# # Enable detailed debug logs for the Strands SDK
# import logging
# logging.getLogger("strands").setLevel(logging.DEBUG)

# # Configure the log handler to stream to stderr
# logging.basicConfig(
#     format="%(levelname)s | %(name)s | %(message)s",
#     handlers=[logging.StreamHandler()]
# )

# common utilities
boto_session = Session()
region = boto_session.region_name

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


### set up agent ###
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
3. web_search() - To access current technical documentation, or for updated information. 
4. get_technical_support() - For troubleshooting issues, setup guides, maintenance tips, and detailed technical assistance
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
agent = Agent(
    model=model,
    session_manager=AgentCoreMemorySessionManager(memory_config, region),
    tools=[
        get_product_info,  # Tool 1: Simple product information lookup
        get_return_policy,  # Tool 2: Simple return policy lookup
        web_search,  # Tool 3: Access the web for updated information
        get_technical_support,  # Tool 4: Technical support & troubleshooting
    ],
    system_prompt=SYSTEM_PROMPT,
    # callback_handler = None # to disable console output
)

print("Loaded tools:", agent.tool_names)
print("Tools configs:", agent.tool_registry.get_all_tools_config())


if __name__ == "__main__":
    # - Note that for this to work properly, you can only run `python -m agents.agent` from within myagents parent folder
    # - If agent.py is outside and within myagents parent folder (ie not within a agents folder), you can run `python agent.py`
    # - All these is so that the python file within each sub folders (e.g. tools/return_policy.py can reference to libraries.debug_tools)

    # agent("What is the latest iphone, its information, its return policy, and how do i setup a phone?")

    # # check return policy
    # print("-" * 50)
    # res = agent("What's the return policy for my thinkpad X1 Carbon?") 

    # # check technical support
    # print("-" * 50)
    # agent("My laptop won't turn on, what should I check?")

    # # check product info
    # print("-" * 50)
    # agent("What is the specs of the phone you are selling?")

    # check memory
    print("-" * 50)
    response1 = agent("Which headphones would you recommend?")

    # check memory
    print("-" * 50)
    agent("What is my preferred laptop brand and requirements?")

    # check memory, 
    print("-" * 50)
    agent("What do you know about my preferences for phone?")
    # check web search
    print("-" * 50)
    agent("What is the latest iphone models?")
    # check memory
    print("-" * 50)
    agent("What is my preferred phone brand and requirements?")