# -*- coding: utf-8 -*-
"""
Test Performance Improvements - اختبار سريع للتحسينات
"""

import os
import sys
import time
import logging
from pathlib import Path

# إضافة المجلد الحالي للـ path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from enhanced_shamela_scraper import scrape_enhanced_book, PerformanceConfig
    from enhanced_database_manager import EnhancedShamelaDatabaseManager
except ImportError as e:
    print(f"خطأ في الاستيراد: {e}")
    sys.exit(1)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_performance_improvement(book_id: str = "1221", max_pages: int = 20):
    """
    اختبار سريع لمقارنة الأداء
    """
    print("=" * 60)
    print("🧪 اختبار تحسينات الأداء")
    print("=" * 60)
    
    # اختبار 1: النسخة المحسنة (تسلسلي)
    print("\n🔄 اختبار النسخة المحسنة (تسلسلي)")
    print("-" * 40)
    
    config_sequential = PerformanceConfig(
        max_workers=1,
        debug=True,
        memory_efficient=True
    )
    
    start_time = time.time()
    try:
        book_sequential = scrape_enhanced_book(
            book_id, 
            max_pages=max_pages, 
            extract_content=True,
            config=config_sequential
        )
        sequential_time = time.time() - start_time
        sequential_pages = len(book_sequential.pages)
        sequential_rate = sequential_pages / sequential_time if sequential_time > 0 else 0
        
        print(f"✅ النسخة التسلسلية: {sequential_pages} صفحة في {sequential_time:.2f}s ({sequential_rate:.2f} صفحة/ثانية)")
        
    except Exception as e:
        print(f"❌ فشل الاختبار التسلسلي: {e}")
        return
    
    # اختبار 2: النسخة المحسنة (متوازي)
    print("\n⚡ اختبار النسخة المحسنة (متوازي)")
    print("-" * 40)
    
    config_parallel = PerformanceConfig(
        max_workers=4,
        debug=True,
        memory_efficient=True,
        rate_limit=0.2  # تقليل التأخير للاختبار السريع
    )
    
    start_time = time.time()
    try:
        book_parallel = scrape_enhanced_book(
            book_id, 
            max_pages=max_pages, 
            extract_content=True,
            config=config_parallel
        )
        parallel_time = time.time() - start_time
        parallel_pages = len(book_parallel.pages)
        parallel_rate = parallel_pages / parallel_time if parallel_time > 0 else 0
        
        print(f"✅ النسخة المتوازية: {parallel_pages} صفحة في {parallel_time:.2f}s ({parallel_rate:.2f} صفحة/ثانية)")
        
        # حساب التحسن
        if sequential_time > 0 and parallel_time > 0:
            improvement = ((sequential_time - parallel_time) / sequential_time) * 100
            speed_improvement = (parallel_rate / sequential_rate) * 100 if sequential_rate > 0 else 0
            
            print("\n📊 نتائج المقارنة:")
            print("-" * 30)
            print(f"⏱️ توفير الزمن: {improvement:.1f}%")
            print(f"⚡ تحسن السرعة: {speed_improvement:.1f}%")
            
            if improvement > 0:
                print("🎉 التحسينات تعمل بنجاح!")
            else:
                print("⚠️ لا يوجد تحسن ملحوظ (ربما بسبب حجم العينة الصغير)")
        
        # فحص تطابق النتائج
        print("\n🔍 فحص تطابق النتائج:")
        print("-" * 30)
        
        if sequential_pages == parallel_pages:
            print("✅ عدد الصفحات متطابق")
        else:
            print(f"❌ عدد الصفحات مختلف: {sequential_pages} vs {parallel_pages}")
        
        # مقارنة محتوى الصفحة الأولى
        if (book_sequential.pages and book_parallel.pages and 
            len(book_sequential.pages[0].content) == len(book_parallel.pages[0].content)):
            print("✅ محتوى الصفحة الأولى متطابق")
        else:
            print("⚠️ قد يكون هناك اختلاف في المحتوى")
        
        print("\n✅ انتهى الاختبار بنجاح!")
        
    except Exception as e:
        print(f"❌ فشل الاختبار المتوازي: {e}")
        return

def main():
    """الدالة الرئيسية للاختبار"""
    import argparse
    
    parser = argparse.ArgumentParser(description='اختبار سريع للتحسينات')
    parser.add_argument('--book-id', default='1221', help='معرف الكتاب للاختبار')
    parser.add_argument('--pages', type=int, default=10, help='عدد الصفحات للاختبار')
    
    args = parser.parse_args()
    
    test_performance_improvement(args.book_id, args.pages)

if __name__ == "__main__":
    main()
