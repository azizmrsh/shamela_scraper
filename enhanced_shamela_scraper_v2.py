#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
محسن الشاملة المتقدم - النسخة الثانية
Enhanced Shamela Scraper V2 - Advanced Async & Multiprocessing

التحسينات الجديدة:
- معالجة غير متزامنة مع aiohttp
- معالجة متوازية متعددة العمليات  
- تحسين HTTP session متقدم
- معالجة HTML سريعة مع lxml
- نظام ذكي للتبديل حسب حجم الكتاب
- إدارة ذاكرة محسنة
"""

import asyncio
import aiohttp
import time
import json
import sys
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing as mp
from typing import List, Dict, Any, Optional, Tuple
import psutil
import os
from dataclasses import dataclass, asdict
from pathlib import Path

try:
    from lxml import html as lxml_html, etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    print("⚠️  lxml غير متوفر - سيتم استخدام BeautifulSoup (أبطأ)")

from bs4 import BeautifulSoup
import mysql.connector
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

# إعدادات التحسين المتقدمة
@dataclass
class AdvancedPerformanceConfig:
    """إعدادات الأداء المتقدمة"""
    
    # إعدادات HTTP المتقدمة
    max_connections: int = 100
    max_connections_per_host: int = 30
    connection_timeout: float = 15.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0
    
    # إعدادات المعالجة غير المتزامنة
    async_semaphore_limit: int = 15
    async_batch_size: int = 50
    retry_attempts: int = 5
    retry_delay: float = 0.5
    
    # إعدادات المعالجة المتوازية
    multiprocessing_threshold: int = 200
    max_processes: int = None
    process_chunk_size: int = 100
    
    # إعدادات التحسين
    enable_http2: bool = True
    enable_compression: bool = True
    enable_keepalive: bool = True
    dns_cache_ttl: int = 300
    
    # إعدادات الذاكرة
    memory_efficient: bool = False
    max_memory_mb: int = 2048
    gc_threshold: int = 1000
    
    def __post_init__(self):
        if self.max_processes is None:
            self.max_processes = min(mp.cpu_count(), 12)

class AdvancedHTTPSession:
    """جلسة HTTP متقدمة مع دعم HTTP/2 ومضاعفة الاتصالات"""
    
    def __init__(self, config: AdvancedPerformanceConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
        self.connector: Optional[aiohttp.TCPConnector] = None
        
    async def __aenter__(self):
        """إنشاء الجلسة عند الدخول"""
        # إعداد الموصل المتقدم
        self.connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections_per_host,
            ttl_dns_cache=self.config.dns_cache_ttl,
            use_dns_cache=True,
            keepalive_timeout=60 if self.config.enable_keepalive else 0,
            enable_cleanup_closed=True,
            force_close=not self.config.enable_keepalive,
            ssl=False  # لـ HTTP فقط في هذه الحالة
        )
        
        # إعداد المهلات الزمنية
        timeout = aiohttp.ClientTimeout(
            total=self.config.total_timeout,
            connect=self.config.connection_timeout,
            sock_read=self.config.read_timeout
        )
        
        # إعداد الرؤوس
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate' if self.config.enable_compression else 'identity',
            'Connection': 'keep-alive' if self.config.enable_keepalive else 'close',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # إنشاء الجلسة
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=timeout,
            headers=headers
        )
        
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """إغلاق الجلسة عند الخروج"""
        if self.session:
            await self.session.close()
        if self.connector:
            await self.connector.close()

class FastHTMLProcessor:
    """معالج HTML سريع باستخدام lxml أو BeautifulSoup"""
    
    @staticmethod
    def extract_page_content(html: str, page_num: int) -> Optional[Dict[str, Any]]:
        """استخراج محتوى الصفحة بأسرع طريقة ممكنة"""
        try:
            if LXML_AVAILABLE:
                return FastHTMLProcessor._extract_with_lxml(html, page_num)
            else:
                return FastHTMLProcessor._extract_with_bs4(html, page_num)
        except Exception as e:
            logging.error(f"خطأ في معالجة HTML للصفحة {page_num}: {e}")
            return None
    
    @staticmethod
    def _extract_with_lxml(html: str, page_num: int) -> Dict[str, Any]:
        """استخراج باستخدام lxml (الأسرع)"""
        try:
            tree = lxml_html.fromstring(html)
            
            # استخراج المحتوى الرئيسي
            content_elements = tree.xpath("//div[@class='nass']")
            if not content_elements:
                content_elements = tree.xpath("//div[contains(@class, 'text')]")
            
            if content_elements:
                content_elem = content_elements[0]
                text_content = content_elem.text_content().strip()
                html_content = lxml_html.tostring(content_elem, encoding='unicode', method='html')
                
                # استخراج معلومات إضافية
                word_count = len(text_content.split())
                char_count = len(text_content)
                
                return {
                    'page_number': page_num,
                    'content': text_content,
                    'html_content': html_content,
                    'word_count': word_count,
                    'char_count': char_count,
                    'extracted_at': datetime.now().isoformat(),
                    'extraction_method': 'lxml'
                }
            
        except Exception:
            # تراجع إلى BeautifulSoup
            pass
        
        return FastHTMLProcessor._extract_with_bs4(html, page_num)
    
    @staticmethod
    def _extract_with_bs4(html: str, page_num: int) -> Dict[str, Any]:
        """استخراج باستخدام BeautifulSoup (بديل)"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # البحث عن المحتوى
        content_div = soup.find('div', class_='nass')
        if not content_div:
            content_div = soup.find('div', class_=re.compile(r'text|content'))
        
        if content_div:
            text_content = content_div.get_text().strip()
            html_content = str(content_div)
            
            return {
                'page_number': page_num,
                'content': text_content,
                'html_content': html_content,
                'word_count': len(text_content.split()),
                'char_count': len(text_content),
                'extracted_at': datetime.now().isoformat(),
                'extraction_method': 'beautifulsoup'
            }
        
        return {
            'page_number': page_num,
            'content': '',
            'html_content': '',
            'word_count': 0,
            'char_count': 0,
            'extracted_at': datetime.now().isoformat(),
            'extraction_method': 'failed'
        }

class AsyncPageExtractor:
    """مستخرج الصفحات غير المتزامن"""
    
    def __init__(self, config: AdvancedPerformanceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def extract_pages_batch(self, book_id: int, page_range: Tuple[int, int], 
                                 session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """استخراج دفعة من الصفحات بشكل غير متزامن"""
        start_page, end_page = page_range
        semaphore = asyncio.Semaphore(self.config.async_semaphore_limit)
        
        async def extract_single_page(page_num: int) -> Optional[Dict[str, Any]]:
            async with semaphore:
                for attempt in range(self.config.retry_attempts):
                    try:
                        url = f"https://shamela.ws/book/{book_id}/{page_num}"
                        
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text()
                                result = FastHTMLProcessor.extract_page_content(html, page_num)
                                if result:
                                    self.logger.debug(f"✅ استخراج ناجح للصفحة {page_num}")
                                    return result
                            
                            elif response.status == 404:
                                self.logger.warning(f"❌ صفحة غير موجودة: {page_num}")
                                return None
                            
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                        
                    except Exception as e:
                        if attempt == self.config.retry_attempts - 1:
                            self.logger.error(f"❌ فشل نهائي في صفحة {page_num}: {e}")
                        else:
                            await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                
                return None
        
        # إنشاء المهام
        tasks = [extract_single_page(page) for page in range(start_page, end_page + 1)]
        
        # تنفيذ المهام مع تجميع النتائج
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # فلترة النتائج الصحيحة
        valid_results = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                valid_results.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"خطأ في المعالجة: {result}")
        
        return valid_results

class MultiprocessExtractor:
    """مستخرج متعدد العمليات للكتب الضخمة"""
    
    def __init__(self, config: AdvancedPerformanceConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def extract_book_parallel(self, book_id: int, total_pages: int) -> List[Dict[str, Any]]:
        """استخراج كتاب باستخدام معالجة متوازية متعددة العمليات"""
        
        # تقسيم الصفحات إلى قطع
        chunks = self._create_page_chunks(total_pages)
        
        self.logger.info(f"🚀 معالجة متوازية: {len(chunks)} دفعة على {self.config.max_processes} عملية")
        
        # معالجة متوازية
        all_pages = []
        with ProcessPoolExecutor(max_workers=self.config.max_processes) as executor:
            # إرسال المهام
            future_to_chunk = {
                executor.submit(extract_chunk_worker, book_id, chunk, asdict(self.config)): chunk 
                for chunk in chunks
            }
            
            # جمع النتائج
            for i, future in enumerate(as_completed(future_to_chunk)):
                chunk = future_to_chunk[future]
                try:
                    chunk_pages = future.result(timeout=600)  # 10 دقائق لكل دفعة
                    all_pages.extend(chunk_pages)
                    
                    start_page, end_page = chunk
                    self.logger.info(f"✅ انتهت الدفعة {i+1}/{len(chunks)} "
                                   f"(صفحات {start_page}-{end_page}): {len(chunk_pages)} صفحة")
                    
                except Exception as e:
                    start_page, end_page = chunk
                    self.logger.error(f"❌ فشلت الدفعة {i+1} (صفحات {start_page}-{end_page}): {e}")
        
        # ترتيب النتائج
        return sorted(all_pages, key=lambda x: x.get('page_number', 0))
    
    def _create_page_chunks(self, total_pages: int) -> List[Tuple[int, int]]:
        """تقسيم الصفحات إلى قطع للمعالجة المتوازية"""
        chunk_size = max(self.config.process_chunk_size, 
                        total_pages // self.config.max_processes)
        
        chunks = []
        for i in range(1, total_pages + 1, chunk_size):
            end = min(i + chunk_size - 1, total_pages)
            chunks.append((i, end))
        
        return chunks

def extract_chunk_worker(book_id: int, page_range: Tuple[int, int], 
                        config_dict: dict) -> List[Dict[str, Any]]:
    """عامل لاستخراج قطعة من الصفحات في عملية منفصلة"""
    # تحويل القاموس إلى إعدادات
    config = AdvancedPerformanceConfig(**config_dict)
    
    # إنشاء حلقة جديدة للعملية
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(extract_chunk_async(book_id, page_range, config))
    finally:
        loop.close()

async def extract_chunk_async(book_id: int, page_range: Tuple[int, int], 
                             config: AdvancedPerformanceConfig) -> List[Dict[str, Any]]:
    """استخراج قطعة باستخدام async في عملية منفصلة"""
    extractor = AsyncPageExtractor(config)
    
    async with AdvancedHTTPSession(config) as session:
        return await extractor.extract_pages_batch(book_id, page_range, session)

class BookInfoExtractor:
    """مستخرج معلومات الكتاب الأساسية"""
    
    @staticmethod
    async def get_book_info(book_id: int, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """استخراج معلومات الكتاب الأساسية"""
        try:
            url = f"https://shamela.ws/book/{book_id}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return BookInfoExtractor._parse_book_info(html, book_id)
                    
        except Exception as e:
            logging.error(f"خطأ في استخراج معلومات الكتاب {book_id}: {e}")
        
        return BookInfoExtractor._get_default_book_info(book_id)
    
    @staticmethod  
    def _parse_book_info(html: str, book_id: int) -> Dict[str, Any]:
        """تحليل معلومات الكتاب من HTML"""
        # تحليل بسيط للحصول على العدد التقريبي للصفحات
        # يمكن تحسينه لاحقاً لاستخراج معلومات أكثر دقة
        
        if LXML_AVAILABLE:
            try:
                tree = lxml_html.fromstring(html)
                # البحث عن روابط الصفحات أو معلومات أخرى
                page_links = tree.xpath("//a[contains(@href, '/book/%d/')]" % book_id)
                estimated_pages = len(page_links) if page_links else 100
            except:
                estimated_pages = 100
        else:
            soup = BeautifulSoup(html, 'html.parser')
            page_links = soup.find_all('a', href=re.compile(f'/book/{book_id}/'))
            estimated_pages = len(page_links) if page_links else 100
        
        return {
            'book_id': book_id,
            'estimated_pages': max(estimated_pages, 50),  # حد أدنى 50 صفحة
            'title': f'كتاب رقم {book_id}',  # يمكن تحسينه
            'author': 'غير محدد',  # يمكن تحسينه
            'extraction_date': datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_default_book_info(book_id: int) -> Dict[str, Any]:
        """معلومات افتراضية للكتاب"""
        return {
            'book_id': book_id,
            'estimated_pages': 100,
            'title': f'كتاب رقم {book_id}',
            'author': 'غير محدد',
            'extraction_date': datetime.now().isoformat()
        }

class AdvancedShamelaScraper:
    """مستخرج الشاملة المتقدم - النسخة الثانية"""
    
    def __init__(self, config: AdvancedPerformanceConfig = None):
        self.config = config or AdvancedPerformanceConfig()
        self.logger = self._setup_logging()
        
        # مكونات الاستخراج
        self.async_extractor = AsyncPageExtractor(self.config)
        self.multiprocess_extractor = MultiprocessExtractor(self.config)
    
    def _setup_logging(self) -> logging.Logger:
        """إعداد نظام التسجيل"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # معالج الملف
            file_handler = logging.FileHandler('enhanced_shamela_v2.log', encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - [%(processName)s-%(threadName)s] - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # معالج وحدة التحكم
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    async def extract_book(self, book_id: int, **kwargs) -> Dict[str, Any]:
        """استخراج كتاب كامل بأقصى سرعة ممكنة"""
        start_time = time.time()
        
        self.logger.info(f"🚀 بدء الاستخراج المتقدم للكتاب {book_id}")
        
        try:
            # الحصول على معلومات الكتاب
            async with AdvancedHTTPSession(self.config) as session:
                book_info = await BookInfoExtractor.get_book_info(book_id, session)
                total_pages = book_info['estimated_pages']
                
                self.logger.info(f"📚 معلومات الكتاب: {total_pages} صفحة متوقعة")
                
                # اختيار طريقة الاستخراج حسب الحجم
                if total_pages <= self.config.multiprocessing_threshold:
                    self.logger.info(f"📖 كتاب صغير/متوسط - استخدام المعالجة غير المتزامنة")
                    pages = await self._extract_async_method(book_id, total_pages, session)
                else:
                    self.logger.info(f"📚 كتاب ضخم - استخدام المعالجة متعددة العمليات")
                    pages = self.multiprocess_extractor.extract_book_parallel(book_id, total_pages)
            
            # حساب الإحصائيات
            elapsed = time.time() - start_time
            pages_per_second = len(pages) / elapsed if elapsed > 0 else 0
            
            # إحصائيات المحتوى
            total_words = sum(page.get('word_count', 0) for page in pages)
            total_chars = sum(page.get('char_count', 0) for page in pages)
            
            result = {
                'book_id': book_id,
                'book_info': book_info,
                'pages': pages,
                'statistics': {
                    'total_pages': len(pages),
                    'extraction_time': elapsed,
                    'pages_per_second': pages_per_second,
                    'total_words': total_words,
                    'total_chars': total_chars,
                    'average_words_per_page': total_words / len(pages) if pages else 0,
                    'extraction_method': 'multiprocessing' if total_pages > self.config.multiprocessing_threshold else 'async'
                },
                'config_used': asdict(self.config),
                'extraction_date': datetime.now().isoformat()
            }
            
            self.logger.info(f"🎉 انتهى الاستخراج المتقدم: {len(pages)} صفحة في {elapsed:.2f} ثانية")
            self.logger.info(f"⚡ السرعة المحققة: {pages_per_second:.2f} صفحة/ثانية")
            self.logger.info(f"📊 إجمالي الكلمات: {total_words:,} كلمة")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في استخراج الكتاب {book_id}: {e}")
            raise
    
    async def _extract_async_method(self, book_id: int, total_pages: int, 
                                   session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """استخراج باستخدام الطريقة غير المتزامنة"""
        
        # تقسيم إلى دفعات
        batch_size = self.config.async_batch_size
        all_pages = []
        
        for i in range(1, total_pages + 1, batch_size):
            end_page = min(i + batch_size - 1, total_pages)
            
            self.logger.info(f"📄 معالجة الدفعة: صفحات {i}-{end_page}")
            
            batch_pages = await self.async_extractor.extract_pages_batch(
                book_id, (i, end_page), session
            )
            
            all_pages.extend(batch_pages)
            
            self.logger.info(f"✅ انتهت الدفعة: {len(batch_pages)} صفحة")
            
            # تنظيف الذاكرة إذا لزم الأمر
            if self.config.memory_efficient and len(all_pages) % self.config.gc_threshold == 0:
                import gc
                gc.collect()
        
        return sorted(all_pages, key=lambda x: x.get('page_number', 0))

async def main():
    """الدالة الرئيسية للاختبار"""
    # إعداد متقدم للأداء العالي
    config = AdvancedPerformanceConfig(
        max_connections=150,
        max_connections_per_host=50,
        async_semaphore_limit=20,
        multiprocessing_threshold=100,
        max_processes=8
    )
    
    # إنشاء المستخرج
    scraper = AdvancedShamelaScraper(config)
    
    # اختبار على كتاب
    book_id = int(sys.argv[1]) if len(sys.argv) > 1 else 41
    
    try:
        result = await scraper.extract_book(book_id)
        
        # حفظ النتائج
        output_file = f"book_{book_id}_advanced_v2.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n🎉 تم حفظ النتائج في: {output_file}")
        print(f"📊 الإحصائيات:")
        stats = result['statistics']
        print(f"   - الصفحات: {stats['total_pages']}")
        print(f"   - الوقت: {stats['extraction_time']:.2f} ثانية")
        print(f"   - السرعة: {stats['pages_per_second']:.2f} صفحة/ثانية")
        print(f"   - الكلمات: {stats['total_words']:,}")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
