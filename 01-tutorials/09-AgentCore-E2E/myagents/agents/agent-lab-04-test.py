from libraries.aws import get_or_create_cognito_pool, get_customer_support_secret
import uuid
import boto3
from bedrock_agentcore_starter_toolkit import Runtime

# Initialize the runtime toolkit
boto_session = boto3.session.Session()
region = boto_session.region_name

execution_role_arn = "arn:aws:iam::654906373546:role/agentcore_full_access"
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

if __name__ == "__main__":
    runtime_id = "jy_customer_support_agent-0roogH9xtM"
    access_token = get_or_create_cognito_pool(refresh_token=True)

    # Create a session ID for demonstrating session continuity
    session_id = uuid.uuid4()

    print(f"Generated session ID: {session_id}")

    test_prompts = [
        "What is the latest iphone, its information, its return policy, and how do i setup a phone?", # check multi tool call
        "What's the return policy for my thinkpad X1 Carbon?", # check return policy call
        "My laptop won't turn on, what should I check?", # check technical support call
        "What is the specs of the phone you are selling?", # check product info call    
        "Which headphones would you recommend?", # check memory
        "What is my preferred laptop brand and requirements?", # check memory
        "What do you know about my preferences for phone?", # check memory
        "What is the latest iphone models?", # check web search
        "What is my preferred phone brand and requirements?",
        "List all of your tools",
        "I bought an iphone 14 last month. I don't like it because it heats up. How do I solve it?",
        "I have a Gaming Console Pro device , I want to check my warranty status, warranty serial number is MNO33333333.",
        "What are the warranty support guidelines?",
        "How can I fix Lenovo Thinkpad with a blue screen",
        "Tell me detailed information about the technical documentation on installing a new CPU",
    ]

    # Function to test the agent
    def test_agent_responses(prompts):
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


    # Run the tests
    test_agent_responses(test_prompts)

