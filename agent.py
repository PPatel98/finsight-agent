import anthropic
import json
from tools import get_stock_price, get_news, search_sec_filing, search_web, tools

def run_agent(user_question: str, collection_id: str = None, chat_history: list = None) -> str:
    client = anthropic.Anthropic()

    # Build messages from full conversation history
    # This gives Claude context for follow-up questions
    messages = []

    if chat_history:
        for msg in chat_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

    # Add the current question at the end
    messages.append({
        "role": "user",
        "content": user_question
    })

    # Safety guard — prevents infinite loops
    max_iterations = 10
    iteration = 0

    while True:
        iteration += 1

        if iteration > max_iterations:
            return "Research could not be completed — maximum iterations reached. Please try a more specific question."

        # Send full conversation history + tool definitions to Claude
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        # Claude is done — return the final text answer
        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text

        # Claude wants to call a tool
        if response.stop_reason == "tool_use":

            # Add Claude's response to messages before running tools
            # This keeps the conversation history accurate
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            tool_results = []

            # Loop through all blocks — Claude may call multiple tools at once
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input

                    print(f"Claude is calling: {tool_name} with {tool_input}")

                    # Dispatcher — run the matching Python function
                    if tool_name == "get_stock_price":
                        result = get_stock_price(**tool_input)
                        result_str = json.dumps(result)

                    elif tool_name == "get_news":
                        result = get_news(**tool_input)
                        result_str = json.dumps(result)

                    elif tool_name == "search_sec_filing":
                        result = search_sec_filing(**tool_input)
                        result_str = result

                    elif tool_name == "search_web":
                        result = search_web(**tool_input)
                        result_str = json.dumps(result)

                    else:
                        result_str = f"Unknown tool: {tool_name}"

                    # Package result with the tool_use_id so Claude knows
                    # which result answers which tool call
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str
                    })

            # Add tool results to messages as a user message
            # Then loop again — Claude reads results and decides next step
            messages.append({
                "role": "user",
                "content": tool_results
            })