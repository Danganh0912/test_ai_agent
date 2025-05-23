import gradio as gr
from search_agent.react_agent import ReActAgent
from search_agent.codeact_agent import CodeActAgent



react_agent = ReActAgent(model_name="qwen2.5:14b-instruct-q8_0", temperature=0.3)
codeact_agent = CodeActAgent(model_name="gemini-2.0-flash", verbose=True)


def route_message(agent_name, message, chat_history):
    if agent_name == 'ReAct':
        response = react_agent.run(message)
    else:
        response = codeact_agent.run(message)
    chat_history = chat_history or []
    chat_history.append((message, response))
    return chat_history, chat_history


with gr.Blocks() as demo:
    gr.Markdown("# Chatbot with Agent")

    with gr.Row():
        agent_selector = gr.Dropdown(
            choices=['ReAct', 'CodeAct'],
            value='ReAct',
            label='Select Agent'
        )
    chatbot = gr.Chatbot(label="Agent Chat")
    state = gr.State([])

    with gr.Row():
        user_input = gr.Textbox(
            placeholder="Type your message here...",
            label="Your Message"
        )
        send_btn = gr.Button("Send")

    
    send_btn.click(
        fn=route_message,
        inputs=[agent_selector, user_input, state],
        outputs=[chatbot, state]
    )

if __name__ == "__main__":
    demo.launch()

