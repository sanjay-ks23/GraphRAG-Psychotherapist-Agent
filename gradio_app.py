"""Gradio Chat UI"""
import gradio as gr
import httpx
import uuid
import os
from typing import Generator

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Custom CSS for ChatGPT-like Glassmorphism look
CSS = """
body { background-color: #f7f7f8; }
.gradio-container { max-width: 900px !important; margin: auto; }
#chatbot-component { 
    height: 65vh !important; 
    border: none !important; 
    background: transparent !important;
}
.message { 
    padding: 16px !important; 
    border-radius: 12px !important; 
    margin-bottom: 12px !important;
    font-family: 'Inter', sans-serif;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.message.user { 
    background-color: #ffffff !important; 
    border: 1px solid #e5e5e5;
    color: #1a1a1a;
}
.message.bot { 
    background-color: #f0fdf4 !important; /* Soft Green tint for wellness */
    border: 1px solid #dcfce7;
    color: #1a1a1a;
}
textarea {
    border-radius: 12px !important;
    border: 1px solid #e5e5e5 !important;
    background: white !important;
    padding: 12px !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
}
.suggestion-btn {
    background: white;
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 8px 12px;
    color: #666;
    font-size: 0.9em;
    cursor: pointer;
    transition: all 0.2s;
}
.suggestion-btn:hover {
    background: #f3f4f6;
    border-color: #d1d5db;
}
"""

def stream_response(message: str, history: list) -> Generator[str, None, None]:
    if not message.strip():
        yield "Please share what's on your mind."
        return
    
    try:
        with httpx.Client(timeout=120) as client:
            with client.stream("POST", f"{API_URL}/chat/stream", json={"query": message, "session_id": str(uuid.uuid4())}) as resp:
                if resp.status_code == 200:
                    full = ""
                    for chunk in resp.iter_text():
                        full += chunk
                        yield full
                else:
                    yield f"Error: {resp.status_code}"
    except httpx.ConnectError:
        yield from demo_response(message)
    except Exception as e:
        yield f"Error: {e}"


def demo_response(message: str) -> Generator[str, None, None]:
    import time
    responses = {
        "anxiety": "I hear that you are feeling anxious. Let's try to ground ourselves:\n\n**1. Breathing Exercise (4-7-8)**\n- Inhale for 4 seconds.\n- Hold for 7 seconds.\n- Exhale for 8 seconds.\n\n**2. Grounding**\n- Notice 5 things you see, 4 you can touch, 3 you hear.\n\nWould you like to talk more about what's worrying you?",
        "default": "I am here to listen without judgment.\n\nIf you are feeling overwhelmed, remember:\n1. **Breathe** - Deep breaths calm the mind.\n2. **Connect** - Talk to a someone you trust.\n3. **Professional Help** - Seeking therapy is a sign of strength.\n\nHow are you feeling right now?"
    }
    key = "anxiety" if any(x in message.lower() for x in ["anxious", "worry", "stress", "tension"]) else "default"
    text = responses[key]
    current = ""
    for char in text:
        current += char
        yield current
        time.sleep(0.008)


def upload_file(file) -> str:
    if not file:
        return "No file selected"
    try:
        with httpx.Client(timeout=60) as client:
            with open(file.name, "rb") as f:
                resp = client.post(f"{API_URL}/documents/upload", files={"file": f})
            if resp.status_code == 200:
                data = resp.json()
                return f"Uploaded: {data['filename']} ({data['chunks']} chunks)"
            return f"Error: {resp.text}"
    except Exception as e:
        return f"Error: {e}"


with gr.Blocks(title="Wellness Companion", css=CSS, theme=gr.themes.Soft(primary_hue="emerald", radius_size="lg")) as app:
    
    with gr.Column(elem_id="main-container"):
        gr.Markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="font-size: 2.5em; margin-bottom: 0.2em;">Wellness Companion</h1>
            <p style="color: #666; font-size: 1.1em;">Your safe space for mental well-being.</p>
        </div>
        """)
        
        chatbot = gr.Chatbot(
            elem_id="chatbot-component", 
            show_label=False, 
            avatar_images=(None, "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix&backgroundColor=b6e3f4"),
            layout="bubble"
        )
        
        with gr.Row(variant="panel"):
            msg = gr.Textbox(
                placeholder="How are you feeling today?", 
                scale=6, 
                show_label=False,
                autofocus=True,
                container=False
            )
            send = gr.Button("➤", variant="primary", scale=1, min_width=50)
        
        with gr.Row(variant="compact"):
            gr.Examples(
                examples=["I feel very stressed about exams.", "How do I manage anger?", "Tips for better sleep."],
                inputs=msg,
                label="Suggestions"
            )
        
        with gr.Accordion("Features & Upload", open=False):
            with gr.Row():
                file = gr.File(label="Upload Medical Reports / Journals", file_types=[".pdf", ".txt", ".md"])
                upload_status = gr.Markdown("")
        
        gr.Markdown("""
        <div style="text-align: center; margin-top: 20px; font-size: 0.8em; color: #888;">
            <p><strong>Emergency Support (India):</strong> Vandrevala Foundation: 1860-266-2345 | KIRAN: 1800-599-0019</p>
            <p>AI can make mistakes. Please verify important information.</p>
        </div>
        """)
    
    # Logic
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
    file.change(upload_file, file, upload_status)


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
