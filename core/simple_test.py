#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print("بدء الاختبار...")

try:
    print("استيراد requests...")
    import requests
    print("✅ requests تم استيراده بنجاح")
    
    print("استيراد BeautifulSoup...")
    from bs4 import BeautifulSoup
    print("✅ BeautifulSoup تم استيراده بنجاح")
    
    print("استيراد category_extractor...")
    from category_extractor import CategoryExtractor
    print("✅ CategoryExtractor تم استيراده بنجاح")
    
    print("إنشاء كائن CategoryExtractor...")
    extractor = CategoryExtractor()
    print("✅ تم إنشاء CategoryExtractor بنجاح")
    
    print("🎉 جميع الاستيرادات تمت بنجاح!")
    
except ImportError as e:
    print(f"❌ خطأ في الاستيراد: {e}")
except Exception as e:
    print(f"❌ خطأ عام: {e}")
    import traceback
    traceback.print_exc()

print("انتهى الاختبار.")
