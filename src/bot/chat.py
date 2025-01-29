import logging
import argparse
from pathlib import Path
import yaml
from .chat_session import ChatSession
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatCLI:
    def __init__(self, verbose=False, very_verbose=False):
        # Load config from package location instead of current directory
        self.config = self._load_config()
        self.session = ChatSession(self.config, verbose, very_verbose)
        
    def _load_config(self) -> dict:
        """Load configuration from config.yaml."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return {}
    
    def start(self):
        """Start the interactive chat session."""
        print("\nWelcome to the Documentation Assistant")
        print("Type 'exit' to quit, 'help' for commands\n")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                    
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                # Get response from Claude with relevant context
                response = self.session.get_response(user_input)
                print("\n" + response)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {str(e)}")
    
    def _show_help(self):
        """Show available commands."""
        print("\nAvailable Commands:")
        print("  help     Show this help message")
        print("  exit     Exit the program")
        print("\nOptions:")
        print("  -v       Show source references")
        print("  -vv      Show source chunks and metadata")

def run_chat(args=None):
    """Entry point for chat functionality."""
    try:
        if args is None:
            # Handle direct script execution
            parser = argparse.ArgumentParser(description="Chat with the documentation assistant")
            parser.add_argument('-v', '--verbose', action='store_true',
                               help='Show source references')
            parser.add_argument('-vv', '--very-verbose', action='store_true',
                               help='Show source chunks and metadata')
            args = parser.parse_args()
        
        cli = ChatCLI(args.verbose, args.very_verbose)
        cli.start()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        print("\nPlease make sure you have set up your ANTHROPIC_API_KEY in the .env file")
        sys.exit(1)

if __name__ == "__main__":
    run_chat()