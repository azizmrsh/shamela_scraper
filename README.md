# Shamela Scraper v2.0

## 📁 هيكل المشروع المنظم

### 🔧 **core/** - السكريبتات الأساسية
يحتوي على جميع السكريبتات الأساسية للمشروع:
- `enhanced_shamela_scraper.py` - السكريبت الرئيسي المحسن
- `enhanced_shamela_scraper_v2.py` - الإصدار الثاني المطور
- `original_shamela_scraper.py` - السكريبت الأصلي
- `enhanced_runner.py` - مشغل محسن
- `enhanced_runner_gui.py` - واجهة رسومية
- `ultra_reliability_system.py` - نظام الموثوقية الفائقة
- `ultra_reliable_*.py` - مكونات النظام فائق الموثوقية
- `enhanced_database_manager.py` - مدير قاعدة البيانات
- `ultra_speed_config.py` - إعدادات السرعة الفائقة

### 🛠️ **utils/** - الأدوات المساعدة
يحتوي على الأدوات والسكريبتات المساندة:
- `analyze_results.py` - تحليل النتائج
- `compare_results.py` - مقارنة النتائج
- `check_*.py` - أدوات الفحص والتحقق
- `performance_*.py` - أدوات قياس الأداء
- `speed_benchmark.py` - قياس السرعة
- `show_book_stats.py` - إحصائيات الكتب

### 🧪 **tests/** - الاختبارات
يحتوي على جميع اختبارات المشروع:
- `test_performance.py` - اختبارات الأداء
- `test_advanced_*.py` - اختبارات متقدمة
- `test_gui_comprehensive.py` - اختبارات الواجهة الرسومية
- `test_ultra_reliability.py` - اختبارات الموثوقية

### 📊 **data/** - البيانات والنتائج
يحتوي على:
- `config.json` - ملف التكوين
- `*.json.gz` - ملفات البيانات المضغوطة
- `ultra_reliable_books/` - مجلد الكتب فائقة الموثوقية

### 📚 **docs/** - الوثائق والتقارير
يحتوي على جميع التقارير والوثائق:
- تقارير الأداء والمقارنات
- أدلة المستخدم
- تقارير التحسينات

### 🚀 **scripts/** - السكريبتات التشغيلية
يحتوي على:
- `benchmark.*` - سكريبتات القياس
- `start_runner_gui.bat` - تشغيل الواجهة الرسومية

## 🔧 كيفية الاستخدام

### تشغيل السكريبت الأساسي:
```bash
python core/enhanced_shamela_scraper.py --book-id 123
```

### تشغيل الواجهة الرسومية:
```bash
python core/enhanced_runner_gui.py
# أو
scripts/start_runner_gui.bat
```

### تشغيل الاختبارات:
```bash
python tests/test_performance.py
```

### استخدام الأدوات المساعدة:
```bash
python utils/analyze_results.py
python utils/speed_benchmark.py
```

## 📝 ملاحظات مهمة

- تم تحديث جميع مسارات الاستيراد لتتوافق مع الهيكل الجديد
- تم إنشاء ملفات `__init__.py` لجعل المجلدات packages صحيحة
- تم حذف الملفات المكررة وغير الضرورية
- الهيكل الجديد يسهل الصيانة والتطوير

## 🆕 التحديثات في v2.0

- ✅ تنظيم كامل لهيكل المشروع
- ✅ إصلاح جميع مسارات الاستيراد
- ✅ حذف الملفات المكررة
- ✅ تحسين التنظيم والوضوح
- ✅ سهولة الوصول والاستخدام