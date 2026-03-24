import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr
from chat_ui import rag_client

DOMAIN_CHOICES = ["auto", "frontend", "backend"]
STACK_CHOICES = ["auto", "react", "spring", "nestjs", "kotlin"]

WELCOME_MESSAGE = {
    "role": "assistant",
    "content": "안녕하세요! 개발 컨벤션 Q&A Bot입니다. 궁금한 점을 질문해주세요.",
}


def _format_bot_message(result: dict) -> str:
    if "error" in result:
        return f"오류: {result['error']}"

    answer = result.get("answer", "")
    answer_type = result.get("answer_type", "")
    doc = result.get("resolved_document") or {}
    doc_title = doc.get("title", "")

    meta_parts = []
    if answer_type:
        meta_parts.append(answer_type)
    if doc_title:
        meta_parts.append(doc_title)

    if meta_parts:
        footer = " | ".join(meta_parts)
        return f"{answer}\n\n---\n_{footer}_"
    return answer


def send_message(message: str, history: list, domain: str, stack: str):
    if not message.strip():
        return history, ""

    history = history + [{"role": "user", "content": message}]

    result = rag_client.query(message, domain, stack)
    bot_content = _format_bot_message(result)

    history = history + [{"role": "assistant", "content": bot_content}]
    return history, ""


def clear_history():
    return [WELCOME_MESSAGE]


with gr.Blocks(title="Developer Convention Q&A Bot") as demo:
    with gr.Row():
        with gr.Column(scale=1, min_width=180):
            gr.Markdown("## Settings")
            domain_dropdown = gr.Dropdown(
                choices=DOMAIN_CHOICES,
                value="auto",
                label="Domain",
            )
            stack_dropdown = gr.Dropdown(
                choices=STACK_CHOICES,
                value="auto",
                label="Stack",
            )
            clear_btn = gr.Button("초기화", variant="secondary")

        with gr.Column(scale=4):
            gr.Markdown("## Developer Convention Q&A Bot")
            chatbot = gr.Chatbot(
                value=[WELCOME_MESSAGE],
                height=500,
                show_label=False,
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="질문 입력...",
                    show_label=False,
                    scale=5,
                )
                send_btn = gr.Button("전송", variant="primary", scale=1)

    send_btn.click(
        fn=send_message,
        inputs=[msg_input, chatbot, domain_dropdown, stack_dropdown],
        outputs=[chatbot, msg_input],
    )
    msg_input.submit(
        fn=send_message,
        inputs=[msg_input, chatbot, domain_dropdown, stack_dropdown],
        outputs=[chatbot, msg_input],
    )
    clear_btn.click(fn=clear_history, outputs=[chatbot])


if __name__ == "__main__":
    demo.launch()
