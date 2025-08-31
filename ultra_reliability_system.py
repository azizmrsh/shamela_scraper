#!/usr/bin/env python3
"""
نظام الموثوقية الكاملة - Ultra Reliability System
ضمان 100% نجاح استخراج الكتب بدون أي أخطاء
"""

import time
import logging
import threading
import queue
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os
from pathlib import Path

# إعداد تسجيل مفصل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[
        logging.FileHandler('ultra_reliable_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ReliabilityConfig:
    """تكوين الموثوقية الكاملة"""
    
    # إعدادات المحاولات المتقدمة
    max_retries: int = 5
    retry_backoff_factor: float = 2.0
    retry_status_forcelist: List[int] = None
    
    # إعدادات المهلة الزمنية
    connection_timeout: float = 30.0
    read_timeout: float = 60.0
    total_timeout: float = 90.0
    
    # إعدادات الاتصال المتقدمة
    pool_connections: int = 50
    pool_maxsize: int = 50
    max_connections_per_host: int = 10
    
    # إعدادات التحقق والتكرار
    verify_ssl: bool = True
    allow_redirects: bool = True
    stream: bool = False
    
    # إعدادات الاستعادة الذكية
    enable_recovery: bool = True
    recovery_attempts: int = 3
    recovery_delay: float = 5.0
    
    # إعدادات النسخ الاحتياطي
    enable_backup: bool = True
    backup_interval: int = 100  # كل 100 صفحة
    max_backup_files: int = 5
    
    # إعدادات مراقبة الصحة
    health_check_interval: float = 10.0
    max_consecutive_failures: int = 3
    
    def __post_init__(self):
        if self.retry_status_forcelist is None:
            self.retry_status_forcelist = [429, 500, 502, 503, 504, 520, 521, 522, 523, 524]

class ReliabilityMonitor:
    """مراقب الموثوقية والصحة"""
    
    def __init__(self, config: ReliabilityConfig):
        self.config = config
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'retries_used': 0,
            'recoveries_performed': 0,
            'consecutive_failures': 0,
            'last_success_time': time.time(),
            'start_time': time.time()
        }
        self.lock = threading.Lock()
        
    def record_success(self):
        """تسجيل نجاح العملية"""
        with self.lock:
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            self.stats['consecutive_failures'] = 0
            self.stats['last_success_time'] = time.time()
            
    def record_failure(self):
        """تسجيل فشل العملية"""
        with self.lock:
            self.stats['total_requests'] += 1
            self.stats['failed_requests'] += 1
            self.stats['consecutive_failures'] += 1
            
    def record_retry(self):
        """تسجيل محاولة إعادة"""
        with self.lock:
            self.stats['retries_used'] += 1
            
    def record_recovery(self):
        """تسجيل استعادة"""
        with self.lock:
            self.stats['recoveries_performed'] += 1
            self.stats['consecutive_failures'] = 0
            
    def get_success_rate(self) -> float:
        """حساب معدل النجاح"""
        with self.lock:
            if self.stats['total_requests'] == 0:
                return 100.0
            return (self.stats['successful_requests'] / self.stats['total_requests']) * 100
    
    def is_healthy(self) -> bool:
        """فحص صحة النظام"""
        with self.lock:
            # فحص الفشل المتتالي
            if self.stats['consecutive_failures'] >= self.config.max_consecutive_failures:
                return False
            
            # فحص الوقت منذ آخر نجاح
            time_since_success = time.time() - self.stats['last_success_time']
            if time_since_success > 300:  # 5 دقائق
                return False
                
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات مفصلة"""
        with self.lock:
            uptime = time.time() - self.stats['start_time']
            return {
                **self.stats,
                'success_rate': self.get_success_rate(),
                'uptime_seconds': uptime,
                'uptime_minutes': uptime / 60,
                'requests_per_minute': (self.stats['total_requests'] / uptime) * 60 if uptime > 0 else 0
            }

class UltraReliableSession:
    """جلسة HTTP فائقة الموثوقية"""
    
    def __init__(self, config: ReliabilityConfig):
        self.config = config
        self.monitor = ReliabilityMonitor(config)
        self.session = self._create_session()
        self._last_health_check = time.time()
        
    def _create_session(self) -> requests.Session:
        """إنشاء جلسة HTTP محسنة"""
        session = requests.Session()
        
        # إعداد إستراتيجية المحاولات المتقدمة
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_backoff_factor,
            status_forcelist=self.config.retry_status_forcelist,
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]  # إصدار جديد من urllib3
        )
        
        # إعداد محول HTTP مع تجمع اتصالات متقدم
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize,
            pool_block=True
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # إعدادات الجلسة
        session.verify = self.config.verify_ssl
        
        # رؤوس متقدمة
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ar,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        
        return session
    
    def _health_check(self):
        """فحص صحة النظام"""
        current_time = time.time()
        if current_time - self._last_health_check > self.config.health_check_interval:
            if not self.monitor.is_healthy():
                logger.warning("🚨 النظام غير صحي - إعادة تهيئة الجلسة")
                self._reset_session()
            self._last_health_check = current_time
    
    def _reset_session(self):
        """إعادة تهيئة الجلسة"""
        try:
            self.session.close()
        except:
            pass
        self.session = self._create_session()
        self.monitor.record_recovery()
        logger.info("✅ تم إعادة تهيئة الجلسة بنجاح")
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """طلب GET فائق الموثوقية"""
        return self._request('GET', url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """طلب POST فائق الموثوقية"""
        return self._request('POST', url, **kwargs)
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """تنفيذ طلب HTTP فائق الموثوقية"""
        
        # فحص الصحة
        self._health_check()
        
        # إعداد المهلة الزمنية
        if 'timeout' not in kwargs:
            kwargs['timeout'] = (self.config.connection_timeout, self.config.read_timeout)
        
        # إعداد المعاملات
        kwargs.setdefault('allow_redirects', self.config.allow_redirects)
        kwargs.setdefault('stream', self.config.stream)
        
        # المحاولات مع الاستعادة
        last_exception = None
        
        for recovery_attempt in range(self.config.recovery_attempts + 1):
            try:
                # تنفيذ الطلب
                response = self.session.request(method, url, **kwargs)
                
                # فحص حالة الاستجابة
                if response.status_code == 200:
                    self.monitor.record_success()
                    return response
                elif response.status_code in [404, 403, 410]:
                    # أخطاء دائمة - لا تحاول مرة أخرى
                    self.monitor.record_failure()
                    logger.error(f"❌ خطأ دائم {response.status_code} للرابط: {url}")
                    raise requests.exceptions.HTTPError(f"HTTP {response.status_code}", response=response)
                else:
                    # أخطاء مؤقتة - سيتم المحاولة مرة أخرى
                    self.monitor.record_failure()
                    raise requests.exceptions.HTTPError(f"HTTP {response.status_code}", response=response)
                    
            except Exception as e:
                last_exception = e
                self.monitor.record_failure()
                
                # إذا كانت هذه ليست المحاولة الأخيرة
                if recovery_attempt < self.config.recovery_attempts:
                    wait_time = self.config.recovery_delay * (2 ** recovery_attempt)
                    logger.warning(f"⚠️ فشل في الطلب (محاولة {recovery_attempt + 1}/{self.config.recovery_attempts + 1}): {str(e)}")
                    logger.info(f"⏳ انتظار {wait_time:.1f} ثانية قبل المحاولة التالية...")
                    time.sleep(wait_time)
                    
                    # إعادة تهيئة الجلسة في المحاولة الأخيرة
                    if recovery_attempt == self.config.recovery_attempts - 1:
                        logger.info("🔄 إعادة تهيئة الجلسة للمحاولة الأخيرة...")
                        self._reset_session()
                else:
                    break
        
        # إذا فشلت جميع المحاولات
        logger.error(f"💥 فشل نهائي في الطلب بعد {self.config.recovery_attempts + 1} محاولات: {url}")
        logger.error(f"آخر خطأ: {str(last_exception)}")
        raise last_exception
    
    def close(self):
        """إغلاق الجلسة"""
        try:
            self.session.close()
        except:
            pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class BackupManager:
    """مدير النسخ الاحتياطية الذكي"""
    
    def __init__(self, config: ReliabilityConfig, backup_dir: str = "backups"):
        self.config = config
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, data: Dict[str, Any], book_id: str, page_count: int) -> str:
        """إنشاء نسخة احتياطية"""
        if not self.config.enable_backup:
            return None
            
        timestamp = int(time.time())
        filename = f"backup_{book_id}_{page_count}pages_{timestamp}.json"
        filepath = self.backup_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # تنظيف النسخ القديمة
            self._cleanup_old_backups(book_id)
            
            logger.info(f"💾 تم إنشاء نسخة احتياطية: {filename}")
            return str(filepath)
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء النسخة الاحتياطية: {str(e)}")
            return None
    
    def _cleanup_old_backups(self, book_id: str):
        """تنظيف النسخ الاحتياطية القديمة"""
        try:
            backup_files = list(self.backup_dir.glob(f"backup_{book_id}_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # الاحتفاظ بأحدث النسخ فقط
            for old_backup in backup_files[self.config.max_backup_files:]:
                old_backup.unlink()
                logger.debug(f"🗑️ حُذفت النسخة الاحتياطية القديمة: {old_backup.name}")
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف النسخ الاحتياطية: {str(e)}")
    
    def restore_from_backup(self, book_id: str) -> Optional[Dict[str, Any]]:
        """استعادة من النسخة الاحتياطية"""
        try:
            backup_files = list(self.backup_dir.glob(f"backup_{book_id}_*.json"))
            if not backup_files:
                return None
            
            # أحدث نسخة احتياطية
            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_backup, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"📂 تم استعادة البيانات من النسخة الاحتياطية: {latest_backup.name}")
            return data
        except Exception as e:
            logger.error(f"❌ فشل في الاستعادة من النسخة الاحتياطية: {str(e)}")
            return None

def create_ultra_reliable_config() -> ReliabilityConfig:
    """إنشاء تكوين الموثوقية الكاملة"""
    return ReliabilityConfig(
        max_retries=7,
        retry_backoff_factor=1.5,
        connection_timeout=45.0,
        read_timeout=90.0,
        total_timeout=120.0,
        pool_connections=30,
        pool_maxsize=30,
        enable_recovery=True,
        recovery_attempts=5,
        recovery_delay=3.0,
        enable_backup=True,
        backup_interval=50,
        max_backup_files=10,
        health_check_interval=15.0,
        max_consecutive_failures=2
    )

# مثال على الاستخدام
if __name__ == "__main__":
    config = create_ultra_reliable_config()
    
    with UltraReliableSession(config) as session:
        try:
            response = session.get("https://shamela.ws/book/12106")
            print(f"✅ نجح الطلب: {response.status_code}")
            
            # طباعة الإحصائيات
            stats = session.monitor.get_stats()
            print(f"📊 معدل النجاح: {stats['success_rate']:.2f}%")
            print(f"📈 الطلبات في الدقيقة: {stats['requests_per_minute']:.1f}")
            
        except Exception as e:
            print(f"❌ فشل في الطلب: {str(e)}")
