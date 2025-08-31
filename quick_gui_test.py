#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تقرير اختبار سريع للواجهة الرسومية
Quick Test Report for Enhanced Runner GUI
"""

import os
import sys
from datetime import datetime

def quick_test_report():
    """تقرير اختبار سريع"""
    print("🧪 تقرير اختبار سريع - Enhanced Runner GUI")
    print("=" * 60)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. فحص الملفات الأساسية
    print("\n📁 فحص الملفات الأساسية:")
    essential_files = {
        'enhanced_runner_gui.py': 'الواجهة الرسومية الرئيسية',
        'enhanced_runner.py': 'مشغل المكتبة الشاملة',
        'enhanced_shamela_scraper.py': 'مستخرج البيانات المحسن',
        'enhanced_database_manager.py': 'مدير قاعدة البيانات',
        'start_runner_gui.bat': 'ملف التشغيل السريع',
        'ENHANCED_RUNNER_GUI_README.md': 'دليل الاستخدام'
    }
    
    all_files_exist = True
    for file, desc in essential_files.items():
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size:,} بايت) - {desc}")
        else:
            print(f"❌ {file} (مفقود) - {desc}")
            all_files_exist = False
    
    # 2. فحص المكتبات المطلوبة
    print("\n📦 فحص المكتبات المطلوبة:")
    try:
        import tkinter as tk
        print("✅ tkinter - واجهة رسومية")
    except ImportError:
        print("❌ tkinter - واجهة رسومية (غير متوفر)")
        all_files_exist = False
    
    try:
        import mysql.connector
        print("✅ mysql-connector-python - قاعدة البيانات")
    except ImportError:
        print("❌ mysql-connector-python - قاعدة البيانات (غير متوفر)")
        print("💡 لتثبيته: pip install mysql-connector-python")
    
    try:
        import requests
        print("✅ requests - طلبات HTTP")
    except ImportError:
        print("⚠️ requests - طلبات HTTP (غير متوفر)")
    
    try:
        import lxml
        print("✅ lxml - معالجة XML/HTML")
    except ImportError:
        print("⚠️ lxml - معالجة XML/HTML (غير متوفر)")
    
    # 3. فحص هيكل المجلدات
    print("\n📂 فحص هيكل المجلدات:")
    folders = {
        'enhanced_books': 'مجلد الكتب المحفوظة',
        'logs': 'مجلد السجلات', 
        '__pycache__': 'مجلد Python المؤقت'
    }
    
    for folder, desc in folders.items():
        if os.path.exists(folder) and os.path.isdir(folder):
            files_count = len(os.listdir(folder))
            print(f"✅ {folder}/ ({files_count} ملف) - {desc}")
        else:
            print(f"⚪ {folder}/ (غير موجود) - {desc}")
    
    # 4. فحص ملفات البيانات
    print("\n📊 فحص ملفات البيانات:")
    data_files = []
    for file in os.listdir('.'):
        if file.startswith('enhanced_book_') and (file.endswith('.json') or file.endswith('.json.gz')):
            data_files.append(file)
    
    if data_files:
        print(f"✅ عدد الكتب المحفوظة: {len(data_files)}")
        for file in data_files[:3]:  # عرض أول 3 ملفات
            size = os.path.getsize(file)
            print(f"  📖 {file} ({size:,} بايت)")
        if len(data_files) > 3:
            print(f"  ... و {len(data_files) - 3} ملف آخر")
    else:
        print("⚪ لا توجد كتب محفوظة حالياً")
    
    # 5. اختبار بسيط للواجهة
    print("\n🖥️ اختبار الواجهة الرسومية:")
    try:
        import tkinter as tk
        
        # إنشاء نافذة اختبار
        root = tk.Tk()
        root.withdraw()  # إخفاءها
        
        # اختبار النص العربي
        label = tk.Label(root, text="اختبار النص العربي - Enhanced Runner")
        
        # اختبار ttk
        from tkinter import ttk
        style = ttk.Style()
        
        root.destroy()
        print("✅ الواجهة الرسومية جاهزة للتشغيل")
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الواجهة: {str(e)[:100]}")
        all_files_exist = False
    
    # 6. النتيجة النهائية
    print("\n" + "=" * 60)
    print("📊 النتيجة النهائية:")
    print("=" * 60)
    
    if all_files_exist:
        print("🎉 جميع الاختبارات نجحت!")
        print("✅ النظام جاهز للاستخدام")
        print()
        print("🚀 لتشغيل الواجهة:")
        print("   1. انقر مزدوج على: start_runner_gui.bat")
        print("   2. أو شغل: python enhanced_runner_gui.py")
        print()
        print("📖 للمساعدة:")
        print("   اقرأ ملف: ENHANCED_RUNNER_GUI_README.md")
        
        return True
    else:
        print("⚠️ بعض المكونات مفقودة أو لا تعمل")
        print("💡 راجع الأخطاء أعلاه وتأكد من تثبيت المتطلبات")
        
        return False

if __name__ == "__main__":
    success = quick_test_report()
    print("\n" + "=" * 60)
    if success:
        print("✅ الاختبار مكتمل بنجاح!")
    else:
        print("❌ الاختبار انتهى مع ملاحظات")
    print("=" * 60)
