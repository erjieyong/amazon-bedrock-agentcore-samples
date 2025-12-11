# ensure that you the knowledge base on aws set up first
# Import libraries
import boto3
from boto3.session import Session

from ddgs.exceptions import DDGSException, RatelimitException
from ddgs import DDGS

from strands import Agent
from strands.tools import tool
from strands.models import BedrockModel
from strands_tools import retrieve

# common utilities
boto_session = Session()
region = boto_session.region_name

### set up tools ###

# set up a get return policy local tool
@tool
def get_return_policy(product_category):
    """
    Get return policy information for a specific product category.

    Args:
        product_category: Electronics category (e.g., 'smartphones', 'laptops', 'accessories')

    Returns:
        Formatted return policy details including timeframes and conditions
    """
    # if the docstring is not provided, the tool schema would not have the description field. While not ideal, it is still functional.
    return_policies = {
        "smartphones": {
            "window": "30 days",
            "condition": "Original packaging, no physical damage, factory reset required",
            "process": "Online RMA portal or technical support",
            "refund_time": "5-7 business days after inspection",
            "shipping": "Free return shipping, prepaid label provided",
            "warranty": "1-year manufacturer warranty included",
        },
        "laptops": {
            "window": "30 days",
            "condition": "Original packaging, all accessories, no software modifications",
            "process": "Technical support verification required before return",
            "refund_time": "7-10 business days after inspection",
            "shipping": "Free return shipping with original packaging",
            "warranty": "1-year manufacturer warranty, extended options available",
        },
        "accessories": {
            "window": "30 days",
            "condition": "Unopened packaging preferred, all components included",
            "process": "Online return portal",
            "refund_time": "3-5 business days after receipt",
            "shipping": "Customer pays return shipping under $50",
            "warranty": "90-day manufacturer warranty",
        },
        "default": {
            "window": "10 days",
            "condition": "Original condition with all included components",
            "process": "Contact technical support",
            "refund_time": "5-7 business days after inspection",
            "shipping": "Return shipping policies vary",
            "warranty": "Standard manufacturer warranty applies",
        },
    }

    return return_policies.get(product_category, return_policies["default"])

@tool
def get_product_info(product_name):
    """
    Get information about a specific product.

    Args:
        product_name: Name of the product to get information about. Currently only works with 'laptops', 'smartphones', 'headphones' and 'monitors'

    Returns:
        Formatted product information including specifications and features
    """
    # Use strands retrieve tool. this only works with amazon bedrock knowledge bases
    tool_use = {
        "toolUseId": "product_info_query",
        "input": {
            "text": product_name,
            "knowledgeBaseId": "ASCSJV2K3V",
            "region": "ap-southeast-1",
            "numberOfResults": 3,
            "score": 0.4,
        },
    }

    result = retrieve.retrieve(tool_use)

    if result["status"] == "success":
        return result["content"][0]["text"]
    else:
        return f"Technical specifications for {product_name} not available. Please contact our technical support team for detailed product information and compatibility requirements."


@tool
def web_search(keywords: str, region: str = "us-en", max_results: int = 5) -> str:
    """Search the web for updated information.

    Args:
        keywords (str): The search query keywords.
        region (str): The search region: wt-wt, us-en, uk-en, ru-ru, etc..
        max_results (int | None): The maximum number of results to return.
    Returns:
        List of dictionaries with search results.

    """
    try:
        results = DDGS().text(keywords, region=region, max_results=max_results)
        return results if results else "No results found."
    except RatelimitException:
        return "Rate limit reached. Please try again later."
    except DDGSException as e:
        return f"Search error: {e}"
    except Exception as e:
        return f"Search error: {str(e)}"
        
@tool
def get_technical_support(issue_description: str) -> str:
    try:
        # Use strands retrieve tool. this only works with amazon bedrock knowledge bases
        tool_use = {
            "toolUseId": "tech_support_query",
            "input": {
                "text": issue_description,
                "knowledgeBaseId": "XYYXNJDEHJ",
                "region": "ap-southeast-1",
                "numberOfResults": 3,
                "score": 0.4,
            },
        }

        result = retrieve.retrieve(tool_use)

        if result["status"] == "success":
            return result["content"][0]["text"]
        else:
            return f"Unable to access technical support documentation. Error: {result['content'][0]['text']}"

    except Exception as e:
        print(f"Detailed error in get_technical_support: {str(e)}")
        return f"Unable to access technical support documentation. Error: {str(e)}"


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

# Create the customer support agent with all tools
agent = Agent(
    model=model,
    tools=[
        get_product_info,  # Tool 1: Simple product information lookup
        get_return_policy,  # Tool 2: Simple return policy lookup
        web_search,  # Tool 3: Access the web for updated information
        get_technical_support,  # Tool 4: Technical support & troubleshooting
    ],
    system_prompt=SYSTEM_PROMPT,
    # callback_handler = None # to disable console output
)

if __name__ == "__main__":

    import json

    def get_tool_schema(tool):
        """
        Print out the strands auto-generated tool schema.

        Args:
            tool: The tool to print the schema for

        Returns:
            None
        """
        spec= tool.tool_spec
        try:
            # If it's a Pydantic model (common in AI frameworks), convert to dict first
            if hasattr(spec, "model_dump"):
                print(json.dumps(spec.model_dump(), indent=4))
            elif hasattr(spec, "dict"):
                print(json.dumps(spec.dict(), indent=4))
            # If it's already a standard dictionary
            elif isinstance(spec, dict):
                print(json.dumps(spec, indent=4))
            else:
                # If it's a custom object, just print it as a string
                print(spec)
        except Exception as e:
            print(f"Could not format as JSON: {e}")
            print(spec)

    get_tool_schema(get_return_policy)
    get_tool_schema(get_product_info)

    print("-"*50)
    print("Product info about smartphone. Note that you dont need exact keyword as knowledge base is using semantic search")
    print(get_product_info("smartphone"))
    print("-"*50)
    print("Technical support for a setting up a phone.")
    print(get_technical_support("how do i setup a phone?"))

    print("-"*50)
    print("Testing agent")
    print(agent("What is the latest iphone, its information, its return policy, and how do i setup a phone?"))

    # test_results = {
    #     "test default return policy": {
    #         "input": "What is the return policy for tv?",
    #         "output": "",
    #         "expected": "10 days",
    #         "pass": ""
    #         },
    #     "test laptop return policy": {
    #         "input": "What is the return policy for laptop?",
    #         "output": "",
    #         "expected": "30 days",
    #         "pass": ""
    #         }
    # }
    # # test the agent
    # for test in test_results:
    #     test_results[test]["output"] = agent(test_results[test]["input"])
    #     if test_results[test]["expected"] in str(test_results[test]["output"]).lower():
    #         test_results[test]["pass"] = "Pass"
    #     else:
    #         test_results[test]["pass"] = "Fail"
    
    # # print the test results
    # for test, result in test_results.items():
    #     print(f"{test}: {result['pass']}")
    #     if result['pass'] == "Fail":
    #         print(result['output'])
        