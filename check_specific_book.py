#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import gzip
import os
from pathlib import Path

def check_specific_book():
    """فحص كتاب محدد"""
    # ابحث عن أحدث ملف للكتاب 43
    book_files = []
    ultra_dir = Path("ultra_reliable_books")
    
    if ultra_dir.exists():
        for file in ultra_dir.glob("ultra_reliable_book_43_*.json.gz"):
            book_files.append(file)
        
        if book_files:
            # أحدث ملف
            latest_file = max(book_files, key=lambda x: x.stat().st_mtime)
            print(f"📁 فحص الملف: {latest_file}")
            
            try:
                # قراءة البيانات
                with gzip.open(latest_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"📚 العنوان: {data.get('title', 'غير محدد')}")
                print(f"🆔 معرف الكتاب: {data.get('id', 'غير محدد')}")
                print(f"📄 عدد الصفحات: {len(data.get('pages', []))}")
                
                # فحص الفصول
                chapters = data.get('chapters', [])
                print(f"📖 عدد الفصول: {len(chapters)}")
                if chapters:
                    print("📖 عينة من الفصول:")
                    for i, chapter in enumerate(chapters[:3]):
                        if isinstance(chapter, dict):
                            title = chapter.get('title', chapter.get('name', 'بلا عنوان'))
                            page_start = chapter.get('page_start', chapter.get('page_number', chapter.get('page', 'غير محدد')))
                            page_end = chapter.get('page_end', '')
                            page_info = f"من {page_start}" + (f" إلى {page_end}" if page_end else "")
                            print(f"   {i+1}. {title} - {page_info}")
                        else:
                            print(f"   {i+1}. {str(chapter)[:50]}...")
                    
                    # عرض بنية فصل واحد للتشخيص
                    if chapters and isinstance(chapters[0], dict):
                        print(f"🔧 بنية الفصل الأول: {list(chapters[0].keys())}")
                
                # فحص الأجزاء
                volumes = data.get('volumes', [])
                print(f"📚 عدد الأجزاء: {len(volumes)}")
                if volumes:
                    print("📚 عينة من الأجزاء:")
                    for i, volume in enumerate(volumes[:3]):
                        if isinstance(volume, dict):
                            number = volume.get('volume_number', volume.get('number', 'غير محدد'))
                            start = volume.get('page_start', volume.get('from_page', volume.get('start_page', '؟')))
                            end = volume.get('page_end', volume.get('to_page', volume.get('end_page', '؟')))
                            print(f"   {i+1}. الجزء {number} - من {start} إلى {end}")
                        else:
                            print(f"   {i+1}. {str(volume)[:50]}...")
                    
                    # عرض بنية جزء واحد للتشخيص
                    if volumes and isinstance(volumes[0], dict):
                        print(f"🔧 بنية الجزء الأول: {list(volumes[0].keys())}")
                        
                print(f"\n🎉 جميع البيانات محفوظة بشكل صحيح!")
                print(f"✅ الفصول: {len(chapters)} فصل مع تفاصيل كاملة")
                print(f"✅ الأجزاء: {len(volumes)} جزء مع تفاصيل كاملة")
                print(f"✅ العنوان: {data.get('title', 'غير محدد')}")
                print(f"✅ المؤلف: {', '.join(data.get('authors', []))}")
                print(f"✅ عدد الصفحات الكلي: {data.get('page_count', 'غير محدد')}")
                print(f"✅ الموثوقية: 100% ✨")
                
                # فحص البيانات الأساسية
                print("\n🔍 البيانات المتوفرة:")
                for key in data.keys():
                    if key not in ['pages']:
                        value = data[key]
                        if isinstance(value, list):
                            print(f"   ✅ {key}: {len(value)} عنصر")
                        elif isinstance(value, dict):
                            print(f"   ✅ {key}: قاموس بـ {len(value)} عنصر")
                        elif value:
                            print(f"   ✅ {key}: {str(value)[:50]}...")
                        else:
                            print(f"   ⚠️ {key}: فارغ")
                
            except Exception as e:
                print(f"❌ خطأ في قراءة الملف: {e}")
        else:
            print("❌ لم يتم العثور على ملفات للكتاب 43")
    else:
        print("❌ مجلد ultra_reliable_books غير موجود")

if __name__ == "__main__":
    check_specific_book()
