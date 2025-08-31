#!/usr/bin/env python3
"""
سكريبت تثبيت المكتبات المطلوبة لمشروع Shamela Scraper
Dependency Installation Script for Shamela Scraper
"""

import subprocess
import sys
import importlib
from pathlib import Path

# قائمة المكتبات المطلوبة
REQUIRED_PACKAGES = [
    'aiohttp',
    'requests', 
    'beautifulsoup4',
    'lxml',
    'mysql-connector-python',
    'pandas',
    'matplotlib',
    'seaborn',
    'psutil',
    'urllib3'
]

def check_package_installed(package_name):
    """فحص ما إذا كانت المكتبة مثبتة"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        # بعض المكتبات لها أسماء مختلفة عند الاستيراد
        package_mapping = {
            'beautifulsoup4': 'bs4',
            'mysql-connector-python': 'mysql.connector',
            'pillow': 'PIL'
        }
        
        if package_name in package_mapping:
            try:
                importlib.import_module(package_mapping[package_name])
                return True
            except ImportError:
                return False
        return False

def install_package(package_name):
    """تثبيت مكتبة واحدة"""
    try:
        print(f"🔄 جاري تثبيت {package_name}...")
        
        # جرب طرق مختلفة للتثبيت
        install_commands = [
            [sys.executable, '-m', 'pip', 'install', package_name],
            ['pip', 'install', package_name],
            ['pip3', 'install', package_name],
            ['py', '-m', 'pip', 'install', package_name]
        ]
        
        for cmd in install_commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                if result.returncode == 0:
                    print(f"✅ تم تثبيت {package_name} بنجاح")
                    return True
                else:
                    print(f"⚠️ فشل الأمر: {' '.join(cmd)}")
                    print(f"خطأ: {result.stderr}")
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                print(f"⚠️ خطأ في الأمر {' '.join(cmd)}: {e}")
                continue
        
        print(f"❌ فشل تثبيت {package_name}")
        return False
        
    except Exception as e:
        print(f"❌ خطأ غير متوقع أثناء تثبيت {package_name}: {e}")
        return False

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء فحص وتثبيت المكتبات المطلوبة...")
    print("=" * 50)
    
    installed_count = 0
    failed_count = 0
    already_installed = 0
    
    for package in REQUIRED_PACKAGES:
        print(f"\n📦 فحص {package}...")
        
        if check_package_installed(package):
            print(f"✅ {package} مثبت مسبقاً")
            already_installed += 1
        else:
            print(f"❌ {package} غير مثبت")
            if install_package(package):
                installed_count += 1
            else:
                failed_count += 1
    
    print("\n" + "=" * 50)
    print("📊 ملخص التثبيت:")
    print(f"✅ مثبت مسبقاً: {already_installed}")
    print(f"🆕 تم تثبيته الآن: {installed_count}")
    print(f"❌ فشل التثبيت: {failed_count}")
    print(f"📦 إجمالي المكتبات: {len(REQUIRED_PACKAGES)}")
    
    if failed_count > 0:
        print("\n⚠️ تحذير: بعض المكتبات لم يتم تثبيتها بنجاح")
        print("يرجى تثبيتها يدوياً أو التحقق من إعدادات Python/pip")
        return False
    else:
        print("\n🎉 تم تثبيت جميع المكتبات بنجاح!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)