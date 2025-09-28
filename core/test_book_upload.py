#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
اختبار سريع لرفع الكتاب 21739 بعد إصلاح مشاكل قاعدة البيانات
"""

import sys
import os
import json
from pathlib import Path

# إضافة مسار core إلى sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_database_manager import EnhancedShamelaDatabaseManager
from enhanced_shamela_scraper import scrape_enhanced_book


def test_book_upload():
    """اختبار رفع الكتاب 21739"""
    
    book_id = 21739
    
    print(f"🔍 بدء اختبار رفع الكتاب {book_id}")
    
    # 1. البحث عن ملف JSON المحفوظ مسبقاً
    enhanced_books_dir = Path(__file__).parent / "enhanced_books"
    json_files = list(enhanced_books_dir.glob(f"enhanced_book_{book_id}_*.json"))
    
    if json_files:
        # استخدام أحدث ملف
        latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 تم العثور على ملف محفوظ: {latest_file}")
        
        # تحميل البيانات
        with open(latest_file, 'r', encoding='utf-8') as f:
            book_data = json.load(f)
        
        print(f"📊 الكتاب: {book_data.get('title', 'غير محدد')}")
        print(f"📄 عدد الصفحات: {len(book_data.get('pages', []))}")
        print(f"📑 عدد الفصول: {len(book_data.get('index', []))}")
        
    else:
        print(f"📖 لم يتم العثور على ملف محفوظ، سيتم استخراج الكتاب من جديد...")
        # استخراج الكتاب  
        book = scrape_enhanced_book(str(book_id))
        if not book:
            print("❌ فشل في استخراج الكتاب")
            return False
        
        # تحويل الكتاب إلى قاموس
        book_data = {
            'title': book.title,
            'pages': [
                {
                    'page_number': p.page_number,
                    'content': p.content,
                    'internal_index': p.internal_index,
                    'original_page_number': p.original_page_number,
                    'word_count': p.word_count,
                    'html_content': p.html_content,
                    'volume_number': p.volume_number,
                    'printed_missing': p.printed_missing
                }
                for p in book.pages
            ],
            'index': [
                {
                    'title': c.title,
                    'order': c.order,
                    'page_number': c.page_number,
                    'page_end': c.page_end,
                    'level': c.level,
                    'volume_number': c.volume_number
                }
                for c in book.index
            ]
        }
    
    # 2. رفع البيانات إلى قاعدة البيانات
    try:
        # إعدادات قاعدة البيانات الافتراضية
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'shamela_enhanced',
            'port': 3306,
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        db_manager = EnhancedShamelaDatabaseManager(db_config)
        
        print(f"🔗 الاتصال بقاعدة البيانات...")
        db_manager.connect()
        
        print(f"🏗️ إنشاء الجداول...")
        db_manager.create_tables()
        
        print(f"💾 رفع البيانات...")
        result = db_manager.save_book_from_json(book_data)
        
        if result:
            print(f"✅ تم رفع الكتاب بنجاح!")
            print(f"🆔 معرف الكتاب: {result.get('book_id')}")
            print(f"📄 عدد الصفحات المرفوعة: {result.get('total_pages', 0)}")
            print(f"📑 عدد الفصول المرفوعة: {result.get('total_chapters', 0)}")
            return True
        else:
            print(f"❌ فشل في رفع الكتاب")
            return False
            
    except Exception as e:
        print(f"❌ خطأ في رفع الكتاب: {e}")
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.disconnect()


if __name__ == "__main__":
    success = test_book_upload()
    if success:
        print(f"🎉 تم اختبار الرفع بنجاح!")
    else:
        print(f"💥 فشل اختبار الرفع!")