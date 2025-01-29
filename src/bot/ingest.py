import logging
from pathlib import Path
import json
from typing import List, Dict
import nltk
from tqdm.auto import tqdm
import chromadb
from chromadb.config import Settings
from .embeddings import InstructorEmbeddingFunction
import yaml
import argparse
from datetime import datetime
from .processor import DocumentProcessor
from tqdm.contrib.logging import logging_redirect_tqdm
import shutil

logger = logging.getLogger(__name__)

class Ingester:
    def __init__(self, debug=False):
        # Reduce noise from external libraries unless in debug mode
        if not debug:
            logging.getLogger('unstructured').setLevel(logging.WARNING)
            logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
        
        # Load config
        with open(Path(__file__).parent.parent.parent / "config.yaml") as f:
            self.config = yaml.safe_load(f)
        
        # Setup paths
        project_root = Path(__file__).parent.parent.parent
        self.raw_dir = project_root / "data/raw"
        self.db_dir = project_root / "data/chromadb"
        
        # Delete existing ChromaDB directory if it exists
        if self.db_dir.exists():
            logger.info("Removing existing ChromaDB directory...")
            try:
                shutil.rmtree(self.db_dir)
                logger.info("Successfully removed existing ChromaDB directory")
            except Exception as e:
                logger.error(f"Error removing ChromaDB directory: {e}")
                raise RuntimeError("Could not clear existing ChromaDB directory")
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.processor = DocumentProcessor()
        self.embedding_function = InstructorEmbeddingFunction()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.db_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get chunking settings
        self.chunk_size = self.config.get('chunking', {}).get('chunk_size', 500)
        self.chunk_overlap = self.config.get('chunking', {}).get('chunk_overlap', 100)

    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        sentences = nltk.sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            if current_size + sentence_size > self.chunk_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    # Add overlap
                    overlap_size = 0
                    overlap_chunk = []
                    for s in reversed(current_chunk):
                        s_size = len(s.split())
                        if overlap_size + s_size > self.chunk_overlap:
                            break
                        overlap_chunk.insert(0, s)
                        overlap_size += s_size
                    current_chunk = overlap_chunk
                    current_size = overlap_size
                current_chunk.append(sentence)
                current_size += sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def ingest_documents(self):
        """Process raw documents into vector database."""
        raw_files = list(self.raw_dir.glob("*.raw"))
        if not raw_files:
            logger.error("No raw files found to process")
            return
        
        print(f"\nProcessing {len(raw_files)} documents...")
        
        # Create/get collection
        collection = self.chroma_client.get_or_create_collection(
            name="documents",
            embedding_function=self.embedding_function
        )
        
        # Use tqdm's logging handler
        with logging_redirect_tqdm():
            progress_bar = tqdm(raw_files, position=0, leave=True)
            for raw_file in progress_bar:
                try:
                    progress_bar.set_description(f"Processing {raw_file.name}")
                    logger.debug(f"Processing: {raw_file}")
                    
                    # Get metadata from corresponding .json file
                    meta_file = raw_file.with_suffix('.json')
                    if not meta_file.exists():
                        logger.warning(f"No metadata file found for {raw_file}")
                        continue
                    
                    # Read content and metadata
                    with open(raw_file, 'r', encoding='utf-8', errors='ignore') as f:
                        raw_content = f.read()
                    
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        try:
                            metadata = yaml.safe_load(f)
                        except yaml.YAMLError as e:
                            logger.error(f"Failed to parse metadata file {meta_file}: {e}")
                            continue
                    
                    # Process document
                    doc = self.processor.process_document(
                        content=raw_content.encode('utf-8'),
                        url=metadata['url'],
                        content_type=metadata.get('content_type')
                    )
                    
                    if not doc:
                        logger.warning(f"Document processor returned None for {raw_file}")
                        continue
                    
                    # Create chunks
                    chunks = self.chunk_text(doc['content'])
                    
                    # Add to database
                    for i, chunk in enumerate(chunks):
                        chunk_metadata = {
                            'url': doc['url'],
                            'type': doc['type'],
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'processed_at': datetime.now().isoformat()
                        }
                        
                        collection.add(
                            documents=[chunk],
                            metadatas=[chunk_metadata],
                            ids=[f"{doc['url']}_{i}"]
                        )
                    
                    logger.info(f"✓ Processed: {raw_file.name}")
                    
                except Exception as e:
                    logger.error(f"Error processing {raw_file}: {str(e)}")
                    logger.debug("Full traceback:", exc_info=True)
                    progress_bar.set_description(f"Error on {raw_file.name}")

def run_ingest(debug=False):
    """Entry point for ingestion."""
    print("Starting document ingestion...")
    
    # Wrap everything in the logging redirect
    with logging_redirect_tqdm():
        ingester = Ingester(debug=debug)
        ingester.ingest_documents()

if __name__ == "__main__":
    run_ingest() 