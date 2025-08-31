#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
أداة اختبار الأداء المتقدم - مقارنة النسخ
Advanced Performance Testing Tool
"""

import asyncio
import time
import json
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import statistics
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

@dataclass
class PerformanceResult:
    """نتيجة اختبار أداء"""
    version: str
    book_id: int
    pages_count: int
    extraction_time: float
    pages_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success_rate: float
    errors_count: int
    total_words: int
    
    def to_dict(self) -> Dict:
        return {
            'version': self.version,
            'book_id': self.book_id, 
            'pages_count': self.pages_count,
            'extraction_time': self.extraction_time,
            'pages_per_second': self.pages_per_second,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'success_rate': self.success_rate,
            'errors_count': self.errors_count,
            'total_words': self.total_words
        }

class AdvancedPerformanceTester:
    """أداة اختبار الأداء المتقدمة"""
    
    def __init__(self):
        self.results: List[PerformanceResult] = []
        
        # المسارات للسكربتات المختلفة
        self.scripts = {
            'v1_original': 'shamela_scraper.py',
            'v1_enhanced': 'enhanced_shamela_scraper.py', 
            'v2_advanced': 'enhanced_shamela_scraper_v2.py'
        }
    
    async def test_version_async(self, version: str, script_path: str, book_id: int, 
                                test_pages: int = None) -> PerformanceResult:
        """اختبار نسخة معينة من السكربت"""
        print(f"🧪 اختبار {version} على الكتاب {book_id}...")
        
        # بدء مراقبة الموارد
        import psutil
        process = psutil.Process()
        
        start_time = time.time()
        start_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        try:
            if version == 'v2_advanced':
                # تشغيل النسخة المتقدمة
                from enhanced_shamela_scraper_v2 import AdvancedShamelaScraper, AdvancedPerformanceConfig
                
                config = AdvancedPerformanceConfig()
                scraper = AdvancedShamelaScraper(config)
                result = await scraper.extract_book(book_id)
                
                pages_count = result['statistics']['total_pages']
                total_words = result['statistics']['total_words']
                errors_count = 0  # يحسب من logs لاحقاً
                
            else:
                # تشغيل النسخ السابقة باستخدام subprocess
                cmd = [sys.executable, script_path, str(book_id)]
                if test_pages:
                    cmd.extend(['--max-pages', str(test_pages)])
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    # تحليل النتائج من stdout
                    output = stdout.decode('utf-8')
                    pages_count = self._extract_pages_count(output)
                    total_words = self._extract_words_count(output)
                    errors_count = self._count_errors(stderr.decode('utf-8'))
                else:
                    raise Exception(f"فشل السكربت: {stderr.decode('utf-8')}")
            
            # حساب الإحصائيات
            end_time = time.time()
            end_memory = process.memory_info().rss / (1024 * 1024)  # MB
            
            extraction_time = end_time - start_time
            pages_per_second = pages_count / extraction_time if extraction_time > 0 else 0
            memory_usage = end_memory - start_memory
            cpu_usage = process.cpu_percent()
            success_rate = (pages_count / (pages_count + errors_count)) * 100 if pages_count + errors_count > 0 else 0
            
            result = PerformanceResult(
                version=version,
                book_id=book_id,
                pages_count=pages_count,
                extraction_time=extraction_time,
                pages_per_second=pages_per_second,
                memory_usage_mb=memory_usage,
                cpu_usage_percent=cpu_usage,
                success_rate=success_rate,
                errors_count=errors_count,
                total_words=total_words
            )
            
            print(f"✅ {version}: {pages_count} صفحة في {extraction_time:.2f}s ({pages_per_second:.2f} ص/ث)")
            return result
            
        except Exception as e:
            print(f"❌ فشل اختبار {version}: {e}")
            return PerformanceResult(
                version=version, book_id=book_id, pages_count=0, extraction_time=float('inf'),
                pages_per_second=0, memory_usage_mb=0, cpu_usage_percent=0,
                success_rate=0, errors_count=1, total_words=0
            )
    
    def _extract_pages_count(self, output: str) -> int:
        """استخراج عدد الصفحات من مخرجات السكربت"""
        import re
        match = re.search(r'(\d+)\s*صفحة', output)
        return int(match.group(1)) if match else 0
    
    def _extract_words_count(self, output: str) -> int:
        """استخراج عدد الكلمات من مخرجات السكربت"""
        import re
        match = re.search(r'(\d+)\s*كلمة', output)
        return int(match.group(1)) if match else 0
    
    def _count_errors(self, stderr: str) -> int:
        """عد الأخطاء من stderr"""
        return stderr.count('ERROR') + stderr.count('خطأ')
    
    async def run_comprehensive_test(self, book_ids: List[int], iterations: int = 3) -> Dict:
        """تشغيل اختبار شامل على عدة كتب"""
        print(f"🚀 بدء الاختبار الشامل على {len(book_ids)} كتاب/كتب")
        print(f"📊 عدد التكرارات لكل اختبار: {iterations}")
        print("=" * 60)
        
        all_results = []
        
        for book_id in book_ids:
            print(f"\n📖 اختبار الكتاب {book_id}")
            print("-" * 40)
            
            for version, script_path in self.scripts.items():
                if not Path(script_path).exists():
                    print(f"⚠️  ملف {script_path} غير موجود، تخطي {version}")
                    continue
                
                version_results = []
                
                for i in range(iterations):
                    print(f"  🔄 التكرار {i+1}/{iterations} لـ {version}")
                    
                    result = await self.test_version_async(version, script_path, book_id)
                    version_results.append(result)
                    all_results.append(result)
                    
                    # راحة قصيرة بين الاختبارات
                    await asyncio.sleep(2)
                
                # حساب المتوسطات
                if version_results:
                    avg_time = statistics.mean([r.extraction_time for r in version_results])
                    avg_speed = statistics.mean([r.pages_per_second for r in version_results])
                    avg_memory = statistics.mean([r.memory_usage_mb for r in version_results])
                    
                    print(f"  📊 متوسط {version}: {avg_speed:.2f} ص/ث، {avg_time:.2f}s، {avg_memory:.1f}MB")
        
        # تحليل شامل للنتائج
        analysis = self._analyze_results(all_results)
        
        # حفظ النتائج
        self._save_results(all_results, analysis)
        
        return {
            'results': all_results,
            'analysis': analysis,
            'summary': self._generate_summary(analysis)
        }
    
    def _analyze_results(self, results: List[PerformanceResult]) -> Dict:
        """تحليل شامل للنتائج"""
        if not results:
            return {}
        
        # تجميع النتائج حسب النسخة
        by_version = {}
        for result in results:
            if result.version not in by_version:
                by_version[result.version] = []
            by_version[result.version].append(result)
        
        # حساب الإحصائيات لكل نسخة
        analysis = {}
        for version, version_results in by_version.items():
            speeds = [r.pages_per_second for r in version_results if r.pages_per_second > 0]
            times = [r.extraction_time for r in version_results if r.extraction_time < float('inf')]
            memory = [r.memory_usage_mb for r in version_results]
            
            analysis[version] = {
                'count': len(version_results),
                'avg_speed': statistics.mean(speeds) if speeds else 0,
                'max_speed': max(speeds) if speeds else 0,
                'min_speed': min(speeds) if speeds else 0,
                'std_speed': statistics.stdev(speeds) if len(speeds) > 1 else 0,
                'avg_time': statistics.mean(times) if times else 0,
                'avg_memory': statistics.mean(memory) if memory else 0,
                'success_rate': statistics.mean([r.success_rate for r in version_results]),
                'total_errors': sum([r.errors_count for r in version_results])
            }
        
        # حساب التحسينات النسبية
        if 'v1_original' in analysis and 'v2_advanced' in analysis:
            original_speed = analysis['v1_original']['avg_speed']
            advanced_speed = analysis['v2_advanced']['avg_speed']
            
            if original_speed > 0:
                speed_improvement = ((advanced_speed - original_speed) / original_speed) * 100
                analysis['improvements'] = {
                    'v2_vs_v1_speed_improvement': speed_improvement,
                    'v2_vs_v1_speed_multiplier': advanced_speed / original_speed if original_speed > 0 else 0
                }
        
        return analysis
    
    def _save_results(self, results: List[PerformanceResult], analysis: Dict):
        """حفظ النتائج في ملفات"""
        timestamp = int(time.time())
        
        # حفظ النتائج المفصلة
        detailed_file = f"performance_test_detailed_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump({
                'results': [r.to_dict() for r in results],
                'analysis': analysis,
                'timestamp': timestamp
            }, f, ensure_ascii=False, indent=2)
        
        # إنشاء تقرير CSV  
        csv_file = f"performance_test_{timestamp}.csv"
        df = pd.DataFrame([r.to_dict() for r in results])
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"💾 تم حفظ النتائج المفصلة: {detailed_file}")
        print(f"📊 تم حفظ جدول البيانات: {csv_file}")
        
        # إنشاء رسوم بيانية
        self._create_visualizations(df, timestamp)
    
    def _create_visualizations(self, df: pd.DataFrame, timestamp: int):
        """إنشاء رسوم بيانية للنتائج"""
        try:
            plt.style.use('default')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # رسم السرعة حسب النسخة
            sns.boxplot(data=df, x='version', y='pages_per_second', ax=axes[0,0])
            axes[0,0].set_title('السرعة حسب النسخة (صفحة/ثانية)')
            axes[0,0].set_ylabel('صفحة/ثانية')
            
            # رسم الوقت حسب النسخة
            sns.boxplot(data=df, x='version', y='extraction_time', ax=axes[0,1])
            axes[0,1].set_title('وقت الاستخراج حسب النسخة (ثانية)')
            axes[0,1].set_ylabel('ثانية')
            
            # رسم استهلاك الذاكرة
            sns.boxplot(data=df, x='version', y='memory_usage_mb', ax=axes[1,0])
            axes[1,0].set_title('استهلاك الذاكرة حسب النسخة (MB)')
            axes[1,0].set_ylabel('MB')
            
            # رسم معدل النجاح
            sns.barplot(data=df, x='version', y='success_rate', ax=axes[1,1])
            axes[1,1].set_title('معدل النجاح حسب النسخة (%)')
            axes[1,1].set_ylabel('%')
            axes[1,1].set_ylim(0, 100)
            
            plt.tight_layout()
            chart_file = f"performance_charts_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"📈 تم حفظ الرسوم البيانية: {chart_file}")
            
        except Exception as e:
            print(f"⚠️  فشل في إنشاء الرسوم البيانية: {e}")
    
    def _generate_summary(self, analysis: Dict) -> str:
        """إنشاء ملخص النتائج"""
        summary = "🎯 ملخص نتائج اختبار الأداء المتقدم\n"
        summary += "=" * 50 + "\n\n"
        
        if not analysis:
            return summary + "❌ لا توجد نتائج للتحليل"
        
        # عرض النتائج لكل نسخة
        for version, stats in analysis.items():
            if version == 'improvements':
                continue
                
            summary += f"📊 {version}:\n"
            summary += f"   - متوسط السرعة: {stats['avg_speed']:.2f} صفحة/ثانية\n"
            summary += f"   - أقصى سرعة: {stats['max_speed']:.2f} صفحة/ثانية\n"
            summary += f"   - متوسط الوقت: {stats['avg_time']:.2f} ثانية\n"
            summary += f"   - متوسط الذاكرة: {stats['avg_memory']:.1f} MB\n"
            summary += f"   - معدل النجاح: {stats['success_rate']:.1f}%\n"
            summary += f"   - إجمالي الأخطاء: {stats['total_errors']}\n\n"
        
        # عرض التحسينات
        if 'improvements' in analysis:
            imp = analysis['improvements']
            summary += "🚀 التحسينات المحققة:\n"
            summary += f"   - تحسن السرعة: {imp['v2_vs_v1_speed_improvement']:+.1f}%\n"
            summary += f"   - مضاعف السرعة: {imp['v2_vs_v1_speed_multiplier']:.1f}x\n"
        
        return summary

async def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(description='اختبار الأداء المتقدم للمستخرجات')
    parser.add_argument('--book-ids', type=int, nargs='+', default=[41], 
                       help='أرقام الكتب للاختبار (افتراضي: 41)')
    parser.add_argument('--iterations', type=int, default=3,
                       help='عدد التكرارات لكل اختبار (افتراضي: 3)')
    parser.add_argument('--quick', action='store_true',
                       help='اختبار سريع (تكرار واحد فقط)')
    
    args = parser.parse_args()
    
    if args.quick:
        args.iterations = 1
    
    print("🧪 أداة اختبار الأداء المتقدم")
    print(f"📚 الكتب المختارة: {args.book_ids}")
    print(f"🔄 عدد التكرارات: {args.iterations}")
    print("=" * 60)
    
    # إنشاء المختبر وتشغيله
    tester = AdvancedPerformanceTester()
    
    try:
        results = await tester.run_comprehensive_test(args.book_ids, args.iterations)
        
        print("\n" + "=" * 60)
        print("🏁 انتهى الاختبار!")
        print(results['summary'])
        
    except KeyboardInterrupt:
        print("\n⏹️  تم إيقاف الاختبار بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ في الاختبار: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
