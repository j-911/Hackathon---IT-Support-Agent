import sys
from agent import ITHelpdeskAgent
from ui import create_gradio_interface
from utils import colorize

def main():
    """Main function to run the IT Helpdesk application."""
    try:
        # Instantiate the agent once to be used by either interface
        helpdesk_agent = ITHelpdeskAgent()
        
        # Check for a '--web' argument to launch the Gradio interface
        if "--web" in sys.argv:
            print(colorize("Launching Gradio web interface...", "\033[36m"))
            print(colorize("Find the URL in the following lines (usually http://127.0.0.1:7860).", "\033[36m"))
            interface = create_gradio_interface(helpdesk_agent)
            interface.launch()
        else:
            # If no '--web' argument, run the original terminal interface
            helpdesk_agent.run()
            
    except Exception as e:
        print(colorize(f"\nAn unexpected error occurred: {e}", "\031m"))

if __name__ == "__main__":
    main()