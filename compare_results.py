#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مقارنة نتائج الملف القديم والجديد للكتاب 43
Comparison of old vs new results for book 43
"""

import json

def compare_files():
    """مقارنة الملفين وعرض الإحصائيات"""
    
    print("🔍 مقارنة نتائج استخراج الكتاب 43")
    print("="*50)
    
    # الملف القديم
    try:
        with open('book43_100pages.json', 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        
        old_total_words = sum(page.get('word_count', 0) for page in old_data.get('pages', []))
        old_first_page_length = len(old_data.get('pages', [{}])[0].get('content', '')) if old_data.get('pages') else 0
        
        print("📄 الملف القديم (book43_100pages.json):")
        print(f"   • إجمالي الكلمات: {old_total_words}")
        print(f"   • طول الصفحة الأولى: {old_first_page_length} حرف")
        print(f"   • متوسط الكلمات/صفحة: {old_total_words/100:.1f}")
        print(f"   • متوسط الأحرف/صفحة: {old_first_page_length:.1f}")
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف القديم: {e}")
        return
    
    # الملف الجديد
    try:
        with open('book43_100pages_fixed.json', 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        
        new_total_words = sum(page.get('word_count', 0) for page in new_data.get('pages', []))
        new_first_page_length = len(new_data.get('pages', [{}])[0].get('content', '')) if new_data.get('pages') else 0
        
        print("\n📄 الملف الجديد (book43_100pages_fixed.json):")
        print(f"   • إجمالي الكلمات: {new_total_words}")
        print(f"   • طول الصفحة الأولى: {new_first_page_length} حرف")
        print(f"   • متوسط الكلمات/صفحة: {new_total_words/100:.1f}")
        print(f"   • متوسط الأحرف/صفحة: {new_first_page_length:.1f}")
        
        # المقارنة
        print("\n🔍 نتائج المقارنة:")
        print("="*30)
        
        if new_total_words > old_total_words:
            improvement = ((new_total_words - old_total_words) / old_total_words) * 100
            print(f"✅ تحسن عدد الكلمات: +{improvement:.1f}%")
        else:
            decline = ((old_total_words - new_total_words) / old_total_words) * 100
            print(f"❌ انخفاض عدد الكلمات: -{decline:.1f}%")
        
        if new_first_page_length > old_first_page_length:
            improvement = ((new_first_page_length - old_first_page_length) / old_first_page_length) * 100
            print(f"✅ تحسن طول المحتوى: +{improvement:.1f}%")
        else:
            decline = ((old_first_page_length - new_first_page_length) / old_first_page_length) * 100
            print(f"❌ انخفاض طول المحتوى: -{decline:.1f}%")
        
        # عرض عينة من المحتوى
        print(f"\n📝 عينة من الصفحة الأولى (الملف الجديد):")
        print("-" * 50)
        first_page_content = new_data.get('pages', [{}])[0].get('content', '')[:200]
        print(first_page_content[:200])
        if len(first_page_content) > 200:
            print("...")
        
        # فحص جودة البيانات
        print(f"\n📊 تحليل جودة البيانات:")
        print("-" * 30)
        
        pages_with_content = len([p for p in new_data.get('pages', []) if p.get('word_count', 0) > 0])
        print(f"   • صفحات تحتوي على محتوى: {pages_with_content}/100")
        print(f"   • نسبة النجاح: {(pages_with_content/100)*100:.1f}%")
        
        # التحقق من استخراج البيانات الإضافية
        print(f"\n🎯 البيانات المحسنة:")
        print("-" * 25)
        print(f"   • العنوان: {new_data.get('title', 'غير متوفر')[:50]}")
        print(f"   • المؤلف: {new_data.get('authors', [{'name': 'غير متوفر'}])[0].get('name', 'غير متوفر')}")
        print(f"   • الناشر: {new_data.get('publisher', {}).get('name', 'غير متوفر') if new_data.get('publisher') else 'غير متوفر'}")
        print(f"   • القسم: {new_data.get('book_section', {}).get('name', 'غير متوفر') if new_data.get('book_section') else 'غير متوفر'}")
        print(f"   • عدد الفصول: {len(new_data.get('index', []))}")
        print(f"   • عدد الأجزاء: {len(new_data.get('volumes', []))}")
        print(f"   • الترقيم الأصلي: {'نعم' if new_data.get('has_original_pagination') else 'لا'}")
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف الجديد: {e}")
        return

if __name__ == "__main__":
    compare_files()
    print("\n" + "="*50)
    print("🎉 انتهت المقارنة!")
