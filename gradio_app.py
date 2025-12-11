"""
Gradio ChatInterface for Mental Wellness Support Agent.

A production-grade chat interface with streaming responses, safety disclaimers,
and a calming mental wellness themed UI.
"""
import gradio as gr
import asyncio
import logging
from typing import Generator, List, Tuple
import httpx

logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
TITLE = "🧠 Mental Wellness Support Agent"
DESCRIPTION = """
<div style="text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;">
    <h3 style="color: white; margin: 0;">Hybrid GraphRAG-Powered Mental Wellness Support</h3>
    <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0;">Combining semantic search with knowledge graph reasoning for grounded, empathetic responses</p>
</div>
"""

SAFETY_DISCLAIMER = """
> ⚠️ **Important Safety Notice**
> 
> This AI assistant is designed for general wellness support and is **not a substitute for professional mental health care**. 
> If you are experiencing a crisis or emergency, please contact:
> - **Emergency Services**: 911 (US) or your local emergency number
> - **Crisis Text Line**: Text HOME to 741741
> - **National Suicide Prevention Lifeline**: 988 (US)
> - **SAMHSA Helpline**: 1-800-662-4357
"""

# Custom CSS for mental wellness theme
CUSTOM_CSS = """
/* Main container styling */
.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Chat container */
.chatbot {
    border-radius: 15px !important;
    border: 1px solid #e0e0e0 !important;
}

/* Message bubbles */
.message {
    border-radius: 15px !important;
}

/* User message */
.message.user {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* Bot message */
.message.bot {
    background: #f8f9fa !important;
    border: 1px solid #e9ecef !important;
}

/* Input box */
.input-box textarea {
    border-radius: 25px !important;
    border: 2px solid #667eea !important;
}

/* Submit button */
.submit-btn {
    border-radius: 25px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* Safety banner */
.safety-banner {
    background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
    border: 1px solid #ffc107;
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 15px;
}

/* Header styling */
h1 {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
"""

# Example prompts for mental wellness
EXAMPLES = [
    ["I've been feeling anxious about work lately. Can you help me understand ways to manage this?"],
    ["What are some techniques for improving sleep quality?"],
    ["Can you explain what mindfulness is and how it might help with stress?"],
    ["I'd like to learn about healthy coping mechanisms for dealing with difficult emotions."],
    ["What's the connection between physical exercise and mental health?"],
]


async def stream_chat_response(message: str, history: List[Tuple[str, str]]) -> Generator[str, None, None]:
    """
    Stream chat responses from the backend API.
    
    Args:
        message: The user's message
        history: List of (user, assistant) message tuples
        
    Yields:
        Streamed response chunks
    """
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/chat",
                json={"query": message},
                timeout=60.0
            )
            
            if response.status_code == 200:
                # The API returns streamed text
                yield response.text
            else:
                yield f"I apologize, but I encountered an issue processing your request. Please try again. (Error: {response.status_code})"
                
    except httpx.TimeoutException:
        yield "I apologize, but the request timed out. Please try again with a shorter question."
    except httpx.ConnectError:
        yield "I'm currently unable to connect to the backend service. Please ensure the server is running and try again."
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        yield f"I apologize, but something went wrong. Please try again. If you're experiencing a crisis, please contact emergency services."


def chat_response(message: str, history: List[Tuple[str, str]]) -> str:
    """
    Synchronous wrapper for the async chat response.
    
    Args:
        message: The user's message
        history: Conversation history
        
    Returns:
        The assistant's response
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_response():
            full_response = ""
            async for chunk in stream_chat_response(message, history):
                full_response += chunk
            return full_response
        
        response = loop.run_until_complete(get_response())
        loop.close()
        return response
        
    except Exception as e:
        logger.error(f"Error in chat_response: {e}")
        return "I apologize, but I encountered an error. Please try again."


def create_gradio_app() -> gr.Blocks:
    """
    Create and configure the Gradio application.
    
    Returns:
        Configured Gradio Blocks application
    """
    with gr.Blocks(
        title=TITLE,
        css=CUSTOM_CSS,
        theme=gr.themes.Soft(
            primary_hue="purple",
            secondary_hue="blue",
            neutral_hue="slate",
        )
    ) as app:
        # Header
        gr.HTML(DESCRIPTION)
        
        # Safety disclaimer
        gr.Markdown(SAFETY_DISCLAIMER)
        
        # Chat interface
        chatbot = gr.ChatInterface(
            fn=chat_response,
            title=TITLE,
            description="Share what's on your mind. I'm here to provide supportive guidance and information.",
            examples=EXAMPLES,
            retry_btn="🔄 Retry",
            undo_btn="↩️ Undo",
            clear_btn="🗑️ Clear",
            submit_btn="Send 💬",
        )
        
        # Footer with additional resources
        gr.Markdown("""
---
### 📚 Additional Resources
- [Mental Health Resources](https://www.mentalhealth.gov/)
- [Mindfulness Practices](https://www.mindful.org/)
- [Crisis Support Services](https://988lifeline.org/)

<p style="text-align: center; color: #666; font-size: 0.9em;">
    Powered by Hybrid GraphRAG • Weaviate + Neo4j • LangGraph Pipeline
</p>
        """)
    
    return app


# Create the app instance
app = create_gradio_app()

if __name__ == "__main__":
    # Launch with production settings
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False,
    )
