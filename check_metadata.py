#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gzip
import json
import os

def check_book_metadata(filepath):
    """فحص البيانات الوصفية للكتاب المستخرج"""
    
    if not os.path.exists(filepath):
        print(f"❌ الملف غير موجود: {filepath}")
        return
    
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📊 تقرير البيانات الوصفية الكامل")
        print("=" * 60)
        
        # البيانات الأساسية
        print("📚 معلومات الكتاب:")
        print(f"   العنوان: {data.get('title', 'غير محدد')}")
        print(f"   معرف الشاملة: {data.get('shamela_id', 'غير محدد')}")
        
        # المؤلفون
        authors = data.get('authors', [])
        if authors:
            print("✍️ المؤلفون:")
            for i, author in enumerate(authors, 1):
                if isinstance(author, dict):
                    author_name = author.get('name', 'غير محدد')
                else:
                    author_name = str(author)
                print(f"   {i}. {author_name}")
        else:
            print("✍️ المؤلف: غير محدد")
            
        # معلومات النشر
        print("\n📖 معلومات النشر:")
        publisher = data.get('publisher', 'غير محدد')
        print(f"   الناشر: {publisher}")
        
        publication_year = data.get('publication_year', 'غير محدد')
        print(f"   سنة النشر: {publication_year}")
        
        edition = data.get('edition', 'غير محدد')
        if edition and edition != 'غير محدد':
            print(f"   الطبعة: {edition}")
            
        edition_number = data.get('edition_number', 'غير محدد')
        if edition_number and edition_number != 'غير محدد':
            print(f"   رقم الطبعة: {edition_number}")
            
        edition_date_hijri = data.get('edition_date_hijri', 'غير محدد')
        if edition_date_hijri and edition_date_hijri != 'غير محدد':
            print(f"   تاريخ الطبعة الهجري: {edition_date_hijri}")
        
        # معلومات التصنيف
        print(f"\n🏷️ معلومات التصنيف:")
        book_section = data.get('book_section', 'غير محدد')
        print(f"   القسم: {book_section}")
        
        categories = data.get('categories', [])
        if categories:
            print(f"   الفئات: {', '.join(categories)}")
        else:
            print(f"   الفئات: غير محدد")
            
        # معلومات المجلدات والفصول
        page_count = data.get('page_count', 'غير محدد') 
        volume_count = data.get('volume_count', 'غير محدد')
        chapters = data.get('chapters', [])
        volumes = data.get('volumes', [])
        
        print(f"\n📊 معلومات الحجم:")
        print(f"   عدد الصفحات المتوقع: {page_count}")
        print(f"   عدد المجلدات: {volume_count}")
        print(f"   عدد الفصول المستخرجة: {len(chapters)}")
        print(f"   عدد الأجزاء المستخرجة: {len(volumes)}")
        
        # عرض عينة من الفصول
        if chapters:
            print(f"\n📑 عينة من الفصول (أول 5):")
            for i, chapter in enumerate(chapters[:5], 1):
                title = chapter.get('title', 'بدون عنوان')
                page_start = chapter.get('page_start', '?')
                page_end = chapter.get('page_end', '?')
                print(f"   {i}. {title} (ص {page_start}-{page_end})")
        
        # عرض عينة من الأجزاء
        if volumes:
            print(f"\n📚 عينة من الأجزاء (أول 5):")
            for i, volume in enumerate(volumes[:5], 1):
                title = volume.get('title', f"الجزء {volume.get('volume_number', i)}")
                page_start = volume.get('page_start', '?')
                page_end = volume.get('page_end', '?')
                print(f"   {i}. {title} (ص {page_start}-{page_end})")
        
        # الوصف
        description = data.get('description', '')
        if description and description.strip():
            print(f"\n📝 وصف الكتاب:")
            # عرض أول 300 حرف من الوصف
            desc_preview = description[:300] + "..." if len(description) > 300 else description
            print(f"   {desc_preview}")
            
        # رابط المصدر
        source_url = data.get('source_url', 'غير محدد')
        print(f"\n🌐 رابط المصدر: {source_url}")
        
        # بيانات الاستخراج
        metadata = data.get('extraction_metadata', {})
        if metadata:
            print("\n📝 بيانات الاستخراج:")
            for key, value in metadata.items():
                print(f"   {key}: {value}")
        
        # إحصائيات الصفحات
        pages = data.get('pages', [])
        print(f"\n📄 إحصائيات الصفحات:")
        print(f"   إجمالي الصفحات: {len(pages)}")
        
        if pages:
            # حساب إحصائيات المحتوى
            total_words = 0
            arabic_pages = 0
            empty_pages = 0
            
            for page in pages:
                content = page.get('content', '').strip()
                if content:
                    words = len(content.split())
                    total_words += words
                    
                    # فحص المحتوى العربي
                    arabic_chars = sum(1 for c in content if '\u0600' <= c <= '\u06FF')
                    if arabic_chars > 10:  # على الأقل 10 أحرف عربية
                        arabic_pages += 1
                else:
                    empty_pages += 1
            
            print(f"   صفحات بمحتوى عربي: {arabic_pages}/{len(pages)}")
            print(f"   صفحات فارغة: {empty_pages}/{len(pages)}")
            print(f"   إجمالي الكلمات: {total_words:,}")
            print(f"   متوسط الكلمات/صفحة: {total_words/len(pages):.1f}")
        
        # عينة من المحتوى
        if pages:
            print("\n📖 عينة من المحتوى (أول صفحة):")
            print("-" * 40)
            first_content = pages[0].get('content', '')
            preview = first_content[:300] + "..." if len(first_content) > 300 else first_content
            print(preview)
        
        # تحليل جودة البيانات
        print(f"\n🔍 تقييم جودة البيانات:")
        quality_score = 0
        max_score = 180  # زيادة النقاط لتشمل الفصول والأجزاء
        checks = []
        
        # الفحوصات الأساسية (20 نقطة لكل فحص)
        if data.get('title'):
            quality_score += 20
            checks.append("✅ العنوان موجود")
        else:
            checks.append("❌ العنوان مفقود")
            
        if data.get('shamela_id'):
            quality_score += 20
            checks.append("✅ معرف الشاملة موجود")
        else:
            checks.append("❌ معرف الشاملة مفقود")
            
        if authors:
            quality_score += 20
            checks.append("✅ معلومات المؤلف موجودة")
        else:
            checks.append("❌ معلومات المؤلف مفقودة")
            
        if pages:
            quality_score += 20
            checks.append(f"✅ الصفحات موجودة ({len(pages)} صفحة)")
        else:
            checks.append("❌ لا توجد صفحات")
            
        if metadata:
            quality_score += 20
            checks.append("✅ بيانات الاستخراج موجودة")
        else:
            checks.append("❌ بيانات الاستخراج مفقودة")
            
        # الفحوصات الإضافية (10 نقاط لكل فحص)
        if data.get('publisher'):
            quality_score += 10
            checks.append("✅ معلومات الناشر موجودة")
        else:
            checks.append("⚠️ معلومات الناشر مفقودة")
            
        if data.get('description'):
            quality_score += 10
            checks.append("✅ وصف الكتاب موجود")
        else:
            checks.append("⚠️ وصف الكتاب مفقود")
            
        if data.get('categories'):
            quality_score += 10
            checks.append("✅ تصنيفات الكتاب موجودة")
        else:
            checks.append("⚠️ تصنيفات الكتاب مفقودة")
            
        if data.get('source_url'):
            quality_score += 10
            checks.append("✅ رابط المصدر موجود")
        else:
            checks.append("⚠️ رابط المصدر مفقود")
            
        if data.get('publication_year'):
            quality_score += 10
            checks.append("✅ سنة النشر موجودة")
        else:
            checks.append("⚠️ سنة النشر مفقودة")
            
        if data.get('book_section'):
            quality_score += 10
            checks.append("✅ قسم الكتاب موجود")
        else:
            checks.append("⚠️ قسم الكتاب مفقود")
            
        # فحوصات الفصول والأجزاء (10 نقاط لكل فحص)
        if chapters:
            quality_score += 10
            checks.append(f"✅ فصول الكتاب موجودة ({len(chapters)} فصل)")
        else:
            checks.append("⚠️ فصول الكتاب مفقودة")
            
        if volumes:
            quality_score += 10
            checks.append(f"✅ أجزاء الكتاب موجودة ({len(volumes)} جزء)")
        else:
            checks.append("⚠️ أجزاء الكتاب مفقودة")
        
        for check in checks:
            print(f"   {check}")
            
        quality_percentage = round((quality_score / max_score) * 100, 1)
        print(f"\n🎯 درجة جودة البيانات الوصفية: {quality_percentage}% ({quality_score}/{max_score})")
        
        # تصنيف الجودة
        if quality_percentage >= 90:
            quality_rating = "🏆 ممتازة"
        elif quality_percentage >= 75:
            quality_rating = "🥇 جيدة جداً"
        elif quality_percentage >= 60:
            quality_rating = "🥈 جيدة"
        elif quality_percentage >= 45:
            quality_rating = "🥉 مقبولة"
        else:
            quality_rating = "❌ ضعيفة"
            
        print(f"📊 تصنيف الجودة: {quality_rating}")
        
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")

if __name__ == "__main__":
    # فحص الملف المضغوط
    filepath = "ultra_reliable_books/ultra_reliable_book_12106_20250823_125421.json.gz"
    check_book_metadata(filepath)
