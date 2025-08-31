# دليل التثبيت - Installation Guide

## 🚨 مشكلة في تثبيت Python/pip

يبدو أن هناك مشكلة في تثبيت Python أو pip على النظام. إليك الحلول:

## 🔧 الحلول المقترحة:

### 1. إعادة تثبيت Python
1. قم بتحميل Python من الموقع الرسمي: https://python.org/downloads/
2. أثناء التثبيت، تأكد من تحديد:
   - ✅ "Add Python to PATH"
   - ✅ "Install pip"
3. أعد تشغيل الكمبيوتر بعد التثبيت

### 2. إصلاح pip
إذا كان Python مثبت، جرب هذه الأوامر في Command Prompt كمدير:

```cmd
# تحميل get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

# تثبيت pip
python get-pip.py

# أو جرب:
py -m ensurepip --upgrade
```

### 3. استخدام Anaconda/Miniconda
بديل ممتاز لـ Python العادي:
1. حمل Anaconda من: https://anaconda.com/products/distribution
2. ثبته واستخدم Anaconda Prompt
3. استخدم الأوامر:
```bash
conda install aiohttp requests beautifulsoup4 lxml pandas matplotlib seaborn psutil
conda install -c conda-forge mysql-connector-python
```

## 📦 المكتبات المطلوبة:

### المكتبات الأساسية:
```bash
pip install aiohttp>=3.8.0
pip install requests>=2.28.0
pip install beautifulsoup4>=4.11.0
pip install lxml>=4.9.0
```

### قاعدة البيانات:
```bash
pip install mysql-connector-python>=8.0.0
```

### تحليل البيانات:
```bash
pip install pandas>=1.5.0
pip install matplotlib>=3.6.0
pip install seaborn>=0.12.0
```

### أدوات النظام:
```bash
pip install psutil>=5.9.0
pip install urllib3>=1.26.0
```

## 🧪 اختبار التثبيت:

بعد التثبيت، جرب هذا الأمر للتأكد:
```python
python -c "import aiohttp, requests, bs4, lxml, mysql.connector, pandas, matplotlib, seaborn, psutil; print('✅ جميع المكتبات مثبتة بنجاح!')"
```

## 🔄 تشغيل السكريبتات بدون مكتبات:

يمكنك تشغيل بعض السكريبتات الأساسية التي تعتمد على المكتبات المدمجة فقط:

### السكريبتات التي تعمل بدون مكتبات خارجية:
- `utils/analyze_results.py` - تحليل النتائج
- `utils/compare_results.py` - مقارنة النتائج
- `utils/show_book_stats.py` - إحصائيات الكتب
- `utils/check_*.py` - أدوات الفحص

### السكريبتات التي تحتاج مكتبات خارجية:
- `core/enhanced_shamela_scraper.py` - يحتاج aiohttp, requests, bs4
- `core/enhanced_runner_gui.py` - يحتاج tkinter (مدمج عادة)
- `tests/test_advanced_performance.py` - يحتاج pandas, matplotlib

## 💡 نصائح:

1. **استخدم Virtual Environment:**
   ```bash
   python -m venv shamela_env
   shamela_env\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **تحقق من إصدار Python:**
   ```bash
   python --version
   # يفضل Python 3.8 أو أحدث
   ```

3. **في حالة استمرار المشاكل:**
   - استخدم PyCharm أو VS Code مع Python extension
   - جرب Google Colab للتطوير السحابي
   - استخدم Docker مع Python image

## 🆘 طلب المساعدة:

إذا استمرت المشاكل، يرجى:
1. تشغيل `python --version` و `pip --version`
2. إرسال رسالة الخطأ كاملة
3. ذكر نظام التشغيل المستخدم

---

**ملاحظة:** بعض السكريبتات قد تعمل بدون جميع المكتبات، لكن للحصول على الوظائف الكاملة، يُنصح بتثبيت جميع المكتبات المطلوبة.