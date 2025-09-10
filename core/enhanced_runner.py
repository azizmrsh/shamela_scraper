# -*- coding: utf-8 -*-
"""
Enhanced Shamela Runner - سكربت تشغيل محسن للمكتبة الشاملة
يجمع جميع الوظائف المحسنة في واجهة واحدة سهلة الاستخدام

الميزات:
- استخراج الكتب مع جميع التحسينات
- حفظ البيانات في قاعدة البيانات المحسنة
- إنشاء تقارير شاملة
- معالجة الأخطاء المحسنة
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from pathlib import Path

# إضافة المجلد الحالي للـ path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from enhanced_shamela_scraper import scrape_enhanced_book, save_enhanced_book_to_json, PerformanceConfig
    from enhanced_database_manager import EnhancedShamelaDatabaseManager, save_enhanced_json_to_database
except ImportError as e:
    print(f"خطأ في استيراد الوحدات: {e}")
    print("تأكد من وجود ملفات enhanced_shamela_scraper.py و enhanced_database_manager.py")
    sys.exit(1)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_shamela_runner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_header():
    """طباعة رأس البرنامج"""
    print("=" * 60)
    print("سكربت المكتبة الشاملة المحسن")
    print("Enhanced Shamela Scraper")
    print("=" * 60)
    print()

def print_separator():
    """طباعة فاصل"""
    print("-" * 60)

def extract_book_full(book_id: str, max_pages: int = None, output_dir: str = None, 
                     config: PerformanceConfig = None) -> dict:
    """
    استخراج كتاب كامل مع جميع التحسينات
    """
    if config is None:
        try:
            from ultra_speed_config import auto_tune_config
            config = auto_tune_config()
            print("🚀 استخدام التكوين الفائق المُحسَّن تلقائياً")
        except ImportError:
            config = PerformanceConfig()
            # التكوين الأمثل للسرعة القصوى
            config.use_async = False  # الطريقة التقليدية أكثر استقراراً
            config.max_workers = 20   # عدد أمثل من العمال
            config.use_lxml = True    # استخدام lxml للسرعة
            config.enable_caching = True  # تفعيل التخزين المؤقت
            config.batch_size = 3000  # دفعات أكبر
            config.request_delay = 0.05  # تأخير قليل لتجنب الحظر
            config.connection_pool_size = 24  # تجمع اتصالات أكبر
            config.enable_compression = False  # عدم ضغط ملفات JSON
        
    print(f"🔍 بدء استخراج الكتاب: {book_id}")
    print(f"⚡ إعدادات السرعة الفائقة: workers={config.max_workers}, delay={config.request_delay}s, lxml={config.use_lxml}")
    print_separator()
    
    try:
        # استخراج الكتاب
        print("📖 استخراج بيانات الكتاب...")
        book = scrape_enhanced_book(book_id, max_pages=max_pages, extract_content=True, config=config)
        
        # تحديد مجلد الإخراج
        if not output_dir:
            output_dir = os.path.join(current_dir, "enhanced_books")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # إنشاء اسم الملف
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = '.json.gz' if config.enable_compression else '.json'
        filename = f"enhanced_book_{book_id}_{timestamp}{extension}"
        output_path = os.path.join(output_dir, filename)
        
        # حفظ الكتاب
        print("💾 حفظ البيانات...")
        save_enhanced_book_to_json(book, output_path, config)
        
        # طباعة النتائج
        print("\n✅ تم استخراج الكتاب بنجاح!")
        print_separator()
        print(f"📚 العنوان: {book.title}")
        print(f"👨‍🎓 المؤلف(ون): {', '.join(author.name for author in book.authors)}")
        
        if book.publisher:
            print(f"🏢 الناشر: {book.publisher.name}")
            if book.publisher.location:
                print(f"📍 الموقع: {book.publisher.location}")
        
        if book.book_section:
            print(f"📂 القسم: {book.book_section.name}")
        
        if book.edition:
            edition_info = f"📄 الطبعة: {book.edition}"
            if book.edition_number:
                edition_info += f" (رقم: {book.edition_number})"
            print(edition_info)
        
        if book.publication_year:
            year_info = f"📅 سنة النشر: {book.publication_year} م"
            if book.edition_date_hijri:
                year_info += f" ({book.edition_date_hijri} هـ)"
            print(year_info)
        
        print(f"📄 عدد الصفحات: {len(book.pages)}")
        print(f"📑 عدد الفصول: {len(book.index)}")
        print(f"📚 عدد الأجزاء: {len(book.volumes)}")
        
        if book.volume_links:
            print(f"🔗 روابط المجلدات: {len(book.volume_links)}")
        
        if book.has_original_pagination:
            print("✅ يستخدم ترقيم الصفحات الأصلي")
        
        print(f"💾 تم الحفظ في: {output_path}")
        
        # إحصائيات إضافية
        total_words = sum(page.word_count or 0 for page in book.pages)
        if total_words > 0:
            print(f"📊 إجمالي الكلمات: {total_words:,}")
        
        return {
            'success': True,
            'book_id': book_id,
            'output_path': output_path,
            'book': book,
            'stats': {
                'pages': len(book.pages),
                'chapters': len(book.index),
                'volumes': len(book.volumes),
                'authors': len(book.authors),
                'words': total_words
            }
        }
        
    except Exception as e:
        logger.error(f"فشل في استخراج الكتاب {book_id}: {e}")
        print(f"❌ خطأ في استخراج الكتاب: {e}")
        return {
            'success': False,
            'book_id': book_id,
            'error': str(e)
        }

def save_to_database(json_path: str, db_config: dict, config: PerformanceConfig = None) -> dict:
    """
    حفظ كتاب في قاعدة البيانات المحسنة
    """
    if config is None:
        config = PerformanceConfig()
        
    print(f"🗄️ حفظ البيانات في قاعدة البيانات...")
    print(f"📁 المسار: {json_path}")
    print(f"⚙️ إعدادات الأداء: batch={config.batch_size}, workers={config.max_workers}")
    print_separator()
    
    try:
        result = save_enhanced_json_to_database(json_path, db_config, config)
        
        print("✅ تم حفظ البيانات في قاعدة البيانات بنجاح!")
        print_separator()
        print(f"🆔 معرف الكتاب: {result['book_id']}")
        print(f"📄 الصفحات: {result['total_pages']}")
        print(f"📑 الفصول: {result['total_chapters']}")
        print(f"👥 المؤلفون: {result['total_authors']}")
        print(f"📚 الأجزاء: {result['total_volumes']}")
        
        if result.get('total_volume_links', 0) > 0:
            print(f"🔗 روابط المجلدات: {result['total_volume_links']}")
        
        if result.get('publisher'):
            print(f"🏢 الناشر: {result['publisher']}")
        
        if result.get('book_section'):
            print(f"📂 القسم: {result['book_section']}")
        
        if result.get('has_original_pagination'):
            print("✅ ترقيم أصلي: نعم")
        
        # إحصائيات الأداء
        if 'performance' in result:
            perf = result['performance']
            print(f"⏱️ زمن الحفظ: {perf['elapsed_time']:.2f} ثانية")
            print(f"⚡ سرعة الحفظ: {perf['pages_per_second']:.2f} صفحة/ثانية")
            if perf['parallel_enabled']:
                print(f"🔄 التوازي: مفعل ({perf['max_workers']} عمال)")
            print(f"📦 حجم الدفعة: {perf['batch_size']}")
        
        return {
            'success': True,
            'result': result
        }
        
    except Exception as e:
        logger.error(f"فشل في حفظ البيانات في قاعدة البيانات: {e}")
        print(f"❌ خطأ في حفظ قاعدة البيانات: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def check_book_in_database(book_id: str, db_config: dict) -> dict:
    """
    التحقق مما إذا كان الكتاب موجوداً بالفعل في قاعدة البيانات
    
    Args:
        book_id: معرف الكتاب في الشاملة
        db_config: إعدادات قاعدة البيانات
        
    Returns:
        dict: نتيجة التحقق مع مفتاح exists يشير إلى وجود الكتاب
    """
    try:
        # استخدام معرف الكتاب كما هو بدون إضافة BK
        shamela_id = book_id.strip()
        
        with EnhancedShamelaDatabaseManager(db_config) as db:
            exists = db.check_book_exists(shamela_id)
        
        return {
            'success': True,
            'exists': exists,
            'book_id': book_id,
            'shamela_id': shamela_id
        }
    except Exception as e:
        logger.error(f"فشل في التحقق من وجود الكتاب {book_id}: {e}")
        return {
            'success': False,
            'exists': False,
            'book_id': book_id,
            'error': str(e)
        }

def extract_and_save_book(book_id: str, max_pages: int = None, 
                         db_config: dict = None, output_dir: str = None) -> dict:
    """
    استخراج كتاب وحفظه في قاعدة البيانات
    ملاحظة: هذه الدالة تستخرج الكتاب مباشرة دون التحقق من وجوده مسبقاً.
    للتحقق من وجود الكتاب، استخدم الأمر check أولاً.
    """
    print_header()
    
    # استخراج الكتاب
    extraction_result = extract_book_full(book_id, max_pages, output_dir)
    
    if not extraction_result['success']:
        return extraction_result
    
    print_separator()
    
    # حفظ في قاعدة البيانات إذا تم توفير الإعدادات
    if db_config:
        db_result = save_to_database(extraction_result['output_path'], db_config)
        
        extraction_result['database'] = db_result
        
        if db_result['success']:
            extraction_result['database_book_id'] = db_result['result']['book_id']
    
    return extraction_result

def create_database_tables(db_config: dict) -> dict:
    """
    إنشاء جداول قاعدة البيانات المحسنة
    """
    print("🏗️ إنشاء جداول قاعدة البيانات المحسنة...")
    print_separator()
    
    try:
        with EnhancedShamelaDatabaseManager(db_config) as db:
            db.create_enhanced_tables()
        
        print("✅ تم إنشاء جداول قاعدة البيانات بنجاح!")
        
        return {'success': True}
        
    except Exception as e:
        logger.error(f"فشل في إنشاء جداول قاعدة البيانات: {e}")
        print(f"❌ خطأ في إنشاء جداول قاعدة البيانات: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_database_stats(book_id: int, db_config: dict) -> dict:
    """
    الحصول على إحصائيات كتاب من قاعدة البيانات
    """
    print(f"📊 جاري الحصول على إحصائيات الكتاب: {book_id}")
    print_separator()
    
    try:
        with EnhancedShamelaDatabaseManager(db_config) as db:
            stats = db.get_enhanced_book_stats(book_id)
        
        book = stats.get('book', {})
        
        print("📊 إحصائيات الكتاب:")
        print_separator()
        print(f"📚 العنوان: {book.get('title', 'غير محدد')}")
        print(f"🔢 معرف الشاملة: {book.get('shamela_id', 'غير محدد')}")
        
        if book.get('edition'):
            edition_info = f"📄 الطبعة: {book['edition']}"
            if book.get('edition_number'):
                edition_info += f" (رقم: {book['edition_number']})"
            print(edition_info)
        
        if book.get('publication_year'):
            year_info = f"📅 سنة النشر: {book['publication_year']} م"
            if book.get('edition_date_hijri'):
                year_info += f" ({book['edition_date_hijri']} هـ)"
            print(year_info)
        
        if book.get('publisher_name'):
            print(f"🏢 الناشر: {book['publisher_name']}")
        
        if book.get('section_name'):
            print(f"📂 القسم: {book['section_name']}")
        
        if book.get('has_original_pagination'):
            print("✅ ترقيم أصلي: نعم")
        else:
            print("❌ ترقيم أصلي: لا")
        
        print(f"📄 عدد الصفحات: {stats.get('pages_count', 0)}")
        print(f"📑 عدد الفصول: {stats.get('chapters_count', 0)}")
        print(f"👥 عدد المؤلفين: {stats.get('authors_count', 0)}")
        print(f"📚 عدد الأجزاء: {stats.get('volumes_count', 0)}")
        print(f"🔗 عدد روابط المجلدات: {stats.get('volume_links_count', 0)}")
        print(f"📊 إجمالي الكلمات: {stats.get('total_words', 0):,}")
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        logger.error(f"فشل في الحصول على الإحصائيات: {e}")
        print(f"❌ خطأ في الحصول على الإحصائيات: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """
    الوظيفة الرئيسية للسكربت
    """
    parser = argparse.ArgumentParser(
        description="سكربت المكتبة الشاملة المحسن - استخراج وحفظ الكتب مع جميع التحسينات",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:

1. استخراج كتاب فقط:
   python enhanced_runner.py extract 12106

2. استخراج كتاب وحفظه في قاعدة البيانات:
   python enhanced_runner.py extract 12106 --db-host localhost --db-user root --db-password secret --db-name bms

3. حفظ ملف JSON موجود في قاعدة البيانات:
   python enhanced_runner.py save-db enhanced_book_12106.json --db-host localhost --db-user root --db-password secret --db-name bms

4. إنشاء جداول قاعدة البيانات:
   python enhanced_runner.py create-tables --db-host localhost --db-user root --db-password secret --db-name bms

5. عرض إحصائيات كتاب من قاعدة البيانات:
   python enhanced_runner.py stats 123 --db-host localhost --db-user root --db-password secret --db-name bms

6. التحقق من وجود كتاب في قاعدة البيانات:
   python enhanced_runner.py check 12106 --db-host localhost --db-user root --db-password secret --db-name bms
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='الأوامر المتاحة')
    
    # أمر الاستخراج
    extract_parser = subparsers.add_parser('extract', help='استخراج كتاب من المكتبة الشاملة')
    extract_parser.add_argument('book_id', help='معرف الكتاب في المكتبة الشاملة')
    extract_parser.add_argument('--max-pages', type=int, help='العدد الأقصى للصفحات')
    extract_parser.add_argument('--output-dir', help='مجلد الإخراج')
    
    # أمر الحفظ في قاعدة البيانات
    save_parser = subparsers.add_parser('save-db', help='حفظ ملف JSON في قاعدة البيانات')
    save_parser.add_argument('json_file', help='مسار ملف JSON')
    
    # أمر إنشاء الجداول
    tables_parser = subparsers.add_parser('create-tables', help='إنشاء جداول قاعدة البيانات')
    
    # أمر الإحصائيات
    stats_parser = subparsers.add_parser('stats', help='عرض إحصائيات كتاب من قاعدة البيانات')
    stats_parser.add_argument('book_id', type=int, help='معرف الكتاب في قاعدة البيانات')
    
    # أمر التحقق من وجود الكتاب
    check_parser = subparsers.add_parser('check', help='التحقق من وجود كتاب في قاعدة البيانات')
    check_parser.add_argument('book_id', help='معرف الكتاب في المكتبة الشاملة')
    
    # إعدادات قاعدة البيانات (مشتركة)
    for subparser in [extract_parser, save_parser, tables_parser, stats_parser, check_parser]:
        subparser.add_argument('--db-host', default='localhost', help='عنوان قاعدة البيانات')
        subparser.add_argument('--db-port', type=int, default=3306, help='منفذ قاعدة البيانات')
        subparser.add_argument('--db-user', default='root', help='اسم المستخدم')
        subparser.add_argument('--db-password', help='كلمة مرور قاعدة البيانات')
        subparser.add_argument('--db-name', default='bms', help='اسم قاعدة البيانات')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # إعدادات قاعدة البيانات
    db_config = None
    if any([args.db_host, args.db_user, args.db_name]):
        # طلب كلمة المرور فقط إذا لم يتم تمريرها نهائياً ولم يتم تعيين متغير البيئة
        if args.db_password is None:
            # تحقق من وجود متغير البيئة لتجنب طلب كلمة المرور
            password_from_env = os.environ.get('DB_PASSWORD_PROVIDED')
            if password_from_env and password_from_env.lower() == 'true':
                # استخدام كلمة مرور فارغة إذا تم تحديد أنها متوفرة من البيئة
                args.db_password = ""
            else:
                import getpass
                args.db_password = getpass.getpass("كلمة مرور قاعدة البيانات: ")
        
        db_config = {
            'host': args.db_host,
            'port': args.db_port,
            'user': args.db_user,
            'password': args.db_password,
            'database': args.db_name
        }
    
    try:
        if args.command == 'extract':
            result = extract_and_save_book(
                args.book_id,
                max_pages=args.max_pages,
                db_config=db_config,
                output_dir=args.output_dir
            )
            
            if not result['success']:
                sys.exit(1)
        
        elif args.command == 'save-db':
            if not db_config:
                print("❌ خطأ: يجب تحديد إعدادات قاعدة البيانات")
                sys.exit(1)
            
            if not os.path.exists(args.json_file):
                print(f"❌ خطأ: الملف غير موجود: {args.json_file}")
                sys.exit(1)
            
            result = save_to_database(args.json_file, db_config)
            
            if not result['success']:
                sys.exit(1)
        
        elif args.command == 'create-tables':
            if not db_config:
                print("❌ خطأ: يجب تحديد إعدادات قاعدة البيانات")
                sys.exit(1)
            
            result = create_database_tables(db_config)
            
            if not result['success']:
                sys.exit(1)
        
        elif args.command == 'stats':
            if not db_config:
                print("❌ خطأ: يجب تحديد إعدادات قاعدة البيانات")
                sys.exit(1)
            
            result = get_database_stats(args.book_id, db_config)
            
            if not result['success']:
                sys.exit(1)
        
        elif args.command == 'check':
            if not db_config:
                print("❌ خطأ: يجب تحديد إعدادات قاعدة البيانات")
                sys.exit(1)
            
            result = check_book_in_database(args.book_id, db_config)
            
            if not result['success']:
                print(f"❌ خطأ في التحقق من الكتاب: {result.get('error', 'خطأ غير معروف')}")
                sys.exit(1)
            
            if result['exists']:
                print(f"✅ الكتاب {args.book_id} موجود في قاعدة البيانات")
                print_separator()
                print("🎉 تمت عملية التحقق بنجاح!")
                # رمز الخروج 0 = الكتاب موجود
                sys.exit(0)
            else:
                print(f"❌ الكتاب {args.book_id} غير موجود في قاعدة البيانات")
                # رمز الخروج 1 = الكتاب غير موجود - لا نطبع رسالة نجاح
                sys.exit(1)
        
        print_separator()
        print("🎉 تمت العملية بنجاح!")
        
    except KeyboardInterrupt:
        print("\n❌ تم إلغاء العملية بواسطة المستخدم")
        sys.exit(1)
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        print(f"❌ خطأ غير متوقع: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
