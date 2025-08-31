#!/usr/bin/env python3
"""
مختبر النظام فائق الموثوقية - Ultra Reliability Tester
اختبار سريع للنظام الجديد
"""

import time
import json
import logging
from pathlib import Path
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
from ultra_reliability_system import UltraReliableSession, create_ultra_reliable_config

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ultra_reliability():
    """اختبار النظام فائق الموثوقية"""
    
    print("🚀 اختبار النظام فائق الموثوقية")
    print("=" * 60)
    
    config = create_ultra_reliable_config()
    
    print(f"⚙️ التكوين:")
    print(f"   محاولات إعادة: {config.max_retries}")
    print(f"   مهلة الاتصال: {config.connection_timeout}s")
    print(f"   مهلة القراءة: {config.read_timeout}s")
    print(f"   تجمع الاتصالات: {config.pool_connections}")
    print(f"   استعادة تلقائية: {'مفعل' if config.enable_recovery else 'معطل'}")
    print(f"   نسخ احتياطية: {'مفعل' if config.enable_backup else 'معطل'}")
    print()
    
    with UltraReliableSession(config) as session:
        
        # اختبار 1: تحميل صفحة أساسية
        print("📋 اختبار 1: تحميل صفحة الكتاب الأساسية...")
        try:
            start_time = time.time()
            response = session.get("https://shamela.ws/book/12106")
            elapsed = time.time() - start_time
            
            print(f"✅ نجح الاختبار 1: {response.status_code} في {elapsed:.2f}ث")
            print(f"   حجم البيانات: {len(response.text):,} حرف")
            
        except Exception as e:
            print(f"❌ فشل الاختبار 1: {str(e)}")
            return False
        
        # اختبار 2: تحميل عدة صفحات
        print("\n📋 اختبار 2: تحميل صفحات متعددة...")
        success_count = 0
        total_tests = 5
        total_time = 0
        
        for page_num in range(1, total_tests + 1):
            try:
                start_time = time.time()
                url = f"https://shamela.ws/book/12106/{page_num}"
                response = session.get(url)
                elapsed = time.time() - start_time
                total_time += elapsed
                
                if response.status_code == 200:
                    success_count += 1
                    print(f"   ✅ صفحة {page_num}: {len(response.text)} حرف في {elapsed:.2f}ث")
                else:
                    print(f"   ⚠️ صفحة {page_num}: خطأ {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ صفحة {page_num}: {str(e)}")
        
        # نتائج الاختبار 2
        success_rate = (success_count / total_tests) * 100
        avg_speed = total_tests / total_time if total_time > 0 else 0
        
        print(f"\n📊 نتائج الاختبار 2:")
        print(f"   معدل النجاح: {success_rate:.1f}% ({success_count}/{total_tests})")
        print(f"   الوقت الإجمالي: {total_time:.2f}ث")
        print(f"   السرعة المتوسطة: {avg_speed:.2f} صفحة/ثانية")
        
        # اختبار 3: فحص الإحصائيات
        print(f"\n📋 اختبار 3: إحصائيات الجلسة...")
        stats = session.monitor.get_stats()
        
        print(f"   إجمالي الطلبات: {stats['total_requests']}")
        print(f"   الطلبات الناجحة: {stats['successful_requests']}")
        print(f"   الطلبات الفاشلة: {stats['failed_requests']}")
        print(f"   معدل النجاح: {stats['success_rate']:.2f}%")
        print(f"   المحاولات المستخدمة: {stats['retries_used']}")
        print(f"   الاستعادات المنجزة: {stats['recoveries_performed']}")
        print(f"   وقت التشغيل: {stats['uptime_minutes']:.2f} دقيقة")
        print(f"   الطلبات/دقيقة: {stats['requests_per_minute']:.1f}")
        
        # تقييم الأداء العام
        print(f"\n🏆 تقييم الأداء العام:")
        
        if success_rate >= 100:
            print("   🌟 ممتاز جداً - موثوقية 100%")
            reliability_grade = "A+"
        elif success_rate >= 95:
            print("   🌟 ممتاز - موثوقية عالية جداً")
            reliability_grade = "A"
        elif success_rate >= 90:
            print("   ⭐ جيد جداً - موثوقية عالية")
            reliability_grade = "B+"
        elif success_rate >= 80:
            print("   ⭐ جيد - موثوقية مقبولة")
            reliability_grade = "B"
        else:
            print("   ⚠️ يحتاج تحسين - موثوقية منخفضة")
            reliability_grade = "C"
        
        print(f"   التقدير النهائي: {reliability_grade}")
        
        # تحديد ما إذا كان النظام جاهز
        is_ready = success_rate >= 95 and avg_speed >= 1.0
        
        if is_ready:
            print("\n✅ النظام جاهز للإنتاج بموثوقية عالية!")
        else:
            print("\n⚠️ النظام يحتاج إلى تحسينات قبل الإنتاج")
        
        return is_ready

def test_backup_system():
    """اختبار نظام النسخ الاحتياطية"""
    
    print("\n🔧 اختبار نظام النسخ الاحتياطية...")
    
    from ultra_reliability_system import BackupManager, create_ultra_reliable_config
    
    config = create_ultra_reliable_config()
    backup_manager = BackupManager(config, "test_backups")
    
    # بيانات تجريبية
    test_data = {
        "book_id": "test_book",
        "title": "كتاب تجريبي",
        "pages": [
            {"page_number": 1, "content": "محتوى الصفحة الأولى"},
            {"page_number": 2, "content": "محتوى الصفحة الثانية"}
        ],
        "extraction_time": time.time()
    }
    
    try:
        # إنشاء نسخة احتياطية
        backup_path = backup_manager.create_backup(test_data, "test_book", 2)
        
        if backup_path and Path(backup_path).exists():
            print("   ✅ تم إنشاء النسخة الاحتياطية بنجاح")
            
            # اختبار الاستعادة
            restored_data = backup_manager.restore_from_backup("test_book")
            
            if restored_data and restored_data.get("book_id") == "test_book":
                print("   ✅ تم اختبار الاستعادة بنجاح")
                
                # تنظيف الاختبار
                Path(backup_path).unlink()
                Path("test_backups").rmdir()
                
                return True
            else:
                print("   ❌ فشل في اختبار الاستعادة")
        else:
            print("   ❌ فشل في إنشاء النسخة الاحتياطية")
            
    except Exception as e:
        print(f"   ❌ خطأ في اختبار النسخ الاحتياطية: {str(e)}")
    
    return False

def main():
    """الدالة الرئيسية للاختبار"""
    
    print("🧪 بدء اختبار شامل للنظام فائق الموثوقية")
    print("=" * 80)
    print()
    
    # اختبار النظام الأساسي
    system_ready = test_ultra_reliability()
    
    # اختبار النسخ الاحتياطية
    backup_ready = test_backup_system()
    
    # التقييم النهائي
    print("\n" + "=" * 80)
    print("📋 تقرير الاختبار النهائي:")
    print("=" * 80)
    
    print(f"🔧 النظام الأساسي: {'✅ جاهز' if system_ready else '❌ يحتاج تحسين'}")
    print(f"💾 نظام النسخ الاحتياطية: {'✅ جاهز' if backup_ready else '❌ يحتاج تحسين'}")
    
    overall_ready = system_ready and backup_ready
    
    if overall_ready:
        print("\n🎉 النظام كاملاً جاهز للاستخدام بموثوقية 100%!")
        print("✅ يمكن البدء في استخراج الكتب بثقة كاملة")
    else:
        print("\n⚠️ النظام يحتاج إلى مزيد من التحسينات")
        print("🔧 راجع الأخطاء المذكورة أعلاه وأصلحها")
    
    print("\n" + "=" * 80)
    
    return overall_ready

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
