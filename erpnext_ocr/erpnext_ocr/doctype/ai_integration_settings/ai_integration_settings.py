# -*- coding: utf-8 -*-
# Copyright (c) 2025, John Vincent Fiel and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json
import base64
import requests
from datetime import datetime

class AIIntegrationSettings(Document):
    @frappe.whitelist()
    def test_connection(self):
        """Test AI provider connection"""
        try:
            if self.ai_provider == "OpenAI":
                return self._test_openai()
            elif self.ai_provider == "Google Gemini":
                return self._test_gemini()
            elif self.ai_provider == "Anthropic Claude":
                return self._test_claude()
            elif self.ai_provider == "Perplexity AI":
                return self._test_perplexity()
            elif self.ai_provider == "OpenRouter":
                return self._test_openrouter()
            elif self.ai_provider == "Local Model":
                return self._test_local_model()
            else:
                return {"status": "error", "message": "Unsupported AI provider"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_openai(self):
        """Test OpenAI connection"""
        if not self.api_key:
            return {"status": "error", "message": "API Key is required for OpenAI"}
        
        headers = {
            "Authorization": f"Bearer {self.get_password('api_key')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name or "gpt-4-vision-preview",
            "messages": [{"role": "user", "content": "Test connection"}],
            "max_tokens": 10
        }
        
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout or 30)
            if response.status_code == 200:
                self.last_tested = datetime.now()
                self.test_status = "Success"
                self.save()
                return {"status": "success", "message": "Connection successful"}
            else:
                return {"status": "error", "message": f"API Error: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_gemini(self):
        """Test Google Gemini connection"""
        if not self.api_key:
            return {"status": "error", "message": "API Key is required for Google Gemini"}
        
        # Implement Gemini API test
        return {"status": "success", "message": "Gemini connection test not implemented yet"}
    
    def _test_claude(self):
        """Test Anthropic Claude connection"""
        if not self.api_key:
            return {"status": "error", "message": "API Key is required for Anthropic Claude"}
        
        # Implement Claude API test
        return {"status": "success", "message": "Claude connection test not implemented yet"}
    
    def _test_perplexity(self):
        """Test Perplexity AI connection"""
        if not self.api_key:
            return {"status": "error", "message": "API Key is required for Perplexity AI"}
        
        headers = {
            "Authorization": f"Bearer {self.get_password('api_key')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name or "sonar-pro",
            "messages": [{"role": "user", "content": "Test connection"}],
            "max_tokens": 10
        }
        
        url = self.base_url or "https://api.perplexity.ai/chat/completions"
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout or 30)
            if response.status_code == 200:
                self.last_tested = datetime.now()
                self.test_status = "Success"
                self.save()
                return {"status": "success", "message": "Connection successful"}
            else:
                return {"status": "error", "message": f"API Error: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_openrouter(self):
        """Test OpenRouter connection"""
        if not self.api_key:
            return {"status": "error", "message": "API Key is required for OpenRouter"}
        
        headers = {
            "Authorization": f"Bearer {self.get_password('api_key')}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model_name or "google/gemini-2.5-flash-image-preview:free",
            "messages": [{"role": "user", "content": "Test connection"}],
            "max_tokens": 10
        }
        
        url = self.base_url or "https://openrouter.ai/api/v1/chat/completions"
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout or 30)
            if response.status_code == 200:
                self.last_tested = datetime.now()
                self.test_status = "Success"
                self.save()
                return {"status": "success", "message": "Connection successful"}
            else:
                return {"status": "error", "message": f"API Error: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _test_local_model(self):
        """Test local model connection"""
        # Implement local model test
        return {"status": "success", "message": "Local model connection test not implemented yet"}

@frappe.whitelist()
def test_ai_query(settings_name, query, query_type="Custom Query"):
    """Test AI query with the given settings"""
    import time
    
    try:
        settings = frappe.get_doc("AI Integration Settings", settings_name)
        
        if not settings.is_active:
            return {"status": "error", "message": "AI Integration Settings is not active"}
        
        start_time = time.time()
        
        # Process the query based on provider
        if settings.ai_provider == "OpenAI":
            result = _test_openai_query(settings, query)
        elif settings.ai_provider == "Google Gemini":
            result = _test_gemini_query(settings, query)
        elif settings.ai_provider == "Anthropic Claude":
            result = _test_claude_query(settings, query)
        elif settings.ai_provider == "Perplexity AI":
            result = _test_perplexity_query(settings, query)
        elif settings.ai_provider == "OpenRouter":
            result = _test_openrouter_query(settings, query)
        else:
            return {"status": "error", "message": "Unsupported AI provider for testing"}
        
        end_time = time.time()
        response_time = f"{(end_time - start_time):.2f}s"
        
        if result["status"] == "success":
            return {
                "status": "success",
                "response": result["response"],
                "usage": result.get("usage", {}),
                "model": result.get("model", ""),
                "response_time": response_time,
                "query_type": query_type
            }
        else:
            return result
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _test_openai_query(settings, query):
    """Test query with OpenAI"""
    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.model_name or "gpt-4",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for document processing and OCR tasks. Provide clear, concise, and helpful responses."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": min(settings.max_tokens or 1000, 1000),  # Limit for testing
        "temperature": settings.temperature or 0.1
    }
    
    url = settings.base_url or "https://api.openai.com/v1/chat/completions"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=settings.timeout or 30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "response": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "")
            }
        else:
            return {"status": "error", "message": f"OpenAI API Error: {response.text}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _test_gemini_query(settings, query):
    """Test query with Google Gemini"""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=settings.get_password('api_key'))
        model = genai.GenerativeModel(settings.model_name or 'gemini-pro')
        
        response = model.generate_content(query)
        
        return {
            "status": "success",
            "response": response.text,
            "usage": {"total_tokens": "N/A (Gemini)"},
            "model": settings.model_name or 'gemini-pro'
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Gemini API Error: {str(e)}"}

def _test_claude_query(settings, query):
    """Test query with Anthropic Claude"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=settings.get_password('api_key'))
        
        message = client.messages.create(
            model=settings.model_name or "claude-3-opus-20240229",
            max_tokens=min(settings.max_tokens or 1000, 1000),
            temperature=settings.temperature or 0.1,
            messages=[
                {
                    "role": "user",
                    "content": query
                }
            ]
        )
        
        return {
            "status": "success",
            "response": message.content[0].text,
            "usage": {"total_tokens": f"{message.usage.input_tokens + message.usage.output_tokens}"},
            "model": settings.model_name or "claude-3-opus-20240229"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Claude API Error: {str(e)}"}

def _test_perplexity_query(settings, query):
    """Test query with Perplexity AI"""
    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.model_name or "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for document processing and OCR tasks. Provide clear, concise, and helpful responses."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": min(settings.max_tokens or 1000, 1000),  # Limit for testing
        "temperature": settings.temperature or 0.1
    }
    
    url = settings.base_url or "https://api.perplexity.ai/chat/completions"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=settings.timeout or 30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "response": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "")
            }
        else:
            return {"status": "error", "message": f"Perplexity API Error: {response.text}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _test_openrouter_query(settings, query):
    """Test query with OpenRouter"""
    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.model_name or "google/gemini-2.5-flash-image-preview:free",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI assistant for document processing and OCR tasks. Provide clear, concise, and helpful responses."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": min(settings.max_tokens or 1000, 1000),  # Limit for testing
        "temperature": settings.temperature or 0.1
    }
    
    url = settings.base_url or "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=settings.timeout or 30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "response": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "model": result.get("model", "")
            }
        else:
            return {"status": "error", "message": f"OpenRouter API Error: {response.text}"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

@frappe.whitelist()
def get_active_ai_settings():
    """Get active AI integration settings"""
    settings = frappe.get_all("AI Integration Settings", 
                             filters={"is_active": 1}, 
                             fields=["name", "title", "ai_provider", "model_name"],
                             limit=1)
    
    if settings:
        return frappe.get_doc("AI Integration Settings", settings[0].name)
    return None

@frappe.whitelist()
def process_image_with_ai(image_path, prompt_type="ocr", custom_prompt=None):
    """Process image with AI"""
    settings = get_active_ai_settings()
    if not settings:
        frappe.throw(_("No active AI integration settings found"))
    
    try:
        # Read and encode image
        full_path = frappe.get_site_path() + image_path
        with open(full_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Get appropriate prompt
        if custom_prompt:
            prompt = custom_prompt
        elif prompt_type == "classification":
            prompt = settings.classification_prompt
        elif prompt_type == "extraction":
            prompt = settings.extraction_prompt
        else:
            prompt = settings.ocr_prompt
        
        # Process based on provider
        if settings.ai_provider == "OpenAI":
            return _process_with_openai(settings, image_data, prompt)
        elif settings.ai_provider == "Google Gemini":
            return _process_with_gemini(settings, image_data, prompt)
        elif settings.ai_provider == "Anthropic Claude":
            return _process_with_claude(settings, image_data, prompt)
        elif settings.ai_provider == "Perplexity AI":
            return _process_with_perplexity(settings, image_data, prompt)
        elif settings.ai_provider == "OpenRouter":
            return _process_with_openrouter(settings, image_data, prompt)
        else:
            frappe.throw(_("Unsupported AI provider: {0}").format(settings.ai_provider))
            
    except Exception as e:
        frappe.throw(_("Error processing image with AI: {0}").format(str(e)))

def _process_with_openai(settings, image_data, prompt):
    """Process image with OpenAI"""
    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.model_name or "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }
                ]
            }
        ],
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

def _process_with_gemini(settings, image_data, prompt):
    """Process image with Google Gemini"""
    # Implement Gemini processing
    frappe.throw(_("Gemini processing not implemented yet"))

def _process_with_claude(settings, image_data, prompt):
    """Process image with Anthropic Claude"""
    # Implement Claude processing
    frappe.throw(_("Claude processing not implemented yet"))

def _process_with_perplexity(settings, image_data, prompt):
    """Process image with Perplexity AI"""
    # Note: Perplexity AI doesn't support vision/image processing yet
    # This is a text-only implementation for now
    frappe.throw(_("Perplexity AI does not currently support image processing. Please use OpenAI, Google Gemini, or Anthropic Claude for OCR tasks."))

def _process_with_openrouter(settings, image_data, prompt):
    """Process image with OpenRouter"""
    headers = {
        "Authorization": f"Bearer {settings.get_password('api_key')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": settings.model_name or "google/gemini-2.5-flash-image-preview:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    }
                ]
            }
        ],
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