# ERPNext OCR with AI Integration - Complete Guide

## Overview

This enhanced ERPNext OCR app now includes powerful AI integration capabilities that can:

- Extract text using traditional OCR (Tesseract) or AI models
- Classify document types automatically
- Extract structured data in JSON format
- Suggest appropriate ERPNext DocTypes
- Create documents automatically from extracted data
- Provide intelligent field mapping

## Features

### 1. **AI Integration Settings**
- Support for multiple AI providers (OpenAI, Google Gemini, Anthropic Claude, Local Models)
- Configurable prompts for different tasks
- API key management and connection testing
- Customizable model parameters

### 2. **Enhanced OCR Read**
- **Image Preview**: Visual preview of uploaded images
- **Dual Processing**: Traditional OCR + AI-powered extraction
- **Document Classification**: Automatic document type detection
- **Structured Data**: JSON format results with field mapping
- **Smart Document Creation**: One-click document creation with field mapping

### 3. **Smart Dialog System**
- Document type selection with confidence scores
- Field mapping interface
- Preview of extracted data
- Customizable target DocType selection

## Installation

### 1. Install Dependencies

```bash
# Install Python packages
pip install pytesseract Pillow requests openai google-generativeai anthropic

# Install Tesseract OCR engine
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# CentOS/RHEL
sudo yum install tesseract

# macOS
brew install tesseract
```

### 2. Install the App

```bash
bench get-app https://github.com/your-repo/erpnext_ocr
bench install-app erpnext_ocr
bench migrate
bench restart
```

## Configuration

### 1. Set up AI Integration Settings

1. Go to **AI Integration Settings**
2. Create a new settings document
3. Configure your AI provider:

#### OpenAI Configuration
```
Title: My OpenAI Settings
AI Provider: OpenAI
API Key: sk-your-openai-api-key
Model Name: gpt-4-vision-preview
Max Tokens: 4000
Temperature: 0.1
```

#### Google Gemini Configuration
```
Title: My Gemini Settings
AI Provider: Google Gemini
API Key: your-gemini-api-key
Model Name: gemini-pro-vision
```

#### Anthropic Claude Configuration
```
Title: My Claude Settings
AI Provider: Anthropic Claude
API Key: your-claude-api-key
Model Name: claude-3-opus
```

### 2. Test Connection

1. Click **Test Connection** button in AI Integration Settings
2. Verify the connection is successful
3. Mark the settings as **Active**

### 3. Customize Prompts

#### OCR Prompt
```
Extract all text from this image. Return the result as clean, structured text maintaining the original layout and formatting where possible.
```

#### Classification Prompt
```
Analyze this document image and classify it. Return a JSON object with:
{
  "document_type": "invoice|receipt|purchase_order|quotation|other",
  "confidence": 0.95,
  "suggested_doctype": "Sales Invoice",
  "key_fields": ["customer_name", "date", "total"]
}
```

#### Extraction Prompt
```
Extract structured data from this document. Return a JSON object with all identifiable fields and their values. Use these field names when possible:
- customer_name, supplier_name
- date, due_date
- total, tax, subtotal
- description, reference
- address, phone, email
- items (as array with name, quantity, rate, amount)
```

## Usage

### 1. Basic OCR Processing

1. Go to **OCR Read**
2. Upload an image using **Image to Read** field
3. View the image preview
4. Choose processing method:
   - **Read with Traditional OCR**: Uses Tesseract
   - **Read with AI**: Uses configured AI model

### 2. Document Classification

1. Upload an image
2. Click **Classify Document**
3. View classification results:
   - Document type
   - Confidence score
   - Suggested ERPNext DocType

### 3. Create Documents from OCR

1. After AI processing and classification
2. Click **Create Document**
3. In the dialog:
   - Confirm or change target DocType
   - Map AI fields to document fields
   - Preview extracted data
4. Click **Create Document**
5. Choose to open the created document

### 4. Field Mapping

The system automatically suggests field mappings:

| AI Field | Common DocType Fields |
|----------|----------------------|
| customer_name | customer_name, party_name |
| supplier_name | supplier_name, supplier |
| date | posting_date, transaction_date |
| total | grand_total, total_amount |
| tax | total_taxes_and_charges |
| reference | reference_no, po_no |

## API Endpoints

### OCR Processing
```bash
# Traditional OCR
POST /api/method/run_doc_method
{
  "docs": "{OCR Read document}",
  "method": "read_image"
}

# AI OCR
POST /api/method/run_doc_method
{
  "docs": "{OCR Read document}",
  "method": "read_with_ai"
}
```

### Document Classification
```bash
POST /api/method/run_doc_method
{
  "docs": "{OCR Read document}",
  "method": "classify_document"
}
```

### Document Creation
```bash
POST /api/method/erpnext_ocr.erpnext_ocr.doctype.ocr_read.ocr_read.create_document_from_ocr
{
  "ocr_read_name": "OCR-READ-001",
  "target_doctype": "Sales Invoice",
  "field_mapping": {
    "customer_name": "customer_name",
    "date": "posting_date",
    "total": "grand_total"
  }
}
```

## Example Workflows

### 1. Invoice Processing
1. Upload invoice image
2. Click **Read with AI**
3. Click **Classify Document** → Detects "Sales Invoice"
4. Click **Create Document**
5. Map fields: customer_name → customer, date → posting_date
6. Create Sales Invoice automatically

### 2. Purchase Order Processing
1. Upload PO image
2. AI extracts: supplier, items, amounts
3. Classification suggests "Purchase Order"
4. Create PO with pre-filled data

### 3. Receipt Processing
1. Upload receipt
2. Extract expense details
3. Create Expense Claim or Journal Entry

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   pip install pytesseract Pillow requests openai
   ```

2. **API Key Issues**
   - Verify API key is correct
   - Check API quotas and billing
   - Test connection in AI Integration Settings

3. **Image Processing Errors**
   - Ensure image format is supported
   - Check file size limits
   - Verify image quality

4. **Field Mapping Issues**
   - Check target DocType permissions
   - Verify field names exist
   - Review mandatory field requirements

### Debug Mode

Enable debug logging:
```python
# In site_config.json
{
  "developer_mode": 1,
  "log_level": "DEBUG"
}
```

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **File Access**: Images are processed securely within Frappe's file system
3. **Data Privacy**: Consider data residency requirements for AI processing
4. **Permissions**: Ensure proper role-based access to OCR functions

## Performance Tips

1. **Image Optimization**: Resize large images before processing
2. **Batch Processing**: Process multiple documents in sequence
3. **Caching**: Results are cached in the OCR Read document
4. **Model Selection**: Choose appropriate model for speed vs accuracy

## Support

For issues and feature requests:
1. Check the troubleshooting section
2. Review logs in ERPNext
3. Test AI provider connections
4. Verify field mappings and permissions