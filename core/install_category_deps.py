#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تثبيت المكتبات المطلوبة لاستخراج الأقسام
"""

import subprocess
import sys

def install_requirements():
    """تثبيت المكتبات المطلوبة"""
    packages = [
        'requests',
        'beautifulsoup4',
        'lxml'  # محلل HTML محسن
    ]
    
    print("🔧 تثبيت المكتبات المطلوبة لاستخراج الأقسام...")
    
    for package in packages:
        try:
            print(f"📦 تثبيت {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ تم تثبيت {package} بنجاح")
        except subprocess.CalledProcessError as e:
            print(f"❌ فشل في تثبيت {package}: {e}")
    
    print("🎉 انتهى تثبيت المكتبات!")
    
    # اختبار الاستيراد
    print("\n🔍 اختبار الاستيرادات...")
    try:
        import requests
        from bs4 import BeautifulSoup
        print("✅ جميع المكتبات متوفرة وجاهزة للاستخدام!")
    except ImportError as e:
        print(f"❌ خطأ في الاستيراد: {e}")

if __name__ == "__main__":
    install_requirements()
