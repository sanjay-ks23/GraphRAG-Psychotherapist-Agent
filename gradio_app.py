"""
Gradio Chat Interface with Streaming

Real-time token streaming for fast perceived response time.
"""
import gradio as gr
import httpx
import uuid
import os
from typing import Generator

API_URL = os.getenv("API_URL", "http://localhost:8000")

# === CSS ===
CSS = """
.gradio-container { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important; }
.chatbot { border-radius: 16px !important; }
.message.user { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important; border-radius: 16px 16px 4px 16px !important; }
.message.bot { background: rgba(255,255,255,0.08) !important; border-radius: 16px 16px 16px 4px !important; }
"""


def stream_response(message: str, history: list) -> Generator[str, None, None]:
    """Stream response from API."""
    if not message.strip():
        yield "Please enter a message."
        return
    
    session_id = str(uuid.uuid4())
    
    try:
        with httpx.Client(timeout=120) as client:
            with client.stream(
                "POST",
                f"{API_URL}/chat/stream",
                json={"query": message, "session_id": session_id}
            ) as resp:
                if resp.status_code == 200:
                    full = ""
                    for chunk in resp.iter_text():
                        full += chunk
                        yield full
                else:
                    yield f"Error: {resp.status_code}"
    except httpx.ConnectError:
        # Demo mode fallback
        yield from demo_response(message)
    except Exception as e:
        yield f"Error: {e}"


def demo_response(message: str) -> Generator[str, None, None]:
    """Fallback demo responses."""
    import time
    
    responses = {
        "anxiety": """I understand you're dealing with anxiety. Here are some techniques:

**Breathing Exercise (4-7-8)**
1. Inhale for 4 seconds
2. Hold for 7 seconds
3. Exhale for 8 seconds

**Grounding (5-4-3-2-1)**
Notice 5 things you see, 4 you touch, 3 you hear, 2 you smell, 1 you taste.

Would you like to explore more strategies?""",
        
        "default": """Thank you for sharing. I'm here to help.

Some suggestions:
1. **Take a moment** - pause and breathe
2. **Reach out** - talk to someone you trust
3. **Professional support** - consider therapy if needed

What would you like to discuss further?"""
    }
    
    text = responses.get("anxiety" if "anxiety" in message.lower() else "default")
    current = ""
    for char in text:
        current += char
        yield current
        time.sleep(0.008)


def upload_file(file) -> str:
    """Upload document to API."""
    if not file:
        return "No file selected"
    
    try:
        with httpx.Client(timeout=60) as client:
            with open(file.name, "rb") as f:
                resp = client.post(
                    f"{API_URL}/documents/upload",
                    files={"file": f}
                )
            if resp.status_code == 200:
                data = resp.json()
                return f"✅ Uploaded: {data['filename']} ({data['chunks']} chunks)"
            return f"❌ Error: {resp.text}"
    except Exception as e:
        return f"❌ {e}"


# === Build UI ===

with gr.Blocks(title="Mental Wellness Assistant", css=CSS, theme=gr.themes.Soft(primary_hue="purple")) as app:
    gr.Markdown("""
# 🧠 Mental Wellness Support
**Powered by GraphRAG** | Streaming responses | Document upload
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, show_copy_button=True)
            
            with gr.Row():
                msg = gr.Textbox(placeholder="Share what's on your mind...", scale=4, show_label=False)
                send = gr.Button("Send", variant="primary")
            
            clear = gr.Button("Clear Chat", size="sm")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Upload Document")
            file = gr.File(label="PDF/TXT/MD", file_types=[".pdf", ".txt", ".md"])
            upload_status = gr.Markdown("*Drop files to add to knowledge base*")
            
            gr.Markdown("---")
            gr.Markdown("""
### 🆘 Crisis Support
- **988** Suicide & Crisis Lifeline
- **741741** Crisis Text Line
            """)
    
    # Events
    def respond(message, history):
        history = history + [(message, "")]
        return "", history
    
    def stream_bot(history):
        user_msg = history[-1][0]
        for response in stream_response(user_msg, history[:-1]):
            history[-1] = (user_msg, response)
            yield history
    
    msg.submit(respond, [msg, chatbot], [msg, chatbot]).then(stream_bot, chatbot, chatbot)
    send.click(respond, [msg, chatbot], [msg, chatbot]).then(stream_bot, chatbot, chatbot)
    clear.click(lambda: [], outputs=chatbot)
    file.change(upload_file, file, upload_status)
    
    gr.Examples(
        examples=[
            "How can I manage anxiety?",
            "What are good stress relief techniques?",
            "Tell me about mindfulness meditation",
        ],
        inputs=msg
    )


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
