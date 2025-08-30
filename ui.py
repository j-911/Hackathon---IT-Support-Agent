import gradio as gr
from utils import strip_ansi_codes

def create_gradio_interface(agent):
    """Creates and returns a Gradio web interface for the agent."""
    with gr.Blocks(theme=gr.themes.Soft(), title="IT Support Agent") as demo:
        gr.Markdown("# 🤖 IT Support Agent")
        gr.Markdown("- Describe a problem to create a ticket (e.g., 'My VPN is not working')")
        gr.Markdown("- Ask a general question (e.g., 'How do I reset my password?')")
        gr.Markdown("- Use 'status [id]' to check a ticket.")
        gr.Markdown("- Use 'close [id][resolution code]' to close a ticket with a resolution code.")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Conversation", height=500, avatar_images=("user.png", "bot.png"))
                user_input = gr.Textbox(label="Your Message", placeholder="e.g., How do I connect to the VPN? or My screen is flickering.", show_label=False)
                with gr.Row():
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear History")
            
            with gr.Column(scale=1):
                ticket_display = gr.Textbox(
                    label="🎫 Open Tickets", 
                    lines=23, 
                    interactive=False,
                    value="No tickets created yet."
                )

        def get_ticket_summary(agent_instance):
            """Generates a string summary of all tickets for display."""
            if not agent_instance.tickets:
                return "No tickets created yet."
            summary = []
            for ticket_id, ticket in sorted(agent_instance.tickets.items()):
                summary.append(f"ID: {ticket_id} | Status: {ticket.status}\nDesc: {ticket.description[:50]}...")
            return "\n\n".join(summary)

        def respond(message, chat_history):
            """Main function to handle user interaction in the Gradio UI."""
            response = agent.process_command(message)
            response_clean = strip_ansi_codes(response)
            chat_history.append((message, response_clean))
            ticket_summary = get_ticket_summary(agent)
            return "", chat_history, ticket_summary

        def clear_history():
            """Clears the conversation history and resets the UI."""
            agent.process_command("clear")
            return [], get_ticket_summary(agent), "Conversation cleared."

        # Event listeners
        user_input.submit(respond, [user_input, chatbot], [user_input, chatbot, ticket_display])
        submit_btn.click(respond, [user_input, chatbot], [user_input, chatbot, ticket_display])
        clear_btn.click(clear_history, [], [chatbot, ticket_display, user_input])

    return demo