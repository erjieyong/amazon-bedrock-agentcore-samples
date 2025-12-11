from strands.tools import tool
from strands_tools import retrieve

class bedrock_kb:
    def __init__(self, kb_id, tool_use_id):
        self.kb_id = kb_id
        self.tool_use_id = tool_use_id

    def retrieve(self, query):
        # Use strands retrieve tool. this only works with amazon bedrock knowledge bases
        tool_use = {
            "toolUseId": self.tool_use_id,
            "input": {
                "text": query,
                "knowledgeBaseId": self.kb_id,
                "region": "ap-southeast-1",
                "numberOfResults": 3,
                "score": 0.4,
            },
        }

        result = retrieve.retrieve(tool_use)

        if result["status"] == "success":
            return result["content"][0]["text"]
        else:
            return f"Unable to access knowledge base documentation. Error: {result['content'][0]['text']}"

@tool
def get_technical_support(issue_description: str) -> str:
    """Retrieves technical support documentation from a knowledge base.

    Args:
        issue_description: Description of the issue to retrieve technical support documentation for. Techincal support documentation only available for laptop maintenance, monitor calibration, smartphone setup, basic troubleshooting, warranty service and wireless connectivity.

    Returns:
        Technical support documentation for the issue.
    """
    kb = bedrock_kb("XYYXNJDEHJ", "tech_support_query")
    try:
        return kb.retrieve(issue_description)
    except Exception as e:
        print(f"Detailed error in get_technical_support: {str(e)}")
        return f"Unable to access technical support documentation. Error: {str(e)}"

@tool
def get_product_info(product_type: str) -> str:
    """Get detailed technical specifications and information for electronics products.

    Args:
        product_type: Electronics product type (e.g., 'laptops', 'smartphones', 'headphones', 'monitors')

    Returns:
        Formatted product information including warranty, features, and policies
    """
    kb = bedrock_kb("ASCSJV2K3V", "product_info_query")
    try:
        return kb.retrieve(product_type)
    except Exception as e:
        print(f"Detailed error in get_product_info: {str(e)}")
        return f"Unable to access product information. Error: {str(e)}"


if __name__ == "__main__":
    print(get_technical_support("laptop maintenance"))
    print(get_product_info("laptops"))