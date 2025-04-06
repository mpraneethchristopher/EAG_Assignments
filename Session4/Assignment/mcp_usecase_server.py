# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics

# Global variable to store Paint application instance
paint_app = None

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.3)  # Reduced wait time
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.3)
        
        # Click on the Rectangle tool (adjusted coordinates)
        paint_window.click_input(coords=(450, 80))  # Updated coordinates for rectangle tool
        time.sleep(0.3)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Calculate the center of the canvas
        canvas_rect = canvas.rectangle()
        center_x = (canvas_rect.left + canvas_rect.right) // 2
        center_y = (canvas_rect.top + canvas_rect.bottom) // 2
        
        # Draw rectangle with proper mouse movement
        # Start from the top-left corner
        start_x = center_x - (x2 - x1) // 2
        start_y = center_y - (y2 - y1) // 2
        
        # Press mouse at starting position
        # canvas.click_input(coords=(x1, y1))
        canvas.press_mouse_input(coords=(start_x, start_y))
        time.sleep(0.1)
        
        # Move to bottom-right corner
        end_x = start_x + (x2 - x1)
        end_y = start_y + (y2 - y1)
        
        # Move mouse diagonally to draw the rectangle
        canvas.move_mouse_input(coords=(end_x, end_y))
        time.sleep(0.1)
        
        # Release mouse to complete the rectangle
        canvas.release_mouse_input(coords=(end_x, end_y))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({start_x},{start_y}) to ({end_x},{end_y})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Click on the Text tool in the Tools group (coordinates for text tool)
        paint_window.click_input(coords=(290, 80))  # Adjusted coordinates for text tool
        time.sleep(0.5)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Calculate center coordinates based on the rectangle position
        # Using the coordinates from the output (583,320) to (783,520)
        center_x = 600  # Middle of rectangle x coordinates (583 + 783) / 2
        center_y = 300  # Middle of rectangle y coordinates (320 + 520) / 2
        
        # Click where to start typing (center of rectangle)
        canvas.click_input(coords=(center_x, center_y))
        time.sleep(0.5)
        
        # Type the text
        paint_window.type_keys(text)
        time.sleep(0.5)
        
        # Click outside to finish text input
        canvas.click_input(coords=(center_x + 100, center_y + 100))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text '{text}' added successfully at center coordinates ({center_x}, {center_y})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error adding text: {str(e)}"
                )
            ]
        }

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
