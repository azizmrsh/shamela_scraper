#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
مقارنة سريعة بين النسخ الثلاث
Quick Performance Comparison Tool
"""

import asyncio
import time
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

class QuickComparison:
    """أداة مقارنة سريعة للنسخ المختلفة"""
    
    def __init__(self):
        self.results = {}
        self.python_exe = "c:/Users/mzyz2/Desktop/BMS-Asset/Bms-project/homeV1/.venv/Scripts/python.exe"
    
    async def test_v1_enhanced(self, book_id: int) -> Dict:
        """اختبار النسخة الأولى المحسنة"""
        print("🧪 اختبار النسخة الأولى المحسنة...")
        
        start_time = time.time()
        try:
            proc = await asyncio.create_subprocess_exec(
                self.python_exe, "enhanced_shamela_scraper.py", str(book_id), 
                "--max-workers", "4",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            elapsed = time.time() - start_time
            
            if proc.returncode == 0:
                # محاولة استخراج النتائج
                output = stdout.decode('utf-8', errors='ignore')
                pages = self._extract_pages_from_output(output)
                
                return {
                    'version': 'v1_enhanced',
                    'success': True,
                    'pages': pages,
                    'time': elapsed,
                    'speed': pages / elapsed if elapsed > 0 else 0,
                    'error': None
                }
            else:
                error = stderr.decode('utf-8', errors='ignore')
                return {
                    'version': 'v1_enhanced',
                    'success': False,
                    'pages': 0,
                    'time': elapsed,
                    'speed': 0,
                    'error': error[:200] + '...' if len(error) > 200 else error
                }
                
        except Exception as e:
            return {
                'version': 'v1_enhanced',
                'success': False,
                'pages': 0,
                'time': time.time() - start_time,
                'speed': 0,
                'error': str(e)
            }
    
    async def test_v2_advanced(self, book_id: int) -> Dict:
        """اختبار النسخة الثانية المتقدمة"""
        print("🚀 اختبار النسخة الثانية المتقدمة...")
        
        start_time = time.time()
        try:
            from enhanced_shamela_scraper_v2 import AdvancedShamelaScraper, AdvancedPerformanceConfig
            
            # إعداد محسن للاختبار السريع
            config = AdvancedPerformanceConfig(
                max_connections=100,
                max_connections_per_host=30,
                async_semaphore_limit=15,
                multiprocessing_threshold=50,  # أقل للاختبار
                max_processes=4
            )
            
            scraper = AdvancedShamelaScraper(config)
            result = await scraper.extract_book(book_id)
            
            elapsed = time.time() - start_time
            pages = result['statistics']['total_pages']
            speed = result['statistics']['pages_per_second']
            
            return {
                'version': 'v2_advanced',
                'success': True,
                'pages': pages,
                'time': elapsed,
                'speed': speed,
                'words': result['statistics']['total_words'],
                'extraction_method': result['statistics']['extraction_method'],
                'error': None
            }
            
        except Exception as e:
            return {
                'version': 'v2_advanced',
                'success': False,
                'pages': 0,
                'time': time.time() - start_time,
                'speed': 0,
                'error': str(e)
            }
    
    def _extract_pages_from_output(self, output: str) -> int:
        """استخراج عدد الصفحات من مخرجات السكربت"""
        import re
        
        # البحث عن أنماط مختلفة
        patterns = [
            r'(\d+)\s*صفحة',
            r'total_pages[\'\"]\s*:\s*(\d+)',
            r'Pages:\s*(\d+)',
            r'استخراج\s*(\d+)\s*صفحة',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return int(match.group(1))
        
        return 0
    
    async def run_comparison(self, book_id: int = 41) -> Dict:
        """تشغيل مقارنة شاملة"""
        print(f"📊 بدء المقارنة السريعة للكتاب {book_id}")
        print("=" * 60)
        
        results = {}
        
        # اختبار النسخة الثانية المتقدمة أولاً
        results['v2_advanced'] = await self.test_v2_advanced(book_id)
        
        print("\n" + "-" * 40)
        
        # اختبار النسخة الأولى المحسنة
        if Path("enhanced_shamela_scraper.py").exists():
            results['v1_enhanced'] = await self.test_v1_enhanced(book_id)
        else:
            print("⚠️  النسخة الأولى المحسنة غير موجودة")
            results['v1_enhanced'] = {
                'version': 'v1_enhanced',
                'success': False,
                'error': 'ملف غير موجود'
            }
        
        # تحليل النتائج
        analysis = self._analyze_results(results)
        
        # عرض النتائج
        self._display_results(results, analysis)
        
        # حفظ النتائج
        self._save_results(results, analysis, book_id)
        
        return {
            'results': results,
            'analysis': analysis
        }
    
    def _analyze_results(self, results: Dict) -> Dict:
        """تحليل النتائج والمقارنة"""
        analysis = {
            'comparison': {},
            'winner': None,
            'improvement': {}
        }
        
        # استخراج النتائج الناجحة
        successful_results = {k: v for k, v in results.items() if v.get('success', False)}
        
        if len(successful_results) >= 2:
            v1_speed = successful_results.get('v1_enhanced', {}).get('speed', 0)
            v2_speed = successful_results.get('v2_advanced', {}).get('speed', 0)
            
            if v1_speed > 0 and v2_speed > 0:
                improvement = ((v2_speed - v1_speed) / v1_speed) * 100
                multiplier = v2_speed / v1_speed
                
                analysis['improvement'] = {
                    'speed_improvement_percent': improvement,
                    'speed_multiplier': multiplier,
                    'time_saved_percent': ((successful_results['v1_enhanced']['time'] - 
                                          successful_results['v2_advanced']['time']) / 
                                         successful_results['v1_enhanced']['time']) * 100
                }
                
                analysis['winner'] = 'v2_advanced' if v2_speed > v1_speed else 'v1_enhanced'
        
        return analysis
    
    def _display_results(self, results: Dict, analysis: Dict):
        """عرض النتائج بشكل جميل"""
        print("\n" + "=" * 60)
        print("🏆 نتائج المقارنة السريعة")
        print("=" * 60)
        
        for version, result in results.items():
            print(f"\n📊 {version.replace('_', ' ').title()}:")
            
            if result.get('success', False):
                print(f"   ✅ النجاح: نعم")
                print(f"   📄 الصفحات: {result.get('pages', 0):,}")
                print(f"   ⏱️  الوقت: {result.get('time', 0):.2f} ثانية")
                print(f"   ⚡ السرعة: {result.get('speed', 0):.2f} صفحة/ثانية")
                
                if result.get('words'):
                    print(f"   📝 الكلمات: {result.get('words', 0):,}")
                
                if result.get('extraction_method'):
                    print(f"   🔧 الطريقة: {result.get('extraction_method')}")
                    
            else:
                print(f"   ❌ النجاح: لا")
                print(f"   🐛 الخطأ: {result.get('error', 'غير محدد')[:100]}...")
        
        # عرض التحليل
        if analysis.get('improvement'):
            imp = analysis['improvement']
            print(f"\n🚀 تحليل التحسن:")
            print(f"   📈 تحسن السرعة: {imp['speed_improvement_percent']:+.1f}%")
            print(f"   ⚡ مضاعف السرعة: {imp['speed_multiplier']:.1f}x")
            print(f"   ⏰ توفير الوقت: {imp['time_saved_percent']:.1f}%")
            
            if analysis.get('winner'):
                winner_name = analysis['winner'].replace('_', ' ').title()
                print(f"   🏆 الفائز: {winner_name}")
    
    def _save_results(self, results: Dict, analysis: Dict, book_id: int):
        """حفظ النتائج في ملف"""
        timestamp = int(time.time())
        filename = f"quick_comparison_{book_id}_{timestamp}.json"
        
        data = {
            'book_id': book_id,
            'timestamp': timestamp,
            'results': results,
            'analysis': analysis
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج في: {filename}")

async def main():
    """الدالة الرئيسية"""
    book_id = int(sys.argv[1]) if len(sys.argv) > 1 else 41
    
    print("⚡ أداة المقارنة السريعة")
    print(f"📚 الكتاب المختار: {book_id}")
    print("🎯 الهدف: مقارنة سرعة النسخ المختلفة")
    
    comparator = QuickComparison()
    
    try:
        await comparator.run_comparison(book_id)
        print("\n🎉 انتهت المقارنة بنجاح!")
        
    except KeyboardInterrupt:
        print("\n⏹️  تم إيقاف المقارنة")
    except Exception as e:
        print(f"\n❌ خطأ في المقارنة: {e}")

if __name__ == "__main__":
    asyncio.run(main())
