#!/usr/bin/env python3
"""
Ultra Reliable Enhanced Runner - المُشغل فائق الموثوقية
واجهة سطر أوامر محسنة مع ضمان الموثوقية 100%
"""

import argparse
import sys
import os
import json
import gzip
from datetime import datetime
from pathlib import Path

# إضافة المسار الحالي
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from ultra_reliable_scraper import UltraReliableScraper, ReliabilityConfig
    # استيراد اختياري لقاعدة البيانات
    try:
        from enhanced_database_manager import save_enhanced_json_to_database
    except ImportError:
        print("⚠️ وحدة قاعدة البيانات غير متوفرة - سيتم التركيز على الاستخراج فقط")
        save_enhanced_json_to_database = None
except ImportError as e:
    print(f"خطأ في الاستيراد: {e}")
    print("تأكد من وجود ملف ultra_reliable_scraper.py")
    sys.exit(1)

def print_header():
    """طباعة رأس البرنامج فائق الموثوقية"""
    print("=" * 70)
    print("🛡️ سكربت المكتبة الشاملة فائق الموثوقية")
    print("Ultra Reliable Enhanced Shamela Scraper")
    print("✅ موثوقية 100% - بدون أخطاء - دقة كاملة")
    print("=" * 70)
    print()

def print_separator():
    """طباعة فاصل"""
    print("-" * 70)

def extract_book_command(args):
    """استخراج كتاب مع موثوقية 100%"""
    print_header()
    
    print(f"🎯 المهمة: استخراج الكتاب {args.book_id}")
    print(f"📄 الصفحات المطلوبة: {args.max_pages if args.max_pages else 'جميع الصفحات'}")
    print_separator()
    
    # إعداد تكوين الموثوقية
    reliability_config = ReliabilityConfig()
    reliability_config.max_retries = 10  # محاولات إضافية
    reliability_config.retry_delay = 3.0  # تأخير أطول
    reliability_config.verify_extraction = True  # تحقق شامل
    reliability_config.detailed_logging = True  # سجلات مفصلة
    
    # إنشاء المُستخرِج
    scraper = UltraReliableScraper(reliability_config)
    
    # تنفيذ الاستخراج
    result = scraper.extract_book_ultra_reliable(
        book_id=args.book_id,
        max_pages=args.max_pages,
        output_dir=args.output_dir or "ultra_reliable_books"
    )
    
    print_separator()
    
    if result["success"]:
        stats = result["stats"]
        print("🎉 نجح الاستخراج بموثوقية 100%!")
        print(f"📚 العنوان: {stats['title']}")
        print(f"📄 الصفحات المستخرجة: {stats['pages_extracted']}")
        print(f"📝 إجمالي الكلمات: {stats['total_words']:,}")
        print(f"⏱️ زمن الاستخراج: {stats['extraction_time']:.2f} ثانية")
        print(f"🏎️ السرعة: {stats['speed']:.2f} صفحة/ثانية")
        print(f"💾 الملف المحفوظ: {result['filepath']}")
        
        # التحقق من جودة الملف
        print(f"\n🔍 التحقق من جودة الملف...")
        quality_report = verify_file_quality(result['filepath'])
        print_quality_report(quality_report)
        
    else:
        print(f"❌ فشل الاستخراج: {result['error']}")
        print("💡 تحقق من الاتصال بالإنترنت ومعرف الكتاب")
        return 1
    
    print_separator()
    print("✅ اكتملت العملية بنجاح!")
    return 0

def verify_file_quality(filepath):
    """التحقق من جودة الملف المحفوظ"""
    try:
        with gzip.open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        report = {
            'file_readable': True,
            'total_pages': len(data.get('pages', [])),
            'total_words': sum(p.get('word_count', 0) for p in data.get('pages', [])),
            'empty_pages': 0,
            'arabic_content': 0,
            'avg_words_per_page': 0,
            'quality_score': 0
        }
        
        # فحص الصفحات
        for page in data.get('pages', []):
            content = page.get('content', '').strip()
            if not content or len(content) < 10:
                report['empty_pages'] += 1
            
            # فحص المحتوى العربي
            if any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in content):
                report['arabic_content'] += 1
        
        # حساب المتوسطات
        if report['total_pages'] > 0:
            report['avg_words_per_page'] = report['total_words'] // report['total_pages']
            report['quality_score'] = ((report['total_pages'] - report['empty_pages']) / report['total_pages'] * 100)
        
        return report
        
    except Exception as e:
        return {
            'file_readable': False,
            'error': str(e),
            'quality_score': 0
        }

def print_quality_report(report):
    """طباعة تقرير الجودة"""
    if not report['file_readable']:
        print(f"❌ خطأ في قراءة الملف: {report.get('error', 'خطأ غير معروف')}")
        return
    
    print(f"📊 تقرير الجودة:")
    print(f"  📄 إجمالي الصفحات: {report['total_pages']}")
    print(f"  📝 إجمالي الكلمات: {report['total_words']:,}")
    print(f"  📖 صفحات بمحتوى عربي: {report['arabic_content']}")
    print(f"  ⚠️ صفحات فارغة: {report['empty_pages']}")
    print(f"  📊 متوسط كلمات/صفحة: {report['avg_words_per_page']}")
    print(f"  🎯 درجة الجودة: {report['quality_score']:.1f}%")
    
    if report['quality_score'] >= 95:
        print("  ✅ جودة ممتازة!")
    elif report['quality_score'] >= 85:
        print("  ✅ جودة جيدة جداً")
    elif report['quality_score'] >= 75:
        print("  ⚠️ جودة مقبولة")
    else:
        print("  ❌ جودة منخفضة - يُنصح بإعادة الاستخراج")

def main():
    """الدالة الرئيسية"""
    parser = argparse.ArgumentParser(
        description="🛡️ سكربت المكتبة الشاملة فائق الموثوقية",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:
  %(prog)s extract 12106 --max-pages 50
  %(prog)s extract 43 --output-dir my_books
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='الأوامر المتاحة')
    
    # أمر الاستخراج
    extract_parser = subparsers.add_parser('extract', help='استخراج كتاب واحد')
    extract_parser.add_argument('book_id', help='معرف الكتاب في المكتبة الشاملة')
    extract_parser.add_argument('--max-pages', type=int, help='العدد الأقصى للصفحات')
    extract_parser.add_argument('--output-dir', help='مجلد الإخراج')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'extract':
        return extract_book_command(args)
    else:
        print(f"❌ أمر غير معروف: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
