import logging
from typing import List, Dict
import anthropic
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from .query import Querier

logger = logging.getLogger(__name__)

class ChatSession:
    def __init__(self, config: dict, verbose: bool = False, very_verbose: bool = False):
        self.config = config
        self.verbose = verbose
        self.very_verbose = very_verbose
        
        # Load environment variables
        load_dotenv()
        
        # Setup Claude client with API key from environment
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
            
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Get model settings
        self.model = self.config['llm']['model']
        self.max_tokens = self.config['llm']['max_tokens_per_request']
        self.temperature = self.config['llm']['temperature']
        
        # Load prompts
        self.system_prompt = self.config['llm']['prompts']['system']
        self.query_prompt = self.config['llm']['prompts']['query']
        
        # Initialize document querier
        self.querier = Querier()
        
        # Chat history
        self.history = []
        self.max_history = self.config['chat'].get('max_history', 10)
        
        # Get chunking settings
        self.max_chunks = self.config['chunking'].get('max_chunks', 5)
        self.min_relevance = self.config['chunking'].get('min_relevance', 0.7)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_response(self, query: str) -> str:
        """Get response from Claude using relevant document context."""
        try:
            # Get relevant documents
            results = self.querier.search(
                query, 
                n_results=self.max_chunks,
                verbose=self.verbose  # Show all search results
            )
            
            context = ""
            if not results:
                logger.warning("No relevant documents found in the vector store")
                if self.verbose:
                    print("\nWarning: No relevant documentation found in local storage.")
            else:
                # Filter results by relevance score
                results = [r for r in results if r['relevance'] >= self.min_relevance]
                
                if not results:
                    logger.warning(f"Found results but none met the minimum relevance threshold of {self.min_relevance}")
                    if self.verbose:
                        print(f"\nWarning: Found results but none met the minimum relevance threshold of {self.min_relevance}")
                else:
                    # Build context from filtered results
                    context_parts = []
                    if self.verbose:
                        print("\nUsing chunks for context:")
                        for i, r in enumerate(results, 1):
                            print(f"  {i}. {r['url']} (relevance: {r['relevance']:.2%})")
                    
                    for r in results:
                        source_ref = f"From {r['url']}"
                        context_parts.append(f"{source_ref}:\n{r['content']}")
                    
                    context = "\n\n".join(context_parts)
            
            # Format prompt with context
            prompt = self.query_prompt.format(context=context or "No relevant documentation found.", query=query)
            
            # Get response from Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self.system_prompt,
                messages=[
                    *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg}
                      for i, msg in enumerate(self.history)],
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Update history
            self.history.extend([prompt, response.content[0].text])
            if len(self.history) > self.max_history * 2:
                self.history = self.history[-self.max_history * 2:]
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            logger.debug("Full traceback:", exc_info=True)
            raise