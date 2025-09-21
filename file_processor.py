"""
File processor for handling PDF and LaTeX files.
Extracts text content and prepares it for embedding generation.
"""

import os
import io
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# PDF processing
try:
    import PyPDF2
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PDF libraries not available. Install PyPDF2 and pypdf for PDF support.")

# LaTeX processing
try:
    import latex
    LATEX_AVAILABLE = True
except ImportError:
    LATEX_AVAILABLE = False
    logging.warning("LaTeX library not available. Install python-latex for LaTeX support.")

logger = logging.getLogger(__name__)


class FileProcessor:
    """Process various file types and extract text content."""
    
    def __init__(self):
        self.supported_extensions = {'.txt', '.pdf', '.tex', '.latex'}
        if PDF_AVAILABLE:
            self.supported_extensions.add('.pdf')
        if LATEX_AVAILABLE:
            self.supported_extensions.add('.tex')
            self.supported_extensions.add('.latex')
    
    def is_supported(self, filename: str) -> bool:
        """Check if file type is supported."""
        ext = Path(filename).suffix.lower()
        return ext in self.supported_extensions
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        if not PDF_AVAILABLE:
            raise ImportError("PDF libraries not available. Install PyPDF2 and pypdf.")
        
        text = ""
        try:
            # Try with pypdf first (more modern)
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.warning(f"pypdf failed, trying PyPDF2: {e}")
            try:
                # Fallback to PyPDF2
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                raise Exception(f"Failed to extract text from PDF: {e2}")
        
        return text.strip()
    
    def extract_text_from_latex(self, file_path: str) -> str:
        """Extract text from LaTeX file."""
        if not LATEX_AVAILABLE:
            raise ImportError("LaTeX library not available. Install python-latex.")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Basic LaTeX text extraction (remove commands, keep content)
            import re
            
            # Remove LaTeX commands but keep the content
            # Remove \command{content} but keep content
            text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', content)
            
            # Remove standalone commands
            text = re.sub(r'\\[a-zA-Z]+', '', text)
            
            # Remove comments
            text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
            
            # Remove multiple whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove common LaTeX environments that don't contain readable text
            text = re.sub(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', '', text, flags=re.DOTALL)
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Failed to extract text from LaTeX: {e}")
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from plain text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            raise Exception(f"Failed to read text file: {e}")
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process a file and extract text content.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            Dictionary with extracted text and metadata
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        filename = os.path.basename(file_path)
        file_ext = Path(filename).suffix.lower()
        
        if not self.is_supported(filename):
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Extract text based on file type
        if file_ext == '.pdf':
            text = self.extract_text_from_pdf(file_path)
        elif file_ext in ['.tex', '.latex']:
            text = self.extract_text_from_latex(file_path)
        elif file_ext == '.txt':
            text = self.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        if not text.strip():
            raise ValueError("No text content extracted from file")
        
        # Generate title from filename
        title = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
        
        return {
            'filename': filename,
            'title': title,
            'text': text,
            'file_type': file_ext,
            'file_size': os.path.getsize(file_path),
            'word_count': len(text.split())
        }
    
    def process_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Process an uploaded file from memory.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Dictionary with extracted text and metadata
        """
        file_ext = Path(filename).suffix.lower()
        
        if not self.is_supported(filename):
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        # Extract text based on file type
        if file_ext == '.pdf':
            if not PDF_AVAILABLE:
                raise ImportError("PDF libraries not available. Install PyPDF2 and pypdf.")
            
            text = ""
            try:
                # Try with pypdf first
                pdf_reader = pypdf.PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            except Exception as e:
                logger.warning(f"pypdf failed, trying PyPDF2: {e}")
                try:
                    # Fallback to PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                except Exception as e2:
                    raise Exception(f"Failed to extract text from PDF: {e2}")
            
        elif file_ext in ['.tex', '.latex']:
            if not LATEX_AVAILABLE:
                raise ImportError("LaTeX library not available. Install python-latex.")
            
            try:
                content = file_content.decode('utf-8')
                
                # Basic LaTeX text extraction
                import re
                
                # Remove LaTeX commands but keep the content
                text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', content)
                text = re.sub(r'\\[a-zA-Z]+', '', text)
                text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'\\begin\{[^}]+\}.*?\\end\{[^}]+\}', '', text, flags=re.DOTALL)
                
            except Exception as e:
                raise Exception(f"Failed to extract text from LaTeX: {e}")
            
        elif file_ext == '.txt':
            try:
                text = file_content.decode('utf-8')
            except Exception as e:
                raise Exception(f"Failed to decode text file: {e}")
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")
        
        if not text.strip():
            raise ValueError("No text content extracted from file")
        
        # Generate title from filename
        title = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
        
        return {
            'filename': filename,
            'title': title,
            'text': text,
            'file_type': file_ext,
            'file_size': len(file_content),
            'word_count': len(text.split())
        }


# Global file processor instance
file_processor = FileProcessor()


if __name__ == "__main__":
    # Test the file processor
    processor = FileProcessor()
    
    print("Supported file types:", processor.supported_extensions)
    
    # Test with a sample file if available
    test_files = [
        "data/machine_learning_basics.txt",
        "data/artificial_intelligence_applications.txt"
    ]
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                result = processor.process_file(file_path)
                print(f"\nProcessed {file_path}:")
                print(f"  Title: {result['title']}")
                print(f"  Word count: {result['word_count']}")
                print(f"  Text preview: {result['text'][:200]}...")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
