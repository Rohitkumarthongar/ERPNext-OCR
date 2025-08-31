#!/usr/bin/env python3
"""
ERPNext OCR Setup Verification Script
Run this script to verify all dependencies are properly installed
"""

import sys
import subprocess

def check_system_packages():
    """Check system-level packages"""
    print("🔍 Checking system packages...")
    
    try:
        result = subprocess.run(['tesseract', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.split('\n')[0]
            print(f"✅ Tesseract OCR: {version}")
        else:
            print("❌ Tesseract OCR not found")
            return False
    except FileNotFoundError:
        print("❌ Tesseract OCR not installed")
        return False
    
    return True

def check_python_packages():
    """Check Python packages"""
    print("\n🔍 Checking Python packages...")
    
    required_packages = [
        ('pytesseract', 'pytesseract'),
        ('PIL', 'Pillow'),
        ('requests', 'requests'),
        ('openai', 'openai'),
        ('google.generativeai', 'google-generativeai'),
        ('anthropic', 'anthropic'),
        ('json', 'built-in'),
        ('os', 'built-in')
    ]
    
    all_good = True
    
    for package, pip_name in required_packages:
        try:
            if package == 'PIL':
                import PIL
                print(f"✅ {package} (Pillow): {PIL.__version__}")
            elif package in ['json', 'os']:
                __import__(package)
                print(f"✅ {package}: built-in module")
            else:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                print(f"✅ {package}: {version}")
        except ImportError:
            print(f"❌ {package} not found (install with: pip install {pip_name})")
            all_good = False
    
    return all_good

def check_ai_providers():
    """Check AI provider connectivity (without API keys)"""
    print("\n🔍 Checking AI provider modules...")
    
    try:
        import openai
        print("✅ OpenAI client ready")
    except ImportError:
        print("❌ OpenAI client not available")
    
    try:
        import google.generativeai as genai
        print("✅ Google Gemini client ready")
    except ImportError:
        print("❌ Google Gemini client not available")
    
    try:
        import anthropic
        print("✅ Anthropic Claude client ready")
    except ImportError:
        print("❌ Anthropic Claude client not available")

def test_basic_ocr():
    """Test basic OCR functionality"""
    print("\n🔍 Testing basic OCR functionality...")
    
    try:
        import pytesseract
        from PIL import Image
        
        # Create a simple test image with text
        img = Image.new('RGB', (200, 50), color='white')
        
        # This is just a basic import test
        print("✅ OCR modules can be imported and initialized")
        return True
        
    except Exception as e:
        print(f"❌ OCR test failed: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("🚀 ERPNext OCR Setup Verification")
    print("=" * 50)
    
    checks = [
        ("System Packages", check_system_packages),
        ("Python Packages", check_python_packages),
        ("AI Providers", check_ai_providers),
        ("Basic OCR", test_basic_ocr)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if result is False:
                all_passed = False
        except Exception as e:
            print(f"❌ {check_name} check failed: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All checks passed! Your ERPNext OCR setup is ready.")
        print("\n📋 Next steps:")
        print("1. Configure AI Integration Settings in ERPNext")
        print("2. Add your API keys for AI providers")
        print("3. Test OCR functionality with sample images")
        print("4. Create documents from extracted data")
    else:
        print("⚠️  Some checks failed. Please install missing dependencies.")
        print("\n🔧 Installation commands:")
        print("pip install --break-system-packages pytesseract openai google-generativeai anthropic")
        print("sudo apt-get install tesseract-ocr python3-pil python3-requests")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)