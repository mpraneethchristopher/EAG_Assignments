import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
# from google import genai
from concurrent.futures import TimeoutError
from functools import partial
import google.generativeai as genai
import time
import json
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)
# client = genai.Client(api_key=api_key)
client = genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.0-flash")
max_iterations = 7
last_response = None
iteration = 0
iteration_response = []

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout and retry logic"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        # model="gemini-2.0-flash",
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: model.generate_content(
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except Exception as e:
        if "429" in str(e):
            print("STATUS: RATE_LIMIT - API quota exceeded. Waiting before retry...")
            time.sleep(25)  # Wait for the retry delay specified in the error
            raise
        print(f"Error in LLM generation: {e}")
        raise

async def main():
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["mcp_usecase_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    if tools:
                        print(f"First tool properties: {dir(tools[0])}")
                        print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are an agent that can perform mathematical operations and create drawings in MS Paint. You have access to various tools.

Available tools:
{tools_description}

OPERATION SEQUENCE:
1. First Operation (Mathematical):
   - Perform the calculation using the appropriate math function
   - Verify the result is within expected range
   - Return FINAL_ANSWER
   - Type: ARITHMETIC_REASONING
   - Status: COMPLETED when FINAL_ANSWER is returned
   - DO NOT repeat after completion

2. Second Operation (Paint Setup):
   - Open Paint application
   - Verify Paint is running
   - Type: SPATIAL_REASONING
   - Status: COMPLETED when Paint is open
   - DO NOT repeat after completion

3. Third Operation (Drawing):
   - Draw rectangle at specified coordinates using draw_rectangle()
   - Verify rectangle is visible and properly positioned
   - Type: SPATIAL_REASONING
   - Status: COMPLETED when rectangle is drawn
   - DO NOT repeat after completion

4. Final Operation (Text):
   - Add the calculated result as text using add_text_in_paint()
   - Verify text is readable and properly positioned
   - Type: SPATIAL_REASONING
   - Status: COMPLETED when text is added
   - DO NOT repeat after completion

Each operation must be completed before moving to the next.
DO NOT repeat operations that have already been completed.
DO NOT return to previous steps unless there's an error.

VALIDATION STEPS:
1. For calculations:
   - Verify result is within expected range
   - Check for arithmetic errors
   - Cross-validate with alternative method if possible

2. For Paint operations:
   - Verify operation completed successfully
   - Check if result is visible
   - Ensure proper positioning
   - Verify contrast and readability

3. Before proceeding:
   - Confirm current step was successful
   - Verify all parameters are valid
   - Check if any adjustments are needed

ERROR HANDLING:
1. Calculation errors:
   - Retry with different method
   - Verify input parameters
   - Check for overflow/underflow

2. Paint errors:
   - Check application state
   - Verify coordinates
   - Ensure proper permissions

3. Coordinate errors:
   - Adjust coordinates
   - Verify screen resolution
   - Retry with adjusted values

4. Timeout handling:
   - Retry operation
   - Check system resources
   - Report if persistent

Respond with EXACTLY ONE of these formats:
1. For function calls (use compact JSON format with no extra whitespace):
   FUNCTION_CALL: {{"function":"function_name","parameters":{{"param1":value1,"param2":value2}}}}
   
   Example: For add(a: integer, b: integer), use:
   FUNCTION_CALL: {{"function":"add","parameters":{{"a":5,"b":3}}}}
   
   For draw_rectangle(x1: integer, y1: integer, x2: integer, y2: integer), use:
   FUNCTION_CALL: {{"function":"draw_rectangle","parameters":{{"x1":700,"y1":100,"x2":1000,"y2":500}}}}
   
   For add_text_in_paint(text: string, x1: integer, y1: integer, x2: integer, y2: integer), use:
   FUNCTION_CALL: {{"function":"add_text_in_paint","parameters":{{"text":"Final Answer: 89","x1":700,"y1":100,"x2":1000,"y2":500}}}}

2. For final answers:
   FINAL_ANSWER: [number]

3. For errors or issues:
   ERROR: [description of the issue]
   SUGGESTION: [proposed solution]

4. For completion:
   COMPLETE: [summary of completed operations]

REASONING TYPES:
1. ARITHMETIC_REASONING:
   - Used for calculations
   - Focus on numerical accuracy
   - Verify results

2. SPATIAL_REASONING:
   - Used for Paint operations
   - Focus on positioning and visibility
   - Verify visual elements

3. LOGICAL_REASONING:
   - Used for decision making
   - Focus on operation sequence
   - Verify completion criteria

STOP CONDITIONS:
1. All operations completed successfully
2. Maximum retry attempts reached
3. Critical error encountered
4. User requests termination

ITERATION RULES:
1. Each operation should be performed exactly once
2. Move to next operation only after current one is completed
3. Do not repeat completed operations
4. If an operation fails, retry once before moving to error handling
5. After all operations are completed, return COMPLETE status
6. Once an operation is marked COMPLETED, do not attempt it again
7. If all operations are completed, return COMPLETE and stop

OPERATION TRACKING:
- Keep track of completed operations
- Do not attempt operations that are already completed
- Move to next operation only when current one is fully completed
- Return COMPLETE when all operations are done

CURRENT OPERATION STATUS:
- Mathematical Operation: PENDING
- Paint Setup: PENDING
- Drawing: PENDING
- Text Addition: PENDING

NEXT STEPS:
1. First, perform the mathematical calculation
2. Then open Paint
3. Draw the rectangle
4. Add the text
5. Return COMPLETE when all steps are done

TROUBLESHOOTING GUIDE:
1. If calculation fails:
   - Verify input numbers
   - Try alternative method
   - Check for overflow

2. If Paint operations fail:
   - Verify Paint is running
   - Check coordinates
   - Ensure proper permissions

3. If text addition fails:
   - Verify rectangle exists
   - Check text position
   - Ensure proper contrast"""

                query = """Add 45 and 44, then draw a rectangle in Paint and write the result inside it"""
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                paint_steps_done = False
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        if not paint_steps_done and response_text.startswith("FINAL_ANSWER:"):
                            current_query = "Now that we have the result, let's draw it in Paint. First, open Paint."
                            paint_steps_done = True
                        else:
                            current_query = current_query + "\n\n" + " ".join(iteration_response)
                            if paint_steps_done:
                                current_query += "\nNow draw a rectangle and add the calculated result response_text as text inside it."
                            else:
                                current_query += "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break

                    if response_text.startswith("FUNCTION_CALL:"):
                        try:
                            # Extract the JSON part after FUNCTION_CALL:
                            json_str = response_text.split(":", 1)[1].strip()
                            # Parse the JSON
                            function_info = json.loads(json_str)
                            
                            func_name = function_info["function"]
                            params = function_info["parameters"]
                            
                            print(f"STATUS: PENDING - Calling function {func_name} with params {params}")
                            try:
                                # Find the matching tool to get its input schema
                                tool = next((t for t in tools if t.name == func_name), None)
                                if not tool:
                                    raise ValueError(f"Unknown tool: {func_name}")

                                # Prepare arguments according to the tool's input schema
                                arguments = {}
                                for param_name, param_info in tool.inputSchema['properties'].items():
                                    # Get the value from params, converting to correct type
                                    value = params.get(param_name)
                                    if value is not None:
                                        if param_info['type'] == 'integer':
                                            arguments[param_name] = int(value)
                                        elif param_info['type'] == 'number':
                                            arguments[param_name] = float(value)
                                        elif param_info['type'] == 'array':
                                            arguments[param_name] = eval(value)
                                        else:
                                            arguments[param_name] = value

                                print(f"STATUS: EXECUTING - MCP tool call with arguments: {arguments}")
                                result = await session.call_tool(func_name, arguments=arguments)
                                
                                # Get the full result content
                                if hasattr(result, 'content'):
                                    if isinstance(result.content[0], str):
                                        iteration_result = result.content[0]
                                    else:
                                        iteration_result = result.content[0].text
                                else:
                                    iteration_result = str(result)
                                    
                                print(f"STATUS: SUCCESS - Function {func_name} completed with result: {iteration_result}")
                                
                                iteration_response.append(
                                    f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                    f"and the function returned {iteration_result}."
                                )

                                # Store the numeric result when it's a calculation
                                if func_name in ['add', 'subtract', 'multiply', 'divide']:
                                    # Format the result as FINAL_ANSWER
                                    last_response = f"FINAL_ANSWER: [{iteration_result}]"
                                    # Share the result back to LLM for evaluation
                                    evaluation_prompt = f"""The addition of 45 and 44 has been completed. 
                                    Result: {iteration_result}
                                    Please evaluate if this result is correct and provide feedback.
                                    Expected result: 89
                                    Actual result: {iteration_result}
                                    Is the result correct? If not, what was the error?"""
                                    
                                    try:
                                        evaluation_response = await generate_with_timeout(client, evaluation_prompt)
                                        print(f"LLM Evaluation: {evaluation_response.text}")
                                        iteration_response.append(f"Evaluation of result: {evaluation_response.text}")
                                    except Exception as eval_error:
                                        print(f"Error getting evaluation: {eval_error}")
                                else:
                                    last_response = iteration_result

                                # Add delay after Paint operations
                                if func_name in ["open_paint", "draw_rectangle", "add_text_in_paint"]:
                                    time.sleep(2)

                            except Exception as e:
                                print(f"Error calling tool: {e}")
                                # If rectangle drawing fails or is repeated, try to add text directly
                                if func_name == "draw_rectangle":
                                    print("Bypassing rectangle drawing, attempting to add text directly...")
                                    try:
                                        # Extract the final answer from last_response
                                        final_answer = last_response.split("[")[1].split("]")[0] if "[" in last_response else "89"
                                        text_params = {
                                            "text": f"Final Answer: {final_answer}",
                                            "x1": 700,
                                            "y1": 100,
                                            "x2": 1000,
                                            "y2": 500
                                        }
                                        print(f"Attempting to add text with params: {text_params}")
                                        text_result = await session.call_tool("add_text_in_paint", arguments=text_params)
                                        iteration_response.append(
                                            f"In the {iteration + 1} iteration, bypassed rectangle drawing and directly added text: {text_result}"
                                        )
                                        last_response = text_result
                                        time.sleep(2)
                                        # Mark paint steps as done to prevent further rectangle attempts
                                        paint_steps_done = True
                                        # Update query to indicate completion
                                        current_query = "Text has been added successfully. Operation complete."
                                    except Exception as text_error:
                                        print(f"Error adding text: {text_error}")
                                        iteration_response.append(f"Error in iteration {iteration + 1}: {str(text_error)}")
                                else:
                                    iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                                break
                                
                        except json.JSONDecodeError as e:
                            print(f"Error parsing function call JSON: {e}")
                            iteration_response.append(f"Error in iteration {iteration + 1}: Invalid JSON format")
                            break
                        except Exception as e:
                            print(f"Error processing function call: {e}")
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Calculation Complete, Starting Paint Operations ===")
                        # Store the FINAL_ANSWER as is for Paint text
                        last_response = response_text
                        paint_steps_done = False
                        continue

                    # After drawing rectangle, update query to use full FINAL_ANSWER format
                    if paint_steps_done and func_name == "draw_rectangle":
                        current_query = f"Add the text '{last_response}' inside the rectangle"
                        continue

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
    
    
