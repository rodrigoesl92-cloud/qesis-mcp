import requests
from fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("TeleGeography-Subsea-Connector")

# Updated: Using an active community mirror for the submarine cable GeoJSON data
GEOJSON_URL = "https://raw.githubusercontent.com/lifewinning/submarine-cable-taps/master/data/submarine_cables.geojson"

@mcp.resource("geojson://subsea-cables")
def get_raw_cable_data() -> str:
    """
    Fetches the raw GeoJSON data of all submarine cables.
    """
    response = requests.get(GEOJSON_URL)
    response.raise_for_status()
    return response.text

@mcp.tool()
def fetch_cables_by_landing_point(landing_point: str) -> dict:
    """
    Parses the geojson and extracts all subsea cables connected to a specific geographical node.
    """
    response = requests.get(GEOJSON_URL)
    response.raise_for_status()
    cable_data = response.json()
    
    matched_cables = []
    
    for feature in cable_data.get("features", []):
        properties = feature.get("properties", {})
        cable_name = properties.get("name", "Unknown")
        cable_id = properties.get("id", "Unknown")
        owners = properties.get("owners", "Unknown")
        
        if landing_point.lower() in str(properties).lower():
            matched_cables.append({
                "cable_id": cable_id,
                "cable_name": cable_name,
                "owners": owners
            })
            
    return {
        "landing_point_searched": landing_point,
        "total_cables_found": len(matched_cables),
        "cables": matched_cables
    }

if __name__ == "__main__":
    mcp.run()