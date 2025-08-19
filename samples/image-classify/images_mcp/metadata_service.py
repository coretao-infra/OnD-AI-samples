
from fastmcp import FastMCP
from app.utils.metadata import extract_metadata, get_profile_fields, get_all_profiles

mcp = FastMCP("Image Metadata MCP Server")

@mcp.tool
def extract_metadata_endpoint(input_dir: str, profile: str = "basic") -> list:
    """
    Generate structured metadata from images in a directory to support downstream tasks such as normalization, unbiased categorization, search, or reporting.

    This tool does not directly normalize images or categorize them, but provides the metadata needed to enable those actions in your workflows or applications.

    Use this tool if you want to:
    - Prepare your images for unbiased categorization or analysis by first extracting their metadata
    - Enable normalization, comparison, or bias reduction by supplying consistent metadata for all images
    - Automate metadata extraction for integration in data pipelines, ML workflows, or analytics

    The optional profile parameter lets you control which fields are included (e.g., use a minimal profile for LLM input limits, or a rich profile for detailed analysis). Most users can use the default.

    Call list_profiles() if you need to see or customize available profiles and their fields.
    """
    return extract_metadata(input_dir, profile)

# Canonical endpoint to list available profiles and their field descriptions
@mcp.tool
def list_profiles() -> dict:
    """
    List available metadata profiles and their fields.

    This tool does not perform normalization or categorization, but helps you understand and select which metadata fields will be generated for your images. This can support downstream tasks such as unbiased categorization, normalization, or analytics.

    Most users do not need to call this directly unless you want to see or change the metadata fields for your workflow.
    """
    return get_all_profiles()

if __name__ == "__main__":
    mcp.run()
