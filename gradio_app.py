"""Gradio Chat UI"""
import gradio as gr
import httpx
import uuid
import os
from typing import Generator

API_URL = os.getenv("API_URL", "http://localhost:8000")


def stream_response(message: str, history: list) -> Generator[str, None, None]:
    if not message.strip():
        yield "Please enter a message."
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
        "anxiety": "I understand you're dealing with anxiety. Here are some techniques:\n\n**Breathing (4-7-8)**: Inhale 4s, hold 7s, exhale 8s.\n\n**Grounding**: Notice 5 things you see, 4 you touch, 3 you hear.",
        "default": "Thank you for sharing. I'm here to help.\n\n1. Take a moment to breathe\n2. Talk to someone you trust\n3. Consider professional support if needed"
    }
    text = responses.get("anxiety" if "anxiety" in message.lower() else "default")
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


with gr.Blocks(title="Mental Wellness Assistant") as app:
    gr.Markdown("# Mental Wellness Assistant\n**GraphRAG-powered support with streaming responses**")
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500)
            with gr.Row():
                msg = gr.Textbox(placeholder="Share what's on your mind...", scale=4, show_label=False)
                send = gr.Button("Send", variant="primary")
            clear = gr.Button("Clear", size="sm")
        
        with gr.Column(scale=1):
            gr.Markdown("### Upload Document")
            file = gr.File(label="PDF/TXT/MD", file_types=[".pdf", ".txt", ".md"])
            upload_status = gr.Markdown("")
            gr.Markdown("---\n### Crisis Support\n**988** Suicide & Crisis Lifeline")
    
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
    
    gr.Examples(examples=["How can I manage anxiety?", "Tips for stress relief", "What is mindfulness?"], inputs=msg)


if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)
