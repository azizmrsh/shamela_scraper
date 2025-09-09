# -*- coding: utf-8 -*-
"""
Enhanced Shamela Scraper - سكربت محسن لسحب الكتب من المكتبة الشاملة
يعالج المشاكل المطروحة في استخراج البيانات وتخزينها

التحسينات الجديدة:
- استخراج تاريخ الإصدار وتحويله للهجري
- استخراج رقم الطبعة كقيمة عددية
- معالجة بيانات الناشر مع جدول منفصل
- معالجة بيانات القسم مع جدول منفصل
- تخزين بطاقة الكتاب الكاملة
- معالجة الكتب متعددة المجلدات
- ترتيب الفهرس المحسن
- ترقيم الصفحات الصحيح

تحسينات الأداء:
- دعم التنفيذ المتوازي للصفحات
- تحسين I/O مع تدفق البيانات
- تقليل استهلاك الذاكرة
- آلية استئناف محسنة
- تسجيل محسن مع تدوير الملفات
"""

from __future__ import annotations
import re, json, time, os, sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Union, Any
import asyncio
import aiohttp
try:
    from lxml import html as lxml_html, etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    print("⚠️  lxml غير متوفر - سيتم استخدام BeautifulSoup (أبطأ)")

import requests
from bs4 import BeautifulSoup
import argparse
from pathlib import Path
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import threading
import multiprocessing as mp
from logging.handlers import RotatingFileHandler
import hashlib
from functools import lru_cache
import io
import gzip
import psutil

# إعداد التسجيل المحسن مع تدوير الملفات
def setup_logging(debug_mode: bool = False, max_log_size: int = 10 * 1024 * 1024, backup_count: int = 5):
    """إعداد نظام التسجيل المحسن"""
    log_level = logging.DEBUG if debug_mode else logging.INFO
    
    # إنشاء محسن مع تدوير
    log_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s'
    )
    
    # ملف دوار
    file_handler = RotatingFileHandler(
        'enhanced_shamela_scraper.log',
        maxBytes=max_log_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level)
    
    # معالج وحدة التحكم
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.WARNING if not debug_mode else logging.DEBUG)
    
    # إعداد المسجل الرئيسي
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    logger.handlers = []  # مسح المعالجات القديمة
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# إعداد التسجيل الافتراضي
logger = setup_logging()

# ========= أعلام الأداء المتقدمة =========
@dataclass
class PerformanceConfig:
    """إعدادات الأداء المحسنة مع التحسينات المتقدمة"""
    # إعدادات HTTP المتقدمة
    max_connections: int = 100
    max_connections_per_host: int = 30
    connection_timeout: float = 15.0
    read_timeout: float = 30.0
    total_timeout: float = 60.0
    
    # إعدادات المعالجة التقليدية
    max_workers: int = 4
    batch_size: int = 500
    timeout: int = 30
    retries: int = 5
    rate_limit: float = 0.3
    
    # إعدادات المعالجة المتقدمة
    use_async: bool = True
    async_semaphore_limit: int = 15
    async_batch_size: int = 50
    multiprocessing_threshold: int = 200
    max_processes: int = None
    process_chunk_size: int = 100
    
    # خيارات التحسينات المتقدمة الجديدة
    aiohttp_workers: int = 8
    use_lxml: bool = False
    force_traditional: bool = False
    
    # تحسينات الشبكة
    enable_http2: bool = True
    enable_compression: bool = False  # تم تعطيل ضغط ملفات JSON
    enable_keepalive: bool = True
    dns_cache_ttl: int = 300
    
    # تحسينات الذاكرة والأداء
    stream_json: bool = False
    skip_existing: bool = True
    resume_enabled: bool = True
    memory_efficient: bool = True
    max_memory_mb: int = 2048
    gc_threshold: int = 1000
    debug: bool = False
    
    def __post_init__(self):
        if self.max_processes is None:
            self.max_processes = min(mp.cpu_count(), 8)

# ========= الثوابت =========
BASE_URL = "https://shamela.ws"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
REQ_TIMEOUT = 30
REQUEST_DELAY = 0.5
MAX_RETRIES = 3

# أسماء الجداول
DB_TABLES = {
    'books': 'books',
    'authors': 'authors',
    'publishers': 'publishers',
    'book_sections': 'book_sections',
    'volumes': 'volumes',
    'chapters': 'chapters',
    'pages': 'pages',
    'author_book': 'author_book',
    'volume_links': 'volume_links'
}

def normalize_book_id(book_id: str) -> str:
    """تطبيع معرف الكتاب - يقبل BK000043 أو 43 ويحولهما إلى 43"""
    book_id = book_id.strip()
    if book_id.startswith('BK'):
        # إزالة BK والأصفار البادئة
        return str(int(book_id[2:]))
    return book_id

# ========= مخزن ذاكرة التخزين المؤقت المحسن =========
class OptimizedCache:
    """ذاكرة تخزين مؤقت محسنة مع حد أقصى للحجم"""
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key: str, default=None):
        if key in self.cache:
            # تحريك إلى النهاية (الأحدث استخداماً)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return default
    
    def set(self, key: str, value):
        if key in self.cache:
            self.cache[key] = value
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # إضافة عنصر جديد
            if len(self.cache) >= self.max_size:
                # إزالة الأقل استخداماً
                oldest = self.access_order.pop(0)
                del self.cache[oldest]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def clear(self):
        self.cache.clear()
        self.access_order.clear()

# مخزن مؤقت عام
global_cache = OptimizedCache()

# ========= جلسة HTTP محسنة =========
class OptimizedHTTPSession:
    """جلسة HTTP محسنة مع تجمع الاتصالات"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'session'):
            self.session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=20,
                max_retries=requests.adapters.Retry(
                    total=3,
                    backoff_factor=1,
                    status_forcelist=[500, 502, 503, 504]
                )
            )
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            self.session.headers.update(HEADERS)
    
    def get(self, url: str, **kwargs):
        return self.session.get(url, **kwargs)
    
    def close(self):
        if hasattr(self, 'session'):
            self.session.close()

# جلسة HTTP عامة
http_session = OptimizedHTTPSession()

# ========= جلسة HTTP متقدمة غير متزامنة =========
class AdvancedHTTPSession:
    """جلسة HTTP متقدمة مع دعم aiohttp"""
    
    def __init__(self, config: PerformanceConfig):
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
            ssl=False
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

# ========= معالج HTML سريع =========
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
            logger.error(f"خطأ في معالجة HTML للصفحة {page_num}: {e}")
            return None
    
    @staticmethod
    def _extract_with_lxml(html: str, page_num: int) -> Dict[str, Any]:
        """استخراج باستخدام lxml (الأسرع)"""
        try:
            tree = lxml_html.fromstring(html)
            
            # التركيز على div.nass أولاً - هو الحاوي الصحيح للمحتوى
            content_selectors = [
                "//div[@class='nass']",  # هذا هو الحاوي الرئيسي للمحتوى في شاملة
                "//div[@id='book']", 
                "//div[@id='text']", 
                "//article", 
                "//div[contains(@class, 'reader-text')]",
                "//div[contains(@class, 'col-md-9')]",
                "//div[contains(@class, 'book-content')]", 
                "//div[contains(@class, 'page-content')]", 
                "//main"
            ]
            
            content_elem = None
            for selector in content_selectors:
                elements = tree.xpath(selector)
                if elements:
                    content_elem = elements[0]
                    break
            
            if not content_elem:
                # استخدام body كاحتياط
                body_elements = tree.xpath("//body")
                if body_elements:
                    content_elem = body_elements[0]
                else:
                    content_elem = tree
            
            if content_elem is not None:
                # إزالة العناصر غير المرغوبة
                unwanted_xpath = [
                    ".//script", ".//style", ".//nav", ".//*[contains(@class, 'share')]",
                    ".//*[contains(@class, 'social')]", ".//*[contains(@class, 'ad')]",
                    ".//*[contains(@class, 'advertisement')]", ".//*[contains(@class, 'menu')]",
                    ".//*[contains(@class, 'sidebar')]", ".//*[contains(@class, 'header')]",
                    ".//*[contains(@class, 'footer')]", ".//*[contains(@class, 'btn')]",
                    ".//*[@class='input-group']", ".//*[@class='modal']",
                    ".//button", ".//*[contains(@id, 'modal')]"
                ]
                
                for xpath in unwanted_xpath:
                    for elem in content_elem.xpath(xpath):
                        if elem.getparent() is not None:
                            elem.getparent().remove(elem)
                
                text_content = content_elem.text_content().strip()
                
                # فلترة النصوص غير المرغوبة
                unwanted_phrases = [
                    'للمساهمة في دعم المكتبة الشاملة',
                    'حول المشروع',
                    'اتصل بنا',
                    'الموقع القديم',
                    'المكتبة الشاملة',
                    'اذهب',
                    'بحث في هذا الكتاب',
                    'رقم الجزء',
                    'مسار الصفحة الحالية',
                    'فهرس الكتاب',
                    'التشكيل',
                    'نسخ الفقرة ورابط لها',
                    'إغلاق',
                    'btn',
                    'fa fa-'
                ]
                
                # تقسيم النص إلى فقرات وتنظيف كل فقرة
                paragraphs = text_content.split('\n')
                cleaned_paragraphs = []
                
                for paragraph in paragraphs:
                    paragraph = paragraph.strip()
                    # تخطي الفقرات الفارغة أو القصيرة جداً
                    if len(paragraph) < 10:
                        continue
                    # تخطي الفقرات التي تحتوي على عبارات غير مرغوبة
                    if any(phrase in paragraph for phrase in unwanted_phrases):
                        continue
                    # تخطي الفقرات التي تحتوي أرقام وحيدة (أرقام الصفحات)
                    if paragraph.isdigit() or re.match(r'^[٠-٩]+$', paragraph):
                        continue
                    
                    cleaned_paragraphs.append(paragraph)
                
                # إعادة تجميع النص المنظف
                text_content = '\n'.join(cleaned_paragraphs)
                
                # تطبيع النص النهائي
                text_content = re.sub(r'\n{3,}', '\n\n', text_content)
                text_content = text_content.strip()
                
                html_content = lxml_html.tostring(content_elem, encoding='unicode', method='html')
                
                return {
                    'page_number': page_num,
                    'content': text_content,
                    'html_content': html_content,
                    'word_count': len(text_content.split()),
                    'char_count': len(text_content),
                    'extracted_at': datetime.now().isoformat(),
                    'extraction_method': 'lxml'
                }
            
        except Exception as e:
            logger.debug(f"خطأ في lxml للصفحة {page_num}: {e}")
            # تراجع إلى BeautifulSoup
            pass
        
        return FastHTMLProcessor._extract_with_bs4(html, page_num)
    
    @staticmethod
    def _extract_with_bs4(html: str, page_num: int) -> Dict[str, Any]:
        """استخراج باستخدام BeautifulSoup (بديل)"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # البحث عن المحتوى - نركز على div.nass أولاً
        content_selectors = [
            "div.nass",  # الحاوي الرئيسي للمحتوى في شاملة
            "#book", 
            "div#text", 
            "article", 
            "div.reader-text",
            "div.col-md-9", 
            ".book-content", 
            ".page-content", 
            "main"
        ]
        
        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        if not main_content:
            main_content = soup.find("body") or soup
        
        if main_content:
            # إزالة العناصر غير المرغوبة
            unwanted_selectors = [
                "script", "style", "nav", ".share", ".social", ".ad", 
                ".advertisement", ".menu", ".sidebar", ".header", ".footer",
                "button", ".btn", ".input-group", ".modal", "[id*='modal']",
                ".dropdown", ".navbar"
            ]
            
            for selector in unwanted_selectors:
                for element in main_content.select(selector):
                    element.decompose()
            
            # استبدال <hr> و <br> بنص واضح قبل استخراج النص
            for hr in main_content.find_all("hr"):
                hr.replace_with("\n<hr/>\n")
            
            for br in main_content.find_all("br"):
                br.replace_with("<br/>\n")
            
            # استخراج النص مع الحفاظ على فواصل الأسطر
            text_content = main_content.get_text(separator="\n", strip=True)
            
            # فلترة النصوص غير المرغوبة
            unwanted_phrases = [
                'للمساهمة في دعم المكتبة الشاملة',
                'حول المشروع',
                'اتصل بنا',
                'الموقع القديم',
                'المكتبة الشاملة',
                'اذهب',
                'بحث في هذا الكتاب',
                'رقم الجزء',
                'مسار الصفحة الحالية',
                'فهرس الكتاب',
                'التشكيل',
                'نسخ الفقرة ورابط لها',
                'إغلاق',
                'btn',
                'fa fa-'
            ]
            
            # تقسيم النص إلى فقرات وتنظيف كل فقرة
            paragraphs = text_content.split('\n')
            cleaned_paragraphs = []
            
            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                # تخطي الفقرات الفارغة أو القصيرة جداً
                if len(paragraph) < 10:
                    continue
                # تخطي الفقرات التي تحتوي على عبارات غير مرغوبة
                if any(phrase in paragraph for phrase in unwanted_phrases):
                    continue
                # تخطي الفقرات التي تحتوي أرقام وحيدة (أرقام الصفحات)
                if paragraph.isdigit() or re.match(r'^[٠-٩]+$', paragraph):
                    continue
                
                cleaned_paragraphs.append(paragraph)
            
            # إعادة تجميع النص المنظف
            text_content = '\n'.join(cleaned_paragraphs)
            
            # تطبيع فواصل الأسطر النهائية
            text_content = re.sub(r'\n{3,}', '\n\n', text_content)
            text_content = text_content.strip()
            
            html_content = str(main_content)
            
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

# ========= دوال مساعدة للتواريخ =========
def gregorian_to_hijri(gregorian_year: int) -> str:
    """
    تحويل السنة الميلادية إلى هجرية (تقريبي)
    """
    if not gregorian_year or gregorian_year < 622:
        return ""
    
    # التحويل التقريبي: الهجري = (الميلادي - 622) × 1.030684
    hijri_year = int((gregorian_year - 622) * 1.030684) + 1
    return str(hijri_year)

def extract_edition_number(edition_text: str) -> Optional[int]:
    """
    استخراج رقم الطبعة من النص
    """
    if not edition_text:
        return None
    
    edition_text = edition_text.strip()
    
    # أنماط مختلفة لاستخراج رقم الطبعة
    patterns = [
        r'الطبعة\s+الأولى',  # الطبعة الأولى
        r'الطبعة\s+الثانية',  # الطبعة الثانية
        r'الطبعة\s+الثالثة',  # الطبعة الثالثة
        r'الطبعة\s+الرابعة',  # الطبعة الرابعة
        r'الطبعة\s+الخامسة',  # الطبعة الخامسة
        r'الطبعة\s+السادسة',  # الطبعة السادسة
        r'الطبعة\s+السابعة',  # الطبعة السابعة
        r'الطبعة\s+الثامنة',  # الطبعة الثامنة
        r'الطبعة\s+التاسعة',  # الطبعة التاسعة
        r'الطبعة\s+العاشرة',  # الطبعة العاشرة
        r'ط\s*(\d+)',          # ط1، ط2، إلخ
        r'الطبعة\s*(\d+)',     # الطبعة 1، الطبعة 2
        r'طبعة\s*(\d+)',       # طبعة 1، طبعة 2
        r'(\d+)\s*طبعة',       # 1 طبعة
    ]
    
    # تحويل الكلمات إلى أرقام
    word_to_number = {
        'الأولى': 1, 'الثانية': 2, 'الثالثة': 3, 'الرابعة': 4, 'الخامسة': 5,
        'السادسة': 6, 'السابعة': 7, 'الثامنة': 8, 'التاسعة': 9, 'العاشرة': 10
    }
    
    # البحث في الكلمات المكتوبة
    for word, number in word_to_number.items():
        if word in edition_text:
            return number
    
    # البحث في الأرقام
    for pattern in patterns:
        match = re.search(pattern, edition_text)
        if match and match.groups():
            try:
                return int(match.group(1))
            except (ValueError, IndexError):
                continue
    
    # محاولة أخيرة لاستخراج أي رقم
    numbers = re.findall(r'\d+', edition_text)
    if numbers:
        try:
            return int(numbers[0])
        except ValueError:
            pass
    
    return None

# ========= نماذج البيانات المحسنة =========
@dataclass
class Publisher:
    """نموذج الناشر"""
    name: str
    slug: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if not self.slug and self.name:
            self.slug = self.slugify(self.name)
    
    @staticmethod
    def slugify(text: str) -> str:
        """تحويل النص إلى slug"""
        import unicodedata
        if not text:
            return ""
        text = unicodedata.normalize("NFKC", text).strip()
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"[^\w\-]+", "", text, flags=re.U)
        return text.strip("-").lower()

@dataclass
class BookSection:
    """نموذج قسم الكتاب"""
    name: str
    slug: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    
    def __post_init__(self):
        if not self.slug and self.name:
            self.slug = Publisher.slugify(self.name)

@dataclass
class VolumeLink:
    """نموذج رابط المجلد"""
    volume_number: int
    title: str
    url: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None

@dataclass
class Author:
    """نموذج المؤلف"""
    name: str
    slug: Optional[str] = None
    biography: Optional[str] = None
    madhhab: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    
    def __post_init__(self):
        if not self.slug and self.name:
            self.slug = Publisher.slugify(self.name)

@dataclass
class Chapter:
    """نموذج الفصل المحسن"""
    title: str
    order: int = 0  # ترتيب الفصل
    page_number: Optional[int] = None
    page_end: Optional[int] = None
    children: List["Chapter"] = field(default_factory=list)
    volume_number: Optional[int] = None
    level: int = 0
    parent_id: Optional[int] = None
    chapter_type: str = 'main'  # main أو sub

@dataclass
class Volume:
    """نموذج الجزء"""
    number: int
    title: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None

@dataclass
class PageContent:
    """نموذج محتوى الصفحة"""
    page_number: int
    content: str
    html_content: Optional[str] = None
    volume_number: Optional[int] = None
    chapter_id: Optional[int] = None
    word_count: Optional[int] = None
    original_page_number: Optional[int] = None  # للترقيم الأصلي
    page_index_internal: Optional[int] = None  # الترقيم الداخلي دائماً
    printed_missing: bool = False  # هل فشل استخراج الترقيم المطبوع
    internal_index: Optional[int] = None  # N من المسار

@dataclass
class Book:
    """نموذج الكتاب المحسن"""
    title: str
    shamela_id: str
    slug: Optional[str] = None
    authors: List[Author] = field(default_factory=list)
    publisher: Optional[Publisher] = None
    book_section: Optional[BookSection] = None
    edition: Optional[str] = None
    edition_number: Optional[int] = None
    publication_year: Optional[int] = None
    edition_date_hijri: Optional[str] = None
    page_count: Optional[int] = None  # سيتم إهماله
    page_count_internal: Optional[int] = None  # عدد الصفحات الداخلي
    page_count_printed: Optional[int] = None  # آخر رقم مطبوع
    volume_count: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    index: List[Chapter] = field(default_factory=list)
    volumes: List[Volume] = field(default_factory=list)
    volume_links: List[VolumeLink] = field(default_factory=list)
    pages: List[PageContent] = field(default_factory=list)
    description: Optional[str] = None  # بطاقة الكتاب الكاملة
    language: str = "ar"
    source_url: Optional[str] = None
    has_original_pagination: bool = False  # ترقيم موافق للمطبوع
    page_navigation_map: Dict[int, int] = field(default_factory=dict)  # خريطة ص→N
    
    def __post_init__(self):
        if not self.slug and self.title:
            self.slug = Publisher.slugify(self.title)

class EnhancedShamelaScraperError(Exception):
    """استثناء خاص بالسكربت المحسن"""
    pass

# ========= وظائف المساعدة =========
def safe_request(url: str, retries: int = MAX_RETRIES, timeout: int = REQ_TIMEOUT, 
                use_cache: bool = True) -> requests.Response:
    """طلب آمن محسن مع تجمع الاتصالات والتخزين المؤقت"""
    
    # التحقق من التخزين المؤقت
    if use_cache:
        cached_response = global_cache.get(url)
        if cached_response:
            return cached_response
    
    for attempt in range(retries):
        try:
            delay = REQUEST_DELAY * (attempt + 1)
            if attempt > 0:
                time.sleep(delay)
            
            enhanced_headers = HEADERS.copy()
            enhanced_headers.update({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })
            
            response = http_session.get(url, headers=enhanced_headers, timeout=timeout)
            
            if response.status_code == 200:
                # حفظ في التخزين المؤقت
                if use_cache:
                    global_cache.set(url, response)
                return response
            elif response.status_code == 404:
                if "الصفحة غير موجودة" in response.text or "Page not found" in response.text:
                    if attempt == retries - 1:
                        raise EnhancedShamelaScraperError(f"الصفحة غير موجودة: {url}")
                else:
                    if attempt < retries - 1:
                        logger.warning(f"محاولة {attempt + 1}: 404 مؤقت محتمل لـ {url}")
                    else:
                        raise EnhancedShamelaScraperError(f"فشل في الوصول إلى {url} بعد {retries} محاولات (404)")
            else:
                response.raise_for_status()
                
        except requests.RequestException as e:
            if attempt < retries - 1:
                logger.warning(f"محاولة {attempt + 1} فشلت لـ {url}: {e}")
            else:
                raise EnhancedShamelaScraperError(f"فشل في الوصول إلى {url} بعد {retries} محاولات: {e}")
            
            time.sleep(REQUEST_DELAY * (attempt + 2))

@lru_cache(maxsize=500)
def get_soup(url: str, use_cache: bool = True) -> BeautifulSoup:
    """الحصول على soup محسن مع تخزين مؤقت"""
    response = safe_request(url, use_cache=use_cache)
    return BeautifulSoup(response.content, 'html.parser')

def clean_text(text: str) -> str:
    """تنظيف النص من المسافات الزائدة والأحرف غير المرغوبة"""
    if not text:
        return ""
    
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = text.replace('\u200c', '').replace('\u200d', '')  # إزالة zero-width characters
    
    return text.strip()

# ========= استخراج بيانات الكتاب المحسن =========
def extract_enhanced_book_info(book_id: str) -> Tuple[Book, BeautifulSoup]:
    """استخراج بيانات الكتاب بطريقة محسنة"""
    normalized_id = normalize_book_id(book_id)
    url = f"{BASE_URL}/book/{normalized_id}"
    logger.info(f"استخراج بيانات الكتاب من {url}")
    
    soup = get_soup(url)
    
    # استخراج العنوان
    title_selectors = [
        "h1.book-title", "h1", ".book-title", "title"
    ]
    
    title = ""
    for selector in title_selectors:
        element = soup.select_one(selector)
        if element:
            title = clean_text(element.get_text())
            if len(title) > 3:
                break
    
    if not title:
        raise EnhancedShamelaScraperError(f"لم يتم العثور على عنوان للكتاب {book_id}")
    
    # استخراج بطاقة الكتاب الكاملة (المحسن)
    description = extract_book_card(soup)
    
    # استخراج المؤلفين
    authors = extract_authors(soup)
    
    # استخراج بيانات الناشر (المحسن)
    publisher = extract_publisher_info(soup)
    
    # استخراج بيانات القسم (جديد)
    book_section = extract_book_section(soup)
    
    # استخراج بيانات الطبعة المحسنة
    edition, edition_number, publication_year, edition_date_hijri = extract_enhanced_edition_info(soup)
    
    # فحص الترقيم الأصلي
    has_original_pagination = check_original_pagination(soup)
    
    # استخراج باقي البيانات
    page_count, volume_count, categories = extract_additional_info(soup)
    
    # إنشاء كائن الكتاب
    book = Book(
        title=title,
        shamela_id=str(book_id),
        authors=authors,
        publisher=publisher,
        book_section=book_section,
        edition=edition,
        edition_number=edition_number,
        publication_year=publication_year,
        edition_date_hijri=edition_date_hijri,
        page_count=page_count,
        volume_count=volume_count,
        categories=categories,
        description=description,
        source_url=url,
        has_original_pagination=has_original_pagination
    )
    
    logger.info(f"تم استخراج البيانات المحسنة للكتاب {book_id}")
    return book, soup

def extract_book_card(soup: BeautifulSoup) -> str:
    """
    استخراج بطاقة الكتاب الكاملة من عنوان "بطاقة الكتاب" إلى "فهرس الموضوعات" قبل خيارات المشاركة
    """
    # البحث عن المحتوى بين "بطاقة الكتاب" و "فهرس الموضوعات"
    text_content = soup.get_text()
    
    # البحث عن نقطة البداية
    start_patterns = [
        r'بطاقة\s*الكتاب',
        r'والكتاب\s*:',
        r'الكتاب\s*:'
    ]
    
    start_pos = 0
    for pattern in start_patterns:
        match = re.search(pattern, text_content)
        if match:
            start_pos = match.start()
            break
    
    # البحث عن نقطة النهاية
    end_patterns = [
        r'فهرس\s*الموضوعات',
        r'فصول\s*الكتاب',
        r'نشر\s*لفيسبوك',
        r'نسخ\s*الرابط',
        r'مشاركة',
        r'شارك'
    ]
    
    end_pos = len(text_content)
    for pattern in end_patterns:
        match = re.search(pattern, text_content[start_pos:])
        if match:
            end_pos = start_pos + match.start()
            break
    
    # استخراج النص بين النقطتين
    description = text_content[start_pos:end_pos]
    
    # تنظيف النص
    unwanted_phrases = [
        "نشر لفيسبوك", "نشر لتويتر", "نشر فيسبوك", "نشر تويتر",
        "نسخ الرابط", "بحــث", "مشاركة", "شارك",
        "فهرس الموضوعات", "فصول الكتاب", "المحتويات", "الفهرس"
    ]
    
    for phrase in unwanted_phrases:
        description = description.replace(phrase, "")
    
    # إزالة الأرقام والروابط المتبقية من الفهرس
    description = re.sub(r'\d+\s*-\s*[^\n]*', '', description)  # إزالة أسطر مثل "1 - عنوان الفصل"
    description = re.sub(r'[+]\s*[^\n]*', '', description)  # إزالة أسطر مثل "[+]عنوان"
    
    # تنظيف المسافات الزائدة مع الحفاظ على فواصل الأسطر
    # بدلاً من دمج الأسطر، نقلل التكرارات الزائدة فقط
    description = re.sub(r'\n{3,}', '\n\n', description)  # تقليل تكرارات \n الزائدة
    description = re.sub(r'[ \t]+', ' ', description)     # تنظيف المسافات الأفقية فقط
    description = description.strip()
    
    # إذا لم نجد محتوى كافي، نستخدم الطريقة القديمة كبديل
    if len(description) < 50:
        card_selectors = [
            ".book-card", ".book-info", ".betaka", ".nass", 
            ".book-description", ".description", "div.nass p"
        ]
        
        for selector in card_selectors:
            elements = soup.select(selector)
            for element in elements:
                # إنشاء نسخة من العنصر لتجنب تعديل الأصل
                element_copy = element.__copy__()
                
                # إزالة عناصر الفهرس والمحتويات
                for index_elem in element_copy.select(".betaka-index, .book-index, .index, #book-index, .table-of-contents, .s-nav, div.s-nav, ul, ol"):
                    index_elem.decompose()
                
                # إزالة عناصر المشاركة والروابط الاجتماعية
                for share_elem in element_copy.select(".share, .social, .social-share, .share-buttons, .social-links"):
                    share_elem.decompose()
                
                # استخراج النص مع الحفاظ على فواصل الأسطر
                text = element_copy.get_text(separator="\n", strip=True)
                
                # تنظيف إضافي
                for phrase in unwanted_phrases:
                    text = text.replace(phrase, "")
                
                # تطبيع فواصل الأسطر مع الحفاظ عليها
                text = re.sub(r'\n{3,}', '\n\n', text)  # تقليل التكرارات الزائدة
                text = re.sub(r'[ \t]+', ' ', text)     # تنظيف المسافات الأفقية فقط
                text = text.strip()
                
                if len(text) > 50:
                    description = text
                    break
            
            if len(description) > 50:
                break
    
    return description

def extract_authors(soup: BeautifulSoup) -> List[Author]:
    """استخراج المؤلفين"""
    authors = []
    
    author_selectors = [
        ".book-author a", ".author a", "a[href*='/author/']",
        ".book-meta .author a", ".book-info .author a"
    ]
    
    for selector in author_selectors:
        elements = soup.select(selector)
        for element in elements:
            name = clean_text(element.get_text())
            if name and len(name) > 2:
                # تجنب التكرار
                if not any(author.name == name for author in authors):
                    authors.append(Author(name=name))
    
    return authors

def extract_publisher_info(soup: BeautifulSoup) -> Optional[Publisher]:
    """
    استخراج بيانات الناشر المحسنة - من بعد "الناشر:" حتى نهاية السطر
    """
    publisher_patterns = [
        r'الناشر\s*[:：]\s*([^\n]+)',           # أولوية عليا
        r'دار\s+النشر\s*[:：]\s*([^\n]+)',      # أولوية ثانية
        r'النشر\s*[:：]\s*([^\n]+)',           # أولوية ثالثة
        r'المطبعة\s*[:：]\s*([^\n]+)',
        r'نشر\s*[:：]\s*([^\n]+)',
    ]
    
    text_content = soup.get_text(separator='\n', strip=True)
    
    for pattern in publisher_patterns:
        match = re.search(pattern, text_content)
        if match:
            publisher_name = clean_text(match.group(1))
            if publisher_name and len(publisher_name) > 2:
                # لا نقطع النص عند الفواصل العربية أو أي شيء آخر
                # نأخذ النص كاملاً كما هو حتى نهاية السطر
                
                # استخراج الموقع من آخر جزء إن أمكن (اختياري)
                location = None
                # البحث عن أنماط الموقع في نهاية النص
                location_patterns = [
                    r'(.+?)،\s*([^،]+)$',  # النص، الموقع
                    r'(.+?)\s*-\s*([^-]+)$'  # النص - الموقع  
                ]
                
                for loc_pattern in location_patterns:
                    location_match = re.search(loc_pattern, publisher_name)
                    if location_match:
                        name_part = clean_text(location_match.group(1))
                        location_part = clean_text(location_match.group(2))
                        # فقط إذا كان الجزء الثاني يبدو كموقع جغرافي
                        if (location_part and len(location_part) < 50 and 
                            any(geo_word in location_part for geo_word in 
                                ['الكويت', 'القاهرة', 'الرياض', 'بيروت', 'دبي', 'دمشق', 'بغداد', 'الدوحة'])):
                            publisher_name = name_part
                            location = location_part
                            break
                
                return Publisher(
                    name=publisher_name,
                    location=location
                )
    
    return None

def extract_book_section(soup: BeautifulSoup) -> Optional[BookSection]:
    """
    استخراج قسم الكتاب
    """
    section_selectors = [
        ".book-category a", ".category a", ".book-section a",
        "a[href*='/section/']", "a[href*='/category/']"
    ]
    
    for selector in section_selectors:
        element = soup.select_one(selector)
        if element:
            section_name = clean_text(element.get_text())
            if section_name and len(section_name) > 2:
                return BookSection(name=section_name)
    
    # البحث في النص
    section_patterns = [
        r'القسم\s*[:：]\s*([^،\n]+)',
        r'التصنيف\s*[:：]\s*([^،\n]+)',
        r'الموضوع\s*[:：]\s*([^،\n]+)',
    ]
    
    text_content = soup.get_text()
    for pattern in section_patterns:
        match = re.search(pattern, text_content)
        if match:
            section_name = clean_text(match.group(1))
            if section_name and len(section_name) > 2:
                return BookSection(name=section_name)
    
    return None

def extract_enhanced_edition_info(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
    """
    استخراج بيانات الطبعة المحسنة مع التعامل مع الكتب بدون تاريخ نشر
    """
    text_content = soup.get_text()
    
    edition = None
    edition_number = None
    publication_year = None
    edition_date_hijri = None
    
    # أنماط استخراج معلومات الطبعة
    edition_patterns = [
        r'الطبعة\s*[:：]\s*([^،\n]+)',
        r'ط\s*[:：]\s*([^،\n]+)',
        r'طبعة\s*[:：]\s*([^،\n]+)',
    ]
    
    for pattern in edition_patterns:
        match = re.search(pattern, text_content)
        if match:
            edition_text = clean_text(match.group(1))
            
            # التعامل مع الكتب بدون تاريخ نشر
            if "بدون تاريخ" in edition_text or "بدون طبعة" in edition_text:
                edition = None
                edition_number = None
            else:
                edition = edition_text
                edition_number = extract_edition_number(edition_text)
            break
    
    # استخراج سنة النشر
    year_patterns = [
        r'(\d{4})\s*هـ',
        r'سنة\s*[:：]\s*(\d{4})',
        r'تاريخ\s*النشر\s*[:：]\s*(\d{4})',
        r'(\d{4})\s*م',
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, text_content)
        if match:
            try:
                year = int(match.group(1))
                if 'هـ' in match.group(0):
                    # السنة هجرية
                    edition_date_hijri = str(year)
                    # تحويل تقريبي للميلادي
                    publication_year = int(year / 1.030684) + 622
                else:
                    # السنة ميلادية
                    publication_year = year
                    edition_date_hijri = gregorian_to_hijri(year)
                break
            except ValueError:
                continue
    
    return edition, edition_number, publication_year, edition_date_hijri

def check_original_pagination(soup: BeautifulSoup) -> bool:
    """
    فحص ما إذا كان الكتاب يستخدم ترقيم الصفحات الأصلي
    """
    text_content = soup.get_text()
    
    pagination_indicators = [
        "ترقيم الكتاب موافق للمطبوع",
        "موافق للمطبوع",
        "ترقيم موافق للمطبوع",
        "الترقيم موافق للمطبوع"
    ]
    
    for indicator in pagination_indicators:
        if indicator in text_content:
            logger.info(f"تم اكتشاف ترقيم أصلي: {indicator}")
            return True
    
    return False

def extract_additional_info(soup: BeautifulSoup) -> Tuple[Optional[int], Optional[int], List[str]]:
    """استخراج المعلومات الإضافية"""
    text_content = soup.get_text()
    
    page_count = None
    volume_count = None
    categories = []
    
    # استخراج عدد الصفحات
    page_patterns = [
        r'(\d+)\s*صفحة',
        r'عدد\s*الصفحات\s*[:：]\s*(\d+)',
        r'الصفحات\s*[:：]\s*(\d+)',
    ]
    
    for pattern in page_patterns:
        match = re.search(pattern, text_content)
        if match:
            try:
                page_count = int(match.group(1))
                break
            except ValueError:
                continue
    
    # استخراج عدد المجلدات
    volume_patterns = [
        r'(\d+)\s*مجلد',
        r'(\d+)\s*جزء',
        r'عدد\s*الأجزاء\s*[:：]\s*(\d+)',
        r'الأجزاء\s*[:：]\s*(\d+)',
    ]
    
    for pattern in volume_patterns:
        match = re.search(pattern, text_content)
        if match:
            try:
                volume_count = int(match.group(1))
                break
            except ValueError:
                continue
    
    # استخراج الفئات
    category_selectors = [
        ".book-categories a", ".categories a", 
        ".book-tags a", ".tags a"
    ]
    
    for selector in category_selectors:
        elements = soup.select(selector)
        for element in elements:
            category = clean_text(element.get_text())
            if category and category not in categories:
                categories.append(category)
    
    return page_count, volume_count, categories

# ========= استخراج الفهرس المحسن =========
def extract_enhanced_book_index(book_id: str, soup: BeautifulSoup) -> List[Chapter]:
    """
    استخراج فهرس الكتاب بطريقة محسنة مع الترتيب وحماية من التعديل
    """
    logger.info(f"بدء استخراج فهرس محسن للكتاب {book_id}")
    
    # إنشاء نسخة من soup لتجنب التأثير على العمليات الأخرى
    soup_copy = BeautifulSoup(str(soup), 'html.parser')
    
    index_selectors = [
        "div.betaka-index ul",
        ".book-index ul",
        ".index ul",
        "#book-index ul",
        ".table-of-contents ul",
        ".s-nav ul",  # إضافة selector جديد للفهرس الجانبي
        "div.s-nav ul"
    ]
    
    index_container = None
    for selector in index_selectors:
        index_container = soup_copy.select_one(selector)
        if index_container:
            logger.info(f"تم العثور على فهرس باستخدام selector: {selector}")
            break
    
    if not index_container:
        logger.warning(f"لم يتم العثور على فهرس للكتاب {book_id}")
        return []
    
    def parse_chapter_list_enhanced(ul_element, level=0, parent_order=0) -> List[Chapter]:
        """
        تحليل قائمة الفصول بشكل تكراري مع الترتيب المحسن
        """
        chapters = []
        order_counter = 0
        
        for li in ul_element.find_all("li", recursive=False):
            order_counter += 1
            current_order = parent_order * 1000 + order_counter  # ترتيب هرمي
            
            # البحث عن الرابط
            link = None
            for a in li.find_all("a", href=True):
                href = a.get("href", "")
                if f"/book/{book_id}/" in href:
                    link = a
                    break
            
            if not link:
                continue
            
            # استخراج العنوان
            title = clean_text(link.get_text())
            if not title:
                continue
            
            # استخراج رقم الصفحة
            page_number = None
            page_end = None
            
            href = link.get("href", "")
            page_match = re.search(rf"/book/{book_id}/(\d+)", href)
            if page_match:
                page_number = int(page_match.group(1))
            
            # تحديد نوع الفصل
            chapter_type = 'sub' if level > 0 else 'main'
            
            # إنشاء الفصل
            chapter = Chapter(
                title=title,
                order=current_order,
                page_number=page_number,
                page_end=page_end,
                level=level,
                chapter_type=chapter_type
            )
            
            # البحث عن الفصول الفرعية
            sub_ul = li.find("ul")
            if sub_ul:
                chapter.children = parse_chapter_list_enhanced(sub_ul, level + 1, current_order)
            
            chapters.append(chapter)
        
        return chapters
    
    chapters = parse_chapter_list_enhanced(index_container)
    
    # تحديد صفحة النهاية لكل فصل
    def set_end_pages(chapter_list: List[Chapter]):
        for i, chapter in enumerate(chapter_list):
            if chapter.page_number:
                # البحث عن الفصل التالي
                next_page = None
                if i + 1 < len(chapter_list):
                    next_chapter = chapter_list[i + 1]
                    if next_chapter.page_number:
                        next_page = next_chapter.page_number - 1
                
                chapter.page_end = next_page
            
            # معالجة الفصول الفرعية
            if chapter.children:
                set_end_pages(chapter.children)
    
    set_end_pages(chapters)
    
    logger.info(f"تم استخراج {len(chapters)} فصل رئيسي مع ترتيب محسن")
    return chapters

# ========= حساب عدد الصفحات من واجهة القراءة =========
def calculate_page_counts_from_reader(book_id: str) -> Tuple[int, Optional[int]]:
    """
    حساب عدد الصفحات من واجهة القراءة (ليس من البطاقة)
    يعيد: (page_count_internal, page_count_printed)
    """
    logger.info(f"حساب عدد الصفحات من واجهة القراءة للكتاب {book_id}")
    
    normalized_id = normalize_book_id(book_id)
    # الخطوة 1: فتح صفحة /book/{id}/1
    url = f"{BASE_URL}/book/{normalized_id}/1"
    soup = get_soup(url)
    
    max_internal_page = 1
    
    # الخطوة 2: البحث عن رابط ">>" في شريط الصفحات
    next_links = soup.find_all("a", string=re.compile(r'>>|»|التالي'))
    for link in next_links:
        href = link.get("href", "")
        page_match = re.search(rf"/book/{book_id}/(\d+)", href)
        if page_match:
            max_internal_page = max(max_internal_page, int(page_match.group(1)))
    
    # الخطوة 3: إن غاب ">>", استخرج من جميع الروابط في الصفحة
    if max_internal_page == 1:
        all_page_links = soup.find_all("a", href=re.compile(rf"/book/{book_id}/(\d+)"))
        for link in all_page_links:
            href = link.get("href", "")
            # تجاهل fragment (#...)
            href = href.split('#')[0]
            page_match = re.search(rf"/book/{book_id}/(\d+)", href)
            if page_match:
                page_number = int(page_match.group(1))
                max_internal_page = max(max_internal_page, page_number)
    
    page_count_internal = max_internal_page
    logger.info(f"عدد الصفحات الداخلي: {page_count_internal}")
    
    # الخطوة 4: حساب عدد الصفحات المطبوع (إن وُجد)
    page_count_printed = None
    
    # فتح آخر صفحة واقرأ رقم ص من <title>
    try:
        last_page_url = f"{BASE_URL}/book/{normalized_id}/{page_count_internal}"
        last_page_soup = get_soup(last_page_url)
        
        # استخراج رقم الصفحة المطبوع من <title>
        printed_page = extract_printed_page_number(last_page_soup)
        if printed_page:
            page_count_printed = printed_page
            logger.info(f"عدد الصفحات المطبوع: {page_count_printed}")
        else:
            logger.info("لا يوجد ترقيم مطبوع في آخر صفحة")
            
    except Exception as e:
        logger.warning(f"خطأ في قراءة آخر صفحة: {e}")
    
    return page_count_internal, page_count_printed

def build_page_navigation_map(book_id: str, total_pages: int, has_original_pagination: bool) -> Dict[int, int]:
    """
    بناء خريطة تنقل مطبوع→داخلي (ص → N)
    """
    if not has_original_pagination:
        return {}
    
    logger.info(f"بناء خريطة التنقل للكتاب {book_id}")
    normalized_id = normalize_book_id(book_id)
    navigation_map = {}
    
    # عينة من الصفحات لبناء خريطة فعالة
    sample_pages = []
    
    if total_pages <= 50:
        # كتاب صغير: اقرأ كل الصفحات
        sample_pages = list(range(1, total_pages + 1))
    else:
        # كتاب كبير: عينة ذكية
        step = max(1, total_pages // 20)  # 20 عينة تقريباً
        sample_pages = list(range(1, total_pages + 1, step))
        # تأكد من إضافة أول وآخر صفحة
        if 1 not in sample_pages:
            sample_pages.insert(0, 1)
        if total_pages not in sample_pages:
            sample_pages.append(total_pages)
    
    logger.info(f"قراءة {len(sample_pages)} صفحة لبناء خريطة التنقل")
    
    for internal_page in sample_pages:
        try:
            url = f"{BASE_URL}/book/{normalized_id}/{internal_page}"
            soup = get_soup(url)
            printed_page = extract_printed_page_number(soup)
            
            if printed_page:
                # إذا لم يكن مسجلاً من قبل، أو إذا كان N الحالي أصغر
                if (printed_page not in navigation_map or 
                    internal_page < navigation_map[printed_page]):
                    navigation_map[printed_page] = internal_page
            
            time.sleep(0.1)  # فترة راحة قصيرة
        except Exception as e:
            logger.warning(f"خطأ في قراءة الصفحة {internal_page}: {e}")
    
    logger.info(f"تم بناء خريطة تنقل بـ {len(navigation_map)} عنصر")
    return navigation_map

def find_internal_page_for_printed(printed_page: int, navigation_map: Dict[int, int]) -> Optional[int]:
    """
    دالة مساعدة للعثور على N الداخلي لرقم ص مطبوع
    """
    if printed_page in navigation_map:
        return navigation_map[printed_page]
    
    # البحث عن أقرب صفحة مطبوعة أكبر أو تساوي
    sorted_printed = sorted(navigation_map.keys())
    for p in sorted_printed:
        if p >= printed_page:
            return navigation_map[p]
    
    # إذا لم توجد، ارجع آخر صفحة
    if sorted_printed:
        return navigation_map[sorted_printed[-1]]
    
    return None

# ========= استخراج المجلدات من dropdown والترقيم المطبوع =========
def convert_arabic_hindi_digits(text: str) -> str:
    """
    تحويل الأرقام العربية-الهندية إلى غربية
    """
    arabic_hindi_map = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
    }
    
    for arabic, western in arabic_hindi_map.items():
        text = text.replace(arabic, western)
    
    return text

def extract_volumes_from_dropdown(book_id: str) -> List[Volume]:
    """
    استخراج المجلدات من قائمة "ج:" في صفحة القراءة
    يحسب internal_start / internal_end بدقة من dropdown
    """
    logger.info(f"استخراج المجلدات من dropdown للكتاب {book_id}")
    
    normalized_id = normalize_book_id(book_id)
    # فتح صفحة قراءة واحدة
    url = f"{BASE_URL}/book/{normalized_id}/1"
    soup = get_soup(url)
    
    volumes = []
    volume_data = []
    
    # البحث عن قائمة dropdown "رقم الجزء"
    dropdown_selectors = [
        'ul.dropdown-menu a[href*="#p1"]',
        'ul.dropdown-menu a[href*="book"]',
        '.dropdown-menu a',
        'select[name*="volume"] option',
        'select[name*="part"] option'
    ]
    
    found_links = []
    for selector in dropdown_selectors:
        links = soup.select(selector)
        if links:
            # تصفية الروابط للتأكد من أنها للأجزاء
            for link in links:
                href = link.get("href", "")
                text = clean_text(link.get_text())
                
                # التحقق من أن الرابط يحتوي على معرف الكتاب و #p1
                if (href and f"/book/{book_id}/" in href and 
                    ("#p1" in href or text.isdigit() or 
                     any(c.isdigit() for c in convert_arabic_hindi_digits(text)))):
                    found_links.append(link)
            
            if found_links:
                break
    
    if not found_links:
        logger.warning(f"لم يتم العثور على قائمة dropdown للأجزاء في الكتاب {book_id}")
        # إنشاء جزء واحد افتراضي
        return [Volume(number=1, title="المجلد الأول", page_start=1, page_end=None)]
    
    # استخراج البيانات من الروابط
    for link in found_links:
        href = link.get("href", "")
        text = clean_text(link.get_text())
        
        # تجاهل العناصر غير الرقمية أو العناوين
        if not text or text in ["رقم الجزء", "الجزء", "المجلد"]:
            continue
        
        # تحويل الأرقام العربية-الهندية
        converted_text = convert_arabic_hindi_digits(text)
        
        # استخراج رقم الجزء من النص
        volume_match = re.search(r'(\d+)', converted_text)
        if not volume_match:
            continue
        
        volume_number = int(volume_match.group(1))
        
        # استخراج startN من href="/book/{id}/{N}#p1"
        page_match = re.search(rf"/book/{book_id}/(\d+)", href)
        if not page_match:
            continue
        
        internal_start = int(page_match.group(1))
        
        volume_data.append((volume_number, internal_start))
    
    # إزالة التكرارات وأخذ أصغر startN لنفس رقم الجزء
    unique_volumes = {}
    for vol_num, start_page in volume_data:
        if vol_num not in unique_volumes:
            unique_volumes[vol_num] = start_page
        else:
            unique_volumes[vol_num] = min(unique_volumes[vol_num], start_page)
    
    # تحويل إلى قائمة مرتبة
    sorted_volumes = sorted(unique_volumes.items())
    
    if not sorted_volumes:
        logger.warning(f"لم يتم العثور على أجزاء صالحة في الكتاب {book_id}")
        return [Volume(number=1, title="المجلد الأول", page_start=1, page_end=None)]
    
    # البحث عن أكبر رقم صفحة داخلي في الصفحة
    max_internal_page = 1
    all_page_links = soup.find_all("a", href=re.compile(rf"/book/{book_id}/(\d+)"))
    for link in all_page_links:
        href = link.get("href", "")
        page_match = re.search(rf"/book/{book_id}/(\d+)", href)
        if page_match:
            page_num = int(page_match.group(1))
            max_internal_page = max(max_internal_page, page_num)
    
    # حساب النهايات
    for i, (vol_num, start_page) in enumerate(sorted_volumes):
        if i + 1 < len(sorted_volumes):
            # النهاية = بداية الجزء التالي - 1
            end_page = sorted_volumes[i + 1][1] - 1
        else:
            # آخر جزء نهايته = أكبر N داخلي
            end_page = max_internal_page
        
        volume = Volume(
            number=vol_num,
            title=f"الجزء {vol_num}",
            page_start=start_page,
            page_end=end_page
        )
        volumes.append(volume)
    
    logger.info(f"تم استخراج {len(volumes)} جزء من dropdown")
    for vol in volumes:
        logger.info(f"الجزء {vol.number}: من {vol.page_start} إلى {vol.page_end}")
    
    return volumes

def extract_printed_page_number(soup_or_title) -> Optional[int]:
    """
    استخراج رقم الصفحة المطبوع من <title>
    """
    if hasattr(soup_or_title, 'find'):
        # إذا تم تمرير soup
        title_tag = soup_or_title.find('title')
        title_text = title_tag.get_text() if title_tag else ""
    elif hasattr(soup_or_title, 'get_text'):
        # إذا تم تمرير title tag مباشرة
        title_text = soup_or_title.get_text()
    else:
        # إذا تم تمرير نص العنوان مباشرة
        title_text = str(soup_or_title)
    
    if not title_text:
        return None
    
    # Regex مرن لاستخراج رقم الصفحة
    pattern = r'[صس]\s*[:：]?\s*([0-9\u0660-\u0669]+)'
    match = re.search(pattern, title_text)
    
    if match:
        page_number_text = match.group(1)
        # تحويل الأرقام العربية-الهندية إلى غربية
        converted_text = convert_arabic_hindi_digits(page_number_text)
        try:
            return int(converted_text)
        except ValueError:
            return None
    
    return None

# ========= استخراج روابط المجلدات =========
def extract_volume_links(book_id: str, soup: BeautifulSoup) -> List[VolumeLink]:
    """
    استخراج روابط المجلدات للكتب متعددة الأجزاء
    """
    logger.info(f"استخراج روابط المجلدات للكتاب {book_id}")
    
    volume_links = []
    
    # البحث عن روابط الأجزاء
    volume_selectors = [
        "a[href*='book'][href*='/'][title*='جزء']",
        "a[href*='book'][href*='/'][title*='مجلد']",
        ".volumes a", ".parts a"
    ]
    
    found_links = []
    for selector in volume_selectors:
        links = soup.select(selector)
        found_links.extend(links)
    
    # تحليل الروابط
    for link in found_links:
        href = link.get("href", "")
        title = clean_text(link.get_text() or link.get("title", ""))
        
        if not title or not href:
            continue
        
        # استخراج رقم الصفحة من الرابط
        page_match = re.search(rf"/book/{book_id}/(\d+)", href)
        if page_match:
            page_start = int(page_match.group(1))
            
            # استخراج رقم المجلد من العنوان
            volume_match = re.search(r'(\d+)', title)
            volume_number = int(volume_match.group(1)) if volume_match else len(volume_links) + 1
            
            # تجنب التكرار
            if not any(vl.volume_number == volume_number for vl in volume_links):
                volume_link = VolumeLink(
                    volume_number=volume_number,
                    title=title,
                    url=href,
                    page_start=page_start
                )
                volume_links.append(volume_link)
    
    # ترتيب الروابط حسب رقم المجلد
    volume_links.sort(key=lambda x: x.volume_number)
    
    # تحديد صفحة النهاية لكل مجلد
    for i, volume_link in enumerate(volume_links):
        if i + 1 < len(volume_links):
            next_volume = volume_links[i + 1]
            volume_link.page_end = next_volume.page_start - 1
    
    logger.info(f"تم استخراج {len(volume_links)} رابط مجلد")
    return volume_links

# ========= استخراج المحتوى المحسن =========
def extract_enhanced_page_content(book_id: str, page_number: int, has_original_pagination: bool = False, 
                                config: PerformanceConfig = None) -> PageContent:
    """
    استخراج محتوى الصفحة مع دعم الترقيم الأصلي وتحسينات الأداء
    """
    if config is None:
        config = PerformanceConfig()
        
    normalized_id = normalize_book_id(book_id)
    url = f"{BASE_URL}/book/{normalized_id}/{page_number}"
    
    # تحقق من التخزين المؤقت أولاً
    cache_key = f"{book_id}:{page_number}"
    if config.skip_existing:
        cached_content = global_cache.get(cache_key)
        if cached_content:
            return cached_content
    
    soup = get_soup(url, use_cache=True)
    
    # محاولة العثور على المحتوى الرئيسي
    content_selectors = [
        "#book", "div#text", "article", "div.reader-text",
        "div.col-md-9", "div.nass", ".book-content", ".page-content", "main"
    ]
    
    main_content = None
    for selector in content_selectors:
        main_content = soup.select_one(selector)
        if main_content:
            break
    
    if not main_content:
        main_content = soup.find("body") or soup
    
    # إزالة العناصر غير المرغوبة (لكن نحافظ على <hr> و <br> و .hamesh)
    unwanted_selectors = [
        "script", "style", "nav", ".share", ".social", ".ad", 
        ".advertisement", ".menu", ".sidebar", ".header", ".footer"
    ]
    
    for selector in unwanted_selectors:
        for element in main_content.select(selector):
            element.decompose()
    
    # استبدال <hr> و <br> بنص واضح قبل استخراج النص
    for hr in main_content.find_all("hr"):
        hr.replace_with("\n<hr/>\n")
    
    for br in main_content.find_all("br"):
        br.replace_with("<br/>\n")
    
    # استخراج النص مع الحفاظ على فواصل الأسطر
    content = main_content.get_text(separator="\n", strip=True)
    
    # تطبيع فواصل الأسطر - تقليل التكرارات الزائدة
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
    
    # تحسين الذاكرة: اختياري حفظ HTML 
    html_content = str(main_content) if not config.memory_efficient else None
    
    # استخراج الترقيم المطبوع من <title>
    printed_page_number = None
    page_index_internal = page_number
    printed_missing = False
    
    if has_original_pagination:
        # استخراج رقم الصفحة المطبوع من <title>
        printed_page_number = extract_printed_page_number(soup)
        
        if printed_page_number is not None:
            # نجح الاستخراج
            page_number = printed_page_number
        else:
            # فشل الاستخراج نادراً
            page_number = page_index_internal
            printed_missing = True
            if config.debug:
                logger.warning(f"لم يتم العثور على رقم صفحة مطبوع في {url}")
    
    # حساب عدد الكلمات (محسن)
    word_count = len(content.split()) if content else 0
    
    page_content = PageContent(
        page_number=page_number,
        content=content,
        html_content=html_content,
        word_count=word_count,
        original_page_number=printed_page_number if has_original_pagination else None,
        page_index_internal=page_index_internal,
        printed_missing=printed_missing if has_original_pagination else False,
        internal_index=page_index_internal  # N من المسار (نفس page_index_internal)
    )
    
    # حفظ في التخزين المؤقت
    if config.skip_existing:
        global_cache.set(cache_key, page_content)
    
    return page_content

# ========= دالة التجميع الرئيسية =========
def scrape_enhanced_book(book_id: str, max_pages: Optional[int] = None, 
                        extract_content: bool = True, config: PerformanceConfig = None) -> Book:
    """
    استخراج كتاب كامل بالطريقة المحسنة مع دعم إعدادات الأداء
    """
    if config is None:
        config = PerformanceConfig()
    
    # تحديث إعدادات المسجل
    if config.debug:
        setup_logging(debug_mode=True)
    
    logger.info(f"بدء استخراج الكتاب المحسن {book_id} - إعدادات الأداء: workers={config.max_workers}, batch={config.batch_size}")
    
    start_time = time.time()
    
    # 1. استخراج البيانات الأساسية
    book, soup = extract_enhanced_book_info(book_id)
    
    # 2. استخراج الفهرس المحسن
    chapters = extract_enhanced_book_index(book_id, soup)
    book.index = chapters  # للتوافق مع الكود القديم
    book.chapters = chapters  # الطريقة الجديدة
    
    # 3. استخراج روابط المجلدات
    book.volume_links = extract_volume_links(book_id, soup)
    
    # 4. استخراج الأجزاء من dropdown (الطريقة الجديدة المحسنة)
    book.volumes = extract_volumes_from_dropdown(book_id)
    book.volume_count = len(book.volumes)
    
    # 5. حساب عدد الصفحات من واجهة القراءة (الطريقة الجديدة المحسنة)
    page_count_internal, page_count_printed = calculate_page_counts_from_reader(book_id)
    book.page_count_internal = page_count_internal
    book.page_count_printed = page_count_printed
    
    # تحديث page_count للتوافق مع الكود القديم (مؤقتاً)
    book.page_count = page_count_internal
    
    # 6. بناء خريطة التنقل للترقيم المطبوع (معطل لتسريع العملية)
    # if book.has_original_pagination:
    #     book.page_navigation_map = build_page_navigation_map(
    #         book_id, page_count_internal, book.has_original_pagination
    #     )
    book.page_navigation_map = {}  # خريطة فارغة
    
    # 7. ربط الفصول بالأجزاء
    assign_chapters_to_volumes_enhanced(book.index, book.volumes)
    
    # 8. استخراج محتوى الصفحات مع التحسينات
    if extract_content:
        book.pages = extract_all_pages_enhanced(
            book_id, book.page_count or 1, max_pages, 
            book.has_original_pagination, config
        )
    
    elapsed_time = time.time() - start_time
    pages_per_second = len(book.pages) / elapsed_time if elapsed_time > 0 else 0
    
    logger.info(f"تم استخراج الكتاب المحسن {book_id} بنجاح في {elapsed_time:.2f} ثانية")
    logger.info(f"- الصفحات: {len(book.pages)} ({pages_per_second:.2f} صفحة/ثانية)")
    logger.info(f"- الفصول: {len(book.index)}")
    logger.info(f"- الأجزاء: {len(book.volumes)}")
    logger.info(f"- روابط المجلدات: {len(book.volume_links)}")
    logger.info(f"- عدد الصفحات الداخلي: {book.page_count_internal}")
    logger.info(f"- عدد الصفحات المطبوع: {book.page_count_printed}")
    logger.info(f"- خريطة التنقل: {len(book.page_navigation_map)} عنصر")
    
    return book
    
    return book

def discover_enhanced_volumes_and_pages(book_id: str, soup: BeautifulSoup, 
                                      volume_links: List[VolumeLink]) -> Tuple[List[Volume], int]:
    """
    اكتشاف الأجزاء والصفحات بطريقة محسنة
    """
    volumes = []
    max_page = 1
    
    # البحث عن إجمالي الصفحات
    page_patterns = [
        rf'/book/{book_id}/(\d+)',
        r'صفحة\s*(\d+)',
        r'الصفحات\s*[:：]\s*(\d+)'
    ]
    
    page_numbers = []
    text_content = soup.get_text()
    
    for pattern in page_patterns:
        matches = re.findall(pattern, text_content)
        for match in matches:
            try:
                page_numbers.append(int(match))
            except ValueError:
                continue
    
    if page_numbers:
        max_page = max(page_numbers)
    
    # إنشاء الأجزاء من الروابط
    if volume_links:
        for i, volume_link in enumerate(volume_links):
            if not volume_link.page_end and i == len(volume_links) - 1:
                volume_link.page_end = max_page
            
            volume = Volume(
                number=volume_link.volume_number,
                title=volume_link.title,
                page_start=volume_link.page_start,
                page_end=volume_link.page_end or max_page
            )
            volumes.append(volume)
    else:
        # إنشاء جزء واحد إذا لم توجد روابط
        volume = Volume(
            number=1,
            title="المجلد الأول",
            page_start=1,
            page_end=max_page
        )
        volumes.append(volume)
    
    return volumes, max_page

def assign_chapters_to_volumes_enhanced(chapters: List[Chapter], volumes: List[Volume]) -> None:
    """
    ربط الفصول بالأجزاء المناسبة بطريقة محسنة
    """
    def get_volume_for_page(page_num: Optional[int]) -> Optional[int]:
        if page_num is None:
            return None
        
        for volume in volumes:
            start = volume.page_start or 1
            end = volume.page_end or float('inf')
            if start <= page_num <= end:
                return volume.number
        return 1  # افتراضي للجزء الأول
    
    def process_chapters_enhanced(chapter_list: List[Chapter]):
        for chapter in chapter_list:
            chapter.volume_number = get_volume_for_page(chapter.page_number)
            if chapter.children:
                process_chapters_enhanced(chapter.children)
    
    process_chapters_enhanced(chapters)

# ========= مستخرج الصفحات المتقدم غير المتزامن =========
class AsyncPageExtractor:
    """مستخرج الصفحات غير المتزامن"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
    
    async def extract_pages_batch_async(self, book_id: str, page_range: Tuple[int, int], 
                                       has_original_pagination: bool, session: aiohttp.ClientSession) -> List[PageContent]:
        """استخراج دفعة من الصفحات بشكل غير متزامن"""
        start_page, end_page = page_range
        semaphore = asyncio.Semaphore(self.config.async_semaphore_limit)
        
        async def extract_single_page_async(page_num: int) -> Optional[PageContent]:
            async with semaphore:
                for attempt in range(self.config.retries):
                    try:
                        url = f"https://shamela.ws/book/{book_id}/{page_num}"
                        
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text()
                                
                                # استخدام معالج HTML السريع
                                result = FastHTMLProcessor.extract_page_content(html, page_num)
                                if result and result['content'].strip():
                                    # تحويل إلى PageContent
                                    page_content = PageContent(
                                        page_number=result['page_number'],
                                        content=result['content'],
                                        html_content=result['html_content'],
                                        word_count=result['word_count']
                                    )
                                    
                                    if self.config.debug:
                                        logger.debug(f"✅ استخراج ناجح للصفحة {page_num} (async)")
                                    
                                    return page_content
                                    
                            elif response.status == 404:
                                if self.config.debug:
                                    logger.warning(f"❌ صفحة غير موجودة: {page_num}")
                                return None
                            
                        await asyncio.sleep(self.config.rate_limit * (2 ** attempt))
                        
                    except Exception as e:
                        if attempt == self.config.retries - 1:
                            logger.error(f"❌ فشل نهائي في صفحة {page_num}: {e}")
                        else:
                            await asyncio.sleep(self.config.rate_limit * (2 ** attempt))
                
                return None
        
        # إنشاء المهام
        tasks = [extract_single_page_async(page) for page in range(start_page, end_page + 1)]
        
        # تنفيذ المهام مع تجميع النتائج
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # فلترة النتائج الصحيحة
        valid_results = []
        for result in results:
            if isinstance(result, PageContent):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"خطأ في المعالجة غير المتزامنة: {result}")
        
        return valid_results

# ========= مستخرج متعدد العمليات للكتب الضخمة =========
class MultiprocessExtractor:
    """مستخرج متعدد العمليات للكتب الضخمة"""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
    
    def extract_book_multiprocess(self, book_id: str, total_pages: int, 
                                 has_original_pagination: bool) -> List[PageContent]:
        """استخراج كتاب باستخدام معالجة متوازية متعددة العمليات"""
        
        # تقسيم الصفحات إلى قطع
        chunks = self._create_page_chunks(total_pages)
        
        logger.info(f"🚀 معالجة متوازية متعددة العمليات: {len(chunks)} دفعة على {self.config.max_processes} عملية")
        
        # معالجة متوازية
        all_pages = []
        with ProcessPoolExecutor(max_workers=self.config.max_processes) as executor:
            # إرسال المهام
            future_to_chunk = {
                executor.submit(extract_chunk_worker, book_id, chunk, has_original_pagination, 
                               self.config.__dict__): chunk 
                for chunk in chunks
            }
            
            # جمع النتائج
            for i, future in enumerate(as_completed(future_to_chunk)):
                chunk = future_to_chunk[future]
                try:
                    chunk_pages = future.result(timeout=600)  # 10 دقائق لكل دفعة
                    all_pages.extend(chunk_pages)
                    
                    start_page, end_page = chunk
                    logger.info(f"✅ انتهت الدفعة {i+1}/{len(chunks)} "
                               f"(صفحات {start_page}-{end_page}): {len(chunk_pages)} صفحة")
                    
                except Exception as e:
                    start_page, end_page = chunk
                    logger.error(f"❌ فشلت الدفعة {i+1} (صفحات {start_page}-{end_page}): {e}")
        
        # ترتيب النتائج
        return sorted(all_pages, key=lambda x: x.page_number)
    
    def _create_page_chunks(self, total_pages: int) -> List[Tuple[int, int]]:
        """تقسيم الصفحات إلى قطع للمعالجة المتوازية"""
        chunk_size = max(self.config.process_chunk_size, 
                        total_pages // self.config.max_processes)
        
        chunks = []
        for i in range(1, total_pages + 1, chunk_size):
            end = min(i + chunk_size - 1, total_pages)
            chunks.append((i, end))
        
        return chunks

def extract_chunk_worker(book_id: str, page_range: Tuple[int, int], 
                        has_original_pagination: bool, config_dict: dict) -> List[PageContent]:
    """عامل لاستخراج قطعة من الصفحات في عملية منفصلة"""
    # تحويل القاموس إلى إعدادات
    config = PerformanceConfig(**config_dict)
    
    # إنشاء حلقة جديدة للعملية
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(extract_chunk_async(book_id, page_range, has_original_pagination, config))
    finally:
        loop.close()

async def extract_chunk_async(book_id: str, page_range: Tuple[int, int], 
                             has_original_pagination: bool, config: PerformanceConfig) -> List[PageContent]:
    """استخراج قطعة باستخدام async في عملية منفصلة"""
    extractor = AsyncPageExtractor(config)
    
    async with AdvancedHTTPSession(config) as session:
        return await extractor.extract_pages_batch_async(book_id, page_range, has_original_pagination, session)

def extract_all_pages_enhanced(book_id: str, total_pages: int, max_pages: Optional[int], 
                              has_original_pagination: bool, config: PerformanceConfig = None) -> List[PageContent]:
    """
    استخراج جميع صفحات الكتاب بطريقة محسنة مع دعم التحسينات المتقدمة
    """
    if config is None:
        config = PerformanceConfig()
    
    actual_max = min(total_pages, max_pages) if max_pages else total_pages
    
    logger.info(f"🚀 بدء الاستخراج المحسن للكتاب {book_id} - {actual_max} صفحة")
    
    # اختيار طريقة الاستخراج حسب الحجم والإعدادات
    if config.use_async and actual_max >= config.multiprocessing_threshold:
        logger.info(f"📚 كتاب ضخم ({actual_max} صفحة) - استخدام المعالجة متعددة العمليات")
        extractor = MultiprocessExtractor(config)
        pages = extractor.extract_book_multiprocess(book_id, actual_max, has_original_pagination)
        
    elif config.use_async:
        logger.info(f"📖 كتاب صغير/متوسط ({actual_max} صفحة) - استخدام المعالجة غير المتزامنة")
        # تشغيل المعالجة غير المتزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            pages = loop.run_until_complete(
                extract_pages_async_method(book_id, actual_max, has_original_pagination, config)
            )
        finally:
            loop.close()
            
    else:
        logger.info(f"📄 استخدام الطريقة التقليدية ({actual_max} صفحة)")
        pages = extract_pages_traditional_method(book_id, actual_max, has_original_pagination, config)
    
    # ترتيب الصفحات حسب الرقم
    pages.sort(key=lambda p: p.page_number)
    
    # إحصائيات
    total_words = sum(page.word_count for page in pages)
    logger.info(f"🎉 تم استخراج {len(pages)} صفحة بنجاح")
    logger.info(f"📊 إجمالي الكلمات: {total_words:,} كلمة")
    
    return pages

async def extract_pages_async_method(book_id: str, total_pages: int, 
                                   has_original_pagination: bool, config: PerformanceConfig) -> List[PageContent]:
    """استخراج باستخدام الطريقة غير المتزامنة"""
    
    extractor = AsyncPageExtractor(config)
    all_pages = []
    
    # تقسيم إلى دفعات
    batch_size = config.async_batch_size
    
    async with AdvancedHTTPSession(config) as session:
        for i in range(1, total_pages + 1, batch_size):
            end_page = min(i + batch_size - 1, total_pages)
            
            if config.debug:
                logger.info(f"📄 معالجة الدفعة غير المتزامنة: صفحات {i}-{end_page}")
            
            batch_pages = await extractor.extract_pages_batch_async(
                book_id, (i, end_page), has_original_pagination, session
            )
            
            all_pages.extend(batch_pages)
            
            if config.debug:
                logger.info(f"✅ انتهت الدفعة: {len(batch_pages)} صفحة")
            
            # تنظيف الذاكرة إذا لزم الأمر
            if config.memory_efficient and len(all_pages) % config.gc_threshold == 0:
                import gc
                gc.collect()
    
    return all_pages

def extract_pages_traditional_method(book_id: str, total_pages: int, 
                                   has_original_pagination: bool, config: PerformanceConfig) -> List[PageContent]:
    """استخراج باستخدام الطريقة التقليدية (threading)"""
    
    pages = []
    
    def extract_single_page(page_num: int) -> Optional[PageContent]:
        """استخراج صفحة واحدة"""
        try:
            if not config.debug and page_num % 100 == 0:
                logger.info(f"استخراج الصفحة {page_num}/{total_pages}")
            elif config.debug:
                logger.debug(f"استخراج الصفحة {page_num}/{total_pages}")
            
            page_content = extract_enhanced_page_content(
                book_id, page_num, has_original_pagination, config
            )
            
            if page_content and page_content.content.strip():  # تجاهل الصفحات الفارغة
                return page_content
            return None
            
        except Exception as e:
            logger.warning(f"فشل في استخراج الصفحة {page_num}: {e}")
            return None
    
    if config.max_workers == 1:
        # استخراج تسلسلي
        for page_num in range(1, total_pages + 1):
            page_content = extract_single_page(page_num)
            if page_content:
                pages.append(page_content)
            
            # تأخير محترم
            if config.rate_limit > 0:
                time.sleep(config.rate_limit)
    else:
        # استخراج متوازي
        page_numbers = list(range(1, total_pages + 1))
        
        with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
            # إرسال المهام
            future_to_page = {
                executor.submit(extract_single_page, page_num): page_num 
                for page_num in page_numbers
            }
            
            # جمع النتائج
            for future in as_completed(future_to_page):
                page_num = future_to_page[future]
                try:
                    page_content = future.result()
                    if page_content:
                        pages.append(page_content)
                except Exception as e:
                    logger.warning(f"فشل في معالجة الصفحة {page_num}: {e}")
                
                # تأخير بين المهام للحد من الضغط على الخادم
                if config.rate_limit > 0:
                    time.sleep(config.rate_limit / config.max_workers)
    
    return pages

# ========= حفظ البيانات المحسنة =========
def save_enhanced_book_to_json(book: Book, output_path: str, config: PerformanceConfig = None) -> None:
    """
    حفظ الكتاب المحسن في ملف JSON مع دعم الضغط والتدفق
    """
    if config is None:
        config = PerformanceConfig()
    
    # تحويل الكتاب إلى قاموس
    book_dict = {
        'title': book.title,
        'shamela_id': book.shamela_id,
        'slug': book.slug,
        'authors': [
            {
                'name': author.name,
                'slug': author.slug,
                'biography': author.biography,
                'madhhab': author.madhhab,
                'birth_date': author.birth_date,
                'death_date': author.death_date
            } for author in book.authors
        ],
        'publisher': {
            'name': book.publisher.name,
            'slug': book.publisher.slug,
            'location': book.publisher.location,
            'description': book.publisher.description
        } if book.publisher else None,
        'book_section': {
            'name': book.book_section.name,
            'slug': book.book_section.slug,
            'description': book.book_section.description
        } if book.book_section else None,
        'edition': book.edition,
        'edition_number': book.edition_number,
        'publication_year': book.publication_year,
        'edition_date_hijri': book.edition_date_hijri,
        'page_count': book.page_count,  # للتوافق القديم
        'page_count_internal': book.page_count_internal,
        'page_count_printed': book.page_count_printed,
        'volume_count': book.volume_count,
        'categories': book.categories,
        'description': book.description,
        'language': book.language,
        'source_url': book.source_url,
        'has_original_pagination': book.has_original_pagination,
        'page_navigation_map': book.page_navigation_map,
        'extraction_date': datetime.now().isoformat(),
        'volumes': [
            {
                'number': volume.number,
                'title': volume.title,
                'page_start': volume.page_start,
                'page_end': volume.page_end
            } for volume in book.volumes
        ],
        'volume_links': [
            {
                'volume_number': vl.volume_number,
                'title': vl.title,
                'url': vl.url,
                'page_start': vl.page_start,
                'page_end': vl.page_end
            } for vl in book.volume_links
        ],
        'index': convert_chapters_to_dict(book.index),
        'pages': [
            {
                'page_number': page.page_number,
                'content': page.content,
                'html_content': page.html_content,
                'volume_number': page.volume_number,
                'word_count': page.word_count,
                'original_page_number': page.original_page_number,
                'page_index_internal': page.page_index_internal,
                'internal_index': page.internal_index,
                'printed_missing': page.printed_missing
            } for page in book.pages
        ]
    }
    
    # حفظ الملف مع الضغط الاختياري
    output_dir = os.path.dirname(output_path)
    if output_dir:  # فقط إنشاء المجلد إذا كان هناك مسار
        os.makedirs(output_dir, exist_ok=True)
    
    if config.enable_compression and output_path.endswith('.json'):
        # حفظ مضغوط
        compressed_path = output_path + '.gz'
        with gzip.open(compressed_path, 'wt', encoding='utf-8') as f:
            json.dump(book_dict, f, ensure_ascii=False, indent=2 if config.debug else None)
        logger.info(f"تم حفظ الكتاب المحسن (مضغوط) في {compressed_path}")
    else:
        # حفظ عادي مع تحسين الذاكرة للملفات الكبيرة
        if config.stream_json and len(book.pages) > 1000:
            # حفظ تدريجي للكتب الكبيرة
            with open(output_path, 'w', encoding='utf-8') as f:
                _write_json_streaming(book_dict, f, config)
        else:
            # حفظ عادي
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(book_dict, f, ensure_ascii=False, 
                         indent=2 if config.debug else None)
        logger.info(f"تم حفظ الكتاب المحسن في {output_path}")

def _write_json_streaming(data: dict, file_obj, config: PerformanceConfig):
    """كتابة JSON بطريقة تدريجية لتوفير الذاكرة"""
    file_obj.write('{\n')
    
    keys = list(data.keys())
    for i, key in enumerate(keys):
        file_obj.write(f'  "{key}": ')
        
        if key == 'pages' and isinstance(data[key], list):
            # كتابة الصفحات تدريجياً
            file_obj.write('[\n')
            for j, page in enumerate(data[key]):
                if j > 0:
                    file_obj.write(',\n')
                json.dump(page, file_obj, ensure_ascii=False, indent=4)
            file_obj.write('\n  ]')
        else:
            json.dump(data[key], file_obj, ensure_ascii=False, indent=2 if config.debug else None)
        
        if i < len(keys) - 1:
            file_obj.write(',')
        file_obj.write('\n')
    
    file_obj.write('}')

def convert_chapters_to_dict(chapters: List[Chapter]) -> List[Dict]:
    """
    تحويل الفصول إلى قاموس للحفظ في JSON
    """
    result = []
    for chapter in chapters:
        chapter_dict = {
            'title': chapter.title,
            'order': chapter.order,
            'page_number': chapter.page_number,
            'page_end': chapter.page_end,
            'volume_number': chapter.volume_number,
            'level': chapter.level,
            'chapter_type': chapter.chapter_type,
            'children': convert_chapters_to_dict(chapter.children) if chapter.children else []
        }
        result.append(chapter_dict)
    return result

# ========= واجهة سطر الأوامر المحسنة =========
def main():
    """
    الوظيفة الرئيسية المحسنة مع دعم أعلام الأداء
    """
    parser = argparse.ArgumentParser(
        description="Enhanced Shamela Scraper with Performance Optimizations"
    )
    
    parser.add_argument('book_id', help='Book ID in Shamela Library')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to extract')
    parser.add_argument('--no-content', action='store_true', help='Skip page content extraction')
    parser.add_argument('--output', '-o', help='JSON output file path')
    
    # Traditional performance flags  
    parser.add_argument('--max-workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    parser.add_argument('--batch-size', type=int, default=500, help='Batch size (default: 500)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--retries', type=int, default=3, help='Number of retries (default: 3)')
    parser.add_argument('--rate', type=float, default=0.5, help='Delay between requests in seconds (default: 0.5)')
    parser.add_argument('--stream-json', action='store_true', help='Enable streaming JSON for large books')
    parser.add_argument('--skip-existing', action='store_true', default=True, help='Skip existing items')
    parser.add_argument('--resume', action='store_true', help='Enable resume functionality')
    parser.add_argument('--compress', action='store_true', help='Enable JSON compression')
    parser.add_argument('--memory-efficient', action='store_true', help='Memory-efficient processing')
    parser.add_argument('--debug', action='store_true', help='Enable detailed debugging')
    
    # Advanced optimization flags
    parser.add_argument('--use-async', action='store_true', help='Use async/await processing')
    parser.add_argument('--multiprocessing-threshold', type=int, default=1000, help='Multiprocessing threshold (default: 1000)')
    parser.add_argument('--aiohttp-workers', type=int, default=8, help='Number of aiohttp workers (default: 8)')
    parser.add_argument('--use-lxml', action='store_true', help='Use lxml for fast HTML parsing')
    parser.add_argument('--async-batch-size', type=int, default=50, help='Async batch size (default: 50)')
    parser.add_argument('--force-traditional', action='store_true', help='Force traditional method')
    
    args = parser.parse_args()
    
    # إنشاء كائن إعدادات الأداء المحسن
    config = PerformanceConfig(
        max_workers=args.max_workers,
        batch_size=args.batch_size,
        timeout=args.timeout,
        retries=args.retries,
        rate_limit=args.rate,
        stream_json=args.stream_json,
        skip_existing=args.skip_existing,
        resume_enabled=args.resume,
        enable_compression=args.compress,
        memory_efficient=args.memory_efficient,
        debug=args.debug
    )
    
    # تحديث خيارات التحسينات المتقدمة
    config.use_async = args.use_async
    config.multiprocessing_threshold = args.multiprocessing_threshold
    config.aiohttp_workers = args.aiohttp_workers
    config.use_lxml = args.use_lxml
    config.async_batch_size = args.async_batch_size
    config.force_traditional = args.force_traditional
    
    # تحديث الثوابت العامة
    global REQ_TIMEOUT, MAX_RETRIES, REQUEST_DELAY
    REQ_TIMEOUT = config.timeout
    MAX_RETRIES = config.retries
    REQUEST_DELAY = config.rate_limit
    
    try:
        # تحديد مسار الإخراج
        if not args.output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = '.json.gz' if config.enable_compression else '.json'
            args.output = f"enhanced_book_{args.book_id}_{timestamp}{extension}"
        
        print("=" * 60)
        print("سكربت المكتبة الشاملة المحسن مع تحسينات الأداء المتقدمة")
        print("Enhanced Shamela Scraper with Advanced Performance Optimizations")
        print("=" * 60)
        print(f"📖 كتاب: {args.book_id}")
        
        # عرض معلومات التحسينات المتقدمة
        if config.use_async:
            print(f"🚀 وضع: غير متزامن (Async)")
            print(f"⚡ عمال Aiohttp: {config.aiohttp_workers}")
            print(f"📦 دفعة غير متزامنة: {config.async_batch_size}")
        elif not config.force_traditional:
            print(f"🔄 وضع: متعدد المعالجات (Multiprocessing)")
            print(f"🎯 عتبة التبديل: {config.multiprocessing_threshold}")
        else:
            print(f"📊 وضع: تقليدي محسن")
        
        print(f"⚡ العمال: {config.max_workers}")
        print(f"📦 الدفعة: {config.batch_size}")
        print(f"⏱️ المهلة: {config.timeout}s")
        print(f"🔄 إعادات: {config.retries}")
        print(f"⏲️ التأخير: {config.rate_limit}s")
        print(f"🏗️ محلل HTML: {'lxml' if config.use_lxml else 'BeautifulSoup'}")
        print(f"💾 ضغط: {'نعم' if config.enable_compression else 'لا'}")
        print(f"🧠 موفر ذاكرة: {'نعم' if config.memory_efficient else 'لا'}")
        print(f"🐛 تطوير: {'نعم' if config.debug else 'لا'}")
        print("-" * 60)
        
        # استخراج الكتاب مع التحسينات
        start_time = time.time()
        book = scrape_enhanced_book(
            args.book_id,
            max_pages=args.max_pages,
            extract_content=not args.no_content,
            config=config
        )
        
        # حفظ الكتاب مع التحسينات
        save_enhanced_book_to_json(book, args.output, config)
        
        elapsed_time = time.time() - start_time
        pages_per_second = len(book.pages) / elapsed_time if elapsed_time > 0 else 0
        
        print("\n" + "=" * 60)
        print("✅ تم استخراج الكتاب بنجاح!")
        print("=" * 60)
        print(f"📚 العنوان: {book.title}")
        print(f"👨‍🎓 المؤلفون: {', '.join(author.name for author in book.authors)}")
        
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
        
        # إحصائيات الأداء
        total_words = sum(page.word_count or 0 for page in book.pages)
        if total_words > 0:
            print(f"📊 إجمالي الكلمات: {total_words:,}")
        
        print(f"⏱️ الزمن الكلي: {elapsed_time:.2f} ثانية")
        print(f"⚡ السرعة: {pages_per_second:.2f} صفحة/ثانية")
        print(f"💾 حُفظ في: {args.output}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"خطأ في استخراج الكتاب: {e}")
        print(f"❌ خطأ: {e}")
        sys.exit(1)
    finally:
        # تنظيف الموارد
        http_session.close()
        global_cache.clear()

if __name__ == "__main__":
    main()
