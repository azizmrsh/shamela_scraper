#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import json

def check_latest_file():
    """فحص أحدث ملف مُستخرج"""
    
    filepath = r'ultra_reliable_books\ultra_reliable_book_12106_20250823_131654.json.gz'
    
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 إحصائيات الملف الفعلية:")
        print(f"   العنوان: {data.get('title', 'غير محدد')}")
        print(f"   عدد الصفحات الفعلي: {len(data.get('pages', []))}")
        
        # تحقق من تاريخ الاستخراج
        metadata = data.get('extraction_metadata', {})
        print(f"   تاريخ الاستخراج: {metadata.get('extraction_date', 'غير محدد')}")
        print(f"   إجمالي الكلمات: {metadata.get('total_words', 'غير محدد')}")
        print(f"   إصدار السكريبت: {metadata.get('scraper_version', 'غير محدد')}")
        
        # عرض أول صفحتين
        pages = data.get('pages', [])
        if pages:
            print(f"\n📖 أول صفحتين:")
            for i, page in enumerate(pages[:2], 1):
                content = page.get('content', '')[:100]
                page_num = page.get('page_number', i)
                word_count = page.get('word_count', 0)
                print(f"   الصفحة {page_num} ({word_count} كلمة): {content}...")
                
        # فحص البيانات الوصفية المحسنة
        print(f"\n🔍 البيانات الوصفية المحسنة:")
        print(f"   الناشر: {data.get('publisher', 'غير محدد')}")
        print(f"   القسم: {data.get('book_section', 'غير محدد')}")  
        print(f"   الوصف: {'موجود' if data.get('description') else 'غير محدد'}")
        print(f"   رابط المصدر: {data.get('source_url', 'غير محدد')}")
        print(f"   ترقيم أصلي: {data.get('has_original_pagination', False)}")
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")

if __name__ == "__main__":
    check_latest_file()
