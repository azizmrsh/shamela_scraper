#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
أداة تثبيت المكتبات المطلوبة للتحسينات المتقدمة
Advanced Dependencies Installer
"""

import subprocess
import sys
import importlib

# قائمة المكتبات المطلوبة
REQUIRED_PACKAGES = [
    'aiohttp>=3.9.0',        # للمعالجة غير المتزامنة
    'lxml>=4.9.0',           # لمعالجة HTML السريعة  
    'psutil>=5.9.0',         # لمعلومات النظام
    'beautifulsoup4>=4.12.0', # بديل lxml
    'mysql-connector-python>=8.0.0',  # قاعدة البيانات
]

def install_package(package):
    """تثبيت مكتبة واحدة"""
    try:
        print(f"🔄 تثبيت {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ تم تثبيت {package} بنجاح")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل في تثبيت {package}: {e}")
        return False

def check_package(package_name):
    """التحقق من وجود مكتبة"""
    try:
        importlib.import_module(package_name)
        return True
    except ImportError:
        return False

def main():
    """تثبيت جميع المكتبات المطلوبة"""
    print("🚀 بدء تثبيت المكتبات المطلوبة للتحسينات المتقدمة...")
    print("=" * 60)
    
    success_count = 0
    total_packages = len(REQUIRED_PACKAGES)
    
    for package in REQUIRED_PACKAGES:
        if install_package(package):
            success_count += 1
        print("-" * 40)
    
    print(f"\n📊 النتائج:")
    print(f"✅ نجح: {success_count}/{total_packages}")
    print(f"❌ فشل: {total_packages - success_count}/{total_packages}")
    
    if success_count == total_packages:
        print("\n🎉 تم تثبيت جميع المكتبات بنجاح!")
        print("💡 يمكنك الآن تشغيل السكربت المحسن الجديد")
    else:
        print("\n⚠️  فشل في تثبيت بعض المكتبات")
        print("💡 تأكد من اتصالك بالإنترنت وحاول مرة أخرى")
    
    # اختبار المكتبات المثبتة
    print("\n🔍 اختبار المكتبات المثبتة:")
    
    test_imports = {
        'aiohttp': 'aiohttp',
        'lxml': 'lxml.html',
        'psutil': 'psutil',
        'beautifulsoup4': 'bs4',
        'mysql-connector-python': 'mysql.connector'
    }
    
    for package_name, import_name in test_imports.items():
        if check_package(import_name.split('.')[0]):
            print(f"✅ {package_name}: متوفر")
        else:
            print(f"❌ {package_name}: غير متوفر")
    
    print("\n" + "=" * 60)
    print("🏁 انتهى تثبيت المكتبات")

if __name__ == "__main__":
    main()
