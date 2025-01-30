import logging
import os
from pathlib import Path
from typing import Dict
import nltk
from bs4 import BeautifulSoup
from unstructured.partition.text import partition_text
from unstructured.partition.html import partition_html
from unstructured.documents.elements import Title, NarrativeText

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process raw documents into clean text."""
    
    def __init__(self):
        # Set NLTK data path to venv directory
        venv_dir = os.environ.get('VIRTUAL_ENV')
        if venv_dir:
            nltk_data_dir = os.path.join(venv_dir, 'nltk_data')
            nltk.data.path.insert(0, nltk_data_dir)
        
        # Ensure NLTK data is available
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', download_dir=nltk_data_dir if venv_dir else None)
    
    def process_document(self, content: bytes, url: str, content_type: str = None) -> Dict:
        """Process document content into clean text."""
        try:
            # Determine document type
            doc_type = self._get_doc_type(url, content_type)
            
            # Convert bytes to text based on type
            if doc_type == 'html':
                text = content.decode('utf-8', errors='ignore')
                elements = partition_html(text=text)
            else:
                text = content.decode('utf-8', errors='ignore')
                elements = partition_text(text=text)
            
            # Extract and clean text
            processed_text = self._process_elements(elements)
            
            if not processed_text.strip():
                raise ValueError("No text could be extracted")
            
            return {
                'url': url,
                'type': doc_type,
                'content': processed_text
            }
            
        except Exception as e:
            logger.error(f"Error processing document {url}: {e}")
            return None
    
    def _get_doc_type(self, url: str, content_type: str = None) -> str:
        """Determine document type from URL and content-type."""
        if content_type:
            if 'html' in content_type:
                return 'html'
            elif 'text' in content_type:
                return 'text'
            elif 'pdf' in content_type:
                return 'pdf'
        
        # Fallback to URL extension
        url_lower = url.lower()
        if url_lower.endswith(('.html', '.htm')):
            return 'html'
        elif url_lower.endswith('.txt'):
            return 'text'
        elif url_lower.endswith('.md'):
            return 'markdown'
        elif url_lower.endswith('.pdf'):
            return 'pdf'
        
        return 'text'  # Default to text
    
    def _process_elements(self, elements) -> str:
        """Convert document elements to clean text."""
        processed = []
        
        for element in elements:
            if isinstance(element, (Title, NarrativeText)):
                text = str(element).strip()
                if text:
                    processed.append(text)
        
        return '\n\n'.join(processed) 