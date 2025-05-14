# import gradio as gr
# from opendeepsearch.agents import get_ollama_response

# CONTEXT = "The user wants to perform a calculation and search for information."

# async def fetch_response_async(message, history):

#     history = history or []
#     history.append((message, None))
#     try:
#         response = get_ollama_response(message, context=CONTEXT)
#     except Exception as e:
#         response = f"An error occurred while processing your request: {e}"
#     history[-1] = (message, response)
#     return history, history


# def respond(message, history):
#     import asyncio
#     return asyncio.run(fetch_response_async(message, history))


# with gr.Blocks() as demo:
#     gr.Markdown("## 🤖 Gradio Chatbot with ReAct Agent")
#     chatbot = gr.Chatbot()
#     state = gr.State([])
#     user_input = gr.Textbox(placeholder="Type your message...", show_label=False)
#     user_input.submit(respond, [user_input, state], [chatbot, state])

#     submit_btn = gr.Button("Send")
#     submit_btn.click(respond, [user_input, state], [chatbot, state])

# demo.launch()
