#!/usr/bin/env python3
"""
Test script for AI Integration functionality
Run this to verify AI Integration Settings are working
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_integration_imports():
    """Test if all AI integration modules can be imported"""
    print("🔍 Testing AI Integration imports...")
    
    try:
        # Test core imports
        import json
        import requests
        print("✅ Core modules imported successfully")
        
        # Test AI provider imports
        try:
            import openai
            print("✅ OpenAI client available")
        except ImportError:
            print("❌ OpenAI client not available")
        
        try:
            import google.generativeai as genai
            print("✅ Google Gemini client available")
        except ImportError:
            print("❌ Google Gemini client not available")
        
        try:
            import anthropic
            print("✅ Anthropic Claude client available")
        except ImportError:
            print("❌ Anthropic Claude client not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return False

def test_ai_settings_structure():
    """Test AI Integration Settings structure"""
    print("\n🔍 Testing AI Integration Settings structure...")
    
    try:
        # Test if we can read the JSON structure
        with open('erpnext_ocr/erpnext_ocr/doctype/ai_integration_settings/ai_integration_settings.json', 'r') as f:
            import json
            settings_json = json.load(f)
        
        required_fields = [
            'ai_provider', 'api_key', 'model_name', 'max_tokens', 
            'temperature', 'timeout', 'enable_ai_ocr', 'enable_document_classification',
            'enable_field_extraction', 'ocr_prompt', 'classification_prompt', 
            'extraction_prompt', 'is_active'
        ]
        
        existing_fields = [field['fieldname'] for field in settings_json['fields']]
        
        missing_fields = []
        for field in required_fields:
            if field not in existing_fields:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False
        else:
            print("✅ All required fields present in AI Integration Settings")
            return True
            
    except Exception as e:
        print(f"❌ Settings structure test failed: {str(e)}")
        return False

def test_ocr_read_structure():
    """Test OCR Read enhancements"""
    print("\n🔍 Testing OCR Read enhancements...")
    
    try:
        # Test if we can read the enhanced OCR Read JSON
        with open('erpnext_ocr/erpnext_ocr/doctype/ocr_read/ocr_read.json', 'r') as f:
            import json
            ocr_json = json.load(f)
        
        enhanced_fields = [
            'image_preview', 'read_with_ai', 'classify_document', 
            'ai_result', 'detected_document_type', 'confidence_score',
            'suggested_doctype', 'proceed_with_doctype'
        ]
        
        existing_fields = [field['fieldname'] for field in ocr_json['fields']]
        
        missing_fields = []
        for field in enhanced_fields:
            if field not in existing_fields:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Missing enhanced fields: {missing_fields}")
            return False
        else:
            print("✅ All enhanced fields present in OCR Read")
            return True
            
    except Exception as e:
        print(f"❌ OCR Read structure test failed: {str(e)}")
        return False

def test_javascript_files():
    """Test if JavaScript files exist"""
    print("\n🔍 Testing JavaScript files...")
    
    js_files = [
        'erpnext_ocr/erpnext_ocr/doctype/ai_integration_settings/ai_integration_settings.js',
        'erpnext_ocr/erpnext_ocr/doctype/ocr_read/ocr_read.js'
    ]
    
    all_exist = True
    for js_file in js_files:
        if os.path.exists(js_file):
            print(f"✅ {js_file} exists")
        else:
            print(f"❌ {js_file} missing")
            all_exist = False
    
    return all_exist

def test_css_files():
    """Test if CSS files exist"""
    print("\n🔍 Testing CSS files...")
    
    css_files = [
        'erpnext_ocr/erpnext_ocr/public/css/ocr_enhancements.css'
    ]
    
    all_exist = True
    for css_file in css_files:
        if os.path.exists(css_file):
            print(f"✅ {css_file} exists")
        else:
            print(f"❌ {css_file} missing")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests"""
    print("🚀 AI Integration Testing Suite")
    print("=" * 50)
    
    tests = [
        ("AI Integration Imports", test_ai_integration_imports),
        ("AI Settings Structure", test_ai_settings_structure),
        ("OCR Read Enhancements", test_ocr_read_structure),
        ("JavaScript Files", test_javascript_files),
        ("CSS Files", test_css_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI Integration is ready.")
        print("\n📋 Next steps:")
        print("1. Run 'bench migrate' to apply changes")
        print("2. Configure AI Integration Settings in ERPNext")
        print("3. Add your API keys")
        print("4. Test the connection using the Test buttons")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)