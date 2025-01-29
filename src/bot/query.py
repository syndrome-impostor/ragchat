import logging
import argparse
from pathlib import Path
import chromadb
from chromadb.config import Settings
from .embeddings import InstructorEmbeddingFunction
import yaml
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

class Querier:
    def __init__(self):
        # Load config
        with open(Path(__file__).parent.parent.parent / "config.yaml") as f:
            self.config = yaml.safe_load(f)
        
        # Setup paths
        self.db_dir = Path(__file__).parent.parent.parent / "data/chromadb"
        
        # Initialize components
        self.embedding_function = InstructorEmbeddingFunction()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get collection
        self.collection = self.chroma_client.get_collection(
            name="documents",
            embedding_function=self.embedding_function
        )

    def show_stats(self) -> None:
        """Display database statistics and information."""
        try:
            results = self.collection.get()
            urls = {meta['url'] for meta in results['metadatas']}
            chunks = len(results['metadatas'])
            
            # Get date ranges
            dates = [
                datetime.fromisoformat(meta['processed_at'])
                for meta in results['metadatas']
                if 'processed_at' in meta
            ]
            
            print("\n=== Document Database Statistics ===")
            print(f"Total Documents: {len(urls)}")
            print(f"Total Chunks: {chunks}")
            print(f"Average Chunks per Document: {chunks/len(urls):.1f}")
            
            if dates:
                print(f"\nDate Range:")
                print(f"  First Added: {min(dates).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Last Added: {max(dates).strftime('%Y-%m-%d %H:%M:%S')}")
            
            print("\nDocument List:")
            for url in sorted(urls):
                doc_chunks = sum(1 for meta in results['metadatas'] if meta['url'] == url)
                print(f"• {url} ({doc_chunks} chunks)")
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            print("No documents found or error accessing database.")

    def list_documents(self) -> None:
        """List all documents in the database."""
        try:
            results = self.collection.get()
            urls = {meta['url'] for meta in results['metadatas']}
            
            print(f"\nFound {len(urls)} unique documents:")
            for url in sorted(urls):
                print(f"• {url}")
                
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            print("No documents found or error accessing database.")

    def search(self, query: str, n_results: int = 5, verbose: bool = False) -> List[Dict]:
        """Search the document collection."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if not results['documents'][0]:
                print("No results found.")
                return []
            
            # Process and display results
            formatted_results = []
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )):
                result = {
                    'rank': i + 1,
                    'url': meta['url'],
                    'chunk_index': meta['chunk_index'],
                    'total_chunks': meta['total_chunks'],
                    'relevance': 1 - dist,  # Convert distance to similarity score
                    'content': doc
                }
                formatted_results.append(result)
                
                # Print result
                print(f"\n{'-'*80}")
                print(f"Result {i+1} (Relevance: {result['relevance']:.2%})")
                print(f"Source: {result['url']}")
                if verbose:
                    print(f"Chunk: {result['chunk_index'] + 1} of {result['total_chunks']}")
                    print(f"\nContent:\n{result['content']}")
                else:
                    print(f"Content: {result['content'][:200]}...")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            print("Error performing search. Please check if the database exists and is not empty.")
            return []

def run_query(args=None):
    """Entry point for query functionality."""
    if args is None:
        # Handle direct script execution
        parser = argparse.ArgumentParser(description="Query the document database")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-l', '--list', action='store_true', help='List all documents')
        group.add_argument('query', nargs='?', help='Search query')
        parser.add_argument('-n', '--num-results', type=int, default=5, help='Number of results to show')
        parser.add_argument('-v', '--verbose', action='store_true', help='Show full result details')
        args = parser.parse_args()
    
    querier = Querier()
    
    if args.list:
        querier.list_documents()
    elif hasattr(args, 'query') and args.query:
        querier.search(args.query, args.num_results, args.verbose)
    else:
        querier.show_stats()

if __name__ == "__main__":
    run_query() 