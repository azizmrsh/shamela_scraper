#!/usr/bin/env python3
"""
اختبار سرعة السكربت مع أحجام كتب مختلفة
"""

import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from enhanced_shamela_scraper import scrape_enhanced_book
from ultra_speed_config import get_optimal_config_for_book_size

def benchmark_book_speed(book_id, page_counts, book_title=""):
    """اختبار سرعة كتاب مع أحجام مختلفة"""
    results = []
    
    print(f"\n🏎️ اختبار سرعة الكتاب {book_id} - {book_title}")
    print("=" * 70)
    
    for pages in page_counts:
        print(f"\n📖 اختبار {pages} صفحة...")
        
        # الحصول على التكوين الأمثل
        config = get_optimal_config_for_book_size(pages)
        
        print(f"   ⚙️ التكوين: workers={config.max_workers}, async={config.use_async}, multiprocess_threshold={config.multiprocessing_threshold}")
        
        # قياس الوقت
        start_time = time.time()
        try:
            book = scrape_enhanced_book(book_id, max_pages=pages, extract_content=True, config=config)
            elapsed = time.time() - start_time
            
            actual_pages = len(book.pages)
            speed = actual_pages / elapsed if elapsed > 0 else 0
            words = sum(p.word_count for p in book.pages)
            words_per_second = words / elapsed if elapsed > 0 else 0
            
            result = {
                'pages': actual_pages,
                'time': elapsed,
                'speed': speed,
                'words': words,
                'words_per_second': words_per_second,
                'config_type': 'multiprocessing' if config.use_async and pages >= config.multiprocessing_threshold else 'async' if config.use_async else 'threading'
            }
            results.append(result)
            
            print(f"   ✅ {actual_pages} صفحة في {elapsed:.2f}ث = {speed:.2f} صفحة/ثانية")
            print(f"   📊 {words:,} كلمة = {words_per_second:.0f} كلمة/ثانية")
            print(f"   🔧 طريقة: {result['config_type']}")
            
        except Exception as e:
            print(f"   ❌ خطأ: {str(e)}")
            results.append({'error': str(e)})
        
        # انتظار قصير بين الاختبارات
        time.sleep(2)
    
    return results

def print_summary_table(results, page_counts):
    """طباعة جدول ملخص النتائج"""
    print("\n" + "=" * 80)
    print("📊 ملخص النتائج:")
    print("=" * 80)
    print(f"{'الصفحات':<10} {'الوقت (ث)':<12} {'السرعة':<15} {'الكلمات':<12} {'الطريقة':<15}")
    print("-" * 80)
    
    for i, result in enumerate(results):
        if 'error' in result:
            print(f"{page_counts[i]:<10} {'خطأ':<12} {'--':<15} {'--':<12} {'--':<15}")
        else:
            print(f"{result['pages']:<10} {result['time']:<12.2f} {result['speed']:<15.2f} {result['words']:<12,} {result['config_type']:<15}")

def estimate_large_book_time(target_pages, reference_results):
    """تقدير وقت كتاب كبير بناء على النتائج المرجعية"""
    if not reference_results or 'error' in reference_results[-1]:
        return None
    
    # أخذ أحدث نتيجة كمرجع
    ref = reference_results[-1]
    ref_speed = ref['speed']
    
    # تعديل السرعة للكتب الكبيرة (عادة تقل قليلاً)
    if target_pages > 1000:
        adjusted_speed = ref_speed * 0.8  # تقليل 20% للكتب الضخمة
    else:
        adjusted_speed = ref_speed
    
    estimated_time = target_pages / adjusted_speed
    estimated_minutes = estimated_time / 60
    
    return {
        'pages': target_pages,
        'estimated_time': estimated_time,
        'estimated_minutes': estimated_minutes,
        'estimated_speed': adjusted_speed
    }

if __name__ == "__main__":
    # اختبار مع كتاب متوسط الحجم
    print("🚀 بدء اختبار شامل للسرعة")
    
    # الكتاب 43 - كتاب للاختبار
    small_results = benchmark_book_speed("43", [10, 20, 30], "كتاب رقم 43")
    print_summary_table(small_results, [10, 20, 30])
    
    # تقدير للكتب الكبيرة
    estimates = []
    for pages in [100, 500, 1000, 2000, 5000]:
        estimate = estimate_large_book_time(pages, small_results)
        if estimate:
            estimates.append(estimate)
    
    print("\n" + "=" * 80)
    print("🔮 تقديرات للكتب الكبيرة (بناء على النتائج الحالية):")
    print("=" * 80)
    print(f"{'الصفحات':<10} {'الوقت المقدر':<15} {'بالدقائق':<12} {'السرعة المقدرة':<15}")
    print("-" * 80)
    
    for est in estimates:
        minutes = f"{est['estimated_minutes']:.1f}د"
        print(f"{est['pages']:<10} {est['estimated_time']:<15.1f} {minutes:<12} {est['estimated_speed']:<15.2f}")
