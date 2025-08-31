#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import json

def check_specific_file():
    """فحص ملف محدد للتأكد من الفصول والأجزاء"""
    
    filepath = r'ultra_reliable_books\ultra_reliable_book_43_20250823_135351.json.gz'
    
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 فحص الملف الجديد مع الفصول والأجزاء:")
        print("=" * 60)
        
        title = data.get('title', 'غير محدد')
        shamela_id = data.get('shamela_id', 'غير محدد')
        print(f"📚 العنوان: {title}")
        print(f"🆔 معرف الكتاب: {shamela_id}")
        
        # فحص الفصول
        chapters = data.get('chapters', [])
        print(f"\n📑 الفصول المستخرجة: {len(chapters)}")
        if chapters:
            print("أول 5 فصول:")
            for i, chapter in enumerate(chapters[:5], 1):
                title = chapter.get('title', 'بدون عنوان')
                page_start = chapter.get('page_start', '?')
                page_end = chapter.get('page_end', '?')
                print(f"   {i}. {title} (ص {page_start}-{page_end})")
        
        # فحص الأجزاء
        volumes = data.get('volumes', [])
        print(f"\n📚 الأجزاء المستخرجة: {len(volumes)}")
        if volumes:
            print("أول 5 أجزاء:")
            for i, volume in enumerate(volumes[:5], 1):
                title = volume.get('title', f"الجزء {volume.get('volume_number', i)}")
                page_start = volume.get('page_start', '?')
                page_end = volume.get('page_end', '?')
                volume_number = volume.get('volume_number', i)
                print(f"   {i}. الجزء {volume_number}: {title} (ص {page_start}-{page_end})")
        
        # فحص البيانات الإضافية
        metadata = data.get('extraction_metadata', {})
        total_chapters = metadata.get('total_chapters', 0)
        total_volumes = metadata.get('total_volumes', 0)
        scraper_version = metadata.get('scraper_version', 'غير محدد')
        
        print(f"\n📊 معلومات الميتاداتا:")
        print(f"   إجمالي الفصول: {total_chapters}")
        print(f"   إجمالي الأجزاء: {total_volumes}")
        print(f"   إصدار السكريبت: {scraper_version}")
        
        # فحص الصفحات
        pages = data.get('pages', [])
        print(f"\n📄 الصفحات المستخرجة: {len(pages)}")
        
        # تحقق من جميع المفاتيح المتاحة
        print(f"\n🔍 جميع المفاتيح في الملف:")
        for key in data.keys():
            if key == 'pages':
                print(f"   - {key}: {len(data[key])} عنصر")
            elif isinstance(data[key], list):
                print(f"   - {key}: قائمة من {len(data[key])} عنصر")
            elif isinstance(data[key], dict):
                print(f"   - {key}: قاموس من {len(data[key])} عنصر")
            else:
                print(f"   - {key}: {data[key]}")
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")

if __name__ == "__main__":
    check_specific_file()
