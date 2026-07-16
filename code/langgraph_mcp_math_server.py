from fastmcp import FastMCP
import math

mcp = FastMCP("math")

# --- BASIC ARITHMETIC ---

@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together. Use this for addition."""
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract the second number from the first number (a - b)."""
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together. Use this for multiplication."""
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide the first number by the second number (a / b)."""
    # CRITICAL: If an LLM divides by zero, it crashes the server. 
    # We catch it and return a string error instead.
    if b == 0:
        return "Error: Division by zero is undefined. Please do not divide by zero."
    return a / b

# --- ADVANCED OPERATIONS ---

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """Raise a base to a specific exponent (base ^ exponent). Example: power(2, 3) returns 8."""
    try:
        return base ** exponent
    except Exception as e:
        return f"Error calculating power: {str(e)}"

@mcp.tool()
def square_root(a: float) -> float:
    """Calculate the square root of a positive number."""
    # Prevent math domain errors if the LLM passes a negative number
    if a < 0:
        return "Error: Cannot calculate the square root of a negative number."
    return math.sqrt(a)

@mcp.tool()
def modulo(a: float, b: float) -> float:
    """Find the remainder of division of the first number by the second (a % b)."""
    if b == 0:
        return "Error: Modulo by zero is undefined."
    return a % b

if __name__ == "__main__":
    mcp.run(transport="stdio")