from strands.tools import tool
from libraries.debug_tools import get_tool_schema

@tool
def get_return_policy(product_category: str) -> str:
    """Get return policy information for a specific product category.

    Args:
        product_category (str): The category of electronices product (e.g., 'smartphones', 'laptops', 'accessories')

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

    return str(return_policies.get(product_category, return_policies["default"]))

if __name__ == "__main__":
    print(get_return_policy("smartphones"))
    print(get_return_policy("monitor"))
    get_tool_schema(get_return_policy) # to test, in 09-AgentCore-E2E run `python -m myagents.tools.return_policy`