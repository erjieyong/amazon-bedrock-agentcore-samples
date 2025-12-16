import boto3
from bedrock_agentcore_starter_toolkit import Runtime
from libraries.aws import get_customer_support_secret

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

launch_result = agentcore_runtime.launch()
print("Launch completed:", launch_result.agent_arn)

if __name__ == "__main__":
    pass
