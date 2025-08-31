#!/usr/bin/env python3
"""
اختبار شامل للتحسينات المتقدمة المدمجة في enhanced_shamela_scraper.py
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def run_test(book_id, mode_description, args_list, expected_improvement=None):
    """تشغيل اختبار واحد وقياس الأداء"""
    print(f"\n{'='*60}")
    print(f"🧪 اختبار: {mode_description}")
    print(f"📖 كتاب: {book_id}")
    print(f"⚙️ المعاملات: {' '.join(args_list)}")
    print('='*60)
    
    cmd = ['python', 'enhanced_shamela_scraper.py', book_id] + args_list
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        end_time = time.time()
        
        if result.returncode == 0:
            # استخراج الإحصائيات من المخرجات
            output_lines = result.stdout.split('\n')
            pages_count = 0
            speed = 0.0
            
            for line in output_lines:
                if "عدد الصفحات:" in line:
                    try:
                        pages_count = int(line.split(':')[1].strip())
                    except:
                        pass
                elif "السرعة:" in line and "صفحة/ثانية" in line:
                    try:
                        speed = float(line.split(':')[1].replace('صفحة/ثانية', '').strip())
                    except:
                        pass
            
            elapsed = end_time - start_time
            print(f"✅ نجح الاختبار!")
            print(f"📄 الصفحات: {pages_count}")
            print(f"⏱️ الزمن: {elapsed:.2f} ثانية")
            print(f"⚡ السرعة: {speed:.2f} صفحة/ثانية")
            
            if expected_improvement:
                print(f"🎯 التحسين المتوقع: {expected_improvement}")
            
            return {
                'success': True,
                'pages': pages_count,
                'time': elapsed,
                'speed': speed,
                'mode': mode_description
            }
            
        else:
            print(f"❌ فشل الاختبار!")
            print(f"خطأ: {result.stderr}")
            return {
                'success': False,
                'error': result.stderr,
                'mode': mode_description
            }
            
    except Exception as e:
        print(f"❌ استثناء في الاختبار: {e}")
        return {
            'success': False,
            'error': str(e),
            'mode': mode_description
        }

def main():
    """الوظيفة الرئيسية لاختبار التحسينات"""
    
    print("🔬 اختبار التحسينات المتقدمة المدمجة")
    print("="*60)
    
    # كتاب صغير للاختبار السريع
    test_book_id = "BK009002"
    
    # قائمة الاختبارات
    tests = [
        {
            'description': 'الوضع التقليدي المحسن',
            'args': ['--force-traditional', '--max-pages', '50', '--debug'],
            'expected': 'خط الأساس'
        },
        {
            'description': 'الوضع غير المتزامن (Async)',
            'args': ['--use-async', '--max-pages', '50', '--debug', '--aiohttp-workers', '4'],
            'expected': '300-500% تحسين'
        },
        {
            'description': 'معالج lxml السريع',
            'args': ['--use-lxml', '--max-pages', '50', '--debug'],
            'expected': '50-100% تحسين في التحليل'
        },
        {
            'description': 'مجموعة التحسينات الكاملة',
            'args': ['--use-async', '--use-lxml', '--max-pages', '50', '--debug', 
                    '--aiohttp-workers', '6', '--async-batch-size', '20'],
            'expected': '400-600% تحسين إجمالي'
        }
    ]
    
    results = []
    
    # تشغيل الاختبارات
    for test in tests:
        result = run_test(
            test_book_id,
            test['description'],
            test['args'],
            test['expected']
        )
        results.append(result)
        
        # توقف قصير بين الاختبارات
        time.sleep(2)
    
    # تحليل النتائج
    print("\n" + "="*60)
    print("📊 تحليل النتائج النهائية")
    print("="*60)
    
    successful_tests = [r for r in results if r['success']]
    
    if not successful_tests:
        print("❌ لا توجد اختبارات ناجحة للمقارنة")
        return
    
    # إيجاد الخط الأساس (التقليدي)
    baseline = None
    for result in successful_tests:
        if 'تقليدي' in result['mode']:
            baseline = result
            break
    
    if not baseline:
        baseline = successful_tests[0]
        print(f"⚠️ استخدام {baseline['mode']} كخط أساس")
    
    print(f"📏 خط الأساس: {baseline['mode']}")
    print(f"   📄 صفحات: {baseline['pages']}")
    print(f"   ⏱️ زمن: {baseline['time']:.2f}s")
    print(f"   ⚡ سرعة: {baseline['speed']:.2f} صفحة/ثانية")
    print()
    
    # مقارنة النتائج
    for result in successful_tests:
        if result == baseline:
            continue
            
        if result['time'] > 0 and baseline['time'] > 0:
            speed_improvement = (baseline['time'] / result['time'] - 1) * 100
            throughput_improvement = (result['speed'] / baseline['speed'] - 1) * 100
            
            print(f"🚀 {result['mode']}:")
            print(f"   📄 صفحات: {result['pages']}")
            print(f"   ⏱️ زمن: {result['time']:.2f}s ({speed_improvement:+.1f}%)")
            print(f"   ⚡ سرعة: {result['speed']:.2f} صفحة/ثانية ({throughput_improvement:+.1f}%)")
            print()
    
    # الخلاصة
    best_result = max(successful_tests, key=lambda x: x['speed'])
    print(f"🏆 أفضل أداء: {best_result['mode']}")
    print(f"   ⚡ السرعة القصوى: {best_result['speed']:.2f} صفحة/ثانية")
    
    if best_result != baseline:
        overall_improvement = (best_result['speed'] / baseline['speed'] - 1) * 100
        print(f"   📈 التحسين الإجمالي: {overall_improvement:.1f}%")

if __name__ == "__main__":
    main()
