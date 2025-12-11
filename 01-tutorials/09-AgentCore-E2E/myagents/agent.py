# ensure that you the knowledge base on aws set up first
# Import libraries
import os
from boto3.session import Session

from strands import Agent
from strands.models import BedrockModel

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
agent = Agent(
    model=model,
    load_tools_from_directory=True,
    system_prompt=SYSTEM_PROMPT,
    # callback_handler = None # to disable console output
)
# print("Loaded tools:", agent.tool_names)
# print("Tools configs:", agent.tool_registry.get_all_tools_config())

# # Create the customer support agent with all tools from directory
# agent = Agent(
#     model=model,
#     tools=[
#         get_product_info,  # Tool 1: Simple product information lookup
#         get_return_policy,  # Tool 2: Simple return policy lookup
#         web_search,  # Tool 3: Access the web for updated information
#         get_technical_support,  # Tool 4: Technical support & troubleshooting
#     ],
#     system_prompt=SYSTEM_PROMPT,
#     # callback_handler = None # to disable console output
# )

if __name__ == "__main__":
    # run `python agent.py` in myagents folder

    agent("What is the latest iphone, its information, its return policy, and how do i setup a phone?")

    # # check return policy
    # print("-" * 50)
    # res = agent("What's the return policy for my thinkpad X1 Carbon?") 
    # print(res.metrics.get_summary())
    # print(agent.messages)

    # # check technical support
    # print("-" * 50)
    # agent("My laptop won't turn on, what should I check?")
    # print(res.metrics.get_summary())
    # print(agent.messages)

    # # check product info
    # print("-" * 50)
    # agent("What is the specs of the phone you are selling?")
    # print(res.metrics.get_summary())
    # print(agent.messages)

    # # check web search
    # print("-" * 50)
    # agent("What is the latest news in singapore?")
    # print(res.metrics.get_summary())
    # print(agent.messages)