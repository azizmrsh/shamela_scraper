#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مقارنة شاملة بين السكربت الأصلي والمحسن
Performance Comparison: Original vs Enhanced Shamela Scraper
"""

import subprocess
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime

class PerformanceComparison:
    def __init__(self):
        self.results = {}
        self.test_book_id = "BK000028"  # صحيح البخاري
        self.max_pages = 5  # عدد صفحات الاختبار (قليل للاختبار السريع)
        
    def run_script_test(self, script_name, script_args, test_name):
        """تشغيل اختبار لسكربت معين"""
        print(f"\n{'='*60}")
        print(f"🧪 اختبار: {test_name}")
        print(f"📜 السكربت: {script_name}")
        print(f"⚙️ المعاملات: {' '.join(script_args)}")
        print('='*60)
        
        # إعداد الأمر
        cmd = ['python', script_name] + script_args
        
        try:
            # قياس الوقت
            start_time = time.time()
            
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8',
                                  timeout=300)  # 5 دقائق timeout
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # تحليل النتائج
            if result.returncode == 0:
                output_lines = result.stdout.split('\n')
                
                # استخراج الإحصائيات
                stats = {
                    'success': True,
                    'time': elapsed_time,
                    'pages_count': 0,
                    'speed': 0.0,
                    'output_file': None,
                    'file_size': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                # البحث عن الإحصائيات في المخرجات
                for line in output_lines:
                    if "عدد الصفحات" in line or "صفحة" in line:
                        try:
                            # استخراج عدد الصفحات
                            numbers = [int(s) for s in line.split() if s.isdigit()]
                            if numbers:
                                stats['pages_count'] = max(numbers)
                        except:
                            pass
                    
                    elif "السرعة" in line or "صفحة/ثانية" in line:
                        try:
                            # استخراج السرعة
                            if ":" in line:
                                speed_part = line.split(':')[1]
                                speed_val = ''.join(c for c in speed_part if c.isdigit() or c == '.')
                                if speed_val:
                                    stats['speed'] = float(speed_val)
                        except:
                            pass
                    
                    elif "حُفظ في" in line or "saved" in line.lower():
                        try:
                            # استخراج مسار الملف
                            words = line.split()
                            for word in words:
                                if word.endswith('.json') or word.endswith('.gz'):
                                    stats['output_file'] = word
                                    break
                        except:
                            pass
                
                # حساب السرعة إذا لم تُستخرج
                if stats['speed'] == 0.0 and stats['pages_count'] > 0 and elapsed_time > 0:
                    stats['speed'] = stats['pages_count'] / elapsed_time
                
                # حساب حجم الملف إذا وُجد
                if stats['output_file'] and os.path.exists(stats['output_file']):
                    stats['file_size'] = os.path.getsize(stats['output_file'])
                
                print(f"✅ نجح الاختبار!")
                print(f"📄 الصفحات: {stats['pages_count']}")
                print(f"⏱️ الزمن: {elapsed_time:.2f} ثانية")
                print(f"⚡ السرعة: {stats['speed']:.2f} صفحة/ثانية")
                if stats['output_file']:
                    print(f"💾 الملف: {stats['output_file']}")
                    print(f"📦 الحجم: {stats['file_size']:,} بايت")
                
                return stats
                
            else:
                print(f"❌ فشل الاختبار!")
                print(f"رمز الخطأ: {result.returncode}")
                print(f"خطأ: {result.stderr}")
                
                return {
                    'success': False,
                    'error': result.stderr,
                    'time': elapsed_time,
                    'returncode': result.returncode
                }
                
        except subprocess.TimeoutExpired:
            print("❌ انتهت مهلة الاختبار (5 دقائق)")
            return {
                'success': False,
                'error': 'Timeout after 5 minutes',
                'time': 300
            }
        except Exception as e:
            print(f"❌ خطأ في تشغيل الاختبار: {e}")
            return {
                'success': False,
                'error': str(e),
                'time': 0
            }
    
    def compare_json_outputs(self, file1, file2):
        """مقارنة ملفات JSON الناتجة"""
        print(f"\n{'='*60}")
        print("📊 مقارنة ملفات JSON")
        print('='*60)
        
        try:
            # قراءة الملفين
            with open(file1, 'r', encoding='utf-8') as f:
                data1 = json.load(f)
            
            with open(file2, 'r', encoding='utf-8') as f:
                data2 = json.load(f)
            
            # مقارنة الهيكل الأساسي
            print(f"📁 الملف الأول ({file1}):")
            self.analyze_json_structure(data1)
            
            print(f"\n📁 الملف الثاني ({file2}):")
            self.analyze_json_structure(data2)
            
            # مقارنة المحتوى
            print(f"\n🔍 تحليل الاختلافات:")
            self.find_json_differences(data1, data2)
            
        except Exception as e:
            print(f"❌ خطأ في مقارنة JSON: {e}")
    
    def analyze_json_structure(self, data):
        """تحليل هيكل JSON"""
        if isinstance(data, dict):
            print(f"   📋 عدد الحقول الرئيسية: {len(data)}")
            
            for key, value in data.items():
                if isinstance(value, list):
                    print(f"   📝 {key}: {len(value)} عنصر")
                elif isinstance(value, dict):
                    print(f"   📂 {key}: كائن ({len(value)} حقل)")
                else:
                    print(f"   🔤 {key}: {type(value).__name__}")
        else:
            print(f"   📊 نوع البيانات: {type(data).__name__}")
    
    def find_json_differences(self, data1, data2):
        """العثور على الاختلافات بين ملفين JSON"""
        if isinstance(data1, dict) and isinstance(data2, dict):
            # مقارنة المفاتيح
            keys1 = set(data1.keys())
            keys2 = set(data2.keys())
            
            if keys1 == keys2:
                print("✅ نفس المفاتيح الرئيسية")
            else:
                only_in_1 = keys1 - keys2
                only_in_2 = keys2 - keys1
                if only_in_1:
                    print(f"⚠️ مفاتيح في الأول فقط: {only_in_1}")
                if only_in_2:
                    print(f"⚠️ مفاتيح في الثاني فقط: {only_in_2}")
            
            # مقارنة المحتوى المشترك
            common_keys = keys1.intersection(keys2)
            for key in common_keys:
                if isinstance(data1[key], list) and isinstance(data2[key], list):
                    len_diff = len(data1[key]) - len(data2[key])
                    if len_diff == 0:
                        print(f"✅ {key}: نفس العدد ({len(data1[key])})")
                    else:
                        print(f"⚠️ {key}: اختلاف في العدد ({len(data1[key])} vs {len(data2[key])})")
    
    def run_comparison(self):
        """تشغيل المقارنة الكاملة"""
        print("🔬 مقارنة شاملة: السكربت الأصلي مقابل المحسن")
        print("="*60)
        
        # الاختبارات (بدون السكربت الأصلي بسبب مشاكل التوافق)
        tests = [
            {
                'name': 'المحسن - الوضع التقليدي (خط الأساس)',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--force-traditional', '--debug']
            },
            {
                'name': 'المحسن - معالج lxml السريع',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--use-lxml', '--force-traditional', '--debug']
            },
            {
                'name': 'المحسن - الوضع غير المتزامن',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--use-async', '--aiohttp-workers', '4', '--debug']
            },
            {
                'name': 'المحسن - التحسينات الكاملة',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--use-async', '--use-lxml', '--aiohttp-workers', '6', '--async-batch-size', '10', '--debug']
            }
        ]
        
        # تشغيل الاختبارات
        for test in tests:
            result = self.run_script_test(test['script'], test['args'], test['name'])
            self.results[test['name']] = result
            
            # فترة راحة بين الاختبارات
            time.sleep(2)
        
        # تحليل النتائج
        self.analyze_results()
        
        # مقارنة ملفات JSON إذا وُجدت
        self.compare_json_files()
    
    def analyze_results(self):
        """تحليل النتائج المقارنة"""
        print(f"\n{'='*60}")
        print("📊 تحليل نتائج المقارنة")
        print('='*60)
        
        successful_tests = {name: result for name, result in self.results.items() if result.get('success')}
        
        if not successful_tests:
            print("❌ لا توجد اختبارات ناجحة للمقارنة")
            return
        
        # إيجاد خط الأساس
        baseline = None
        for name, result in successful_tests.items():
            if 'أصلي' in name:
                baseline = result
                baseline_name = name
                break
        
        if not baseline:
            # استخدام أول اختبار ناجح كخط أساس
            baseline_name = list(successful_tests.keys())[0]
            baseline = successful_tests[baseline_name]
        
        print(f"📏 خط الأساس: {baseline_name}")
        print(f"   ⏱️ الزمن: {baseline['time']:.2f}s")
        print(f"   ⚡ السرعة: {baseline['speed']:.2f} صفحة/ثانية")
        print()
        
        # مقارنة النتائج
        for name, result in successful_tests.items():
            if name == baseline_name:
                continue
            
            if result['time'] > 0 and baseline['time'] > 0:
                speed_improvement = (baseline['time'] / result['time'] - 1) * 100
                throughput_improvement = (result['speed'] / baseline['speed'] - 1) * 100
                
                print(f"🚀 {name}:")
                print(f"   ⏱️ الزمن: {result['time']:.2f}s ({speed_improvement:+.1f}%)")
                print(f"   ⚡ السرعة: {result['speed']:.2f} صفحة/ثانية ({throughput_improvement:+.1f}%)")
                
                if result.get('file_size', 0) > 0:
                    print(f"   💾 حجم الملف: {result['file_size']:,} بايت")
                print()
        
        # أفضل نتيجة
        best_result = max(successful_tests.values(), key=lambda x: x.get('speed', 0))
        best_name = [name for name, result in successful_tests.items() if result == best_result][0]
        
        print(f"🏆 أفضل أداء: {best_name}")
        print(f"   ⚡ أعلى سرعة: {best_result['speed']:.2f} صفحة/ثانية")
        
        if best_result != baseline:
            overall_improvement = (best_result['speed'] / baseline['speed'] - 1) * 100
            print(f"   📈 التحسين الإجمالي: {overall_improvement:.1f}%")
    
    def compare_json_files(self):
        """مقارنة ملفات JSON المُنتجة"""
        json_files = []
        
        # البحث عن ملفات JSON
        for name, result in self.results.items():
            if result.get('success') and result.get('output_file'):
                if os.path.exists(result['output_file']):
                    json_files.append((name, result['output_file']))
        
        if len(json_files) >= 2:
            print(f"\n🔍 مقارنة ملفات JSON:")
            # مقارنة الأول مع الباقي
            baseline_file = json_files[0][1]
            for i in range(1, len(json_files)):
                print(f"\n--- مقارنة: {json_files[0][0]} مع {json_files[i][0]} ---")
                self.compare_json_outputs(baseline_file, json_files[i][1])

def main():
    """الوظيفة الرئيسية"""
    print("🚀 بدء مقارنة الأداء الشاملة")
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    comparison = PerformanceComparison()
    comparison.run_comparison()
    
    print(f"\n{'='*60}")
    print("✅ اكتملت المقارنة!")
    print('='*60)

if __name__ == "__main__":
    main()
