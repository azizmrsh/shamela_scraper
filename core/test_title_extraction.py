#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار سريع لوظيفة استخراج العنوان
"""

import sys
import os
import subprocess
import tempfile
import json

def test_title_extraction(book_id):
    """اختبار استخراج عنوان كتاب محدد"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"🧪 اختبار استخراج عنوان الكتاب {book_id}...")
    
    try:
        # إنشاء مجلد مؤقت
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_output_path = os.path.join(temp_dir, f"temp_book_{book_id}.json")
            
            # أمر لاستخراج معلومات الكتاب الأساسية فقط
            command = [
                sys.executable,
                os.path.join(current_dir, "enhanced_shamela_scraper.py"),
                str(book_id),
                "--max-pages", "1",  # صفحة واحدة فقط
                "--output", temp_output_path  # حفظ في المجلد المؤقت
            ]
            
            print(f"🔧 الأمر: {' '.join(command)}")
            
            # إعداد متغيرات البيئة
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # تشغيل الأمر
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=current_dir,
                env=env,
                timeout=120
            )
            
            print(f"📤 رمز الخروج: {result.returncode}")
            print(f"📄 طول المخرجات: {len(result.stdout)} حرف")
            print(f"📄 طول الأخطاء: {len(result.stderr)} حرف")
            
            title = None
            
            if result.returncode == 0:
                # محاولة قراءة الملف المؤقت
                if os.path.exists(temp_output_path):
                    print(f"✅ تم إنشاء الملف المؤقت: {temp_output_path}")
                    try:
                        with open(temp_output_path, 'r', encoding='utf-8') as f:
                            book_data = json.load(f)
                            title = book_data.get('title', '')
                            if title:
                                print(f"📚 العنوان من الملف: '{title}'")
                                return title
                            else:
                                print("⚠️ لا يوجد عنوان في ملف JSON")
                    except Exception as e:
                        print(f"❌ خطأ في قراءة ملف JSON: {e}")
                else:
                    print("❌ لم يتم إنشاء الملف المؤقت")
                
                # البحث في المخرجات
                print("🔍 البحث عن العنوان في المخرجات...")
                output_lines = result.stdout.split('\\n')
                for i, line in enumerate(output_lines):
                    if '📚 العنوان:' in line:
                        title = line.split('📚 العنوان:')[1].strip()
                        print(f"📚 العنوان من المخرجات (سطر {i+1}): '{title}'")
                        return title
                    elif 'العنوان:' in line:
                        title = line.split('العنوان:')[1].strip()
                        print(f"📚 العنوان من المخرجات (سطر {i+1}): '{title}'")
                        return title
                
                # طباعة عينة من المخرجات للفحص
                print("📄 أول 10 أسطر من المخرجات:")
                for i, line in enumerate(output_lines[:10]):
                    print(f"  {i+1}: {line}")
                
                print("📄 آخر 10 أسطر من المخرجات:")
                for i, line in enumerate(output_lines[-10:]):
                    print(f"  {len(output_lines)-10+i+1}: {line}")
            
            else:
                print(f"❌ فشل الأمر برمز {result.returncode}")
                if result.stderr:
                    print(f"🔍 الأخطاء: {result.stderr[:500]}")
                if result.stdout:
                    print(f"🔍 المخرجات: {result.stdout[:500]}")
            
            return None
            
    except subprocess.TimeoutExpired:
        print(f"⏰ انتهت مهلة الاستخراج (120 ثانية)")
        return None
    except Exception as e:
        print(f"❌ خطأ عام: {str(e)}")
        return None

if __name__ == "__main__":
    # اختبار مع كتاب محدد
    book_id = 1  # يمكن تغيير هذا الرقم
    if len(sys.argv) > 1:
        book_id = int(sys.argv[1])
    
    print(f"🚀 بدء اختبار استخراج العنوان للكتاب {book_id}")
    title = test_title_extraction(book_id)
    
    if title:
        print(f"🎉 نجح الاختبار! العنوان: '{title}'")
        
        # اختبار تنظيف العنوان
        import re
        def clean_book_title_for_filename(title):
            if not title:
                return "كتاب_غير_محدد"
                
            # استبدال الأحرف غير المسموحة في أسماء الملفات
            invalid_chars = '<>:"/\\\\|?*'
            cleaned = title
            for char in invalid_chars:
                cleaned = cleaned.replace(char, '_')
            
            # تنظيف المسافات المتعددة والنقاط
            cleaned = re.sub(r'\\s+', ' ', cleaned)
            cleaned = re.sub(r'\\.+', '.', cleaned)
            cleaned = cleaned.strip('. ')
            
            # تحديد الطول الأقصى
            max_length = 150
            if len(cleaned) > max_length:
                cleaned = cleaned[:max_length].rstrip('. ')
            
            if not cleaned:
                cleaned = "كتاب_غير_محدد"
            
            # استبدال المسافات بـ underscores
            cleaned = cleaned.replace(' ', '_')
                
            return cleaned
        
        cleaned_title = clean_book_title_for_filename(title)
        print(f"🧹 العنوان المنظف: '{cleaned_title}'")
        print(f"📄 اسم الملف النهائي: '{cleaned_title}.json'")
    else:
        print("❌ فشل في استخراج العنوان")