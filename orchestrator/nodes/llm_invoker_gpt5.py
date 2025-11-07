"""
LLM invoker node: call GPT-5 API with streaming
"""
from __future__ import annotations

import time
from openai import OpenAI
from orchestrator.graph_dag import PipelineState
from core.config import settings
from core.utils import get_logger

logger = get_logger(__name__)
client = OpenAI(api_key=settings.OPENAI_API_KEY)


async def llm_invoker_node(state: PipelineState) -> PipelineState:
    """Invoke GPT-5 and stream response"""
    start = time.time()
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are Sahyog, an empathetic AI counselor."},
                {"role": "user", "content": state.prompt}
            ],
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            stream=False  # Non-streaming for pipeline; streaming handled in WebSocket
        )
        
        state.llm_response = response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"LLM invocation failed: {str(e)}")
        state.llm_response = "I apologize, but I'm having trouble responding right now."
        state.error = str(e)
    
    state.node_timings["llm_invocation"] = time.time() - start
    logger.info(f"LLM response generated ({len(state.llm_response)} chars)")
    
    return state


async def llm_invoke_streaming(prompt: str, callback):
    """
    Stream GPT-5 response with callback for WebSocket
    
    Args:
        prompt: Full prompt string
        callback: Async function to call with each token
    """
    try:
        stream = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are Sahyog, an empathetic AI counselor."},
                {"role": "user", "content": prompt}
            ],
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                await callback(chunk.choices[0].delta.content)
                
    except Exception as e:
        logger.error(f"Streaming failed: {str(e)}")
        await callback(f"\n[Error: {str(e)}]")
