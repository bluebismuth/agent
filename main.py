import argparse
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from prompts import system_prompt
from call_function import available_functions, call_function

MAX_ITERATIONS = 20


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("user_prompt", type=str)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Add it to your .env file, e.g. OPENROUTER_API_KEY=sk-or-..."
        )
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": args.user_prompt,
        }
    ]
    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model="mistralai/mistral-large-4-0",
            messages=messages,
            tools=available_functions,
        )
        usage = response.usage
        if usage is None:
            raise RuntimeError(
                "Response usage is None; cannot report token consumption."
            )
        if args.verbose:
            print(f"User prompt: {args.user_prompt}")
            print(f"Prompt tokens: {usage.prompt_tokens}")
            print(f"Response tokens: {usage.completion_tokens}")
        message = response.choices[0].message
        messages.append(message)
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result_message = call_function(tool_call, args.verbose)
                if not result_message["content"]:
                    raise RuntimeError(
                        f"Function call returned empty content: {result_message}"
                    )
                if args.verbose:
                    print(f"-> {result_message['content']}")
                messages.append(result_message)
        else:
            print(message.content)
            return
    print(
        f"Agent reached the maximum of {MAX_ITERATIONS} iterations without a final response."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
