#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""عرض إحصائيات الكتاب المحمل"""

import json

def show_book_stats():
    with open('book43_100pages.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("🎉 تم تحميل الكتاب بنجاح!")
    print("="*50)
    print(f"📚 العنوان: {data['title']}")
    print(f"👨‍🎓 المؤلف: {data['authors'][0]['name']}")
    print(f"📂 القسم: {data['book_section']['name']}")
    print(f"🆔 معرف الكتاب: {data['shamela_id']}")
    print("="*50)
    
    print("📊 الإحصائيات:")
    print(f"📄 عدد الصفحات المحملة: {len(data['pages'])}")
    print(f"📑 عدد الفصول: {len(data['index'])}")
    print(f"📚 عدد الأجزاء: {len(data['volumes'])}")
    print(f"📝 إجمالي الصفحات في الكتاب: {data['page_count']:,}")
    print(f"📖 عدد الصفحات المطبوعة: {data['page_count_printed']}")
    
    # حساب الكلمات
    total_words = sum(page.get('word_count', 0) for page in data['pages'])
    total_chars = sum(page.get('char_count', 0) for page in data['pages'])
    
    print(f"🧮 إجمالي عدد الكلمات: {total_words:,}")
    print(f"📊 معدل الكلمات لكل صفحة: {total_words // len(data['pages'])}")
    print(f"📝 إجمالي عدد الأحرف: {total_chars:,}")
    
    # إحصائيات الأداء من معلومات المعالجة
    if 'processing_stats' in data:
        stats = data['processing_stats']
        print("="*50)
        print("⚡ إحصائيات الأداء:")
        print(f"⏱️ الزمن الكلي: {stats.get('processing_time_seconds', 0):.2f} ثانية")
        print(f"🚀 السرعة: {stats.get('pages_per_second', 0):.2f} صفحة/ثانية")
        print(f"📦 طريقة المعالجة: {stats.get('processing_method', 'غير محدد')}")
        
    print("="*50)
    print("✅ تم تحليل الكتاب بنجاح!")

if __name__ == "__main__":
    show_book_stats()
