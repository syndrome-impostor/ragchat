import logging
import argparse
from pathlib import Path
import yaml
from .chat_session import ChatSession
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
import sys

logger = logging.getLogger(__name__)

class ChatCLI:
    def __init__(self, verbose=False, very_verbose=False):
        # Configure logging based on verbosity
        log_level = logging.INFO if verbose else logging.WARNING
        
        # Configure root logger to control all module logging
        logging.getLogger().setLevel(log_level)
        
        # Specifically silence the sentence-transformers and embeddings loggers unless verbose
        logging.getLogger('sentence_transformers').setLevel(log_level)
        logging.getLogger('bot.embeddings').setLevel(log_level)
        
        # Load config from package location instead of current directory
        self.config = self._load_config()
        self.session = ChatSession(self.config, verbose, very_verbose)
        
        # Setup prompt_toolkit session and keybindings
        self.prompt_session = PromptSession()
        self.kb = KeyBindings()
        self._setup_keybindings()
        
    def _load_config(self) -> dict:
        """Load configuration from config.yaml."""
        try:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return {}
    
    def _setup_keybindings(self):
        """Setup custom keybindings for the prompt."""
        
        @self.kb.add('enter')
        def _(event):
            """Handle Enter key press."""
            event.current_buffer.validate_and_handle()
            
        @self.kb.add('c-v')  # Ctrl+V
        def _(event):
            """Handle Ctrl+V for newline."""
            event.current_buffer.insert_text('\n')
            
        @self.kb.add('escape', 'enter')  # Meta/Alt+Enter
        def _(event):
            """Handle Meta/Alt+Enter for newline."""
            event.current_buffer.insert_text('\n')
    
    def _get_input(self) -> str:
        """Get multi-line input from user using prompt_toolkit."""
        try:
            # Use custom prompt with key bindings
            user_input = self.prompt_session.prompt(
                "\n> ",
                key_bindings=self.kb,
                multiline=True,
                wrap_lines=True,
                enable_suspend=True,  # Allow Ctrl+C to work
            )
            return user_input.strip()
            
        except KeyboardInterrupt:
            print("\nGoodbye!")  # Add newline and message
            raise  # Re-raise to trigger the outer handler
        except EOFError:
            return "exit"
    
    def start(self):
        """Start the interactive chat session."""
        print("Type 'exit' to quit, 'help' for commands")
        if sys.platform == "darwin":
            print("Use Ctrl+V or Option+Enter for new lines, Enter to submit")
        else:
            print("Use Ctrl+V or Alt+Enter for new lines, Enter to submit")
        
        while True:
            try:
                user_input = self._get_input()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                    
                if user_input.lower() == 'help':
                    self._show_help()
                    continue
                
                try:
                    # Get response from Claude with relevant context
                    response = self.session.get_response(user_input)
                    print("\n" + response)
                except Exception as e:
                    logger.error(f"Error getting response: {str(e)}")
                    print("\nSorry, there was an error getting a response. Please try again.")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error: {str(e)}")
                print("\nAn error occurred. Please try again.")
    
    def _show_help(self):
        """Show available commands."""
        print("\nAvailable Commands:")
        print("  help     Show this help message")
        print("  exit     Exit the program")
        print("\nInput Controls:")
        print("  Enter         Submit input")
        print("  Ctrl+V        Insert new line")
        if sys.platform == "darwin":
            print("  Option+Enter  Insert new line")
        else:
            print("  Alt+Enter     Insert new line")
        print("  Up/Down       Navigate history")
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
        if "ANTHROPIC_API_KEY" in str(e):
            logger.error(f"Configuration error: {str(e)}")
            print("\nPlease make sure you have set up your ANTHROPIC_API_KEY in the .env file")
        else:
            logger.error(f"Error: {str(e)}")
            print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\nAn error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_chat()