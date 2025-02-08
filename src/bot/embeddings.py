from typing import List
from sentence_transformers import SentenceTransformer
from chromadb.utils import embedding_functions
import torch
import logging
import yaml
from pathlib import Path
from tqdm.auto import tqdm

logger = logging.getLogger(__name__)

class InstructorEmbeddingFunction(embedding_functions.EmbeddingFunction):
    """Custom embedding function using Instructor model through sentence-transformers."""
    
    def __init__(self):
        # Load config
        config_path = Path(__file__).parent.parent.parent / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Get device type from config
        device_type = config.get('device', {}).get('type', 'cpu').lower()
        
        # Determine the device
        if device_type == 'rocm' and torch.cuda.is_available():
            self.device = "cuda"
            tqdm.write("INFO:bot.embeddings:Using ROCm/CUDA device for embeddings")
        elif device_type == 'mps' and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            self.device = "mps"
            tqdm.write("INFO:bot.embeddings:Using Apple Silicon (MPS) for embeddings")
        elif device_type == 'cuda' and torch.cuda.is_available():
            self.device = "cuda"
            tqdm.write("INFO:bot.embeddings:Using CUDA device for embeddings")
        else:
            if device_type != 'cpu':
                tqdm.write(f"WARNING:bot.embeddings:Requested device type '{device_type}' not available, falling back to CPU")
            self.device = "cpu"
            tqdm.write("INFO:bot.embeddings:Using CPU for embeddings")
            
        # Use sentence-transformers version instead of INSTRUCTOR directly
        self.model = SentenceTransformer('hkunlp/instructor-xl')
        self.model.to(self.device)
        
        # Instruction for document embeddings
        self.instruction = "Represent this document for retrieval of relevant information about OAuth and SAML security:"

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
            
        # Prepare input with instruction
        texts_with_instruction = [f"{self.instruction} {text}" for text in texts]
        
        # Generate embeddings
        embeddings = self.model.encode(texts_with_instruction)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query text."""
        if not text:
            return []
            
        # Use __call__ to ensure consistent embedding generation
        result = self.__call__([text])
        return result[0]  # Return first (and only) embedding 