#!/usr/bin/env python3
"""
تكوين السرعة الفائقة - Ultra Speed Configuration
إعدادات متقدمة لتحقيق أقصى سرعة ممكنة
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))
from enhanced_shamela_scraper import PerformanceConfig

class UltraSpeedConfig(PerformanceConfig):
    """تكوين السرعة الفائقة"""
    
    def __init__(self):
        super().__init__()
        
        # ⚡ إعدادات الشبكة الفائقة
        self.max_workers = 24  # أقصى عدد عمال
        self.connection_pool_size = 30  # تجمع اتصالات أكبر
        self.request_delay = 0.05  # أقل تأخير ممكن
        self.max_retries = 2  # تقليل المحاولات
        self.timeout = 5  # انتظار أقل
        
        # 🚀 إعدادات المعالجة المتقدمة
        self.use_async = False  # ثابت للاستقرار
        self.use_lxml = True  # أسرع محلل
        self.enable_caching = True  # تخزين مؤقت ذكي
        self.batch_size = 5000  # دفعات ضخمة
        self.async_batch_size = 20  # دفعات غير متزامنة أكبر
        
        # 💾 تحسينات الذاكرة
        self.memory_optimization = True
        self.compress_responses = True
        self.clear_cache_interval = 1000
        self.enable_compression = False  # عدم ضغط ملفات JSON
        
        # 🎯 تحسينات ذكية
        self.adaptive_delay = True  # تأخير متكيف
        self.smart_retry = True  # إعادة محاولة ذكية
        self.connection_reuse = True  # إعادة استخدام الاتصالات
        
        # 📊 مراقبة الأداء
        self.performance_monitoring = True
        self.log_performance_stats = True

def get_ultra_speed_config():
    """الحصول على تكوين السرعة الفائقة"""
    return UltraSpeedConfig()

# إعدادات خاصة بأنواع الكتب
BOOK_SIZE_CONFIGS = {
    'small': {  # أقل من 100 صفحة
        'workers': 16,
        'batch_size': 2000,
        'delay': 0.1
    },
    'medium': {  # 100-1000 صفحة
        'workers': 20,
        'batch_size': 3000,
        'delay': 0.08
    },
    'large': {  # 1000-5000 صفحة
        'workers': 24,
        'batch_size': 4000,
        'delay': 0.05
    },
    'huge': {  # أكثر من 5000 صفحة
        'workers': 28,
        'batch_size': 5000,
        'delay': 0.03,
        'use_multiprocessing': True
    }
}

def get_optimal_config_for_book_size(page_count):
    """الحصول على التكوين الأمثل حسب حجم الكتاب"""
    config = UltraSpeedConfig()
    
    if page_count < 100:
        # كتب صغيرة - طريقة تقليدية سريعة
        settings = BOOK_SIZE_CONFIGS['small']
        config.use_async = False
    elif page_count < 500:
        # كتب متوسطة - استخدام threading
        settings = BOOK_SIZE_CONFIGS['medium'] 
        config.use_async = False
        config.multiprocessing_threshold = 999999  # تعطيل multiprocessing
    elif page_count < 1000:
        # كتب كبيرة - تفعيل async لكن بدون multiprocessing
        settings = BOOK_SIZE_CONFIGS['large']
        config.use_async = True
        config.multiprocessing_threshold = 2000  # رفع العتبة
    else:
        # كتب ضخمة - تفعيل المعالجة متعددة العمليات
        settings = BOOK_SIZE_CONFIGS['huge']
        config.use_async = True
        config.multiprocessing_threshold = 200  # تفعيل multiprocessing للكتب الضخمة
        config.use_multiprocessing = True
    
    # تطبيق الإعدادات
    config.max_workers = settings['workers']
    config.batch_size = settings['batch_size']
    config.request_delay = settings['delay']
    
    return config

# اختبار سرعة الشبكة وتحسين الإعدادات تلقائياً
def auto_tune_config():
    """ضبط تلقائي للإعدادات حسب سرعة الشبكة"""
    import time
    import requests
    
    config = UltraSpeedConfig()
    
    # اختبار سرعة الاتصال
    try:
        start_time = time.time()
        response = requests.get('https://shamela.ws', timeout=5)
        ping_time = time.time() - start_time
        
        if ping_time < 0.5:
            # اتصال سريع جداً
            config.max_workers = 32
            config.request_delay = 0.02
            config.batch_size = 8000
        elif ping_time < 1.0:
            # اتصال سريع
            config.max_workers = 24
            config.request_delay = 0.05
            config.batch_size = 5000
        elif ping_time < 2.0:
            # اتصال متوسط
            config.max_workers = 16
            config.request_delay = 0.1
            config.batch_size = 3000
        else:
            # اتصال بطيء
            config.max_workers = 8
            config.request_delay = 0.2
            config.batch_size = 1000
            
    except Exception:
        # في حالة فشل الاختبار، استخدم الإعدادات الافتراضية
        pass
    
    return config

if __name__ == "__main__":
    # اختبار التكوين الفائق
    config = get_ultra_speed_config()
    print("🚀 تكوين السرعة الفائقة:")
    print(f"   العمال: {config.max_workers}")
    print(f"   حجم الدفعة: {config.batch_size}")
    print(f"   تجمع الاتصالات: {config.connection_pool_size}")
    print(f"   التأخير: {config.request_delay}s")
    print(f"   lxml: {config.use_lxml}")
    print(f"   التخزين المؤقت: {config.enable_caching}")
