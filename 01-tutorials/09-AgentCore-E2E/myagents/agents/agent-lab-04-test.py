from libraries.aws import get_or_create_cognito_pool, get_customer_support_secret
import uuid
import boto3
from bedrock_agentcore_starter_toolkit import Runtime

# Initialize the runtime toolkit
boto_session = boto3.session.Session()
region = boto_session.region_name
access_token = get_or_create_cognito_pool(refresh_token=True)
execution_role_arn = "arn:aws:iam::654906373546:role/agentcore_full_access"
agent_arn = "arn:aws:bedrock-agentcore:ap-southeast-1:654906373546:runtime/jy_customer_support_agent-0roogH9xtM"

# ------------------------------------------------------------------
# Using bedrock_agentcore_starter_toolkit
# ------------------------------------------------------------------

def _prepare_agentcore_runtime_config():
    cognito_config = get_customer_support_secret()

    agentcore_runtime = Runtime()

    # Configure the deployment
    response = agentcore_runtime.configure(
        entrypoint="agents/agent-lab-04.py",
        execution_role=execution_role_arn,
        auto_create_ecr=True,
        requirements_file="agents/requirements.txt",
        region=region,
        agent_name="jy_customer_support_agent",
        authorizer_configuration={
            "customJWTAuthorizer": {
                "allowedClients": [
                    cognito_config.get("client_id")
                ],
                "discoveryUrl": cognito_config.get("discovery_url"),
            }
        },
        # Add custom header allowlist for Authorization and custom headers
        request_header_configuration={
            "requestHeaderAllowlist": [
                "Authorization",  # Required for OAuth propogation
                "X-Amzn-Bedrock-AgentCore-Runtime-Custom-H1",  # Custom header
            ]
        },
    )

    print("Configuration completed:", response)
    return agentcore_runtime

# Function to test the agent
def test_agent_responses(prompts, session_id):
    """
    Note that agentcore_runtime is part of the `bedrock_agentcore_starter_toolkit` and is intended to simplify development workflow. NOT recommended for production use.
    """
    agentcore_runtime = _prepare_agentcore_runtime_config()

    for i, prompt in enumerate(prompts, 1):
        print(f"\nTest Case {i}: {prompt}")
        print("-" * 50)
        try:
            response = agentcore_runtime.invoke(
                {"prompt": prompt},
                bearer_token=access_token["bearer_token"],
                session_id=str(session_id), 
            )
            print(response)
        except Exception as e:
            print(f"Error: {str(e)}")
        print("-" * 50)


# ------------------------------------------------------------------
# Using standard http requests
# ------------------------------------------------------------------
import requests
import urllib.parse
import json

def invoke_agentcore_agent(prompt, session_id, agent_arn=agent_arn, region=region, access_token=access_token):
    # URL encode the agent ARN
    escaped_agent_arn = urllib.parse.quote(agent_arn, safe='')

    # Construct the URL
    url = f"https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{escaped_agent_arn}/invocations?qualifier=DEFAULT"

    # Set up headers
    headers = {
        "Authorization": f"Bearer {access_token['bearer_token']}",
        # "X-Amzn-Trace-Id": "your-trace-id", 
        "Content-Type": "application/json",
        "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": str(session_id)
    }

    # Enable verbose logging for requests
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.DEBUG)

    invoke_response = requests.post(
        url,
        headers=headers,
        data=json.dumps({"prompt": prompt}),
        stream=True
    )

    # Print response in a safe manner
    print(f"Status Code: {invoke_response.status_code}")
    print(f"Response Headers: {dict(invoke_response.headers)}")

    if invoke_response.status_code == 200:
        print("\n--- Streaming Response ---")
        for line in invoke_response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data: "):
                    content = decoded_line[6:] # Remove 'data: ' prefix
                    try:
                        # Try to handle it as JSON if possible, otherwise print raw
                        # In strands/agentcore, 'data' events usually are steps/objects, 'message' are strings
                        # But here we are yielding raw objects which agentcore runtime wraps in SSE 'data: ...'
                        
                        # Just print the raw line for visibility first
                        print(f"{content}")
                    except json.JSONDecodeError:
                        print(f"Stream Line: {content}")
    elif invoke_response.status_code >= 400:
        print(f"Error Response ({invoke_response.status_code}):")
        print(invoke_response.text)
    else:
        print(f"Unexpected status code: {invoke_response.status_code}")
        print(invoke_response.text[:500])

# ------------------------------------------------------------------
# Using websockets
# ------------------------------------------------------------------

from bedrock_agentcore.runtime import AgentCoreRuntimeClient
import websockets
import asyncio

async def main():
    client = AgentCoreRuntimeClient(region="ap-southeast-1")

    # Generate WebSocket connection with OAuth
    ws_url, headers = client.generate_ws_connection_oauth(
        runtime_arn=agent_arn,
        bearer_token=access_token["bearer_token"]
    )

    async with websockets.connect(ws_url, additional_headers=headers) as ws:
        await ws.send('{"inputText": "Hello!"}')
        response = await ws.recv()
        print(f"Received: {response}")


if __name__ == "__main__":
    # Create a session ID for demonstrating session continuity
    session_id = uuid.uuid4()

    print(f"Generated session ID: {session_id}")

    test_prompts = [
        "What is the latest iphone, its information, its return policy, and how do i setup a phone?", # check multi tool call
        # "What's the return policy for my thinkpad X1 Carbon?", # check return policy call
        # "My laptop won't turn on, what should I check?", # check technical support call
        # "What is the specs of the phone you are selling?", # check product info call    
        # "Which headphones would you recommend?", # check memory
        # "What is my preferred laptop brand and requirements?", # check memory
        # "What do you know about my preferences for phone?", # check memory
        # "What is the latest iphone models?", # check web search
        # "What is my preferred phone brand and requirements?",
        # "List all of your tools",
        # "I bought an iphone 14 last month. I don't like it because it heats up. How do I solve it?",
        # "I have a Gaming Console Pro device , I want to check my warranty status, warranty serial number is MNO33333333.",
        # "What are the warranty support guidelines?",
        # "How can I fix Lenovo Thinkpad with a blue screen",
        # "Tell me detailed information about the technical documentation on installing a new CPU",
    ]

    # Run the tests using agentcore runtime
    # test_agent_responses(test_prompts, session_id)

    # Run the tests using standard http requests
    for prompt in test_prompts:
        invoke_agentcore_agent(prompt, session_id)

    # Run the tests using websockets
    # asyncio.run(main())