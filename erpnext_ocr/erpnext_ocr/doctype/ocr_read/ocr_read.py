# Copyright (c) 2025, John Vincent Fiel and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import json
import os
import mimetypes
from erpnext_ocr.erpnext_ocr.doctype.ai_integration_settings.ai_integration_settings import process_image_with_ai

#Alternative to "File Upload Disconnected. Please try again."

@frappe.whitelist()
def check_ocr_dependencies():
    """Check if file processing dependencies are installed"""
    missing_deps = []
    optional_deps = []
    
    # Core OCR dependencies
    try:
        import pytesseract
    except ImportError:
        missing_deps.append("pytesseract")
    
    try:
        from PIL import Image
    except ImportError:
        missing_deps.append("Pillow")
    
    # PDF processing
    try:
        import PyPDF2
    except ImportError:
        try:
            import pypdf
        except ImportError:
            optional_deps.append("PyPDF2 or pypdf (for PDF files)")
    
    # DOCX processing
    try:
        from docx import Document
    except ImportError:
        optional_deps.append("python-docx (for DOCX files)")
    
    if missing_deps:
        return {
            "status": "missing",
            "missing_dependencies": missing_deps,
            "optional_dependencies": optional_deps,
            "message": "Missing core dependencies: {}. Install with: pip install {}".format(
                ", ".join(missing_deps), " ".join(missing_deps)
            )
        }
    elif optional_deps:
        return {
            "status": "partial",
            "missing_dependencies": [],
            "optional_dependencies": optional_deps,
            "message": "Core dependencies installed. Optional: {}".format(", ".join(optional_deps))
        }
    else:
        return {
            "status": "ok",
            "message": "All file processing dependencies are installed"
        }

#erpnext_ocr.erpnext_ocr.doctype.ocr_read.ocr_read.force_attach_file
@frappe.whitelist()
def force_attach_file():
    filename = "Picture_010.tif"
    name = "a2cbc0186c"
    force_attach_file_doc(filename,name)

@frappe.whitelist()
def force_attach_file_doc(filename,name):
    # file = "/private/files/"

    file_url = "/private/files/" + filename
    # file_url = "/files/" + filename

    attachment_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": filename,
        # "file_url": path,
        "file_url": file_url,
        "attached_to_name": name,
        "attached_to_doctype": "OCR Read",
        "old_parent": "Home/Attachments",
        "folder": "Home/Attachments",
        "is_private": 1
        # "is_private": 0
    })
    attachment_doc.insert()

    frappe.db.sql("""UPDATE `tabOCR Read` SET file_to_read=%s WHERE name=%s""", (file_url, name))


class OCRRead(Document):
    def validate(self):
        """Validate document before saving"""
        if not self.title and self.file_to_read:
            # Auto-generate title from filename
            filename = os.path.basename(self.file_to_read)
            self.title = os.path.splitext(filename)[0]
            
        if self.file_to_read:
            self.detect_file_type()
            if hasattr(self, 'file_preview') and not self.file_preview:
                self.set_file_preview()
    
    def detect_file_type(self):
        """Detect and set file type based on file extension"""
        if self.file_to_read:
            filename = os.path.basename(self.file_to_read)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Map file extensions to types
            type_mapping = {
                '.jpg': 'Image (JPEG)',
                '.jpeg': 'Image (JPEG)', 
                '.png': 'Image (PNG)',
                '.tiff': 'Image (TIFF)',
                '.tif': 'Image (TIFF)',
                '.bmp': 'Image (BMP)',
                '.gif': 'Image (GIF)',
                '.pdf': 'PDF Document',
                '.docx': 'Word Document',
                '.doc': 'Word Document',
                '.csv': 'CSV File',
                '.txt': 'Text File',
                '.rtf': 'Rich Text File'
            }
            
            if hasattr(self, 'file_type'):
                self.file_type = type_mapping.get(file_ext, f'Unknown ({file_ext})')
    
    def set_file_preview(self):
        """Set file preview HTML based on file type"""
        if not self.file_to_read:
            return
            
        filename = os.path.basename(self.file_to_read)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Image files - show preview
        if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
            preview_html = f"""
            <div style="text-align: center; margin: 10px 0;">
                <img src="{self.file_to_read}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; border-radius: 4px;" />
                <p style="margin-top: 5px; font-size: 12px; color: #666;">
                    File: {filename}
                </p>
            </div>
            """
        # Other files - show file info
        else:
            file_icon = self.get_file_icon(file_ext)
            preview_html = f"""
            <div style="text-align: center; margin: 10px 0; padding: 20px; border: 1px solid #ddd; border-radius: 4px;">
                <div style="font-size: 48px; margin-bottom: 10px;">{file_icon}</div>
                <p style="margin: 5px 0; font-weight: bold;">{filename}</p>
                <p style="margin: 5px 0; font-size: 12px; color: #666;">
                    Type: {getattr(self, 'file_type', 'Unknown')}
                </p>
                <a href="{self.file_to_read}" target="_blank" style="color: #007bff; text-decoration: none;">
                    📥 Download File
                </a>
            </div>
            """
        
        if hasattr(self, 'file_preview'):
            self.file_preview = preview_html
    
    def get_file_icon(self, file_ext):
        """Get appropriate icon for file type"""
        icons = {
            '.pdf': '📄',
            '.docx': '📝',
            '.doc': '📝', 
            '.csv': '📊',
            '.txt': '📄',
            '.rtf': '📄'
        }
        return icons.get(file_ext, '📎')
    
    @frappe.whitelist()
    def get_ocr_status(self):
        """Get OCR processing status and dependencies"""
        return check_ocr_dependencies()
    
    @frappe.whitelist()
    def read_image(self):
        """Enhanced text extraction with better error handling and progress tracking"""
        if not self.file_to_read:
            frappe.throw(_("No file selected for processing"), title=_("File Required"))

        try:
            # Validate file path
            fullpath = frappe.get_site_path() + self.file_to_read
            if not os.path.exists(fullpath):
                frappe.throw(_("File not found: {0}").format(self.file_to_read))
            
            filename = os.path.basename(self.file_to_read)
            file_ext = os.path.splitext(filename)[1].lower()
            
            frappe.publish_realtime(
                "ocr_progress", 
                {"message": f"Processing {file_ext.upper()} file: {filename}", "progress": 10},
                user=frappe.session.user
            )
            
            text = ""
            processing_method = ""
            
            # Handle different file types with progress updates
            if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "Running OCR on image...", "progress": 30},
                    user=frappe.session.user
                )
                text = self._extract_text_from_image(fullpath)
                processing_method = "Tesseract OCR"
                
            elif file_ext == '.pdf':
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "Extracting text from PDF...", "progress": 30},
                    user=frappe.session.user
                )
                text = self._extract_text_from_pdf(fullpath)
                processing_method = "PDF Text Extraction"
                
            elif file_ext in ['.docx', '.doc']:
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "Extracting text from Word document...", "progress": 30},
                    user=frappe.session.user
                )
                text = self._extract_text_from_docx(fullpath)
                processing_method = "DOCX Parser"
                
            elif file_ext == '.csv':
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "Parsing CSV file...", "progress": 30},
                    user=frappe.session.user
                )
                text = self._extract_text_from_csv(fullpath)
                processing_method = "CSV Parser"
                
            elif file_ext in ['.txt', '.rtf']:
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "Reading text file...", "progress": 30},
                    user=frappe.session.user
                )
                text = self._extract_text_from_text(fullpath)
                processing_method = "Text Reader"
                
            else:
                frappe.throw(_("Unsupported file type: {0}. Supported types: JPG, PNG, PDF, DOCX, CSV, TXT").format(file_ext))
            
            frappe.publish_realtime(
                "ocr_progress", 
                {"message": "Processing extracted text...", "progress": 80},
                user=frappe.session.user
            )
            
            if text:
                text = text.strip()
                # Store result in the document
                self.read_result = text
                
                # Auto-suggest document type based on extracted text
                suggested_type = self._quick_classify_text(text)
                if suggested_type and hasattr(self, 'detected_document_type'):
                    self.detected_document_type = suggested_type["document_type"]
                    self.confidence_score = suggested_type["confidence"]
                    self.suggested_doctype = suggested_type["suggested_doctype"]
                
                self.save()
                
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "Text extraction completed!", "progress": 100},
                    user=frappe.session.user
                )
                
                result = {
                    "status": "success", 
                    "text": text,
                    "method": processing_method,
                    "word_count": len(text.split()),
                    "char_count": len(text)
                }
                
                if suggested_type:
                    result["suggested_classification"] = suggested_type
                
                return result
            else:
                frappe.publish_realtime(
                    "ocr_progress", 
                    {"message": "No text found in file", "progress": 100},
                    user=frappe.session.user
                )
                frappe.msgprint(_("No text could be extracted from the file"))
                return {"status": "warning", "text": "", "method": processing_method}
                
        except Exception as e:
            frappe.publish_realtime(
                "ocr_progress", 
                {"message": f"Error: {str(e)}", "progress": 100, "error": True},
                user=frappe.session.user
            )
            frappe.throw(
                _("Error processing file: {0}").format(str(e)),
                title=_("File Processing Error")
            )
    
    def _extract_text_from_image(self, filepath):
        """Extract text from image using Tesseract OCR with enhanced error handling"""
        try:
            from PIL import Image
            import pytesseract
        except ImportError:
            frappe.throw(
                _("Required OCR dependencies are not installed. Please install them using: pip install pytesseract Pillow"),
                title=_("Missing Dependencies")
            )
        
        try:
            # Check if Tesseract is installed
            try:
                pytesseract.get_tesseract_version()
            except Exception:
                frappe.throw(
                    _("Tesseract OCR is not installed or not in PATH. Please install Tesseract OCR engine."),
                    title=_("Tesseract Not Found")
                )
            
            # Open and validate image
            try:
                im = Image.open(filepath)
                # Convert to RGB if necessary
                if im.mode != 'RGB':
                    im = im.convert('RGB')
            except Exception as e:
                frappe.throw(_("Cannot open image file: {0}").format(str(e)))
            
            # Configure Tesseract with timeout and better settings
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,!?@#$%^&*()_+-=[]{}|;:\'\"<>/\\ '
            
            # Extract text with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("OCR processing timed out")
            
            # Set timeout for OCR processing (30 seconds)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            try:
                text = pytesseract.image_to_string(im, lang='eng', config=custom_config)
                signal.alarm(0)  # Cancel timeout
                return text
            except TimeoutError:
                signal.alarm(0)
                frappe.throw(_("OCR processing timed out. The image might be too complex or large."))
            except Exception as e:
                signal.alarm(0)
                # Fallback: try with simpler config
                try:
                    text = pytesseract.image_to_string(im, lang='eng')
                    return text
                except Exception:
                    frappe.throw(_("OCR processing failed: {0}").format(str(e)))
                    
        except Exception as e:
            if "timeout" in str(e).lower():
                frappe.throw(_("OCR processing is taking too long. Please try with a smaller or clearer image."))
            else:
                frappe.throw(_("Image OCR failed: {0}").format(str(e)))
    
    def _extract_text_from_pdf(self, filepath):
        """Extract text from PDF file"""
        try:
            import PyPDF2
        except ImportError:
            try:
                import pypdf
                PyPDF2 = pypdf
            except ImportError:
                frappe.throw(
                    _("PDF processing requires PyPDF2 or pypdf. Install with: pip install PyPDF2"),
                    title=_("Missing Dependencies")
                )
        
        text = ""
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_text_from_docx(self, filepath):
        """Extract text from DOCX file"""
        try:
            from docx import Document
        except ImportError:
            frappe.throw(
                _("DOCX processing requires python-docx. Install with: pip install python-docx"),
                title=_("Missing Dependencies")
            )
        
        doc = Document(filepath)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    
    def _extract_text_from_csv(self, filepath):
        """Extract text from CSV file"""
        import csv
        
        text = ""
        with open(filepath, 'r', encoding='utf-8', newline='') as file:
            # Try to detect delimiter
            sample = file.read(1024)
            file.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.reader(file, delimiter=delimiter)
            for row_num, row in enumerate(reader):
                if row_num == 0:
                    text += "Headers: " + " | ".join(row) + "\n\n"
                else:
                    text += f"Row {row_num}: " + " | ".join(row) + "\n"
        return text
    
    def _extract_text_from_text(self, filepath):
        """Extract text from text file"""
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    
    @frappe.whitelist()
    def read_with_ai(self):
        """Read file using AI"""
        if not self.file_to_read:
            frappe.throw(_("No file selected for AI processing"), title=_("File Required"))
        
        try:
            filename = os.path.basename(self.file_to_read)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # For image files, use AI vision processing
            if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
                result = process_image_with_ai(self.file_to_read, "extraction")
            else:
                # For non-image files, extract text first then process with AI
                text_content = self._get_file_content_for_ai(file_ext)
                result = self._process_text_with_ai(text_content, "extraction")
            
            if result["status"] == "success":
                # Try to parse as JSON
                try:
                    ai_data = json.loads(result["content"])
                    self.ai_result = json.dumps(ai_data, indent=2)
                except json.JSONDecodeError:
                    # If not JSON, store as text
                    self.ai_result = json.dumps({"extracted_text": result["content"]}, indent=2)
                
                self.save()
                return {
                    "status": "success", 
                    "data": self.ai_result,
                    "usage": result.get("usage", {}),
                    "model": result.get("model", "")
                }
            else:
                frappe.throw(_("AI processing failed: {0}").format(result.get("message", "Unknown error")))
                
        except Exception as e:
            frappe.throw(_("Error processing file with AI: {0}").format(str(e)))
    
    def _get_file_content_for_ai(self, file_ext):
        """Get file content for AI processing"""
        fullpath = frappe.get_site_path() + self.file_to_read
        
        if file_ext == '.pdf':
            return self._extract_text_from_pdf(fullpath)
        elif file_ext in ['.docx', '.doc']:
            return self._extract_text_from_docx(fullpath)
        elif file_ext == '.csv':
            return self._extract_text_from_csv(fullpath)
        elif file_ext in ['.txt', '.rtf']:
            return self._extract_text_from_text(fullpath)
        else:
            frappe.throw(_("Unsupported file type for AI processing: {0}").format(file_ext))
    
    def _process_text_with_ai(self, text_content, prompt_type):
        """Process text content with AI"""
        from erpnext_ocr.erpnext_ocr.doctype.ai_integration_settings.ai_integration_settings import get_active_ai_settings
        
        settings = get_active_ai_settings()
        if not settings:
            frappe.throw(_("No active AI integration settings found"))
        
        # Get appropriate prompt
        if prompt_type == "classification":
            prompt = settings.classification_prompt
        elif prompt_type == "extraction":
            prompt = settings.extraction_prompt
        else:
            prompt = settings.ocr_prompt
        
        # Combine prompt with text content
        full_prompt = f"{prompt}\n\nDocument Content:\n{text_content[:4000]}"  # Limit content length
        
        # Use text-based AI processing
        if settings.ai_provider == "OpenAI":
            return self._process_text_with_openai(settings, full_prompt)
        elif settings.ai_provider == "Perplexity AI":
            return self._process_text_with_perplexity(settings, full_prompt)
        elif settings.ai_provider == "OpenRouter":
            return self._process_text_with_openrouter(settings, full_prompt)
        else:
            frappe.throw(_("AI provider {0} not supported for text processing").format(settings.ai_provider))
    
    def _process_text_with_openai(self, settings, prompt):
        """Process text with OpenAI"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {settings.get_password('api_key')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.model_name or "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.max_tokens or 4000,
            "temperature": settings.temperature or 0.1
        }
        
        url = settings.base_url or "https://api.openai.com/v1/chat/completions"
        
        response = requests.post(url, headers=headers, json=data, timeout=settings.timeout or 30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "")
            }
        else:
            frappe.throw(_("OpenAI API Error: {0}").format(response.text))
    
    def _process_text_with_perplexity(self, settings, prompt):
        """Process text with Perplexity AI"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {settings.get_password('api_key')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.model_name or "sonar-pro",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.max_tokens or 4000,
            "temperature": settings.temperature or 0.1
        }
        
        url = settings.base_url or "https://api.perplexity.ai/chat/completions"
        
        response = requests.post(url, headers=headers, json=data, timeout=settings.timeout or 30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "")
            }
        else:
            frappe.throw(_("Perplexity API Error: {0}").format(response.text))
    
    def _process_text_with_openrouter(self, settings, prompt):
        """Process text with OpenRouter"""
        import requests
        
        headers = {
            "Authorization": f"Bearer {settings.get_password('api_key')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": settings.model_name or "google/gemini-2.5-flash-image-preview:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": settings.max_tokens or 4000,
            "temperature": settings.temperature or 0.1
        }
        
        url = settings.base_url or "https://openrouter.ai/api/v1/chat/completions"
        
        response = requests.post(url, headers=headers, json=data, timeout=settings.timeout or 30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "")
            }
        else:
            frappe.throw(_("OpenRouter API Error: {0}").format(response.text))
    
    @frappe.whitelist()
    def classify_document(self):
        """Classify document type using AI"""
        if not self.file_to_read:
            frappe.throw(_("No file selected for classification"), title=_("File Required"))
        
        try:
            filename = os.path.basename(self.file_to_read)
            file_ext = os.path.splitext(filename)[1].lower()
            
            # For image files, use AI vision processing
            if file_ext in ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif']:
                result = process_image_with_ai(self.file_to_read, "classification")
            else:
                # For non-image files, extract text first then classify with AI
                text_content = self._get_file_content_for_ai(file_ext)
                result = self._process_text_with_ai(text_content, "classification")
            
            if result["status"] == "success":
                try:
                    classification_data = json.loads(result["content"])
                    
                    self.detected_document_type = classification_data.get("document_type", "Unknown")
                    self.confidence_score = classification_data.get("confidence", 0.0)
                    self.suggested_doctype = classification_data.get("suggested_doctype", "")
                    
                    self.save()
                    
                    return {
                        "status": "success",
                        "classification": classification_data,
                        "usage": result.get("usage", {}),
                        "model": result.get("model", "")
                    }
                except json.JSONDecodeError:
                    # If response is not JSON, parse the text response intelligently
                    content = result["content"]
                    classification_data = self._parse_classification_text(content)
                    
                    self.detected_document_type = classification_data.get("document_type", "Unknown")
                    self.confidence_score = classification_data.get("confidence", 0.8)
                    self.suggested_doctype = classification_data.get("suggested_doctype", "")
                    
                    self.save()
                    
                    return {
                        "status": "success",
                        "classification": classification_data,
                        "usage": result.get("usage", {}),
                        "model": result.get("model", ""),
                        "raw_response": content
                    }
            else:
                frappe.throw(_("Document classification failed: {0}").format(result.get("message", "Unknown error")))
                
        except Exception as e:
            frappe.throw(_("Error classifying document: {0}").format(str(e)))
    
    @frappe.whitelist()
    def classify_ocr_result(self):
        """Classify document type using AI based on OCR extracted text"""
        if not self.read_result:
            frappe.throw(_("No OCR result available for classification. Please extract text first."), title=_("OCR Result Required"))
        
        try:
            # Use the extracted OCR text for classification
            result = self._process_text_with_ai(self.read_result, "classification")
            
            if result["status"] == "success":
                try:
                    classification_data = json.loads(result["content"])
                    
                    self.detected_document_type = classification_data.get("document_type", "Unknown")
                    self.confidence_score = classification_data.get("confidence", 0.0)
                    self.suggested_doctype = classification_data.get("suggested_doctype", "")
                    
                    self.save()
                    
                    return {
                        "status": "success",
                        "classification": classification_data,
                        "usage": result.get("usage", {}),
                        "model": result.get("model", ""),
                        "source": "OCR Text"
                    }
                except json.JSONDecodeError:
                    # If response is not JSON, parse the text response intelligently
                    content = result["content"]
                    classification_data = self._parse_classification_text(content)
                    
                    self.detected_document_type = classification_data.get("document_type", "Unknown")
                    self.confidence_score = classification_data.get("confidence", 0.8)
                    self.suggested_doctype = classification_data.get("suggested_doctype", "")
                    
                    self.save()
                    
                    return {
                        "status": "success",
                        "classification": classification_data,
                        "usage": result.get("usage", {}),
                        "model": result.get("model", ""),
                        "raw_response": content,
                        "source": "OCR Text"
                    }
            else:
                frappe.throw(_("OCR result classification failed: {0}").format(result.get("message", "Unknown error")))
                
        except Exception as e:
            frappe.throw(_("Error classifying OCR result: {0}").format(str(e)))
    
    @frappe.whitelist()
    def compare_classifications(self):
        """Compare classification results from original document vs OCR text"""
        if not self.file_to_read:
            frappe.throw(_("No file selected"), title=_("File Required"))
        
        results = {
            "original_document": None,
            "ocr_result": None,
            "comparison": {}
        }
        
        try:
            # Classify original document
            try:
                original_result = self.classify_document()
                results["original_document"] = original_result
            except Exception as e:
                results["original_document"] = {"status": "error", "message": str(e)}
            
            # Classify OCR result if available
            if self.read_result:
                try:
                    ocr_result = self.classify_ocr_result()
                    results["ocr_result"] = ocr_result
                except Exception as e:
                    results["ocr_result"] = {"status": "error", "message": str(e)}
            else:
                results["ocr_result"] = {"status": "error", "message": "No OCR result available"}
            
            # Compare results
            if (results["original_document"] and results["original_document"].get("status") == "success" and
                results["ocr_result"] and results["ocr_result"].get("status") == "success"):
                
                orig_type = results["original_document"]["classification"].get("document_type")
                ocr_type = results["ocr_result"]["classification"].get("document_type")
                orig_confidence = results["original_document"]["classification"].get("confidence", 0)
                ocr_confidence = results["ocr_result"]["classification"].get("confidence", 0)
                
                results["comparison"] = {
                    "match": orig_type == ocr_type,
                    "original_type": orig_type,
                    "ocr_type": ocr_type,
                    "original_confidence": orig_confidence,
                    "ocr_confidence": ocr_confidence,
                    "recommended_source": "original" if orig_confidence > ocr_confidence else "ocr"
                }
            
            return results
            
        except Exception as e:
            frappe.throw(_("Error comparing classifications: {0}").format(str(e)))
    
    def _parse_classification_text(self, content):
        """Parse classification information from text response"""
        import re
        
        # Common ERPNext doctypes mapping
        doctype_mapping = {
            "purchase order": "Purchase Order",
            "sales order": "Sales Order", 
            "sales invoice": "Sales Invoice",
            "purchase invoice": "Purchase Invoice",
            "quotation": "Quotation",
            "delivery note": "Delivery Note",
            "purchase receipt": "Purchase Receipt",
            "payment entry": "Payment Entry",
            "journal entry": "Journal Entry",
            "expense claim": "Expense Claim",
            "timesheet": "Timesheet",
            "job card": "Job Card",
            "work order": "Work Order",
            "material request": "Material Request",
            "stock entry": "Stock Entry",
            "customer": "Customer",
            "supplier": "Supplier",
            "item": "Item",
            "lead": "Lead",
            "opportunity": "Opportunity"
        }
        
        content_lower = content.lower()
        
        # Try to extract from structured response patterns
        detected_doctype = None
        suggested_doctype = None
        confidence = 0.5
        reasoning = ""
        
        # Look for explicit doctype pattern like "Purchase Order (PO) doctype"
        doctype_pattern = r'(\w+\s*\w*)\s*(?:\([\w\s]*\))?\s*doctype'
        matches = re.findall(doctype_pattern, content, re.IGNORECASE)
        if matches:
            for match in matches:
                match_clean = match.strip().lower()
                for key, value in doctype_mapping.items():
                    if key in match_clean or match_clean in key:
                        detected_doctype = value
                        suggested_doctype = value
                        confidence = 0.95
                        break
                if detected_doctype:
                    break
        
        # Look for "This data is linked with the **DocType**" pattern
        linked_pattern = r'linked with.*?\*\*(.*?)\*\*'
        linked_matches = re.findall(linked_pattern, content, re.IGNORECASE)
        if linked_matches and not detected_doctype:
            for match in linked_matches:
                match_clean = match.strip().lower()
                for key, value in doctype_mapping.items():
                    if key in match_clean:
                        detected_doctype = value
                        suggested_doctype = value
                        confidence = 0.9
                        break
                if detected_doctype:
                    break
        
        # Look for explicit doctype mentions in the content
        if not detected_doctype:
            for key, value in doctype_mapping.items():
                if key in content_lower:
                    detected_doctype = value
                    suggested_doctype = value
                    confidence = 0.85
                    break
        
        # Look for specific field patterns if no explicit doctype found
        if not detected_doctype:
            # Purchase Order patterns
            if any(term in content_lower for term in ["po_no", "purchase order number", "supplier details", "job work"]):
                detected_doctype = "Purchase Order"
                suggested_doctype = "Purchase Order"
                confidence = 0.8
            
            # Sales Order patterns  
            elif any(term in content_lower for term in ["so_no", "sales order", "customer order", "order confirmation"]):
                detected_doctype = "Sales Order"
                suggested_doctype = "Sales Order"
                confidence = 0.8
            
            # Invoice patterns
            elif any(term in content_lower for term in ["invoice", "bill", "payment due", "invoice number"]):
                if any(term in content_lower for term in ["purchase", "vendor", "supplier"]):
                    detected_doctype = "Purchase Invoice"
                    suggested_doctype = "Purchase Invoice"
                else:
                    detected_doctype = "Sales Invoice" 
                    suggested_doctype = "Sales Invoice"
                confidence = 0.75
            
            # Quotation patterns
            elif any(term in content_lower for term in ["quotation", "quote", "proposal", "estimate"]):
                detected_doctype = "Quotation"
                suggested_doctype = "Quotation"
                confidence = 0.75
            
            # Default fallback
            else:
                detected_doctype = "Document"
                suggested_doctype = ""
                confidence = 0.3
        
        # Extract key fields mentioned in the content
        key_fields = []
        field_patterns = {
            "po_no": ["po_no", "purchase order number", "po number"],
            "customer": ["customer", "client"],
            "supplier": ["supplier", "vendor", "supplier details"],
            "items": ["items", "products", "line items", "item details"],
            "total": ["total", "amount", "grand total"],
            "date": ["date", "order date", "required by date"],
            "taxes": ["tax", "gst", "vat", "hsn"],
            "terms": ["terms", "conditions", "payment terms"],
            "shipping": ["shipping", "delivery", "shipping details"],
            "company": ["company", "company details"]
        }
        
        for field, patterns in field_patterns.items():
            if any(pattern in content_lower for pattern in patterns):
                key_fields.append(field)
        
        # Extract reasoning from content
        reasoning_patterns = [
            r'key reasons?:?\s*(.*?)(?:\n\n|\Z)',
            r'reasons?:?\s*(.*?)(?:\n\n|\Z)', 
            r'because:?\s*(.*?)(?:\n\n|\Z)',
            r'this.*?because\s*(.*?)(?:\n\n|\Z)'
        ]
        
        for pattern in reasoning_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                reasoning = match.group(1).strip()[:200]  # Limit reasoning length
                break
        
        if not reasoning:
            reasoning = content[:200] + "..." if len(content) > 200 else content
        
        return {
            "document_type": detected_doctype,
            "confidence": confidence,
            "suggested_doctype": suggested_doctype,
            "key_fields": key_fields,
            "reasoning": reasoning,
            "analysis": content[:500] + "..." if len(content) > 500 else content
        }
    
    def _quick_classify_text(self, text):
        """Quick classification of extracted text for auto-suggestion"""
        if not text or len(text.strip()) < 10:
            return None
        
        text_lower = text.lower()
        
        # Quick pattern matching for common document types
        patterns = {
            "Purchase Order": {
                "keywords": ["purchase order", "po number", "po no", "vendor", "supplier", "order date"],
                "confidence": 0.7
            },
            "Sales Invoice": {
                "keywords": ["invoice", "bill to", "customer", "invoice number", "due date", "payment"],
                "confidence": 0.7
            },
            "Purchase Invoice": {
                "keywords": ["invoice", "vendor", "supplier", "bill from", "payment due"],
                "confidence": 0.7
            },
            "Quotation": {
                "keywords": ["quotation", "quote", "proposal", "estimate", "valid until"],
                "confidence": 0.6
            },
            "Delivery Note": {
                "keywords": ["delivery", "shipped", "dispatch", "consignment", "delivery note"],
                "confidence": 0.6
            },
            "Sales Order": {
                "keywords": ["sales order", "order confirmation", "customer order", "so number"],
                "confidence": 0.7
            }
        }
        
        best_match = None
        highest_score = 0
        
        for doc_type, pattern in patterns.items():
            score = 0
            matched_keywords = []
            
            for keyword in pattern["keywords"]:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Calculate confidence based on matches
            match_ratio = score / len(pattern["keywords"])
            confidence = match_ratio * pattern["confidence"]
            
            if confidence > highest_score and confidence > 0.3:
                highest_score = confidence
                best_match = {
                    "document_type": doc_type,
                    "suggested_doctype": doc_type,
                    "confidence": round(confidence, 2),
                    "matched_keywords": matched_keywords,
                    "match_count": score
                }
        
        return best_match
    
    @frappe.whitelist()
    def proceed_with_doctype(self, target_doctype=None):
        """Route to new document with OCR/AI data pre-filled"""
        # Use detected doctype if no target specified
        if not target_doctype:
            target_doctype = self.suggested_doctype or self.detected_document_type
        
        if not target_doctype:
            frappe.throw(_("No document type detected. Please run classification first."))
        
        # Validate doctype exists and is valid
        if not frappe.db.exists("DocType", target_doctype):
            frappe.throw(_("DocType '{0}' does not exist").format(target_doctype))
        
        # Check if doctype is creatable (not single, not table, not disabled)
        doctype_meta = frappe.get_meta(target_doctype)
        if doctype_meta.issingle or doctype_meta.istable:
            frappe.throw(_("Cannot create document of type '{0}' - it's a single or table doctype").format(target_doctype))
        
        try:
            # Prepare the data to be passed to the new document
            ocr_data = self._prepare_ocr_data_for_routing(target_doctype)
            
            # Create route with OCR data
            route_name = target_doctype.lower().replace(' ', '-')
            
            return {
                "status": "success",
                "action": "route_to_new_doc",
                "doctype": target_doctype,
                "route": f"/app/{route_name}/new",
                "ocr_data": ocr_data,
                "message": _("Routing to new {0} with OCR data").format(target_doctype),
                "confidence": self.confidence_score or 0,
                "source_ocr": self.name,
                "has_ai_data": bool(self.ai_result),
                "has_ocr_data": bool(self.read_result)
            }
                
        except Exception as e:
            frappe.log_error(f"Error in proceed_with_doctype: {str(e)}")
            frappe.throw(_("Error preparing document data: {0}").format(str(e)))
    
    def _prepare_ocr_data_for_routing(self, target_doctype):
        """Prepare OCR/AI data for routing to new document"""
        # Get extracted data
        ai_data = {}
        ocr_text = self.read_result or ""
        
        # Parse AI result if available
        if self.ai_result:
            try:
                ai_data = json.loads(self.ai_result)
            except json.JSONDecodeError:
                ai_data = {"raw_ai_result": self.ai_result}
        
        # Create temporary document to get field mappings (don't save)
        temp_doc = frappe.new_doc(target_doctype)
        
        # Apply smart field mapping to get the mapped data
        mapped_fields = self._apply_smart_mapping(temp_doc, ai_data, ocr_text, target_doctype)
        
        # Prepare the data structure for the frontend
        prepared_data = {
            "source_ocr_doc": self.name,
            "confidence": self.confidence_score or 0,
            "detected_type": self.detected_document_type,
            "mapped_fields": {},
            "items_data": [],
            "raw_ocr_text": ocr_text,
            "ai_data": ai_data
        }
        
        # Extract field values from temp document
        for field in temp_doc.meta.fields:
            if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Button", "Tab Break"]:
                field_value = getattr(temp_doc, field.fieldname, None)
                if field_value is not None and field_value != "":
                    prepared_data["mapped_fields"][field.fieldname] = {
                        "value": field_value,
                        "label": field.label or field.fieldname,
                        "fieldtype": field.fieldtype,
                        "mapped": field.fieldname in mapped_fields
                    }
        
        # Extract items data if available
        if hasattr(temp_doc, 'items') and temp_doc.items:
            for item in temp_doc.items:
                item_data = {}
                for field in item.meta.fields:
                    if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Button"]:
                        value = getattr(item, field.fieldname, None)
                        if value is not None and value != "":
                            item_data[field.fieldname] = value
                if item_data:
                    prepared_data["items_data"].append(item_data)
        
        return prepared_data
    
    def _smart_field_mapping(self, doc, ai_data, target_doctype):
        """Intelligent field mapping based on doctype and available data"""
        mapped_fields = {}
        
        # Common field mappings for different doctypes
        field_mappings = {
            "Purchase Order": {
                "supplier": ["supplier_name", "vendor", "supplier"],
                "supplier_name": ["supplier_name", "vendor_name", "supplier"],
                "transaction_date": ["date", "order_date", "po_date"],
                "schedule_date": ["required_by_date", "delivery_date", "due_date"],
                "po_no": ["po_no", "po_number", "purchase_order_number"],
                "total": ["grand_total", "total", "amount"],
                "remarks": ["description", "notes", "remarks"]
            },
            "Sales Order": {
                "customer": ["customer_name", "customer", "client"],
                "customer_name": ["customer_name", "client_name"],
                "transaction_date": ["date", "order_date", "so_date"],
                "delivery_date": ["delivery_date", "required_by_date"],
                "po_no": ["customer_po", "po_no", "reference"],
                "total": ["grand_total", "total", "amount"]
            },
            "Sales Invoice": {
                "customer": ["customer_name", "customer", "client"],
                "customer_name": ["customer_name", "client_name"],
                "posting_date": ["date", "invoice_date"],
                "due_date": ["due_date", "payment_due"],
                "invoice_no": ["invoice_no", "invoice_number"],
                "total": ["grand_total", "total", "amount"]
            },
            "Purchase Invoice": {
                "supplier": ["supplier_name", "vendor", "supplier"],
                "supplier_name": ["supplier_name", "vendor_name"],
                "posting_date": ["date", "invoice_date", "bill_date"],
                "due_date": ["due_date", "payment_due"],
                "bill_no": ["invoice_no", "bill_no", "invoice_number"],
                "total": ["grand_total", "total", "amount"]
            },
            "Quotation": {
                "party_name": ["customer_name", "client", "party"],
                "transaction_date": ["date", "quotation_date"],
                "valid_till": ["valid_until", "expiry_date"],
                "total": ["grand_total", "total", "amount"]
            }
        }
        
        # Get mapping for current doctype
        doctype_mapping = field_mappings.get(target_doctype, {})
        
        # Apply mappings
        for doc_field, possible_ai_fields in doctype_mapping.items():
            if hasattr(doc, doc_field):
                for ai_field in possible_ai_fields:
                    if ai_field in ai_data and ai_data[ai_field]:
                        try:
                            # Handle different data types
                            value = ai_data[ai_field]
                            
                            # Date field handling
                            if 'date' in doc_field.lower() and isinstance(value, str):
                                try:
                                    from dateutil import parser
                                    parsed_date = parser.parse(value)
                                    value = parsed_date.date()
                                except:
                                    pass  # Keep original value if parsing fails
                            
                            # Numeric field handling
                            elif doc_field in ['total', 'grand_total', 'amount'] and isinstance(value, str):
                                try:
                                    # Remove currency symbols and commas
                                    clean_value = ''.join(c for c in value if c.isdigit() or c == '.')
                                    value = float(clean_value) if clean_value else 0
                                except:
                                    value = 0
                            
                            setattr(doc, doc_field, value)
                            mapped_fields[doc_field] = value
                            break  # Use first matching field
                        except Exception:
                            continue  # Skip if setting field fails
        
        # Handle items if present in AI data
        if "items" in ai_data and isinstance(ai_data["items"], list):
            if hasattr(doc, 'items') and target_doctype in ["Purchase Order", "Sales Order", "Sales Invoice", "Purchase Invoice", "Quotation"]:
                try:
                    for item_data in ai_data["items"][:5]:  # Limit to 5 items
                        if isinstance(item_data, dict):
                            item_row = doc.append('items', {})
                            
                            # Map item fields
                            item_mappings = {
                                "item_name": ["name", "description", "item_name", "product"],
                                "qty": ["quantity", "qty", "amount_qty"],
                                "rate": ["rate", "price", "unit_price"],
                                "amount": ["amount", "total", "line_total"]
                            }
                            
                            for item_field, possible_fields in item_mappings.items():
                                if hasattr(item_row, item_field):
                                    for field in possible_fields:
                                        if field in item_data and item_data[field]:
                                            try:
                                                value = item_data[field]
                                                if item_field in ['qty', 'rate', 'amount']:
                                                    value = float(str(value).replace(',', '')) if value else 0
                                                setattr(item_row, item_field, value)
                                                break
                                            except Exception:
                                                continue
                            
                            # Set default values if not mapped
                            if not item_row.qty:
                                item_row.qty = 1
                            if not item_row.item_name:
                                item_row.item_name = "OCR Extracted Item"
                                
                    mapped_fields["items_count"] = len(doc.items)
                except Exception:
                    pass  # Skip items if mapping fails
        
        return mapped_fields
    
    def _apply_smart_mapping(self, doc, ai_data, ocr_text, target_doctype):
        """Apply intelligent field mapping based on doctype and available data"""
        mapped_fields = {}
        
        # Common field mappings for different doctypes
        field_mappings = {
            "Sales Invoice": {
                "customer": ["customer_name", "customer", "client_name", "bill_to"],
                "customer_name": ["customer_name", "client_name", "customer"],
                "posting_date": ["date", "invoice_date", "bill_date"],
                "due_date": ["due_date", "payment_due_date"],
                "grand_total": ["total", "grand_total", "amount", "invoice_total"],
                "remarks": ["notes", "description", "remarks"],
                "po_no": ["po_number", "purchase_order", "reference"]
            },
            "Purchase Invoice": {
                "supplier": ["supplier_name", "vendor", "supplier"],
                "supplier_name": ["supplier_name", "vendor_name"],
                "posting_date": ["date", "invoice_date", "bill_date"],
                "due_date": ["due_date", "payment_due_date"],
                "grand_total": ["total", "grand_total", "amount", "bill_total"],
                "bill_no": ["invoice_no", "bill_no", "invoice_number"],
                "remarks": ["notes", "description", "remarks"]
            },
            "Sales Order": {
                "customer": ["customer_name", "customer", "client_name"],
                "customer_name": ["customer_name", "client_name"],
                "transaction_date": ["date", "order_date"],
                "delivery_date": ["delivery_date", "required_date"],
                "grand_total": ["total", "grand_total", "amount"],
                "po_no": ["customer_po", "po_number", "reference"]
            },
            "Purchase Order": {
                "supplier": ["supplier_name", "vendor", "supplier"],
                "supplier_name": ["supplier_name", "vendor_name"],
                "transaction_date": ["date", "order_date"],
                "schedule_date": ["delivery_date", "required_date"],
                "grand_total": ["total", "grand_total", "amount"]
            },
            "Quotation": {
                "party_name": ["customer_name", "client", "party"],
                "quotation_to": "Customer",
                "transaction_date": ["date", "quotation_date"],
                "valid_till": ["valid_until", "expiry_date"],
                "grand_total": ["total", "grand_total", "amount"]
            }
        }
        
        # Get mapping for current doctype
        doctype_mapping = field_mappings.get(target_doctype, {})
        
        # Apply field mappings
        for doc_field, ai_field_options in doctype_mapping.items():
            if hasattr(doc, doc_field):
                # Handle static values
                if isinstance(ai_field_options, str):
                    try:
                        setattr(doc, doc_field, ai_field_options)
                        mapped_fields[doc_field] = ai_field_options
                    except:
                        pass
                    continue
                
                # Handle field mapping from AI data
                for ai_field in ai_field_options:
                    if ai_field in ai_data and ai_data[ai_field]:
                        try:
                            value = ai_data[ai_field]
                            
                            # Handle date fields
                            if 'date' in doc_field.lower() and isinstance(value, str):
                                value = self._parse_date(value)
                            
                            # Handle numeric fields
                            elif doc_field in ['grand_total', 'total', 'amount'] and isinstance(value, str):
                                value = self._parse_amount(value)
                            
                            setattr(doc, doc_field, value)
                            mapped_fields[doc_field] = value
                            break
                        except Exception:
                            continue
        
        # Handle items if present
        if "items" in ai_data and isinstance(ai_data["items"], list) and hasattr(doc, 'items'):
            items_mapped = self._map_items(doc, ai_data["items"], target_doctype)
            if items_mapped:
                mapped_fields["items_count"] = items_mapped
        
        # Fallback: try to extract data from OCR text if no AI mapping worked
        if not mapped_fields and ocr_text:
            text_mapped = self._extract_from_text(doc, ocr_text, target_doctype)
            mapped_fields.update(text_mapped)
        
        return mapped_fields
    
    def _set_document_metadata(self, doc, target_doctype):
        """Set metadata fields for the document"""
        # Set title if available
        if hasattr(doc, 'title') and not doc.title:
            doc.title = f"From OCR - {self.title or self.name}"
        
        # Set company if available and required
        if hasattr(doc, 'company') and not doc.company:
            default_company = frappe.db.get_single_value("Global Defaults", "default_company")
            if default_company:
                doc.company = default_company
        
        # Set default values for common fields to avoid validation errors
        if hasattr(doc, 'currency') and not doc.currency:
            doc.currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "USD"
        
        if hasattr(doc, 'selling_price_list') and not doc.selling_price_list:
            doc.selling_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
        
        if hasattr(doc, 'buying_price_list') and not doc.buying_price_list:
            doc.buying_price_list = frappe.db.get_single_value("Buying Settings", "buying_price_list")
        
        # Add OCR reference in remarks/description
        ocr_reference = f"Created from OCR document: {self.name}"
        if hasattr(doc, 'remarks') and not doc.remarks:
            doc.remarks = ocr_reference
        elif hasattr(doc, 'description') and not doc.description:
            doc.description = ocr_reference
        elif hasattr(doc, 'notes') and not doc.notes:
            doc.notes = ocr_reference
    
    def _parse_date(self, date_str):
        """Parse date string to date object"""
        try:
            from dateutil import parser
            parsed_date = parser.parse(date_str)
            return parsed_date.date()
        except:
            try:
                import datetime
                # Try common date formats
                for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                    try:
                        return datetime.datetime.strptime(date_str, fmt).date()
                    except:
                        continue
            except:
                pass
        return None
    
    def _parse_amount(self, amount_str):
        """Parse amount string to float"""
        try:
            # Remove currency symbols and commas
            clean_amount = ''.join(c for c in str(amount_str) if c.isdigit() or c in '.-')
            return float(clean_amount) if clean_amount else 0.0
        except:
            return 0.0
    
    def _map_items(self, doc, items_data, target_doctype):
        """Map items data to document items table"""
        try:
            items_mapped = 0
            for item_data in items_data[:10]:  # Limit to 10 items
                if isinstance(item_data, dict):
                    item_row = doc.append('items', {})
                    
                    # Map common item fields
                    item_mappings = {
                        "item_name": ["name", "description", "item_name", "product", "item"],
                        "qty": ["quantity", "qty", "amount_qty"],
                        "rate": ["rate", "price", "unit_price", "cost"],
                        "amount": ["amount", "total", "line_total"]
                    }
                    
                    for item_field, possible_fields in item_mappings.items():
                        if hasattr(item_row, item_field):
                            for field in possible_fields:
                                if field in item_data and item_data[field]:
                                    try:
                                        value = item_data[field]
                                        if item_field in ['qty', 'rate', 'amount']:
                                            value = self._parse_amount(value)
                                        setattr(item_row, item_field, value)
                                        break
                                    except:
                                        continue
                    
                    # Set defaults if not mapped
                    if not item_row.qty:
                        item_row.qty = 1
                    if not item_row.item_name:
                        item_row.item_name = f"OCR Item {items_mapped + 1}"
                    
                    items_mapped += 1
            
            return items_mapped
        except Exception:
            return 0
    
    def _extract_from_text(self, doc, ocr_text, target_doctype):
        """Extract data from OCR text using pattern matching"""
        import re
        mapped_fields = {}
        text_lower = ocr_text.lower()
        
        # Common patterns
        patterns = {
            "total": [r'total[:\s]*([0-9,]+\.?[0-9]*)', r'amount[:\s]*([0-9,]+\.?[0-9]*)'],
            "date": [r'date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'],
            "invoice_no": [r'invoice[:\s#]*([A-Z0-9-]+)', r'bill[:\s#]*([A-Z0-9-]+)'],
            "customer": [r'customer[:\s]*([A-Za-z\s]+)', r'client[:\s]*([A-Za-z\s]+)']
        }
        
        for field_type, regex_list in patterns.items():
            for regex in regex_list:
                match = re.search(regex, text_lower)
                if match:
                    value = match.group(1).strip()
                    
                    # Map to appropriate document field
                    if field_type == "total" and hasattr(doc, 'grand_total'):
                        doc.grand_total = self._parse_amount(value)
                        mapped_fields['grand_total'] = value
                    elif field_type == "date" and hasattr(doc, 'posting_date'):
                        parsed_date = self._parse_date(value)
                        if parsed_date:
                            doc.posting_date = parsed_date
                            mapped_fields['posting_date'] = value
                    elif field_type == "customer" and hasattr(doc, 'customer_name'):
                        doc.customer_name = value.title()
                        mapped_fields['customer_name'] = value
                    
                    break
        
        return mapped_fields
    
    @frappe.whitelist()
    def preview_document_creation(self, target_doctype=None):
        """Preview what document will be created without actually creating it"""
        # Use detected doctype if no target specified
        if not target_doctype:
            target_doctype = self.suggested_doctype or self.detected_document_type
        
        if not target_doctype:
            frappe.throw(_("No document type detected. Please run classification first."))
        
        # Validate doctype exists
        if not frappe.db.exists("DocType", target_doctype):
            frappe.throw(_("DocType '{0}' does not exist").format(target_doctype))
        
        try:
            # Get extracted data
            ai_data = {}
            ocr_text = self.read_result or ""
            
            if self.ai_result:
                try:
                    ai_data = json.loads(self.ai_result)
                except json.JSONDecodeError:
                    ai_data = {"raw_ai_result": self.ai_result}
            
            # Create temporary document (don't save)
            temp_doc = frappe.new_doc(target_doctype)
            
            # Apply field mapping to preview
            mapped_fields = self._apply_smart_mapping(temp_doc, ai_data, ocr_text, target_doctype)
            
            # Get document structure for preview
            preview_data = {}
            for field in temp_doc.meta.fields:
                if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Button", "Tab Break"]:
                    field_value = getattr(temp_doc, field.fieldname, None)
                    if field_value is not None and field_value != "":
                        preview_data[field.fieldname] = {
                            "label": field.label or field.fieldname,
                            "value": str(field_value),
                            "fieldtype": field.fieldtype,
                            "mapped": field.fieldname in mapped_fields,
                            "required": field.reqd
                        }
            
            # Get items preview if applicable
            items_preview = []
            if hasattr(temp_doc, 'items') and temp_doc.items:
                for idx, item in enumerate(temp_doc.items):
                    item_data = {"row_index": idx + 1}
                    for field in item.meta.fields:
                        if field.fieldtype not in ["Section Break", "Column Break", "HTML", "Button"]:
                            value = getattr(item, field.fieldname, None)
                            if value is not None and value != "":
                                item_data[field.fieldname] = {
                                    "label": field.label or field.fieldname,
                                    "value": str(value),
                                    "fieldtype": field.fieldtype
                                }
                    if len(item_data) > 1:  # More than just row_index
                        items_preview.append(item_data)
            
            # Get available doctypes for selection
            available_doctypes = self._get_common_doctypes()
            
            return {
                "status": "success",
                "doctype": target_doctype,
                "preview_data": preview_data,
                "items_preview": items_preview,
                "mapped_fields_count": len(mapped_fields),
                "total_fields": len(preview_data),
                "items_count": len(items_preview),
                "confidence": self.confidence_score or 0,
                "ai_data_available": bool(self.ai_result),
                "ocr_data_available": bool(self.read_result),
                "available_doctypes": available_doctypes,
                "source_data": {
                    "ai_fields": list(ai_data.keys()) if ai_data else [],
                    "ocr_length": len(ocr_text),
                    "detected_type": self.detected_document_type
                }
            }
            
        except Exception as e:
            frappe.log_error(f"Error in preview_document_creation: {str(e)}")
            frappe.throw(_("Error generating preview: {0}").format(str(e)))
    
    def _get_common_doctypes(self):
        """Get list of common doctypes for document creation"""
        common_doctypes = [
            "Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order",
            "Quotation", "Delivery Note", "Purchase Receipt", "Customer", "Supplier",
            "Item", "Lead", "Opportunity"
        ]
        
        result = []
        for doctype in common_doctypes:
            if frappe.db.exists("DocType", doctype):
                result.append({
                    "name": doctype,
                    "label": doctype
                })
        
        return result

@frappe.whitelist()
def get_available_doctypes():
    """Get list of available doctypes for document creation"""
    # Common document types that might be created from OCR
    common_doctypes = [
        "Sales Invoice", "Purchase Invoice", "Quotation", "Sales Order", 
        "Purchase Order", "Delivery Note", "Purchase Receipt", "Customer",
        "Supplier", "Item", "Lead", "Opportunity", "Issue", "Task"
    ]
    
    # Get all available doctypes
    all_doctypes = frappe.get_all("DocType", 
                                 filters={"issingle": 0, "istable": 0, "disabled": 0},
                                 fields=["name", "module"],
                                 order_by="name")
    
    # Filter to show common ones first, then others
    result = []
    for dt in all_doctypes:
        if dt.name in common_doctypes:
            result.insert(0, dt)  # Add to beginning
        else:
            result.append(dt)  # Add to end
    
    return result

@frappe.whitelist()
def create_document_from_ocr(ocr_read_name, target_doctype, field_mapping=None):
    """Create a new document from OCR data"""
    ocr_doc = frappe.get_doc("OCR Read", ocr_read_name)
    
    if not ocr_doc.ai_result:
        frappe.throw(_("No AI extracted data available"))
    
    try:
        ai_data = json.loads(ocr_doc.ai_result)
        
        # Create new document
        new_doc = frappe.new_doc(target_doctype)
        
        # Apply field mapping if provided
        if field_mapping:
            field_mapping = json.loads(field_mapping) if isinstance(field_mapping, str) else field_mapping
            
            for ai_field, target_field in field_mapping.items():
                if ai_field in ai_data and hasattr(new_doc, target_field):
                    setattr(new_doc, target_field, ai_data[ai_field])
        
        # Auto-map common fields
        auto_map_fields(new_doc, ai_data)
        
        # Insert document
        new_doc.insert()
        
        return {
            "status": "success",
            "doctype": target_doctype,
            "name": new_doc.name,
            "message": _("Document {0} created successfully").format(new_doc.name)
        }
        
    except Exception as e:
        frappe.throw(_("Error creating document: {0}").format(str(e)))

def auto_map_fields(doc, ai_data):
    """Auto-map common fields from AI data to document"""
    # Common field mappings
    field_mappings = {
        "customer_name": ["customer_name", "party_name", "customer"],
        "supplier_name": ["supplier_name", "supplier"],
        "company": ["company"],
        "date": ["posting_date", "transaction_date", "date"],
        "due_date": ["due_date"],
        "total": ["grand_total", "total", "amount"],
        "tax": ["total_taxes_and_charges", "tax_amount"],
        "description": ["description", "subject", "title"],
        "address": ["address", "customer_address", "supplier_address"],
        "phone": ["phone", "mobile_no", "contact_no"],
        "email": ["email_id", "email"],
        "reference": ["reference_no", "po_no", "invoice_no"]
    }
    
    for ai_field, possible_doc_fields in field_mappings.items():
        if ai_field in ai_data:
            for doc_field in possible_doc_fields:
                if hasattr(doc, doc_field):
                    setattr(doc, doc_field, ai_data[ai_field])
                    break  # Use first matching field