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