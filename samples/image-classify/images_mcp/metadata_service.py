
from fastmcp import FastMCP
from app.utils.metadata import extract_metadata, get_profile_fields, get_all_profiles

mcp = FastMCP("Image Metadata MCP Server")

@mcp.tool
def extract_metadata_endpoint(input_dir: str, profile: str = "basic") -> list:
    """
    Extract metadata from images for downstream analysis, machine learning, search, or reporting.

    Returns structured metadata for all images in the given directory, enabling automation and integration in data pipelines, ML workflows, and analytics.

    The optional profile parameter lets you control which fields are included (e.g., use a minimal profile for LLM input limits, or a rich profile for detailed analysis). Most users can use the default.

    Call list_profiles() if you need to see or customize available profiles and their fields.
    """
    return extract_metadata(input_dir, profile)

# Canonical endpoint to list available profiles and their field descriptions
@mcp.tool
def list_profiles() -> dict:
    """
    List available metadata profiles and their fields, only useful when extract_metadata() is needed and only if you need to optimize field selection or token limits within your workflow. Most users do not need to call this directly nor beforehand.
    """
    return get_all_profiles()

if __name__ == "__main__":
    mcp.run()
