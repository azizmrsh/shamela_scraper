#!/usr/bin/env python3
"""
نظام استخراج فائق الموثوقية - Ultra Reliable Scraper
موثوقية 100% مع معالجة شاملة للأخطاء
"""

import time
import logging
import traceback
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import json
import gzip
import os
from datetime import datetime

# استيراد الوحدات الأساسية
try:
    from enhanced_shamela_scraper import scrape_enhanced_book, PerformanceConfig, Book
    from enhanced_database_manager import save_enhanced_json_to_database
except ImportError as e:
    print(f"خطأ في الاستيراد: {e}")
    print("تأكد من وجود الملفات المطلوبة")

@dataclass
class ReliabilityConfig:
    """تكوين الموثوقية الفائقة"""
    max_retries: int = 5  # محاولات إضافية
    retry_delay: float = 2.0  # تأخير بين المحاولات
    exponential_backoff: bool = True  # زيادة التأخير تدريجياً
    verify_extraction: bool = True  # تحقق من النتائج
    auto_recovery: bool = True  # استرداد تلقائي
    save_progress: bool = True  # حفظ التقدم
    detailed_logging: bool = True  # سجلات مفصلة

class UltraReliableScraper:
    """سكربت فائق الموثوقية"""
    
    def __init__(self, config: ReliabilityConfig = None):
        self.reliability_config = config or ReliabilityConfig()
        self.setup_logging()
        self.failed_pages = []
        self.progress_file = None
        
    def setup_logging(self):
        """إعداد نظام تسجيل مفصل"""
        log_format = '%(asctime)s - [%(levelname)s] - %(funcName)s:%(lineno)d - %(message)s'
        
        # إنشاء مجلد السجلات
        os.makedirs('logs', exist_ok=True)
        
        # تكوين التسجيل
        logging.basicConfig(
            level=logging.DEBUG if self.reliability_config.detailed_logging else logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(f'logs/ultra_reliable_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🛡️ تم تفعيل نظام الموثوقية الفائقة")

    def get_optimal_config(self, estimated_pages: int = None) -> PerformanceConfig:
        """الحصول على التكوين الأمثل والأكثر استقراراً"""
        config = PerformanceConfig()
        
        # إعدادات موثوقة ومجربة
        config.use_async = False  # طريقة تقليدية مضمونة
        config.use_lxml = True
        config.enable_caching = True
        config.max_retries = 3
        config.timeout = 30  # وقت انتظار كافي
        config.request_delay = 0.5  # تأخير آمن لتجنب الحظر
        
        # تكوين حسب الحجم المقدر
        if estimated_pages and estimated_pages > 1000:
            # كتب ضخمة - إعدادات محافظة
            config.max_workers = 8
            config.batch_size = 1000
            config.connection_pool_size = 8
            config.request_delay = 1.0
        elif estimated_pages and estimated_pages > 500:
            # كتب كبيرة - إعدادات متوازنة
            config.max_workers = 12
            config.batch_size = 1500
            config.connection_pool_size = 12
            config.request_delay = 0.7
        else:
            # كتب صغيرة-متوسطة - إعدادات سريعة
            config.max_workers = 16
            config.batch_size = 2000
            config.connection_pool_size = 16
            config.request_delay = 0.5
            
        self.logger.info(f"⚙️ تكوين مُحسَّن: workers={config.max_workers}, delay={config.request_delay}s")
        return config

    def verify_book_extraction(self, book: Book, expected_pages: int = None) -> bool:
        """التحقق من صحة الاستخراج"""
        try:
            # فحوصات أساسية
            if not book:
                self.logger.error("❌ الكتاب فارغ")
                return False
                
            if not book.title:
                self.logger.error("❌ عنوان الكتاب فارغ")
                return False
                
            if not book.pages:
                self.logger.error("❌ لا توجد صفحات مستخرجة")
                return False
                
            # فحص جودة المحتوى
            empty_pages = [p for p in book.pages if not p.content or len(p.content.strip()) < 10]
            if len(empty_pages) > len(book.pages) * 0.5:  # أكثر من 50% فارغة
                self.logger.error(f"❌ {len(empty_pages)} صفحة فارغة من {len(book.pages)}")
                return False
                
            # فحص التسلسل
            page_numbers = [p.page_number for p in book.pages]
            if len(page_numbers) != len(set(page_numbers)):
                self.logger.error("❌ أرقام صفحات مكررة")
                return False
                
            # فحص المحتوى العربي
            arabic_pages = 0
            for page in book.pages[:min(5, len(book.pages))]:  # فحص أول 5 صفحات
                if any('\u0600' <= char <= '\u06FF' for char in page.content):
                    arabic_pages += 1
                    
            if arabic_pages == 0:
                self.logger.warning("⚠️ لا يوجد محتوى عربي في الصفحات المفحوصة")
                
            self.logger.info(f"✅ التحقق نجح: {len(book.pages)} صفحة، {len(empty_pages)} فارغة")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في التحقق: {str(e)}")
            return False

    def extract_with_retry(self, book_id: str, max_pages: int = None, config: PerformanceConfig = None) -> Optional[Book]:
        """استخراج مع إعادة المحاولة التلقائية"""
        
        for attempt in range(self.reliability_config.max_retries + 1):
            try:
                self.logger.info(f"🔄 المحاولة {attempt + 1}/{self.reliability_config.max_retries + 1} للكتاب {book_id}")
                
                # تنفيذ الاستخراج
                book = scrape_enhanced_book(book_id, max_pages=max_pages, extract_content=True, config=config)
                
                # التحقق من النتيجة
                if self.reliability_config.verify_extraction:
                    if not self.verify_book_extraction(book, max_pages):
                        raise Exception("فشل في التحقق من جودة الاستخراج")
                
                self.logger.info(f"✅ نجح استخراج الكتاب {book_id} في المحاولة {attempt + 1}")
                return book
                
            except Exception as e:
                self.logger.error(f"❌ فشل في المحاولة {attempt + 1}: {str(e)}")
                
                if attempt < self.reliability_config.max_retries:
                    # حساب زمن التأخير
                    if self.reliability_config.exponential_backoff:
                        delay = self.reliability_config.retry_delay * (2 ** attempt)
                    else:
                        delay = self.reliability_config.retry_delay
                    
                    self.logger.info(f"⏳ انتظار {delay} ثانية قبل المحاولة التالية...")
                    time.sleep(delay)
                    
                    # تعديل التكوين للمحاولة التالية
                    if config:
                        config.request_delay += 0.5  # زيادة التأخير
                        config.max_workers = max(4, config.max_workers - 2)  # تقليل العمال
                        self.logger.info(f"🔧 تعديل التكوين: delay={config.request_delay}, workers={config.max_workers}")
                else:
                    self.logger.error(f"💥 فشل نهائياً في استخراج الكتاب {book_id} بعد {self.reliability_config.max_retries + 1} محاولة")
                    
        return None

    def save_with_verification(self, book: Book, output_dir: str) -> Optional[str]:
        """حفظ مع التحقق من سلامة الملف"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # إنشاء اسم الملف
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ultra_reliable_book_{book.shamela_id}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # تحويل إلى dict مع جميع البيانات الوصفية - مع معالجة جميع الكائنات المعقدة
            def safe_convert(obj, attr, default=None):
                """تحويل آمن للكائنات المعقدة"""
                if not hasattr(obj, attr):
                    return default
                value = getattr(obj, attr)
                if value is None:
                    return default
                if hasattr(value, 'name'):
                    return value.name
                if isinstance(value, (str, int, bool, float)):
                    return value
                if isinstance(value, list):
                    return [item.name if hasattr(item, 'name') else str(item) for item in value]
                return str(value)
            
            book_data = {
                "title": book.title,
                "shamela_id": book.shamela_id,
                "authors": [{"name": author.name} for author in book.authors] if book.authors else [],
                "publisher": safe_convert(book, 'publisher'),
                "book_section": safe_convert(book, 'book_section'),
                "edition": safe_convert(book, 'edition'),
                "edition_number": safe_convert(book, 'edition_number'),
                "publication_year": safe_convert(book, 'publication_year'),
                "edition_date_hijri": safe_convert(book, 'edition_date_hijri'),
                "page_count": safe_convert(book, 'page_count'),
                "volume_count": safe_convert(book, 'volume_count'),
                "categories": safe_convert(book, 'categories', []),
                "description": safe_convert(book, 'description'),
                "source_url": safe_convert(book, 'source_url'),
                "has_original_pagination": safe_convert(book, 'has_original_pagination', False),
                
                # إضافة الفصول والأجزاء
                "chapters": [
                    {
                        "title": chapter.title,
                        "page_start": chapter.page_number,
                        "page_end": chapter.page_end,
                        "volume": chapter.volume_number if hasattr(chapter, 'volume_number') else None,
                        "order": chapter.order if hasattr(chapter, 'order') else None,
                        "level": chapter.level if hasattr(chapter, 'level') else None
                    } for chapter in book.chapters
                ] if hasattr(book, 'chapters') and book.chapters else [],
                
                "volumes": [
                    {
                        "volume_number": vol.number,
                        "page_start": vol.page_start,
                        "page_end": vol.page_end,
                        "title": vol.title if hasattr(vol, 'title') else f"الجزء {vol.number}"
                    } for vol in book.volumes
                ] if hasattr(book, 'volumes') and book.volumes else [],
                
                "pages": [{"page_number": p.page_number, "content": p.content, "word_count": p.word_count} 
                         for p in book.pages],
                "extraction_metadata": {
                    "extraction_date": datetime.now().isoformat(),
                    "total_pages": len(book.pages),
                    "total_words": sum(p.word_count for p in book.pages),
                    "total_chapters": len(book.chapters) if hasattr(book, 'chapters') and book.chapters else 0,
                    "total_volumes": len(book.volumes) if hasattr(book, 'volumes') and book.volumes else 0,
                    "reliability_verified": True,
                    "scraper_version": "Ultra Reliable v3.1",
                    "extraction_method": "enhanced_reliability_with_structure"
                }
            }
            
            # حفظ بصيغة JSON مضغوط
            with gzip.open(f"{filepath}.gz", 'wt', encoding='utf-8') as f:
                json.dump(book_data, f, ensure_ascii=False, indent=2)
            
            # التحقق من الحفظ
            try:
                with gzip.open(f"{filepath}.gz", 'rt', encoding='utf-8') as f:
                    verified_data = json.load(f)
                    
                if len(verified_data['pages']) != len(book.pages):
                    raise Exception("عدد الصفحات المحفوظة لا يطابق الأصل")
                    
                self.logger.info(f"💾 تم الحفظ والتحقق: {filepath}.gz")
                return f"{filepath}.gz"
                
            except Exception as ve:
                self.logger.error(f"❌ فشل في التحقق من الملف المحفوظ: {str(ve)}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في الحفظ: {str(e)}")
            return None

    def extract_book_ultra_reliable(self, book_id: str, max_pages: int = None, output_dir: str = None) -> Dict[str, Any]:
        """الدالة الرئيسية للاستخراج فائق الموثوقية"""
        
        start_time = time.time()
        result = {
            "book_id": book_id,
            "success": False,
            "error": None,
            "filepath": None,
            "stats": {},
            "attempts": 0
        }
        
        try:
            self.logger.info(f"🚀 بدء الاستخراج فائق الموثوقية للكتاب {book_id}")
            
            # الحصول على التكوين الأمثل
            config = self.get_optimal_config(max_pages)
            
            # الاستخراج مع إعادة المحاولة
            book = self.extract_with_retry(book_id, max_pages, config)
            
            if not book:
                result["error"] = "فشل في الاستخراج بعد جميع المحاولات"
                return result
            
            # الحفظ مع التحقق
            output_dir = output_dir or "ultra_reliable_books"
            filepath = self.save_with_verification(book, output_dir)
            
            if not filepath:
                result["error"] = "فشل في حفظ الملف"
                return result
            
            # إحصائيات النجاح
            elapsed_time = time.time() - start_time
            result.update({
                "success": True,
                "filepath": filepath,
                "stats": {
                    "pages_extracted": len(book.pages),
                    "total_words": sum(p.word_count for p in book.pages),
                    "extraction_time": elapsed_time,
                    "speed": len(book.pages) / elapsed_time if elapsed_time > 0 else 0,
                    "title": book.title
                }
            })
            
            self.logger.info(f"🎉 اكتمل بنجاح: {len(book.pages)} صفحة في {elapsed_time:.2f}ث")
            return result
            
        except Exception as e:
            error_msg = f"خطأ غير متوقع: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            self.logger.debug(traceback.format_exc())
            
            result["error"] = error_msg
            return result

def main():
    """الدالة الرئيسية للاختبار"""
    
    print("🛡️ اختبار النظام فائق الموثوقية")
    print("=" * 50)
    
    # إنشاء المُستخرِج
    scraper = UltraReliableScraper()
    
    # اختبار مع كتاب صغير
    result = scraper.extract_book_ultra_reliable("12106", max_pages=20)
    
    if result["success"]:
        stats = result["stats"]
        print(f"\n✅ نجح الاستخراج!")
        print(f"📚 العنوان: {stats['title']}")
        print(f"📄 الصفحات: {stats['pages_extracted']}")
        print(f"📝 الكلمات: {stats['total_words']:,}")
        print(f"⏱️ الوقت: {stats['extraction_time']:.2f}ث")
        print(f"🏎️ السرعة: {stats['speed']:.2f} صفحة/ثانية")
        print(f"💾 الملف: {result['filepath']}")
    else:
        print(f"\n❌ فشل الاستخراج: {result['error']}")

if __name__ == "__main__":
    main()
