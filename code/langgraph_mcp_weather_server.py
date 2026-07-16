from fastmcp import FastMCP
import httpx

mcp = FastMCP("Weather")

@mcp.tool()
async def get_weather(location: str) -> str:
    """
    Get the current weather conditions for a specific city or location.
    Use this tool whenever the user asks about the weather, temperature, or wind.
    """
    # wttr.in is a free, no-auth API. 
    # We use ?format=j1 to get clean JSON data instead of ASCII art.
    url = f"https://wttr.in/{location}?format=j1"
    
    try:
        # Use async client so we don't block the FastMCP server
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status() # Raise an error if the city doesn't exist
            data = response.json()

            # Parse the specific fields we want from the JSON response
            current = data['current_condition'][0]
            
            desc = current['weatherDesc'][0]['value']
            temp_c = current['temp_C']
            feels_like_c = current['FeelsLikeC']
            wind_kph = current['windspeedKmph']
            humidity = current['humidity']

            return (
                f"Weather in {location.capitalize()}:\n"
                f"Condition: {desc}\n"
                f"Temperature: {temp_c}°C (Feels like {feels_like_c}°C)\n"
                f"Wind: {wind_kph} kph\n"
                f"Humidity: {humidity}%"
            )
            
    except httpx.HTTPStatusError:
        return f"Error: Could not find weather data for '{location}'. Please check the spelling."
    except httpx.RequestError as e:
        return f"Error: Network issue occurred while fetching weather - {str(e)}"
    except (KeyError, IndexError):
        return f"Error: Unexpected data format received from weather service."

if __name__ == "__main__":
    # Note: You specified streamable-http here, which is perfect for this
    mcp.run(transport="streamable-http")