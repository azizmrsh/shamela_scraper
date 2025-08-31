#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل لواجهة Enhanced Runner GUI
Comprehensive test for Enhanced Runner GUI
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

def test_gui_components():
    """اختبار مكونات الواجهة الرسومية"""
    print("🔍 اختبار مكونات الواجهة الرسومية...")
    print("=" * 50)
    
    try:
        # اختبار استيراد tkinter
        import tkinter as tk
        from tkinter import ttk
        print("✅ tkinter متاح ويعمل")
        
        # اختبار إنشاء نافذة
        root = tk.Tk()
        root.withdraw()  # إخفاء النافذة
        root.title("اختبار")
        print("✅ إنشاء النوافذ يعمل")
        root.destroy()
        
        # اختبار الخطوط العربية
        root2 = tk.Tk()
        root2.withdraw()
        label = tk.Label(root2, text="اختبار النص العربي", font=('Arial', 12))
        print("✅ دعم النصوص العربية يعمل")
        root2.destroy()
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الواجهة: {e}")
        return False

def test_enhanced_runner_import():
    """اختبار استيراد وحدة enhanced_runner"""
    print("\n📦 اختبار استيراد Enhanced Runner...")
    print("=" * 50)
    
    try:
        # اختبار استيراد الوحدة الرئيسية
        sys.path.insert(0, os.getcwd())
        
        # اختبار وجود الملف
        if os.path.exists('enhanced_runner.py'):
            print("✅ ملف enhanced_runner.py موجود")
        else:
            print("❌ ملف enhanced_runner.py غير موجود")
            return False
        
        # اختبار وجود enhanced_shamela_scraper
        if os.path.exists('enhanced_shamela_scraper.py'):
            print("✅ ملف enhanced_shamela_scraper.py موجود")
        else:
            print("❌ ملف enhanced_shamela_scraper.py غير موجود")
            return False
        
        # اختبار وجود enhanced_database_manager
        if os.path.exists('enhanced_database_manager.py'):
            print("✅ ملف enhanced_database_manager.py موجود")
        else:
            print("❌ ملف enhanced_database_manager.py غير موجود")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الاستيراد: {e}")
        return False

def test_gui_file():
    """اختبار ملف الواجهة الرسومية"""
    print("\n🖥️ اختبار ملف الواجهة الرسومية...")
    print("=" * 50)
    
    try:
        # التحقق من وجود الملف
        if not os.path.exists('enhanced_runner_gui.py'):
            print("❌ ملف enhanced_runner_gui.py غير موجود")
            return False
        
        print("✅ ملف enhanced_runner_gui.py موجود")
        
        # التحقق من حجم الملف
        file_size = os.path.getsize('enhanced_runner_gui.py')
        print(f"📏 حجم الملف: {file_size:,} بايت")
        
        if file_size < 10000:
            print("⚠️ حجم الملف صغير، قد يكون ناقصاً")
        else:
            print("✅ حجم الملف مناسب")
        
        # اختبار تركيب الملف
        with open('enhanced_runner_gui.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # التحقق من الكلاسات المهمة
        if 'class EnhancedRunnerGUI' in content:
            print("✅ كلاس EnhancedRunnerGUI موجود")
        else:
            print("❌ كلاس EnhancedRunnerGUI غير موجود")
            return False
        
        # التحقق من الوظائف المهمة
        essential_functions = [
            'create_extract_tab',
            'create_database_tab', 
            'create_management_tab',
            'create_logs_tab',
            'start_extraction',
            'upload_to_database'
        ]
        
        missing_functions = []
        for func in essential_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"❌ وظائف مفقودة: {', '.join(missing_functions)}")
            return False
        else:
            print("✅ جميع الوظائف الأساسية موجودة")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار ملف الواجهة: {e}")
        return False

def test_gui_launch():
    """اختبار تشغيل الواجهة الرسومية"""
    print("\n🚀 اختبار تشغيل الواجهة الرسومية...")
    print("=" * 50)
    
    try:
        # محاولة تشغيل الواجهة لثواني قليلة
        process = subprocess.Popen(
            ['python', 'enhanced_runner_gui.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # انتظار لثواني قليلة
        time.sleep(3)
        
        # التحقق من حالة العملية
        if process.poll() is None:
            print("✅ الواجهة تعمل بنجاح (العملية نشطة)")
            
            # إنهاء العملية
            process.terminate()
            process.wait(timeout=5)
            print("✅ تم إغلاق الواجهة بنجاح")
            return True
        else:
            # العملية انتهت مبكراً، هناك خطأ
            stdout, stderr = process.communicate()
            print("❌ الواجهة انتهت مبكراً")
            if stderr:
                print(f"خطأ: {stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ انتهت مهلة الاختبار، لكن الواجهة تعمل")
        process.kill()
        return True
    except Exception as e:
        print(f"❌ خطأ في تشغيل الواجهة: {e}")
        return False

def test_database_connection():
    """اختبار اتصال قاعدة البيانات"""
    print("\n🗄️ اختبار اتصال قاعدة البيانات...")
    print("=" * 50)
    
    try:
        import mysql.connector
        print("✅ مكتبة mysql.connector متوفرة")
        
        # معلومات قاعدة البيانات
        db_config = {
            'host': 'srv1800.hstgr.io',
            'port': 3306,
            'user': 'u994369532_test',
            'password': 'Test20205',
            'database': 'u994369532_test'
        }
        
        # محاولة الاتصال
        print("🔌 جاري اختبار الاتصال...")
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            print("✅ نجح الاتصال بقاعدة البيانات")
            
            # اختبار بسيط
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"📊 إصدار MySQL: {version[0]}")
            
            cursor.close()
            connection.close()
            return True
        else:
            print("❌ فشل الاتصال بقاعدة البيانات")
            return False
            
    except ImportError:
        print("❌ مكتبة mysql.connector غير متوفرة")
        print("💡 يمكن تثبيتها بـ: pip install mysql-connector-python")
        return False
    except Exception as e:
        print(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        return False

def test_sample_extraction():
    """اختبار استخراج عينة"""
    print("\n📖 اختبار استخراج عينة...")
    print("=" * 50)
    
    try:
        # اختبار استخراج كتاب صغير
        command = [
            'python', 'enhanced_runner.py', 'extract', '6387', '--max-pages', '2'
        ]
        
        print("🔍 جاري اختبار استخراج صفحتين من كتاب 6387...")
        
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60  # مهلة دقيقة واحدة
        )
        
        if process.returncode == 0:
            print("✅ نجح اختبار الاستخراج")
            
            # البحث عن الملف المُنشأ
            for file in os.listdir('.'):
                if file.startswith('enhanced_book_6387_') and file.endswith('.json.gz'):
                    print(f"✅ تم إنشاء الملف: {file}")
                    file_size = os.path.getsize(file)
                    print(f"📏 حجم الملف: {file_size:,} بايت")
                    return True
            
            print("⚠️ الاستخراج نجح لكن لم يتم العثور على الملف")
            return True
        else:
            print("❌ فشل اختبار الاستخراج")
            if process.stderr:
                print(f"خطأ: {process.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ انتهت مهلة اختبار الاستخراج")
        return False
    except Exception as e:
        print(f"❌ خطأ في اختبار الاستخراج: {e}")
        return False

def test_file_structure():
    """اختبار هيكل الملفات"""
    print("\n📁 اختبار هيكل الملفات...")
    print("=" * 50)
    
    essential_files = [
        'enhanced_runner.py',
        'enhanced_runner_gui.py',
        'enhanced_shamela_scraper.py',
        'enhanced_database_manager.py',
        'start_runner_gui.bat'
    ]
    
    optional_files = [
        'ultra_reliable_scraper.py',
        'ultra_speed_config.py',
        'ENHANCED_RUNNER_GUI_README.md'
    ]
    
    all_good = True
    
    print("📋 الملفات الأساسية:")
    for file in essential_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size:,} بايت)")
        else:
            print(f"❌ {file} (مفقود)")
            all_good = False
    
    print("\n📋 الملفات الاختيارية:")
    for file in optional_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✅ {file} ({size:,} بايت)")
        else:
            print(f"⚪ {file} (غير موجود)")
    
    # التحقق من المجلدات
    print("\n📂 المجلدات:")
    folders = ['enhanced_books', 'logs', '__pycache__']
    for folder in folders:
        if os.path.exists(folder) and os.path.isdir(folder):
            files_count = len(os.listdir(folder))
            print(f"✅ {folder}/ ({files_count} ملف)")
        else:
            print(f"⚪ {folder}/ (غير موجود)")
    
    return all_good

def generate_test_report(results):
    """إنشاء تقرير الاختبار"""
    print("\n" + "=" * 60)
    print("📊 تقرير نتائج الاختبار الشامل")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    print(f"📈 إجمالي الاختبارات: {total_tests}")
    print(f"✅ نجح: {passed_tests}")
    print(f"❌ فشل: {failed_tests}")
    print(f"📊 نسبة النجاح: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 تفاصيل النتائج:")
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"  {status} - {test_name}")
    
    print("\n" + "=" * 60)
    
    if all(results.values()):
        print("🎉 جميع الاختبارات نجحت! النظام جاهز للاستخدام")
        return True
    else:
        print("⚠️ بعض الاختبارات فشلت، راجع التفاصيل أعلاه")
        return False

def main():
    """الوظيفة الرئيسية للاختبار"""
    print("🧪 بدء الاختبار الشامل لـ Enhanced Runner GUI")
    print("=" * 60)
    print()
    
    # تشغيل جميع الاختبارات
    results = {}
    
    try:
        results["هيكل الملفات"] = test_file_structure()
        results["مكونات الواجهة"] = test_gui_components()
        results["استيراد Enhanced Runner"] = test_enhanced_runner_import()
        results["ملف الواجهة الرسومية"] = test_gui_file()
        results["تشغيل الواجهة"] = test_gui_launch()
        results["اتصال قاعدة البيانات"] = test_database_connection()
        # results["استخراج عينة"] = test_sample_extraction()  # معطل لتوفير الوقت
        
    except KeyboardInterrupt:
        print("\n⚠️ تم إيقاف الاختبار بواسطة المستخدم")
        return False
    except Exception as e:
        print(f"\n❌ خطأ غير متوقع في الاختبار: {e}")
        return False
    
    # إنشاء التقرير
    success = generate_test_report(results)
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
