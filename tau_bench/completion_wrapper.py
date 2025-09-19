import os
from typing import List, Dict, Any, Optional
from litellm import completion as litellm_completion


def hosted_vllm_completion(
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.0,
    tools: Optional[List[Dict[str, Any]]] = None,
    **kwargs
):
    """Custom completion function for hosted VLLM using OpenAI client"""
    from openai import OpenAI

    # Get environment variables
    base_url = os.getenv("VLLM_BASE_URL")
    api_key = os.getenv("VLLM_API_KEY", "empty")

    if base_url is None:
        raise ValueError("VLLM_BASE_URL environment variable is not set")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Prepare the completion call
    completion_kwargs = {
        "model": model,
        "messages": messages,
        "temperature": max(temperature, 1e-5),  # Ensure temperature is not 0
    }

    if tools:
        completion_kwargs["tools"] = tools

    # Make the call
    response = client.chat.completions.create(**completion_kwargs)

    # Create a mock LiteLLM response structure
    class MockResponse:
        def __init__(self, openai_response):
            self.choices = openai_response.choices
            self._hidden_params = {"response_cost": 0.0}  # Mock cost

    return MockResponse(response)


def completion(
    model: str,
    messages: List[Dict[str, Any]],
    custom_llm_provider: Optional[str] = None,
    temperature: float = 0.0,
    tools: Optional[List[Dict[str, Any]]] = None,
    **kwargs
):
    """Wrapper around LiteLLM completion that handles hosted_vllm specially"""
    if custom_llm_provider == "hosted_vllm":
        return hosted_vllm_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            tools=tools,
            **kwargs
        )
    else:
        return litellm_completion(
            model=model,
            messages=messages,
            custom_llm_provider=custom_llm_provider,
            temperature=temperature,
            tools=tools,
            **kwargs
        )