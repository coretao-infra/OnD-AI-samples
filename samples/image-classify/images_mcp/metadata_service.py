
from fastmcp import FastMCP
from app.utils.metadata import extract_metadata

mcp = FastMCP("Image Metadata MCP Server")

@mcp.tool
def extract_metadata_endpoint(input_dir: str) -> list:
    """Extract metadata for all images in the given directory. Returns a list of dicts."""
    return extract_metadata(input_dir)

if __name__ == "__main__":
    mcp.run()
