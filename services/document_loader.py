import requests
import pdfplumber
import docx
import tempfile
import os
import mimetypes
import magic  # You might need to install this
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def detect_file_type(file_path: str, url: str) -> str:
    """Detect file type using multiple methods"""
    
    # Method 1: Check URL extension
    if url.lower().endswith('.pdf'):
        return 'pdf'
    elif url.lower().endswith(('.docx', '.doc')):
        return 'docx'
    
    # Method 2: Check file extension
    _, ext = os.path.splitext(file_path)
    if ext.lower() == '.pdf':
        return 'pdf'
    elif ext.lower() in ['.docx', '.doc']:
        return 'docx'
    
    # Method 3: Read file signature (magic bytes)
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            
            # PDF signature
            if header.startswith(b'%PDF'):
                return 'pdf'
            
            # DOCX signature (ZIP-based)
            if header.startswith(b'PK'):
                return 'docx'
                
            # DOC signature 
            if header.startswith(b'\xd0\xcf\x11\xe0'):
                return 'doc'
                
    except Exception as e:
        logger.warning(f"Could not read file signature: {e}")
    
    # Method 4: Use python-magic if available
    try:
        import magic
        mime_type = magic.from_file(file_path, mime=True)
        if 'pdf' in mime_type.lower():
            return 'pdf'
        elif 'word' in mime_type.lower() or 'officedocument' in mime_type.lower():
            return 'docx'
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"Magic detection failed: {e}")
    
    # Default fallback
    return 'pdf'

def download_file(url: str) -> tuple[str, str]:
    """Download file and return path and detected type"""
    try:
        logger.info(f"Downloading file from: {url}")
        
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Create temp file without extension first
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(response.content)
            temp_path = tmp.name
        
        # Detect file type
        file_type = detect_file_type(temp_path, url)
        
        # Rename with correct extension
        if file_type == 'pdf':
            final_path = temp_path + '.pdf'
        else:
            final_path = temp_path + '.docx'
        
        os.rename(temp_path, final_path)
        
        logger.info(f"Downloaded {len(response.content)} bytes, detected as {file_type}")
        return final_path, file_type
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise

def extract_pdf_text(file_path: str) -> str:
    """Extract text from PDF with better error handling"""
    try:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            logger.info(f"Processing PDF with {len(pdf.pages)} pages")
            for i, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                    else:
                        logger.warning(f"No text found on page {i+1}")
                except Exception as e:
                    logger.warning(f"Error extracting page {i+1}: {e}")
                    continue
        
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
            
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
        
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise

def extract_docx_text(file_path: str) -> str:
    """Extract text from DOCX with better error handling"""
    try:
        logger.info(f"Processing DOCX file: {file_path}")
        
        # Check if file exists and has content
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError("File is empty")
        
        logger.info(f"File size: {file_size} bytes")
        
        # Try to open as DOCX
        try:
            doc = docx.Document(file_path)
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            
            if not paragraphs:
                raise ValueError("No text content found in DOCX")
            
            text = "\n".join(paragraphs)
            logger.info(f"Extracted {len(text)} characters from DOCX")
            return text
            
        except docx.opc.exceptions.PackageNotFoundError:
            logger.warning("File is not a valid DOCX, trying as PDF...")
            # Try to process as PDF instead
            return extract_pdf_text(file_path)
            
    except Exception as e:
        logger.error(f"Error extracting DOCX text: {e}")
        raise

def extract_text_fallback(file_path: str) -> str:
    """Fallback text extraction using different methods"""
    logger.info("Attempting fallback text extraction...")
    
    try:
        # Try reading as plain text
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            if len(text.strip()) > 100:  # Reasonable text content
                return text
    except:
        pass
    
    try:
        # Try reading with different encoding
        with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
            text = f.read()
            if len(text.strip()) > 100:
                return text
    except:
        pass
    
    raise ValueError("Could not extract text using any method")

async def load_document(url: str) -> str:
    """Main document loading function with comprehensive error handling"""
    file_path = None
    
    try:
        # Download file and detect type
        file_path, file_type = download_file(url)
        
        # Extract text based on detected type
        if file_type == 'pdf':
            try:
                return extract_pdf_text(file_path)
            except Exception as e:
                logger.warning(f"PDF extraction failed, trying fallback: {e}")
                return extract_text_fallback(file_path)
                
        elif file_type in ['docx', 'doc']:
            try:
                return extract_docx_text(file_path)
            except Exception as e:
                logger.warning(f"DOCX extraction failed, trying as PDF: {e}")
                try:
                    return extract_pdf_text(file_path)
                except Exception as e2:
                    logger.warning(f"PDF fallback failed, trying text fallback: {e2}")
                    return extract_text_fallback(file_path)
        else:
            # Unknown type, try both
            try:
                return extract_pdf_text(file_path)
            except:
                try:
                    return extract_docx_text(file_path)
                except:
                    return extract_text_fallback(file_path)
                    
    except Exception as e:
        logger.error(f"Document loading failed: {e}")
        raise ValueError(f"Failed to load document from {url}: {str(e)}")
        
    finally:
        # Clean up temp file
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temp file {file_path}: {e}")