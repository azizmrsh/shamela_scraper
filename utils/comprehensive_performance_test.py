#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مقارنة شاملة بين السكربت الأصلي والمحسن
Comprehensive Performance Comparison: Original vs Enhanced Shamela Scraper
"""

import subprocess
import time
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import shutil

class ComprehensiveComparison:
    def __init__(self):
        self.results = {}
        self.test_book_id = "BK000028"  # صحيح البخاري
        self.max_pages = 10  # عدد صفحات الاختبار
        self.comparison_dir = "comparison_results"
        
        # إنشاء مجلد النتائج
        os.makedirs(self.comparison_dir, exist_ok=True)
        
    def setup_original_script(self):
        """إعداد السكربت الأصلي للمقارنة"""
        print("🔧 إعداد السكربت الأصلي للمقارنة...")
        
        # نسخ السكربت الأصلي من المرفقات
        original_path = "c:\\Users\\mzyz2\\Desktop\\BMS-Asset\\Bms-project\\homeV1\\script\\shamela_scraper_final\\enhanced_shamela_scraper.py"
        target_path = "original_shamela_scraper_for_comparison.py"
        
        try:
            shutil.copy2(original_path, target_path)
            print(f"✅ تم نسخ السكربت الأصلي إلى {target_path}")
            return True
        except Exception as e:
            print(f"❌ خطأ في نسخ السكربت الأصلي: {e}")
            return False
    
    def run_script_test(self, script_name, script_args, test_name):
        """تشغيل اختبار لسكربت معين"""
        print(f"\n{'='*80}")
        print(f"🧪 اختبار: {test_name}")
        print(f"📜 السكربت: {script_name}")
        print(f"⚙️ المعاملات: {' '.join(script_args)}")
        print('='*80)
        
        # إعداد الأمر
        cmd = ['python', script_name] + script_args
        
        try:
            # قياس الوقت
            start_time = time.time()
            
            result = subprocess.run(cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  encoding='utf-8',
                                  timeout=600)  # 10 دقائق timeout
            
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
                    'word_count': 0,
                    'chapters_count': 0,
                    'volumes_count': 0,
                    'authors_count': 0,
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
                # استخراج الإحصائيات من المخرجات
                for line in output_lines:
                    if "عدد الصفحات" in line or "📄" in line:
                        numbers = [int(s) for s in line.split() if s.isdigit()]
                        if numbers:
                            stats['pages_count'] = max(numbers)
                    
                    elif "السرعة" in line or "صفحة/ثانية" in line:
                        try:
                            speed_part = line.split(':')[-1] if ':' in line else line
                            speed_val = ''.join(c for c in speed_part if c.isdigit() or c == '.')
                            if speed_val:
                                stats['speed'] = float(speed_val)
                        except:
                            pass
                    
                    elif "إجمالي الكلمات" in line or "📊" in line:
                        try:
                            numbers = [int(s.replace(',', '')) for s in line.split() if s.replace(',', '').isdigit()]
                            if numbers:
                                stats['word_count'] = max(numbers)
                        except:
                            pass
                    
                    elif "عدد الفصول" in line or "📑" in line:
                        numbers = [int(s) for s in line.split() if s.isdigit()]
                        if numbers:
                            stats['chapters_count'] = max(numbers)
                    
                    elif "عدد الأجزاء" in line or "📚" in line:
                        numbers = [int(s) for s in line.split() if s.isdigit()]
                        if numbers:
                            stats['volumes_count'] = max(numbers)
                    
                    elif "المؤلف" in line or "👨‍🎓" in line:
                        # تقدير عدد المؤلفين من النص
                        if "،" in line:
                            stats['authors_count'] = len(line.split("،"))
                        else:
                            stats['authors_count'] = 1
                    
                    elif "حُفظ في" in line or "💾" in line or "saved" in line.lower():
                        words = line.split()
                        for word in words:
                            if word.endswith('.json') or word.endswith('.gz'):
                                stats['output_file'] = word
                                break
                
                # حساب السرعة إذا لم تُستخرج
                if stats['speed'] == 0.0 and stats['pages_count'] > 0 and elapsed_time > 0:
                    stats['speed'] = stats['pages_count'] / elapsed_time
                
                # حساب حجم الملف إذا وُجد
                if stats['output_file'] and os.path.exists(stats['output_file']):
                    stats['file_size'] = os.path.getsize(stats['output_file'])
                    # نسخ الملف إلى مجلد المقارنة
                    dest_file = os.path.join(self.comparison_dir, f"{test_name.replace(' ', '_')}.json")
                    shutil.copy2(stats['output_file'], dest_file)
                    stats['comparison_file'] = dest_file
                
                print(f"✅ نجح الاختبار!")
                print(f"📄 الصفحات: {stats['pages_count']}")
                print(f"⏱️ الزمن: {elapsed_time:.2f} ثانية")
                print(f"⚡ السرعة: {stats['speed']:.2f} صفحة/ثانية")
                print(f"📊 الكلمات: {stats['word_count']:,}")
                print(f"📑 الفصول: {stats['chapters_count']}")
                print(f"📚 الأجزاء: {stats['volumes_count']}")
                print(f"👥 المؤلفون: {stats['authors_count']}")
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
                    'returncode': result.returncode,
                    'stdout': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            print("❌ انتهت مهلة الاختبار (10 دقائق)")
            return {
                'success': False,
                'error': 'Timeout after 10 minutes',
                'time': 600
            }
        except Exception as e:
            print(f"❌ خطأ في تشغيل الاختبار: {e}")
            return {
                'success': False,
                'error': str(e),
                'time': 0
            }
    
    def compare_json_outputs(self):
        """مقارنة ملفات JSON المُنتجة"""
        print(f"\n{'='*80}")
        print("📊 مقارنة ملفات JSON المُنتجة")
        print('='*80)
        
        json_files = []
        for filename in os.listdir(self.comparison_dir):
            if filename.endswith('.json'):
                json_files.append(os.path.join(self.comparison_dir, filename))
        
        if len(json_files) < 2:
            print("⚠️ تحتاج إلى ملفين على الأقل للمقارنة")
            return
        
        try:
            # قراءة جميع الملفات
            data_sets = {}
            for file_path in json_files:
                filename = os.path.basename(file_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data_sets[filename] = json.load(f)
            
            # مقارنة الهيكل
            print("\n🔍 مقارنة هيكل البيانات:")
            for filename, data in data_sets.items():
                print(f"\n📁 {filename}:")
                self.analyze_json_structure(data)
            
            # مقارنة المحتوى
            if len(data_sets) >= 2:
                files = list(data_sets.keys())
                print(f"\n🔍 مقارنة المحتوى بين {files[0]} و {files[1]}:")
                self.find_json_differences(data_sets[files[0]], data_sets[files[1]])
                
        except Exception as e:
            print(f"❌ خطأ في مقارنة JSON: {e}")
    
    def analyze_json_structure(self, data):
        """تحليل هيكل JSON"""
        if isinstance(data, dict):
            print(f"   📋 عدد الحقول الرئيسية: {len(data)}")
            
            key_info = []
            for key, value in data.items():
                if isinstance(value, list):
                    key_info.append(f"📝 {key}: {len(value)} عنصر")
                elif isinstance(value, dict):
                    key_info.append(f"📂 {key}: كائن ({len(value)} حقل)")
                else:
                    key_info.append(f"🔤 {key}: {type(value).__name__}")
            
            for info in key_info[:10]:  # أول 10 حقول
                print(f"   {info}")
                
            if len(key_info) > 10:
                print(f"   ... و {len(key_info) - 10} حقل آخر")
        else:
            print(f"   📊 نوع البيانات: {type(data).__name__}")
    
    def find_json_differences(self, data1, data2):
        """العثور على الاختلافات بين ملفين JSON"""
        if isinstance(data1, dict) and isinstance(data2, dict):
            # مقارنة المفاتيح
            keys1 = set(data1.keys())
            keys2 = set(data2.keys())
            
            common_keys = keys1.intersection(keys2)
            only_in_1 = keys1 - keys2
            only_in_2 = keys2 - keys1
            
            print(f"🔗 مفاتيح مشتركة: {len(common_keys)}")
            if only_in_1:
                print(f"⚠️ مفاتيح في الأول فقط: {list(only_in_1)[:5]}")
            if only_in_2:
                print(f"⚠️ مفاتيح في الثاني فقط: {list(only_in_2)[:5]}")
            
            # مقارنة المحتوى المشترك
            for key in list(common_keys)[:10]:  # أول 10 مفاتيح
                if isinstance(data1[key], list) and isinstance(data2[key], list):
                    len_diff = len(data1[key]) - len(data2[key])
                    if len_diff == 0:
                        print(f"✅ {key}: نفس العدد ({len(data1[key])})")
                    else:
                        print(f"⚠️ {key}: اختلاف في العدد ({len(data1[key])} vs {len(data2[key])})")
                elif data1[key] == data2[key]:
                    print(f"✅ {key}: متطابق")
                else:
                    print(f"⚠️ {key}: مختلف")
    
    def run_comprehensive_comparison(self):
        """تشغيل المقارنة الشاملة"""
        print("🔬 مقارنة شاملة: السكربت الأصلي مقابل المحسن")
        print("="*80)
        print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📖 كتاب الاختبار: {self.test_book_id}")
        print(f"📄 عدد الصفحات: {self.max_pages}")
        print("="*80)
        
        # الاختبارات
        tests = [
            {
                'name': 'السكربت_الأصلي',
                'script': 'original_shamela_scraper_for_comparison.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages)]
            },
            {
                'name': 'المحسن_التقليدي',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--force-traditional']
            },
            {
                'name': 'المحسن_lxml',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--use-lxml', '--force-traditional']
            },
            {
                'name': 'المحسن_async',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--use-async', '--aiohttp-workers', '4']
            },
            {
                'name': 'المحسن_الكامل',
                'script': 'enhanced_shamela_scraper.py',
                'args': [self.test_book_id, '--max-pages', str(self.max_pages), '--use-async', '--use-lxml', '--aiohttp-workers', '6']
            }
        ]
        
        # إعداد السكربت الأصلي
        if not self.setup_original_script():
            print("⚠️ تعذر إعداد السكربت الأصلي، سيتم استخدام المحسن فقط")
            tests = tests[1:]  # إزالة اختبار السكربت الأصلي
        
        # تشغيل الاختبارات
        for test in tests:
            result = self.run_script_test(test['script'], test['args'], test['name'])
            self.results[test['name']] = result
            
            # فترة راحة بين الاختبارات
            time.sleep(3)
        
        # تحليل النتائج
        self.analyze_comprehensive_results()
        
        # مقارنة ملفات JSON
        self.compare_json_outputs()
        
        # حفظ تقرير المقارنة
        self.save_comparison_report()
    
    def analyze_comprehensive_results(self):
        """تحليل النتائج الشاملة"""
        print(f"\n{'='*80}")
        print("📊 تحليل نتائج المقارنة الشاملة")
        print('='*80)
        
        successful_tests = {name: result for name, result in self.results.items() if result.get('success')}
        
        if not successful_tests:
            print("❌ لا توجد اختبارات ناجحة للمقارنة")
            return
        
        # إيجاد خط الأساس (السكربت الأصلي أو أول محسن)
        baseline = None
        baseline_name = None
        
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
        print(f"   📊 الكلمات: {baseline['word_count']:,}")
        print(f"   📦 حجم الملف: {baseline.get('file_size', 0):,} بايت")
        print()
        
        # جدول مقارنة شامل
        print("📋 جدول المقارنة الشامل:")
        print("-" * 120)
        print(f"{'الاختبار':<20} {'الزمن (ث)':<12} {'السرعة':<15} {'التحسين %':<12} {'الكلمات':<12} {'الحجم (KB)':<12}")
        print("-" * 120)
        
        for name, result in successful_tests.items():
            if result['time'] > 0 and baseline['time'] > 0:
                speed_improvement = (baseline['time'] / result['time'] - 1) * 100
                
                print(f"{name:<20} "
                      f"{result['time']:<12.2f} "
                      f"{result['speed']:<15.2f} "
                      f"{speed_improvement:<12.1f} "
                      f"{result['word_count']:<12,} "
                      f"{result.get('file_size', 0)//1024:<12}")
        
        print("-" * 120)
        
        # أفضل نتيجة
        best_result = max(successful_tests.values(), key=lambda x: x.get('speed', 0))
        best_name = [name for name, result in successful_tests.items() if result == best_result][0]
        
        print(f"\n🏆 أفضل أداء: {best_name}")
        print(f"   ⚡ أعلى سرعة: {best_result['speed']:.2f} صفحة/ثانية")
        
        if best_result != baseline:
            overall_improvement = (best_result['speed'] / baseline['speed'] - 1) * 100
            time_saved = baseline['time'] - best_result['time']
            print(f"   📈 التحسين الإجمالي: {overall_improvement:.1f}%")
            print(f"   ⏱️ الوقت المُوفّر: {time_saved:.2f} ثانية")
    
    def save_comparison_report(self):
        """حفظ تقرير المقارنة"""
        report_path = os.path.join(self.comparison_dir, "comparison_report.json")
        
        report_data = {
            'test_info': {
                'date': datetime.now().isoformat(),
                'book_id': self.test_book_id,
                'max_pages': self.max_pages,
                'total_tests': len(self.results)
            },
            'results': self.results,
            'summary': {
                'successful_tests': len([r for r in self.results.values() if r.get('success')]),
                'failed_tests': len([r for r in self.results.values() if not r.get('success')])
            }
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ تقرير المقارنة في: {report_path}")

def main():
    """الوظيفة الرئيسية"""
    print("🚀 بدء المقارنة الشاملة للأداء")
    
    comparison = ComprehensiveComparison()
    comparison.run_comprehensive_comparison()
    
    print(f"\n{'='*80}")
    print("✅ اكتملت المقارنة الشاملة!")
    print('='*80)
    print("📁 النتائج محفوظة في مجلد: comparison_results")
    print("📊 راجع التقرير المفصل في: comparison_results/comparison_report.json")

if __name__ == "__main__":
    main()
