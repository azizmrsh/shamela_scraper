#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحليل نتائج الكتاب 43 الجديد مقابل المتوقع
Analysis of book 43 new results vs expected
"""

import json
import os

def analyze_new_file():
    """تحليل الملف الجديد وعرض التحسينات"""
    
    print("📊 تحليل نتائج الكتاب 43 المحسن")
    print("="*45)
    
    try:
        file_path = r"c:\Users\mzyz2\Desktop\BMS-Asset\Bms-project\homeV1\optimized_version\book43_100pages_fixed.json"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # إحصائيات أساسية
        total_pages = len(data.get('pages', []))
        total_words = sum(page.get('word_count', 0) for page in data.get('pages', []))
        pages_with_content = len([p for p in data.get('pages', []) if p.get('word_count', 0) > 0])
        
        print(f"📚 معلومات أساسية:")
        print(f"   • العنوان: {data.get('title', 'غير متوفر')}")
        print(f"   • المؤلف: {data.get('authors', [{'name': 'غير متوفر'}])[0].get('name', 'غير متوفر')}")
        print(f"   • عدد الصفحات: {total_pages}")
        print(f"   • إجمالي الكلمات: {total_words:,}")
        print(f"   • متوسط الكلمات/صفحة: {total_words/max(total_pages,1):.1f}")
        print(f"   • صفحات تحتوي على محتوى: {pages_with_content}/{total_pages}")
        print(f"   • نسبة النجاح: {(pages_with_content/max(total_pages,1))*100:.1f}%")
        
        # البيانات المحسنة
        print(f"\n🎯 البيانات المحسنة:")
        print(f"   • الناشر: {data.get('publisher', {}).get('name', 'غير متوفر') if data.get('publisher') else 'غير متوفر'}")
        print(f"   • القسم: {data.get('book_section', {}).get('name', 'غير متوفر') if data.get('book_section') else 'غير متوفر'}")
        print(f"   • عدد الفصول: {len(data.get('index', []))}")
        print(f"   • عدد الأجزاء: {len(data.get('volumes', []))}")
        print(f"   • الترقيم الأصلي: {'نعم' if data.get('has_original_pagination') else 'لا'}")
        print(f"   • عدد الصفحات الداخلي: {data.get('page_count_internal', 'غير متوفر')}")
        print(f"   • عدد الصفحات المطبوع: {data.get('page_count_printed', 'غير متوفر')}")
        
        # عينة من المحتوى
        if data.get('pages') and len(data['pages']) > 0:
            first_page = data['pages'][0]
            print(f"\n📝 عينة من الصفحة الأولى:")
            print("-" * 40)
            content_sample = first_page.get('content', '')[:300]
            print(content_sample)
            if len(first_page.get('content', '')) > 300:
                print("...")
            print(f"\n   • عدد كلمات الصفحة الأولى: {first_page.get('word_count', 0)}")
            print(f"   • عدد أحرف الصفحة الأولى: {len(first_page.get('content', ''))}")
        
        # إحصائيات متقدمة
        if pages_with_content > 0:
            words_per_page = [p.get('word_count', 0) for p in data.get('pages', []) if p.get('word_count', 0) > 0]
            print(f"\n📈 إحصائيات متقدمة:")
            print(f"   • أكبر عدد كلمات في صفحة: {max(words_per_page)}")
            print(f"   • أقل عدد كلمات في صفحة: {min(words_per_page)}")
            print(f"   • متوسط كلمات الصفحات النشطة: {sum(words_per_page)/len(words_per_page):.1f}")
        
        # مقارنة مع النتائج المتوقعة من السكربت الأصلي
        print(f"\n🔍 مقارنة مع المتوقع:")
        print("-" * 30)
        
        # نتائج متوقعة من السكربت الأصلي
        expected_words_per_page = 500  # متوقع من السكربت الأصلي
        expected_total_words = expected_words_per_page * total_pages
        
        actual_avg_words = total_words / max(total_pages, 1)
        
        if actual_avg_words >= expected_words_per_page * 0.5:  # 50% من المتوقع على الأقل
            print(f"✅ جودة الاستخراج: جيدة ({actual_avg_words:.1f} vs {expected_words_per_page} متوقع)")
        elif actual_avg_words >= expected_words_per_page * 0.2:  # 20% من المتوقع
            print(f"⚠️  جودة الاستخراج: متوسطة ({actual_avg_words:.1f} vs {expected_words_per_page} متوقع)")
        else:
            print(f"❌ جودة الاستخراج: منخفضة ({actual_avg_words:.1f} vs {expected_words_per_page} متوقع)")
        
        # تقييم التحسينات
        print(f"\n🚀 تقييم التحسينات:")
        print("-" * 25)
        
        improvements = []
        if data.get('publisher'):
            improvements.append("✅ استخراج بيانات الناشر")
        if data.get('book_section'):
            improvements.append("✅ استخراج قسم الكتاب")
        if len(data.get('index', [])) > 10:
            improvements.append(f"✅ فهرس شامل ({len(data.get('index', []))} فصل)")
        if len(data.get('volumes', [])) > 1:
            improvements.append(f"✅ تقسيم الأجزاء ({len(data.get('volumes', []))} جزء)")
        if data.get('has_original_pagination'):
            improvements.append("✅ دعم الترقيم الأصلي")
        
        if improvements:
            for improvement in improvements:
                print(f"   {improvement}")
        else:
            print("   ⚠️ لم يتم العثور على تحسينات واضحة")
        
        # الخلاصة
        print(f"\n🎉 الخلاصة:")
        print("="*20)
        if actual_avg_words >= 10 and pages_with_content >= total_pages * 0.9:
            print("✅ السكربت المحسن يعمل بكفاءة عالية!")
            print("✅ استخراج المحتوى نجح بشكل ممتاز")
            print("✅ البيانات الإضافية متوفرة")
        elif actual_avg_words >= 5 and pages_with_content >= total_pages * 0.7:
            print("⚠️ السكربت المحسن يعمل بكفاءة متوسطة")
            print("⚠️ استخراج المحتوى نجح جزئياً")
        else:
            print("❌ السكربت المحسن يحتاج مزيد من التحسين")
            print("❌ استخراج المحتوى لم ينجح بالشكل المطلوب")
        
        # حجم الملف
        file_size = os.path.getsize(file_path)
        print(f"\n📁 معلومات الملف:")
        print(f"   • حجم الملف: {file_size/1024:.1f} KB")
        print(f"   • متوسط الحجم/صفحة: {file_size/(total_pages*1024):.2f} KB")
        
    except Exception as e:
        print(f"❌ خطأ في تحليل الملف: {e}")
        return

if __name__ == "__main__":
    analyze_new_file()
    print("\n" + "="*45)
    print("🔚 انتهى التحليل!")
