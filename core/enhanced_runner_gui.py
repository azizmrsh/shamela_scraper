#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Shamela Runner GUI - واجهة رسومية محسنة لتشغيل المكتبة الشاملة
واجهة رسومية شاملة لجميع وظائف enhanced_runner.py

المميزات:
- استخراج الكتب مع جميع التحسينات
- حفظ البيانات في قاعدة البيانات
- إدارة الجداول وعرض الإحصائيات
- واجهة عربية متكاملة مع دعم RTL
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import os
import sys
import json
import threading
import subprocess
import time
from datetime import datetime
from pathlib import Path

# المكتبات المطلوبة لاستخراج الأقسام
try:
    import requests
    import re
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    CATEGORY_EXTRACTION_AVAILABLE = True
except ImportError:
    CATEGORY_EXTRACTION_AVAILABLE = False

# إعداد الترميز لـ Windows
if sys.platform.startswith('win'):
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'ar_SA.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Arabic_Saudi Arabia.1256')
        except:
            pass  # استخدم الإعدادات الافتراضية

# إضافة المجلد الحالي للـ path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# كلاس مستخرج الأقسام المضمن
class CategoryExtractor:
    """مستخرج كتب الأقسام من موقع الشاملة - مضمن في الواجهة"""
    
    def __init__(self):
        self.base_url = "https://shamela.ws"
        if CATEGORY_EXTRACTION_AVAILABLE:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
    
    def extract_category_books(self, category_id, progress_callback=None):
        """استخراج جميع كتب قسم معين"""
        if not CATEGORY_EXTRACTION_AVAILABLE:
            raise ImportError("المكتبات المطلوبة غير متوفرة. يرجى تثبيت: pip install requests beautifulsoup4")
        
        try:
            category_url = f"{self.base_url}/category/{category_id}"
            response = self.session.get(category_url, timeout=30)
            response.raise_for_status()
            
            # تحليل الصفحة
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # البحث عن روابط الكتب
            book_links = soup.find_all('a', href=re.compile(r'/book/\d+'))
            
            if not book_links:
                return []
            
            # استخراج أرقام الكتب
            book_ids = []
            for link in book_links:
                href = link.get('href', '')
                match = re.search(r'/book/(\d+)', href)
                if match:
                    book_id = int(match.group(1))
                    if book_id not in book_ids:
                        book_ids.append(book_id)
            
            return book_ids
            
        except Exception as e:
            raise Exception(f"خطأ في استخراج كتب القسم {category_id}: {str(e)}")
    
    def _extract_category_name(self, category_id):
        """استخراج اسم القسم"""
        if not CATEGORY_EXTRACTION_AVAILABLE:
            return f"القسم {category_id}"
        
        try:
            category_url = f"{self.base_url}/category/{category_id}"
            response = self.session.get(category_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # البحث عن عنوان الصفحة أو عنوان القسم
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
                # إزالة أجزاء غير مرغوب فيها من العنوان
                title = title.replace(' - المكتبة الشاملة', '').strip()
                return title
            
            # البحث عن عنوان h1 أو h2
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                text = heading.get_text().strip()
                if text and 'قسم' in text:
                    return text
            
            return f"القسم {category_id}"
            
        except:
            return f"القسم {category_id}"
    
    def extract_multiple_categories(self, categories, max_books_per_category=None, progress_callback=None):
        """استخراج أقسام متعددة"""
        if not CATEGORY_EXTRACTION_AVAILABLE:
            raise ImportError("المكتبات المطلوبة غير متوفرة")
        
        results = {}
        
        for category_id in categories:
            try:
                # استخراج معلومات القسم
                books = self.extract_category_books(category_id)
                category_name = self._extract_category_name(category_id)
                
                # تطبيق الحد الأقصى إذا تم تحديده
                if max_books_per_category and len(books) > max_books_per_category:
                    books = books[:max_books_per_category]
                
                results[category_id] = {
                    'name': category_name,
                    'books': {},
                    'total_books': len(books)
                }
                
                # معالجة كل كتاب
                for i, book_id in enumerate(books, 1):
                    if progress_callback:
                        progress_callback(category_id, i, len(books), book_id, f"كتاب {book_id}")
                    
                    # هنا يمكن إضافة معالجة إضافية للكتاب
                    results[category_id]['books'][book_id] = {
                        'title': f'كتاب {book_id}',
                        'success': True  # افتراضياً ناجح
                    }
                    
                    # إيقاف قصير لتجنب التحميل الزائد
                    time.sleep(0.1)
                    
            except Exception as e:
                results[category_id] = {
                    'error': str(e),
                    'books': {},
                    'total_books': 0
                }
        
        return results

# استيراد مكتبات قاعدة البيانات
try:
    import mysql.connector
except ImportError:
    mysql.connector = None

class EnhancedRunnerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Shamela Runner - مشغل المكتبة الشاملة المحسن")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        
        # متغيرات الواجهة
        self.setup_variables()
        
        # تطبيق الأنماط
        self.setup_styles()
        
        # إنشاء الواجهة
        self.create_widgets()
        
        # متغيرات التحكم
        self.current_process = None
        self.is_running = False
        
    def setup_variables(self):
        """إعداد متغيرات الواجهة"""
        # متغيرات الكتاب
        self.book_id_var = tk.StringVar()
        self.max_pages_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.json_file_var = tk.StringVar()
        self.db_book_id_var = tk.StringVar()
        
        # متغيرات ملفات JSON المتعددة
        self.json_folder_var = tk.StringVar()
        self.selected_files_var = tk.StringVar()
        self.json_files_list = []  # قائمة الملفات المكتشفة
        
        # متغيرات الأقسام
        self.category_id_var = tk.StringVar()
        self.category_mode_var = tk.StringVar(value="single")  # single أو multiple
        self.category_list_var = tk.StringVar()
        self.max_books_per_category_var = tk.StringVar()
        self.category_operation_var = tk.StringVar(value="extract_only")  # extract_only أو extract_and_database
        self.category_output_dir_var = tk.StringVar()  # مجلد الإخراج للأقسام
        
        # متغيرات قاعدة البيانات - تطابق السكريبت
        self.db_host_var = tk.StringVar(value="145.223.98.97")
        self.db_port_var = tk.StringVar(value="3306")
        self.db_user_var = tk.StringVar(value="bms_db")
        self.db_password_var = tk.StringVar(value="")  # فارغة افتراضياً
        self.db_name_var = tk.StringVar(value="bms_db")
        
        # متغيرات التحكم
        self.operation_var = tk.StringVar(value="extract")
        self.progress_var = tk.DoubleVar()
        
    def setup_styles(self):
        """إعداد أنماط الواجهة"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # تعريف الألوان الرئيسية
        self.primary_color = "#1e88e5"  # أزرق داكن
        self.secondary_color = "#43a047"  # أخضر
        self.accent_color = "#f57c00"  # برتقالي
        self.bg_color = "#f5f5f5"  # رمادي فاتح
        self.dark_color = "#263238"  # أسود مائل للأزرق
        self.light_color = "#ffffff"  # أبيض
        self.warning_color = "#ff9800"  # برتقالي تحذير
        self.error_color = "#e53935"  # أحمر خطأ
        self.success_color = "#43a047"  # أخضر نجاح
        
        # تطبيق الخلفية الرئيسية
        self.root.configure(bg=self.bg_color)
        
        # أنماط مخصصة
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabelframe', background=self.bg_color)
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.dark_color, font=('Arial', 11, 'bold'))
        
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground=self.primary_color, background=self.bg_color)
        style.configure('Heading.TLabel', font=('Arial', 11, 'bold'), foreground=self.dark_color, background=self.bg_color)
        style.configure('Success.TLabel', foreground=self.success_color, background=self.bg_color)
        style.configure('Error.TLabel', foreground=self.error_color, background=self.bg_color)
        style.configure('Warning.TLabel', foreground=self.warning_color, background=self.bg_color)
        
        # أزرار جميلة
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'), background=self.primary_color, foreground=self.light_color)
        style.configure('Success.TButton', font=('Arial', 10, 'bold'), background=self.success_color, foreground=self.light_color)
        style.configure('Warning.TButton', font=('Arial', 10, 'bold'), background=self.warning_color, foreground=self.light_color)
        style.configure('Error.TButton', font=('Arial', 10, 'bold'), background=self.error_color, foreground=self.light_color)
        
        # أنماط للتبويبات الرئيسية
        style.configure('LeftPane.TNotebook', background=self.primary_color, borderwidth=0)
        style.map('LeftPane.TNotebook.Tab', background=[('selected', self.light_color), ('!selected', self.primary_color)],
                 foreground=[('selected', self.primary_color), ('!selected', self.light_color)])
        style.configure('LeftPane.TNotebook.Tab', font=('Arial', 11, 'bold'), padding=[15, 10], background=self.primary_color, foreground=self.light_color)
        
        # أنماط شريط التقدم
        style.configure('TProgressbar', background=self.primary_color, troughcolor=self.bg_color, borderwidth=0)
        
        # أنماط قائمة الملفات
        style.configure('TListbox', background=self.light_color, font=('Arial', 9))
        
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        # إنشاء الحاوي الرئيسي
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ============= الجزء الأيسر: التبويبات =============
        left_frame = ttk.Frame(main_container)
        
        # شعار التطبيق وعنوان التطبيق في أعلى الجزء الأيسر
        header_frame = ttk.Frame(left_frame)
        header_frame.pack(fill=tk.X, pady=(5, 15))
        
        app_title = ttk.Label(header_frame, text="المكتبة الشاملة المحسنة", style='Title.TLabel')
        app_title.pack(side=tk.TOP, pady=(5, 0))
        
        app_subtitle = ttk.Label(header_frame, text="استخراج وإدارة كتب المكتبة الشاملة", style='Heading.TLabel')
        app_subtitle.pack(side=tk.TOP, pady=(0, 10))
        
        # إنشاء النوافذ المبوبة بشكل عمودي على اليسار
        self.notebook = ttk.Notebook(left_frame, style='LeftPane.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # إنشاء التبويبات
        self.create_extract_tab()
        self.create_database_tab()
        self.create_category_tab()
        self.create_management_tab()
        
        # إضافة الجزء الأيسر للحاوي الرئيسي
        main_container.add(left_frame, weight=3)
        
        # ============= الجزء الأيمن: السجلات والمخرجات =============
        right_frame = ttk.Frame(main_container)
        
        # عنوان السجلات
        logs_title_frame = ttk.Frame(right_frame)
        logs_title_frame.pack(fill=tk.X, pady=(5, 0))
        
        logs_title = ttk.Label(logs_title_frame, text="📋 السجلات والمخرجات", style='Title.TLabel')
        logs_title.pack(side=tk.TOP, pady=(5, 10))
        
        # إطار السجلات
        logs_frame = ttk.LabelFrame(right_frame, text="النتائج والعمليات", padding="10")
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # إنشاء قسم السجلات
        self.create_shared_logs_section(logs_frame)
        
        # إضافة الجزء الأيمن للحاوي الرئيسي
        main_container.add(right_frame, weight=2)
        
        # شريط الحالة
        self.create_status_bar()
        
        # تسجيل رسالة الترحيب
        self.log_message("🚀 تم تشغيل واجهة المكتبة الشاملة المحسنة")
        
    def create_extract_tab(self):
        """إنشاء تبويب الاستخراج"""
        extract_frame = ttk.Frame(self.notebook)
        self.notebook.add(extract_frame, text="🔍 استخراج الكتب")
        
        # عنوان رئيسي
        title_label = ttk.Label(extract_frame, text="🔍 استخراج الكتب من المكتبة الشاملة", 
                               style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # إطار معلومات الكتاب
        book_frame = ttk.LabelFrame(extract_frame, text="📚 معلومات الكتاب", padding="10")
        book_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # معرف الكتاب
        ttk.Label(book_frame, text="معرف الكتاب:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        book_entry = ttk.Entry(book_frame, textvariable=self.book_id_var, width=15, font=('Arial', 11))
        book_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # عدد الصفحات المحدود
        ttk.Label(book_frame, text="عدد الصفحات (اختياري):", style='Heading.TLabel').grid(
            row=0, column=2, sticky=tk.W, padx=(0, 10))
        pages_entry = ttk.Entry(book_frame, textvariable=self.max_pages_var, width=15, font=('Arial', 11))
        pages_entry.grid(row=0, column=3, sticky=tk.W)
        
        # مجلد الإخراج
        ttk.Label(book_frame, text="مجلد الإخراج (اختياري):", style='Heading.TLabel').grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        output_entry = ttk.Entry(book_frame, textvariable=self.output_dir_var, width=40, font=('Arial', 9))
        output_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        browse_btn = ttk.Button(book_frame, text="تصفح", command=self.browse_output_dir)
        browse_btn.grid(row=1, column=3, sticky=tk.W, pady=(10, 0))
        
        # إطار إعدادات قاعدة البيانات
        self.create_database_config(extract_frame)
        
        # إطار خيارات الاستخراج
        options_frame = ttk.LabelFrame(extract_frame, text="⚙️ خيارات الاستخراج", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # نوع العملية
        ttk.Label(options_frame, text="نوع العملية:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        operation_combo = ttk.Combobox(options_frame, textvariable=self.operation_var, 
                                      values=["extract", "extract + database"], 
                                      state="readonly", width=20)
        operation_combo.grid(row=0, column=1, sticky=tk.W)
        operation_combo.set("extract")
        
        # أزرار التحكم
        control_frame = ttk.Frame(extract_frame)
        control_frame.pack(pady=20)
        
        self.extract_btn = ttk.Button(control_frame, text="🚀 بدء الاستخراج", 
                                     command=self.start_extraction, style='Accent.TButton')
        self.extract_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(control_frame, text="⏹️ إيقاف", 
                                  command=self.stop_operation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_btn = ttk.Button(control_frame, text="🗑️ مسح", command=self.clear_extract_form)
        clear_btn.pack(side=tk.LEFT)
        
    def create_database_tab(self):
        """إنشاء تبويب قاعدة البيانات"""
        db_frame = ttk.Frame(self.notebook)
        self.notebook.add(db_frame, text="🗄️ قاعدة البيانات")
        
        # عنوان رئيسي
        title_label = ttk.Label(db_frame, text="🗄️ إدارة قاعدة البيانات", style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # إطار رفع ملف واحد
        single_upload_frame = ttk.LabelFrame(db_frame, text="📤 رفع ملف JSON واحد", padding="10")
        single_upload_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # اختيار ملف JSON واحد
        ttk.Label(single_upload_frame, text="ملف JSON:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        json_entry = ttk.Entry(single_upload_frame, textvariable=self.json_file_var, width=50, font=('Arial', 9))
        json_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        browse_json_btn = ttk.Button(single_upload_frame, text="تصفح", command=self.browse_json_file)
        browse_json_btn.grid(row=0, column=2, sticky=tk.W)
        
        single_upload_frame.columnconfigure(1, weight=1)
        
        # زر رفع ملف واحد
        single_control_frame = ttk.Frame(single_upload_frame)
        single_control_frame.grid(row=1, column=0, columnspan=3, pady=(15, 0))
        
        self.upload_btn = ttk.Button(single_control_frame, text="📤 رفع ملف واحد", 
                                    command=self.upload_to_database, style='Accent.TButton')
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # إطار رفع ملفات متعددة
        multiple_upload_frame = ttk.LabelFrame(db_frame, text="📦 رفع ملفات JSON متعددة", padding="10")
        multiple_upload_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # اختيار مجلد الملفات
        ttk.Label(multiple_upload_frame, text="مجلد ملفات JSON:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.json_folder_var = tk.StringVar()
        folder_entry = ttk.Entry(multiple_upload_frame, textvariable=self.json_folder_var, width=50, font=('Arial', 9))
        folder_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        browse_folder_btn = ttk.Button(multiple_upload_frame, text="تصفح مجلد", command=self.browse_json_folder)
        browse_folder_btn.grid(row=0, column=2, sticky=tk.W)
        
        multiple_upload_frame.columnconfigure(1, weight=1)
        
        # أو اختيار ملفات متعددة
        ttk.Label(multiple_upload_frame, text="أو اختر ملفات متعددة:", style='Heading.TLabel').grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.selected_files_var = tk.StringVar()
        files_entry = ttk.Entry(multiple_upload_frame, textvariable=self.selected_files_var, width=50, font=('Arial', 9))
        files_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=(10, 0))
        browse_files_btn = ttk.Button(multiple_upload_frame, text="اختر ملفات", command=self.browse_multiple_json_files)
        browse_files_btn.grid(row=1, column=2, sticky=tk.W, pady=(10, 0))
        
        # قائمة الملفات المكتشفة
        files_list_frame = ttk.Frame(multiple_upload_frame)
        files_list_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(files_list_frame, text="ملفات JSON المكتشفة:", style='Heading.TLabel').pack(anchor="w")
        
        # إنشاء Listbox لعرض الملفات
        listbox_frame = ttk.Frame(files_list_frame)
        listbox_frame.pack(fill="both", expand=True, pady=(5, 0))
        
        self.files_listbox = tk.Listbox(listbox_frame, height=6, font=('Arial', 9))
        files_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=files_scrollbar.set)
        
        self.files_listbox.pack(side="left", fill="both", expand=True)
        files_scrollbar.pack(side="right", fill="y")
        
        # أزرار التحكم في الملفات المتعددة
        multiple_control_frame = ttk.Frame(multiple_upload_frame)
        multiple_control_frame.grid(row=3, column=0, columnspan=3, pady=(15, 0))
        
        self.scan_files_btn = ttk.Button(multiple_control_frame, text="🔍 فحص الملفات", 
                                        command=self.scan_json_files)
        self.scan_files_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.upload_multiple_btn = ttk.Button(multiple_control_frame, text="� رفع جميع الملفات", 
                                             command=self.upload_multiple_to_database, style='Accent.TButton')
        self.upload_multiple_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_list_btn = ttk.Button(multiple_control_frame, text="🗑️ مسح القائمة", 
                                   command=self.clear_files_list)
        clear_list_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # عداد الملفات
        self.files_counter_label = ttk.Label(multiple_control_frame, text="عدد الملفات: 0", 
                                           style='Heading.TLabel')
        self.files_counter_label.pack(side=tk.RIGHT)
        
        # إطار إنشاء الجداول
        tables_frame = ttk.LabelFrame(db_frame, text="🏗️ إدارة الجداول", padding="10")
        tables_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        tables_control_frame = ttk.Frame(tables_frame)
        tables_control_frame.pack()
        
        self.create_tables_btn = ttk.Button(tables_control_frame, text="🏗️ إنشاء الجداول", 
                                           command=self.create_database_tables)
        self.create_tables_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.fix_database_btn = ttk.Button(tables_control_frame, text="🔧 إصلاح قاعدة البيانات", 
                                          command=self.fix_database_structure)
        self.fix_database_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # إطار إعدادات قاعدة البيانات (مكرر للتبويب)
        self.create_database_config(db_frame)
        
    def create_management_tab(self):
        """إنشاء تبويب الإدارة والإحصائيات"""
        mgmt_frame = ttk.Frame(self.notebook)
        self.notebook.add(mgmt_frame, text="📊 الإدارة والإحصائيات")
        
        # عنوان رئيسي
        title_label = ttk.Label(mgmt_frame, text="📊 إدارة الكتب والإحصائيات", style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # إطار عرض الإحصائيات
        stats_frame = ttk.LabelFrame(mgmt_frame, text="📈 عرض إحصائيات كتاب", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # معرف الكتاب في قاعدة البيانات
        ttk.Label(stats_frame, text="معرف الكتاب في قاعدة البيانات:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        db_book_entry = ttk.Entry(stats_frame, textvariable=self.db_book_id_var, width=15, font=('Arial', 11))
        db_book_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.show_stats_btn = ttk.Button(stats_frame, text="📊 عرض الإحصائيات", 
                                        command=self.show_book_stats, style='Accent.TButton')
        self.show_stats_btn.grid(row=0, column=2, sticky=tk.W)
        
        # إطار إدارة الملفات
        files_frame = ttk.LabelFrame(mgmt_frame, text="📁 إدارة الملفات", padding="10")
        files_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        files_control_frame = ttk.Frame(files_frame)
        files_control_frame.pack()
        
        ttk.Button(files_control_frame, text="📂 فتح مجلد الكتب", 
                  command=self.open_books_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(files_control_frame, text="📄 عرض السجلات", 
                  command=self.open_logs_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(files_control_frame, text="🔍 البحث في الملفات", 
                  command=self.search_files).pack(side=tk.LEFT)
        
    def create_category_tab(self):
        """إنشاء تبويب استخراج الأقسام"""
        category_frame = ttk.Frame(self.notebook)
        self.notebook.add(category_frame, text="📚 استخراج الأقسام")
        
        # عنوان رئيسي
        title_label = ttk.Label(category_frame, text="📚 استخراج كتب الأقسام", style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # إعدادات الأقسام
        settings_frame = ttk.LabelFrame(category_frame, text="⚙️ إعدادات الأقسام", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        # اختيار نوع العملية
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill="x", pady=5)
        
        ttk.Label(mode_frame, text="نوع العملية:", style='Heading.TLabel').pack(side="left")
        
        single_radio = ttk.Radiobutton(mode_frame, text="قسم واحد", 
                                     variable=self.category_mode_var, value="single")
        single_radio.pack(side="left", padx=(10, 5))
        
        multiple_radio = ttk.Radiobutton(mode_frame, text="أقسام متعددة", 
                                       variable=self.category_mode_var, value="multiple")
        multiple_radio.pack(side="left", padx=5)
        
        # إدخال رقم القسم (للقسم الواحد)
        single_frame = ttk.Frame(settings_frame)
        single_frame.pack(fill="x", pady=5)
        
        ttk.Label(single_frame, text="رقم القسم:", style='Heading.TLabel').pack(side="left")
        category_entry = ttk.Entry(single_frame, textvariable=self.category_id_var, width=15)
        category_entry.pack(side="left", padx=(10, 5))
        
        # زر فحص القسم
        check_btn = ttk.Button(single_frame, text="🔍 فحص القسم", 
                             command=self.check_category)
        check_btn.pack(side="left", padx=5)
        
        # إدخال قائمة الأقسام (للأقسام المتعددة)
        multiple_frame = ttk.Frame(settings_frame)
        multiple_frame.pack(fill="x", pady=5)
        
        ttk.Label(multiple_frame, text="قائمة الأقسام (مفصولة بفواصل):", style='Heading.TLabel').pack(anchor="w")
        category_list_entry = ttk.Entry(multiple_frame, textvariable=self.category_list_var, width=50)
        category_list_entry.pack(fill="x", pady=(5, 0))
        
        # الحد الأقصى للكتب لكل قسم
        limit_frame = ttk.Frame(settings_frame)
        limit_frame.pack(fill="x", pady=5)
        
        ttk.Label(limit_frame, text="الحد الأقصى للكتب لكل قسم (اختياري):", style='Heading.TLabel').pack(side="left")
        limit_entry = ttk.Entry(limit_frame, textvariable=self.max_books_per_category_var, width=15)
        limit_entry.pack(side="left", padx=(10, 5))
        
        # زر فحص الأقسام المتعددة
        check_categories_btn = ttk.Button(limit_frame, text="🔍 فحص الأقسام المتعددة", 
                                        command=self.check_multiple_categories)
        check_categories_btn.pack(side="left", padx=5)
        
        # نوع العملية (استخراج فقط أو استخراج ورفع)
        operation_frame = ttk.Frame(settings_frame)
        operation_frame.pack(fill="x", pady=10)
        
        ttk.Label(operation_frame, text="نوع العملية:", style='Heading.TLabel').pack(side="left")
        
        extract_only_radio = ttk.Radiobutton(operation_frame, text="🔍 استخراج فقط", 
                                           variable=self.category_operation_var, value="extract_only",
                                           command=self.update_extraction_button_text)
        extract_only_radio.pack(side="left", padx=(10, 5))
        
        extract_and_db_radio = ttk.Radiobutton(operation_frame, text="🔍📤 استخراج ورفع على قاعدة البيانات", 
                                             variable=self.category_operation_var, value="extract_and_database",
                                             command=self.update_extraction_button_text)
        extract_and_db_radio.pack(side="left", padx=5)
        
        # مجلد الإخراج
        output_frame = ttk.Frame(settings_frame)
        output_frame.pack(fill="x", pady=10)
        
        ttk.Label(output_frame, text="مجلد الإخراج (اختياري):", style='Heading.TLabel').pack(side="left")
        
        output_entry_frame = ttk.Frame(output_frame)
        output_entry_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
        
        category_output_entry = ttk.Entry(output_entry_frame, textvariable=self.category_output_dir_var, 
                                         width=40, font=('Arial', 9))
        category_output_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(output_entry_frame, text="📁 تصفح", 
                                     command=self.browse_category_output_dir)
        browse_output_btn.pack(side="left")
        
        # إعدادات قاعدة البيانات للأقسام
        self.create_database_config(category_frame)
        
        # معلومات القسم
        info_frame = ttk.LabelFrame(category_frame, text="ℹ️ معلومات القسم", padding=10)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        self.category_info_text = tk.Text(info_frame, height=4, wrap="word", font=('Arial', 9))
        self.category_info_text.pack(fill="x")
        
        # أزرار التحكم (تم نقلها إلى الأعلى)
        controls_frame = ttk.Frame(category_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # إطار الأزرار الرئيسية
        main_buttons_frame = ttk.Frame(controls_frame)
        main_buttons_frame.pack(fill="x", pady=(0, 5))
        
        # زر بدء الاستخراج (بارز)
        self.start_extraction_btn = ttk.Button(main_buttons_frame, text="🚀 بدء استخراج جميع الكتب", 
                                        command=self.start_category_extraction, style='Accent.TButton')
        self.start_extraction_btn.pack(side="left", padx=(0, 10), ipadx=20, ipady=5)
        
        # زر إيقاف العملية
        self.stop_category_btn = ttk.Button(main_buttons_frame, text="⏹️ إيقاف العملية", 
                            command=self.stop_operation, state=tk.DISABLED)
        self.stop_category_btn.pack(side="left", padx=(0, 10))
        
        # إطار الأزرار الثانوية
        secondary_buttons_frame = ttk.Frame(controls_frame)
        secondary_buttons_frame.pack(fill="x")
        
        # زر مسح القائمة
        clear_btn = ttk.Button(secondary_buttons_frame, text="🗑️ مسح القائمة", 
                             command=self.clear_books_list)
        clear_btn.pack(side="left", padx=(0, 10))
        
        # زر تصدير القائمة
        export_btn = ttk.Button(secondary_buttons_frame, text="📤 تصدير القائمة", 
                              command=self.export_books_list)
        export_btn.pack(side="left", padx=(0, 10))
        
        # عداد الكتب
        self.books_counter_label = ttk.Label(secondary_buttons_frame, text="عدد الكتب: 0", 
                                           style='Heading.TLabel')
        self.books_counter_label.pack(side="right")
        
        # قائمة الكتب المستخرجة
        books_frame = ttk.LabelFrame(category_frame, text="📖 الكتب المستخرجة", padding=10)
        books_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # إنشاء Treeview لعرض الكتب
        columns = ("book_id", "title", "status")
        self.books_tree = ttk.Treeview(books_frame, columns=columns, show="headings", height=10)
        
        # تحديد عناوين الأعمدة
        self.books_tree.heading("book_id", text="رقم الكتاب")
        self.books_tree.heading("title", text="العنوان")
        self.books_tree.heading("status", text="الحالة")
        
        # تحديد عرض الأعمدة
        self.books_tree.column("book_id", width=100)
        self.books_tree.column("title", width=300)
        self.books_tree.column("status", width=100)
        
        # شريط التمرير للقائمة
        books_scrollbar = ttk.Scrollbar(books_frame, orient="vertical", command=self.books_tree.yview)
        self.books_tree.configure(yscrollcommand=books_scrollbar.set)
        
        self.books_tree.pack(side="left", fill="both", expand=True)
        books_scrollbar.pack(side="right", fill="y")
        
        # تحديث نص زر الاستخراج عند الإنشاء
        self.update_extraction_button_text()
        
    def create_shared_logs_section(self, parent):
        """إنشاء قسم السجلات المشترك"""
        # تعريف إطار مخصص للسجلات
        logs_container = ttk.Frame(parent)
        logs_container.pack(fill=tk.BOTH, expand=True)
        
        # شريط الحالة والتقدم (في الأعلى)
        status_frame = ttk.Frame(logs_container)
        status_frame.pack(fill=tk.X, padx=5, pady=(0, 10))
        
        # إطار العنوان والحالة
        status_header_frame = ttk.Frame(status_frame)
        status_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # عرض الحالة
        self.shared_status_label = ttk.Label(status_header_frame, text="جاهز للبدء ✓", 
                                           style='Success.TLabel', font=('Arial', 11, 'bold'))
        self.shared_status_label.pack(side=tk.LEFT)
        
        # شريط التقدم بتصميم أفضل
        progress_frame = ttk.Frame(status_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.shared_progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate', style='TProgressbar')
        self.shared_progress_bar.pack(fill=tk.X, expand=True, padx=5)
        
        # إطار أزرار التحكم بالسجلات (مع أزرار أجمل)
        controls_frame = ttk.Frame(logs_container)
        controls_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Button(controls_frame, text="🔄 تحديث", command=self.refresh_logs, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=(0, 5), pady=5, ipadx=5)
        
        ttk.Button(controls_frame, text="🗑️ مسح", command=self.clear_logs, 
                  style='Warning.TButton').pack(side=tk.LEFT, padx=(0, 5), pady=5, ipadx=5)
        
        ttk.Button(controls_frame, text="💾 حفظ", command=self.save_logs, 
                  style='Success.TButton').pack(side=tk.LEFT, padx=(0, 5), pady=5, ipadx=5)
        
        # قسم نص السجلات بتصميم جديد
        logs_frame = ttk.Frame(logs_container)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # منطقة عرض السجلات (نسق أفضل)
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=15, wrap=tk.WORD,
                                                  font=('Consolas', 10), bg=self.light_color,
                                                  fg=self.dark_color, padx=10, pady=10,
                                                  insertbackground=self.primary_color)
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # تطبيق ألوان على نص السجلات
        self.logs_text.tag_configure("success", foreground=self.success_color)
        self.logs_text.tag_configure("error", foreground=self.error_color)
        self.logs_text.tag_configure("warning", foreground=self.warning_color)
        self.logs_text.tag_configure("info", foreground=self.primary_color)
        self.logs_text.tag_configure("timestamp", foreground=self.dark_color)
        
    def create_database_config(self, parent):
        """إنشاء إطار إعدادات قاعدة البيانات"""
        db_frame = ttk.LabelFrame(parent, text="🗄️ إعدادات قاعدة البيانات", padding="10")
        db_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # الصف الأول
        ttk.Label(db_frame, text="الخادم:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(db_frame, textvariable=self.db_host_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        ttk.Label(db_frame, text="المنفذ:", style='Heading.TLabel').grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Entry(db_frame, textvariable=self.db_port_var, width=8).grid(
            row=0, column=3, sticky=tk.W)
        
        # الصف الثاني
        ttk.Label(db_frame, text="المستخدم:", style='Heading.TLabel').grid(
            row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(db_frame, textvariable=self.db_user_var, width=20).grid(
            row=1, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        ttk.Label(db_frame, text="قاعدة البيانات:", style='Heading.TLabel').grid(
            row=1, column=2, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        ttk.Entry(db_frame, textvariable=self.db_name_var, width=20).grid(
            row=1, column=3, sticky=tk.W, pady=(10, 0))
        
        # كلمة المرور
        ttk.Label(db_frame, text="كلمة المرور (اختياري):", style='Heading.TLabel').grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        password_entry = ttk.Entry(db_frame, textvariable=self.db_password_var, show="*", width=20)
        password_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # زر اختبار الاتصال
        test_btn = ttk.Button(db_frame, text="🔌 اختبار الاتصال", command=self.test_database_connection)
        test_btn.grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
    def create_status_bar(self):
        """إنشاء شريط الحالة"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_text = ttk.Label(self.status_bar, text="جاهز", relief=tk.SUNKEN)
        self.status_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.version_label = ttk.Label(self.status_bar, text="Enhanced Runner v2.0")
        self.version_label.pack(side=tk.RIGHT, padx=5)
        
    # وظائف معالجة الأحداث
    def browse_output_dir(self):
        """تصفح مجلد الإخراج"""
        directory = filedialog.askdirectory(title="اختر مجلد الإخراج")
        if directory:
            self.output_dir_var.set(directory)
    
    def browse_category_output_dir(self):
        """تصفح مجلد الإخراج للأقسام"""
        directory = filedialog.askdirectory(title="اختر مجلد الإخراج للأقسام")
        if directory:
            self.category_output_dir_var.set(directory)
    
    def clean_category_name_for_folder(self, category_name):
        """تنظيف اسم القسم ليصبح صالحاً كاسم مجلد"""
        import re
        # استبدال الأحرف غير المسموحة في أسماء المجلدات
        invalid_chars = '<>:"/\\|?*'
        cleaned = category_name
        for char in invalid_chars:
            cleaned = cleaned.replace(char, '_')
        
        # تنظيف المسافات المتعددة والنقاط
        cleaned = re.sub(r'\s+', ' ', cleaned)  # استبدال المسافات المتعددة بمسافة واحدة
        cleaned = re.sub(r'\.+', '.', cleaned)  # استبدال النقاط المتعددة بنقطة واحدة
        cleaned = cleaned.strip('. ')  # إزالة النقاط والمسافات من البداية والنهاية
        
        # تحديد الطول الأقصى لاسم المجلد
        max_length = 100
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].rstrip('. ')
        
        # إذا كان النص فارغاً بعد التنظيف، استخدم اسم افتراضي
        if not cleaned:
            cleaned = "قسم_غير_محدد"
            
        return cleaned
    
    def clean_book_title_for_filename(self, title):
        """تنظيف عنوان الكتاب ليصبح صالحاً كاسم ملف"""
        if not title:
            return "كتاب_غير_محدد"
            
        import re
        # استبدال الأحرف غير المسموحة في أسماء الملفات
        invalid_chars = '<>:"/\\|?*'
        cleaned = title
        for char in invalid_chars:
            cleaned = cleaned.replace(char, '_')
        
        # تنظيف المسافات المتعددة والنقاط
        cleaned = re.sub(r'\s+', ' ', cleaned)  # استبدال المسافات المتعددة بمسافة واحدة
        cleaned = re.sub(r'\.+', '.', cleaned)  # استبدال النقاط المتعددة بنقطة واحدة
        cleaned = cleaned.strip('. ')  # إزالة النقاط والمسافات من البداية والنهاية
        
        # تحديد الطول الأقصى لاسم الملف (مع ترك مساحة للامتداد)
        max_length = 150
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length].rstrip('. ')
        
        # إذا كان النص فارغاً بعد التنظيف، استخدم اسم افتراضي
        if not cleaned:
            cleaned = "كتاب_غير_محدد"
        
        # استبدال المسافات بـ underscores للتوافق الأفضل مع أنظمة الملفات
        cleaned = cleaned.replace(' ', '_')
            
        return cleaned
    
    def extract_book_title(self, book_id):
        """استخراج عنوان الكتاب فقط دون محتوى ودون حفظ ملفات"""
        try:
            # إنشاء مجلد مؤقت في system temp لتجنب حفظ ملفات في مجلد المشروع
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_output_path = os.path.join(temp_dir, f"temp_book_{book_id}.json")
                
                # أمر لاستخراج معلومات الكتاب الأساسية فقط
                # نزيل --no-content ونستخدم --max-pages 1 لضمان استخراج المعلومات الأساسية
                command = [
                    sys.executable,
                    os.path.join(current_dir, "enhanced_shamela_scraper.py"),
                    str(book_id),
                    "--max-pages", "1",  # صفحة واحدة فقط للحصول على المعلومات الأساسية
                    "--output", temp_output_path  # حفظ في المجلد المؤقت
                ]
                
                # إعداد متغيرات البيئة
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'
                
                # تشغيل الأمر مع timeout قصير
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=current_dir,
                    env=env,
                    timeout=120  # زيادة الوقت إلى دقيقتين لضمان نجاح الاستخراج
                )
                
                title = None
                
                if result.returncode == 0:
                    # أولاً: محاولة قراءة الملف المؤقت (أكثر موثوقية)
                    if os.path.exists(temp_output_path):
                        import json
                        try:
                            with open(temp_output_path, 'r', encoding='utf-8') as f:
                                book_data = json.load(f)
                                title = book_data.get('title', '')
                                if title:
                                    self.root.after(0, lambda t=title: self.log_message(f"📚 تم استخراج العنوان من الملف: {t}"))
                                    return title
                        except Exception as e:
                            self.root.after(0, lambda: self.log_message(f"⚠️ خطأ في قراءة ملف JSON المؤقت: {e}"))
                    
                    # ثانياً: البحث عن العنوان في المخرجات كاحتياطي
                    output_lines = result.stdout.split('\n')
                    for line in output_lines:
                        # البحث عن العنوان بأشكال مختلفة
                        if '📚 العنوان:' in line:
                            # استخراج العنوان من السطر
                            title = line.split('📚 العنوان:')[1].strip()
                            if title:
                                self.root.after(0, lambda t=title: self.log_message(f"📚 تم استخراج العنوان من المخرجات: {t}"))
                                return title
                        elif 'العنوان:' in line:
                            # شكل آخر للعنوان
                            title = line.split('العنوان:')[1].strip()
                            if title:
                                self.root.after(0, lambda t=title: self.log_message(f"📚 تم استخراج العنوان من المخرجات: {t}"))
                                return title
                
                # إذا فشل كل شيء، سجل السبب
                if result.returncode != 0:
                    self.root.after(0, lambda: self.log_message(f"❌ فشل استخراج معلومات الكتاب {book_id}: رمز الخطأ {result.returncode}"))
                    if result.stderr:
                        self.root.after(0, lambda: self.log_message(f"🔍 تفاصيل الخطأ: {result.stderr.strip()[:200]}"))
                else:
                    self.root.after(0, lambda: self.log_message(f"⚠️ لم يتم العثور على عنوان في مخرجات الكتاب {book_id}"))
                    # طباعة جزء من المخرجات للتشخيص
                    if result.stdout:
                        output_sample = result.stdout[:500]
                        self.root.after(0, lambda: self.log_message(f"🔍 عينة من المخرجات: {output_sample}"))
                
                return None
                # الملف المؤقت سيُحذف تلقائياً عند انتهاء with block
            
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.log_message(f"⏰ انتهت مهلة استخراج عنوان الكتاب {book_id} (120 ثانية)"))
            return None
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ خطأ في استخراج عنوان الكتاب {book_id}: {str(e)}"))
            return None
    
    def browse_json_file(self):
        """تصفح ملف JSON"""
        file_path = filedialog.askopenfilename(
            title="اختر ملف JSON",
            filetypes=[("JSON files", "*.json"), ("Compressed JSON", "*.json.gz"), ("All files", "*.*")]
        )
        if file_path:
            self.json_file_var.set(file_path)
    
    def browse_json_folder(self):
        """تصفح مجلد ملفات JSON"""
        folder_path = filedialog.askdirectory(title="اختر مجلد ملفات JSON")
        if folder_path:
            self.json_folder_var.set(folder_path)
            # فحص الملفات تلقائياً
            self.scan_json_files()
    
    def browse_multiple_json_files(self):
        """اختيار ملفات JSON متعددة"""
        file_paths = filedialog.askopenfilenames(
            title="اختر ملفات JSON متعددة",
            filetypes=[("JSON files", "*.json"), ("Compressed JSON", "*.json.gz"), ("All files", "*.*")]
        )
        if file_paths:
            self.selected_files_var.set(f"{len(file_paths)} ملف تم اختياره")
            self.json_files_list = list(file_paths)
            self.update_files_listbox()
    
    def scan_json_files(self):
        """فحص ملفات JSON في المجلد المحدد"""
        folder_path = self.json_folder_var.get().strip()
        if not folder_path:
            messagebox.showerror("خطأ", "يرجى اختيار مجلد أولاً")
            return
        
        if not os.path.exists(folder_path):
            messagebox.showerror("خطأ", "المجلد المحدد غير موجود")
            return
        
        try:
            # البحث عن ملفات JSON
            json_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.json', '.json.gz')):
                        full_path = os.path.join(root, file)
                        json_files.append(full_path)
            
            self.json_files_list = json_files
            self.update_files_listbox()
            
            if json_files:
                self.log_message(f"🔍 تم العثور على {len(json_files)} ملف JSON في المجلد")
            else:
                messagebox.showwarning("تحذير", "لم يتم العثور على ملفات JSON في المجلد المحدد")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في فحص المجلد: {str(e)}")
    
    def update_files_listbox(self):
        """تحديث قائمة الملفات المعروضة"""
        self.files_listbox.delete(0, tk.END)
        
        for file_path in self.json_files_list:
            # عرض اسم الملف فقط بدلاً من المسار الكامل
            file_name = os.path.basename(file_path)
            self.files_listbox.insert(tk.END, file_name)
        
        # تحديث العداد
        self.files_counter_label.configure(text=f"عدد الملفات: {len(self.json_files_list)}")
    
    def clear_files_list(self):
        """مسح قائمة الملفات"""
        self.json_files_list = []
        self.files_listbox.delete(0, tk.END)
        self.files_counter_label.configure(text="عدد الملفات: 0")
        self.json_folder_var.set("")
        self.selected_files_var.set("")
        self.log_message("🗑️ تم مسح قائمة الملفات")
    
    def upload_multiple_to_database(self):
        """رفع ملفات JSON متعددة إلى قاعدة البيانات"""
        if not self.json_files_list:
            messagebox.showerror("خطأ", "لا توجد ملفات للرفع. يرجى فحص المجلد أو اختيار ملفات أولاً")
            return
        
        # التحقق من إعدادات قاعدة البيانات
        if not self.validate_database_settings():
            return
        
        # تأكيد من المستخدم
        result = messagebox.askyesno(
            "تأكيد الرفع", 
            f"هل تريد رفع {len(self.json_files_list)} ملف إلى قاعدة البيانات؟\n\nقد تستغرق هذه العملية وقتاً طويلاً."
        )
        
        if not result:
            return
        
        # تحديث الواجهة
        self.is_running = True
        self.upload_multiple_btn.configure(state=tk.DISABLED)
        self.scan_files_btn.configure(state=tk.DISABLED)
        self.shared_status_label.configure(text="📦 بدء رفع الملفات المتعددة...")
        self.shared_progress_bar.start()
        
        # بدء العملية في خيط منفصل
        self.multiple_upload_thread = threading.Thread(
            target=self.upload_multiple_worker,
            args=(self.json_files_list.copy(),)
        )
        self.multiple_upload_thread.daemon = True
        self.multiple_upload_thread.start()
    
    def upload_multiple_worker(self, files_list):
        """العامل الرئيسي لرفع الملفات المتعددة"""
        successful_uploads = 0
        failed_uploads = 0
        
        try:
            for i, file_path in enumerate(files_list, 1):
                if not self.is_running:  # فحص إذا تم إيقاف العملية
                    break
                
                file_name = os.path.basename(file_path)
                
                # تحديث الحالة
                self.root.after(0, lambda idx=i, total=len(files_list), name=file_name: 
                               self.shared_status_label.configure(text=f"📤 رفع {idx}/{total}: {name}"))
                
                # تحديث قائمة الملفات لإظهار الحالة
                self.root.after(0, lambda idx=i-1, status="🔄 جاري الرفع": 
                               self.update_file_status_in_listbox(idx, status))
                
                try:
                    # التحقق من وجود الملف
                    if not os.path.exists(file_path):
                        self.root.after(0, lambda path=file_path: 
                                       self.log_message(f"❌ الملف غير موجود: {os.path.basename(path)}"))
                        failed_uploads += 1
                        self.root.after(0, lambda idx=i-1: 
                                       self.update_file_status_in_listbox(idx, "❌ غير موجود"))
                        continue
                    
                    # رفع الملف باستخدام enhanced_runner.py
                    success = self.upload_single_file(file_path)
                    
                    if success:
                        successful_uploads += 1
                        self.root.after(0, lambda idx=i-1: 
                                       self.update_file_status_in_listbox(idx, "✅ تم بنجاح"))
                        self.root.after(0, lambda name=file_name: 
                                       self.log_message(f"✅ تم رفع {name} بنجاح"))
                    else:
                        failed_uploads += 1
                        self.root.after(0, lambda idx=i-1: 
                                       self.update_file_status_in_listbox(idx, "❌ فشل"))
                        self.root.after(0, lambda name=file_name: 
                                       self.log_message(f"❌ فشل رفع {name}"))
                    
                    # إيقاف قصير بين الملفات
                    time.sleep(1)
                    
                except Exception as e:
                    failed_uploads += 1
                    self.root.after(0, lambda idx=i-1: 
                                   self.update_file_status_in_listbox(idx, "❌ خطأ"))
                    self.root.after(0, lambda name=file_name, err=str(e): 
                                   self.log_message(f"❌ خطأ في رفع {name}: {err}"))
            
            # إنهاء العملية
            self.root.after(0, lambda: self.multiple_upload_completed(successful_uploads, failed_uploads))
            
        except Exception as e:
            error_msg = f"خطأ في رفع الملفات المتعددة: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.multiple_upload_error(msg))
    
    def upload_single_file(self, file_path):
        """رفع ملف واحد إلى قاعدة البيانات"""
        try:
            # إعداد الأمر
            command = [
                sys.executable,
                os.path.join(current_dir, "enhanced_runner.py"),
                "save-db",
                file_path,
                "--db-host", self.db_host_var.get(),
                "--db-port", self.db_port_var.get(),
                "--db-user", self.db_user_var.get(),
                "--db-name", self.db_name_var.get(),
                "--db-password", self.db_password_var.get()
            ]
            
            # إعداد متغيرات البيئة
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # تشغيل الأمر
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=current_dir,
                env=env,
                timeout=3600  # 60 دقيقة timeout
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False
    
    def update_file_status_in_listbox(self, index, status):
        """تحديث حالة ملف في قائمة الملفات"""
        try:
            if 0 <= index < self.files_listbox.size():
                current_text = self.files_listbox.get(index)
                # إزالة الحالة السابقة إذا كانت موجودة
                if " - " in current_text:
                    current_text = current_text.split(" - ")[0]
                new_text = f"{current_text} - {status}"
                self.files_listbox.delete(index)
                self.files_listbox.insert(index, new_text)
        except Exception:
            pass  # تجاهل أخطاء التحديث
    
    def multiple_upload_completed(self, successful, failed):
        """إنهاء عملية رفع الملفات المتعددة"""
        self.is_running = False
        self.upload_multiple_btn.configure(state=tk.NORMAL)
        self.scan_files_btn.configure(state=tk.NORMAL)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text=f"✅ انتهى الرفع - {successful} نجح، {failed} فشل")
        
        # عرض تقرير مفصل
        total = successful + failed
        success_rate = (successful / total * 100) if total > 0 else 0
        
        report = f"تم إنهاء رفع الملفات المتعددة\n\n"
        report += f"إجمالي الملفات: {total}\n"
        report += f"نجح: {successful} ملف\n"
        report += f"فشل: {failed} ملف\n"
        report += f"معدل النجاح: {success_rate:.1f}%"
        
        messagebox.showinfo("تم الإنهاء", report)
        
        # تسجيل الإحصائيات النهائية
        self.log_message(f"📊 إحصائيات الرفع المتعدد: {successful} نجح، {failed} فشل من أصل {total}")
    
    def multiple_upload_error(self, error_msg):
        """معالجة خطأ في رفع الملفات المتعددة"""
        self.is_running = False
        self.upload_multiple_btn.configure(state=tk.NORMAL)
        self.scan_files_btn.configure(state=tk.NORMAL)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="❌ خطأ في رفع الملفات")
        
        self.log_message(error_msg)
        messagebox.showerror("خطأ", error_msg)
    
    def start_extraction(self):
        """بدء عملية الاستخراج"""
        # التحقق من صحة البيانات
        if not self.book_id_var.get().strip():
            messagebox.showerror("خطأ", "يجب إدخال معرف الكتاب")
            return
        
        try:
            int(self.book_id_var.get().strip())
        except ValueError:
            messagebox.showerror("خطأ", "معرف الكتاب يجب أن يكون رقماً")
            return
        
        # بناء الأمر
        command = self.build_extraction_command()
        
        # تحديث الواجهة
        self.is_running = True
        self.extract_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.shared_status_label.configure(text="جاري الاستخراج...", style='Success.TLabel')
        self.shared_progress_bar.start()
        
        # بدء العملية في خيط منفصل
        self.extraction_thread = threading.Thread(target=self.run_extraction, args=(command,))
        self.extraction_thread.daemon = True
        self.extraction_thread.start()
        
        # بدء مراقبة التقدم
        self.start_time = time.time()
        self.monitor_progress()
    
    def build_extraction_command(self):
        """بناء أمر الاستخراج"""
        command = ["python", "enhanced_runner.py", "extract", self.book_id_var.get().strip()]
        
        # إضافة المعاملات الاختيارية
        if self.max_pages_var.get().strip():
            command.extend(["--max-pages", self.max_pages_var.get().strip()])
        
        if self.output_dir_var.get().strip():
            command.extend(["--output-dir", self.output_dir_var.get().strip()])
        
        # إضافة إعدادات قاعدة البيانات إذا كان نوع العملية يتطلب ذلك
        if self.operation_var.get() == "extract + database":
            command.extend([
                "--db-host", self.db_host_var.get(),
                "--db-port", self.db_port_var.get(),
                "--db-user", self.db_user_var.get(),
                "--db-name", self.db_name_var.get(),
                "--db-password", self.db_password_var.get()  # تمرير كلمة السر دائماً حتى لو فارغة
            ])
        
        return command
    
    def run_extraction(self, command):
        """تشغيل عملية الاستخراج"""
        try:
            # إعداد متغيرات البيئة للترميز
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=current_dir,
                env=env
            )
            
            # قراءة المخرجات
            while True:
                try:
                    output = self.current_process.stdout.readline()
                    if output == '' and self.current_process.poll() is not None:
                        break
                    if output:
                        self.log_message(output.strip())
                except UnicodeDecodeError as e:
                    self.log_message(f"❌ خطأ في ترميز النص: {str(e)}")
                    continue
            
            # التحقق من رمز الخروج
            return_code = self.current_process.poll()
            
            if return_code == 0:
                self.extraction_completed(True)
            else:
                self.extraction_completed(False)
                
        except Exception as e:
            self.extraction_error(str(e))
    
    def upload_to_database(self):
        """رفع ملف JSON إلى قاعدة البيانات"""
        if not self.json_file_var.get().strip():
            messagebox.showerror("خطأ", "يجب اختيار ملف JSON")
            return
        
        if not os.path.exists(self.json_file_var.get()):
            messagebox.showerror("خطأ", "الملف المحدد غير موجود")
            return
        
        # بناء الأمر
        command = [
            "python", "enhanced_runner.py", "save-db", self.json_file_var.get(),
            "--db-host", self.db_host_var.get(),
            "--db-port", self.db_port_var.get(),
            "--db-user", self.db_user_var.get(),
            "--db-name", self.db_name_var.get(),
            "--db-password", self.db_password_var.get()  # تمرير كلمة السر دائماً حتى لو فارغة
        ]
        
        # تحديث الواجهة
        self.is_running = True
        self.upload_btn.configure(state=tk.DISABLED)
        self.shared_status_label.configure(text="جاري الرفع...", style='Success.TLabel')
        self.shared_progress_bar.start()
        
        # تشغيل العملية
        threading.Thread(target=self.run_database_operation, args=(command, "upload")).start()
    
    def create_database_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        command = [
            "python", "enhanced_runner.py", "create-tables",
            "--db-host", self.db_host_var.get(),
            "--db-port", self.db_port_var.get(),
            "--db-user", self.db_user_var.get(),
            "--db-name", self.db_name_var.get(),
            "--db-password", self.db_password_var.get()  # تمرير كلمة السر دائماً حتى لو فارغة
        ]
        
        # تحديث الواجهة
        self.is_running = True
        self.create_tables_btn.configure(state=tk.DISABLED)
        self.shared_status_label.configure(text="جاري إنشاء الجداول...", style='Success.TLabel')
        self.shared_progress_bar.start()
        
        # تشغيل العملية
        threading.Thread(target=self.run_database_operation, args=(command, "create_tables")).start()
    
    def fix_database_structure(self):
        """إصلاح هيكل قاعدة البيانات"""
        # تأكيد من المستخدم
        result = messagebox.askyesno(
            "إصلاح قاعدة البيانات", 
            "هل تريد إصلاح هيكل قاعدة البيانات؟\n\n• سيتم جعل حقل edition دائماً NULL\n• سيتم حفظ رقم الطبعة في edition_number\n• سيتم تحسين دعم النصوص العربية"
        )
        
        if not result:
            return
        
        # تحديث الواجهة
        self.is_running = True
        self.fix_database_btn.configure(state=tk.DISABLED)
        self.shared_status_label.configure(text="🔧 جاري إصلاح قاعدة البيانات...")
        self.shared_progress_bar.start()
        
        # تشغيل العملية في خيط منفصل
        threading.Thread(target=self.fix_database_worker).start()
    
    def fix_database_worker(self):
        """عامل إصلاح قاعدة البيانات"""
        try:
            # إعداد معاملات الاتصال
            connection_params = {
                'host': self.db_host_var.get(),
                'port': int(self.db_port_var.get()),
                'user': self.db_user_var.get(),
                'database': self.db_name_var.get(),
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci'
            }
            
            # إضافة كلمة المرور إذا لم تكن فارغة
            if self.db_password_var.get().strip():
                connection_params['password'] = self.db_password_var.get()
            
            self.root.after(0, lambda: self.log_message("🔌 الاتصال بقاعدة البيانات..."))
            
            connection = mysql.connector.connect(**connection_params)
            cursor = connection.cursor()
            
            self.root.after(0, lambda: self.log_message("🔍 فحص هيكل الجدول الحالي..."))
            
            # فحص هيكل الجدول
            cursor.execute("DESCRIBE books")
            columns = cursor.fetchall()
            
            # البحث عن حقل edition
            edition_column = None
            for column in columns:
                if column[0] == 'edition':
                    edition_column = column
                    break
            
            if edition_column:
                self.root.after(0, lambda col=edition_column[1]: 
                               self.log_message(f"📋 حقل edition الحالي: {col}"))
                
                # فحص إذا كان النوع يحتاج إصلاح
                if 'int' in edition_column[1].lower() or 'varchar' not in edition_column[1].lower():
                    self.root.after(0, lambda: 
                                   self.log_message("⚠️ حقل edition يحتاج إصلاح!"))
                    
                    self.root.after(0, lambda: 
                                   self.log_message("🔧 تحويل حقل edition إلى VARCHAR(255)..."))
                    
                    # تنفيذ الإصلاح
                    alter_query = "ALTER TABLE books MODIFY COLUMN edition VARCHAR(255) NULL"
                    cursor.execute(alter_query)
                    connection.commit()
                    
                    self.root.after(0, lambda: 
                                   self.log_message("✅ تم تحويل حقل edition بنجاح!"))
                else:
                    self.root.after(0, lambda: 
                                   self.log_message("✅ حقل edition من النوع الصحيح"))
                
                # جعل جميع حقول edition موجودة = NULL
                self.root.after(0, lambda: 
                               self.log_message("🔄 تنظيف بيانات حقل edition..."))
                
                update_query = "UPDATE books SET edition = NULL"
                cursor.execute(update_query)
                rows_affected = cursor.rowcount
                connection.commit()
                
                self.root.after(0, lambda rows=rows_affected: 
                               self.log_message(f"✅ تم تنظيف {rows} صف من حقل edition"))
            
            # فحص إضافي للحقول الأخرى
            fixes_applied = []
            
            # التأكد من أن جميع حقول النصوص تدعم UTF8
            text_fields = ['title', 'slug', 'description', 'source_url']
            for field in text_fields:
                try:
                    cursor.execute(f"ALTER TABLE books MODIFY COLUMN {field} TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    fixes_applied.append(f"تحديث ترميز حقل {field}")
                except:
                    pass
            
            # التأكد من ترميز جدول الناشرين
            try:
                cursor.execute("ALTER TABLE publishers MODIFY COLUMN name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                fixes_applied.append("تحديث ترميز جدول الناشرين")
            except:
                pass
            
            # التأكد من ترميز جدول أقسام الكتب
            try:
                cursor.execute("ALTER TABLE book_sections MODIFY COLUMN name VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                fixes_applied.append("تحديث ترميز جدول أقسام الكتب")
            except:
                pass
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # تقرير الإصلاحات
            if fixes_applied:
                for fix in fixes_applied:
                    self.root.after(0, lambda f=fix: self.log_message(f"🔧 {f}"))
            
            self.root.after(0, self.fix_database_completed)
            
        except mysql.connector.Error as e:
            error_msg = f"خطأ في قاعدة البيانات: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.fix_database_error(msg))
        except Exception as e:
            error_msg = f"خطأ في إصلاح قاعدة البيانات: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.fix_database_error(msg))
    
    def fix_database_completed(self):
        """إنهاء إصلاح قاعدة البيانات"""
        self.is_running = False
        self.fix_database_btn.configure(state=tk.NORMAL)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="✅ تم إصلاح قاعدة البيانات")
        
        self.log_message("🎉 تم إصلاح قاعدة البيانات بنجاح!")
        messagebox.showinfo("تم الإصلاح", "تم إصلاح هيكل قاعدة البيانات بنجاح!\n\nيمكنك الآن إعادة محاولة رفع ملفات JSON.")
    
    def fix_database_error(self, error_msg):
        """معالجة خطأ في إصلاح قاعدة البيانات"""
        self.is_running = False
        self.fix_database_btn.configure(state=tk.NORMAL)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="❌ فشل إصلاح قاعدة البيانات")
        
        self.log_message(f"❌ {error_msg}")
        messagebox.showerror("خطأ في الإصلاح", f"فشل في إصلاح قاعدة البيانات:\n{error_msg}")
    
    def show_book_stats(self):
        """عرض إحصائيات كتاب"""
        if not self.db_book_id_var.get().strip():
            messagebox.showerror("خطأ", "يجب إدخال معرف الكتاب")
            return
        
        try:
            int(self.db_book_id_var.get().strip())
        except ValueError:
            messagebox.showerror("خطأ", "معرف الكتاب يجب أن يكون رقماً")
            return
        
        command = [
            "python", "enhanced_runner.py", "stats", self.db_book_id_var.get(),
            "--db-host", self.db_host_var.get(),
            "--db-port", self.db_port_var.get(),
            "--db-user", self.db_user_var.get(),
            "--db-name", self.db_name_var.get(),
            "--db-password", self.db_password_var.get()  # تمرير كلمة السر دائماً حتى لو فارغة
        ]
        
        # تحديث الواجهة
        self.is_running = True
        self.show_stats_btn.configure(state=tk.DISABLED)
        self.shared_status_label.configure(text="جاري جلب الإحصائيات...", style='Success.TLabel')
        self.shared_progress_bar.start()
        
        # تشغيل العملية
        threading.Thread(target=self.run_database_operation, args=(command, "stats")).start()
    
    def run_database_operation(self, command, operation_type):
        """تشغيل عملية قاعدة البيانات"""
        try:
            # إعداد متغيرات البيئة للترميز
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=current_dir,
                env=env
            )
            
            # قراءة المخرجات
            while True:
                try:
                    output = self.current_process.stdout.readline()
                    if output == '' and self.current_process.poll() is not None:
                        break
                    if output:
                        self.log_message(output.strip())
                except UnicodeDecodeError as e:
                    self.log_message(f"❌ خطأ في ترميز النص: {str(e)}")
                    continue
            
            # التحقق من رمز الخروج
            return_code = self.current_process.poll()
            
            if return_code == 0:
                self.database_operation_completed(True, operation_type)
            else:
                self.database_operation_completed(False, operation_type)
                
        except Exception as e:
            self.database_operation_error(str(e), operation_type)
    
    def test_database_connection(self):
        """اختبار اتصال قاعدة البيانات"""
        try:
            # محاولة الاتصال بقاعدة البيانات
            import mysql.connector
            
            # إعداد معاملات الاتصال
            connection_params = {
                'host': self.db_host_var.get(),
                'port': int(self.db_port_var.get()),
                'user': self.db_user_var.get(),
                'database': self.db_name_var.get(),
                'password': self.db_password_var.get()  # تمرير كلمة السر دائماً حتى لو فارغة
            }
            
            connection = mysql.connector.connect(**connection_params)
            
            if connection.is_connected():
                connection.close()
                messagebox.showinfo("نجح الاتصال", "تم الاتصال بقاعدة البيانات بنجاح! ✅")
                self.log_message("✅ نجح اختبار الاتصال بقاعدة البيانات")
            
        except Exception as e:
            messagebox.showerror("فشل الاتصال", f"فشل الاتصال بقاعدة البيانات:\n{str(e)}")
            self.log_message(f"❌ فشل اختبار الاتصال: {str(e)}")
    
    def stop_operation(self):
        """إيقاف العملية الجارية"""
        if self.current_process:
            self.current_process.terminate()
        
        # إيقاف جميع أنواع العمليات
        self.is_running = False
        
        self.log_message("⏹️ تم إيقاف العملية بواسطة المستخدم")
        self.operation_stopped()
    
    def clear_extract_form(self):
        """مسح نموذج الاستخراج"""
        self.book_id_var.set("")
        self.max_pages_var.set("")
        self.output_dir_var.set("")
        self.log_message("🗑️ تم مسح النموذج")
    
    def open_books_folder(self):
        """فتح مجلد الكتب"""
        books_folder = os.path.join(current_dir, "enhanced_books")
        if os.path.exists(books_folder):
            os.startfile(books_folder)
        else:
            messagebox.showwarning("تحذير", "مجلد الكتب غير موجود")
    
    def open_logs_folder(self):
        """فتح مجلد السجلات"""
        logs_folder = os.path.join(current_dir, "logs")
        if os.path.exists(logs_folder):
            os.startfile(logs_folder)
        else:
            # فتح المجلد الحالي إذا لم يوجد مجلد السجلات
            os.startfile(current_dir)
    
    def search_files(self):
        """البحث في الملفات"""
        search_window = tk.Toplevel(self.root)
        search_window.title("البحث في الملفات")
        search_window.geometry("400x300")
        
        ttk.Label(search_window, text="البحث في ملفات JSON:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_window, textvariable=search_var, width=50)
        search_entry.pack(pady=5)
        
        def perform_search():
            search_term = search_var.get().strip()
            if not search_term:
                return
            
            # البحث في ملفات JSON
            books_folder = os.path.join(current_dir, "enhanced_books")
            if os.path.exists(books_folder):
                results = []
                for file in os.listdir(books_folder):
                    if file.endswith('.json') or file.endswith('.json.gz'):
                        if search_term.lower() in file.lower():
                            results.append(file)
                
                if results:
                    result_text = "\n".join(results)
                    messagebox.showinfo("نتائج البحث", f"تم العثور على {len(results)} ملف:\n\n{result_text}")
                else:
                    messagebox.showinfo("نتائج البحث", "لم يتم العثور على أي ملف")
        
        ttk.Button(search_window, text="بحث", command=perform_search).pack(pady=10)
    
    def refresh_logs(self):
        """تحديث السجلات"""
        # قراءة ملف السجل
        log_file = os.path.join(current_dir, "enhanced_shamela_runner.log")
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.logs_text.delete(1.0, tk.END)
                    self.logs_text.insert(tk.END, content)
                    self.logs_text.see(tk.END)
            except Exception as e:
                self.log_message(f"خطأ في قراءة ملف السجل: {str(e)}")
    
    def clear_logs(self):
        """مسح السجلات"""
        self.logs_text.delete(1.0, tk.END)
        self.log_message("تم مسح السجل")
    
    def save_logs(self):
        """حفظ السجلات"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                content = self.logs_text.get(1.0, tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("تم الحفظ", f"تم حفظ السجل في:\n{file_path}")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل في حفظ السجل:\n{str(e)}")
    
    def update_extraction_button_text(self):
        """تحديث نص زر الاستخراج بناءً على نوع العملية المختار"""
        try:
            if hasattr(self, 'start_extraction_btn'):
                operation_type = self.category_operation_var.get()
                if operation_type == "extract_only":
                    button_text = "🔍 بدء استخراج جميع الكتب"
                else:  # extract_and_database
                    button_text = "🔍📤 بدء استخراج الكتب ورفعها للقاعدة"
                
                self.start_extraction_btn.configure(text=button_text)
        except Exception as e:
            if hasattr(self, 'log_message'):
                self.log_message(f"خطأ في تحديث نص الزر: {e}")
    
    def log_message(self, message):
        """إضافة رسالة للسجل"""
        try:
            # التأكد من أن الرسالة نص صحيح
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            elif not isinstance(message, str):
                message = str(message)
                
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            
            self.logs_text.insert(tk.END, formatted_message)
            self.logs_text.see(tk.END)
            
            # تحديث شريط الحالة إذا كان موجوداً
            if hasattr(self, 'status_text'):
                self.status_text.configure(text=message[:100])
        except Exception as e:
            # في حالة فشل كل شيء، اعرض رسالة خطأ بسيطة
            timestamp = datetime.now().strftime("%H:%M:%S")
            error_message = f"[{timestamp}] ❌ خطأ في عرض الرسالة: {str(e)}\n"
            self.logs_text.insert(tk.END, error_message)
            self.logs_text.see(tk.END)
    
    def monitor_progress(self):
        """مراقبة التقدم"""
        if self.is_running:
            elapsed = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            # تحديث معلومات الوقت في شريط الحالة
            if hasattr(self, 'status_text'):
                current_text = self.shared_status_label.cget("text")
                self.status_text.configure(text=f"{current_text} - الوقت: {elapsed_str}")
    
    # ===== وظائف استخراج الأقسام =====
    
    def check_category(self):
        """فحص القسم وعرض معلوماته"""
        category_id = self.category_id_var.get().strip()
        if not category_id:
            messagebox.showerror("خطأ", "يرجى إدخال رقم القسم")
            return
        
        try:
            # التحقق من توفر المكتبات المطلوبة
            if not CATEGORY_EXTRACTION_AVAILABLE:
                error_msg = "❌ مكتبات مطلوبة غير متوفرة!\n\nيرجى تثبيت المكتبات المطلوبة بتشغيل:\npip install requests beautifulsoup4"
                self.category_info_text.delete(1.0, tk.END)
                self.category_info_text.insert(tk.END, error_msg)
                messagebox.showerror("خطأ في المكتبات", error_msg)
                return
            
            # إنشاء مستخرج الأقسام
            extractor = CategoryExtractor()
            
            # تحديث واجهة المستخدم
            self.category_info_text.delete(1.0, tk.END)
            self.category_info_text.insert(tk.END, "🔍 جاري فحص القسم...\n")
            self.root.update()
            
            # استخراج معلومات القسم
            books = extractor.extract_category_books(category_id)
            category_name = extractor._extract_category_name(category_id)
            
            if books:
                info_text = f"📚 اسم القسم: {category_name}\n"
                info_text += f"📊 عدد الكتب: {len(books)}\n"
                info_text += f"🔗 الرابط: https://shamela.ws/category/{category_id}\n"
                info_text += f"📋 أرقام الكتب: {', '.join(map(str, books[:10]))}"
                if len(books) > 10:
                    info_text += f" وآخرين ({len(books) - 10} كتاب إضافي)"
                
                self.category_info_text.delete(1.0, tk.END)
                self.category_info_text.insert(tk.END, info_text)
                
                # إظهار رسالة نجاح
                messagebox.showinfo("تم الفحص", f"تم العثور على {len(books)} كتاب في القسم")
            else:
                self.category_info_text.delete(1.0, tk.END)
                self.category_info_text.insert(tk.END, "❌ لم يتم العثور على كتب في هذا القسم")
                messagebox.showwarning("تحذير", "لم يتم العثور على كتب في هذا القسم")
                
        except Exception as e:
            error_msg = f"❌ خطأ في فحص القسم: {str(e)}"
            self.category_info_text.delete(1.0, tk.END)
            self.category_info_text.insert(tk.END, error_msg)
            messagebox.showerror("خطأ", error_msg)
    
    def check_multiple_categories(self):
        """فحص الأقسام المتعددة وعرض معلوماتها"""
        category_list = self.category_list_var.get().strip()
        if not category_list:
            messagebox.showerror("خطأ", "يرجى إدخال قائمة الأقسام المفصولة بفواصل")
            return
        
        try:
            # تحويل قائمة الأقسام
            categories = [cat.strip() for cat in category_list.split(',') if cat.strip()]
            if not categories:
                messagebox.showerror("خطأ", "قائمة الأقسام فارغة")
                return
                
            # التحقق من توفر المكتبات المطلوبة
            if not CATEGORY_EXTRACTION_AVAILABLE:
                error_msg = "❌ مكتبات مطلوبة غير متوفرة!\n\nيرجى تثبيت المكتبات المطلوبة بتشغيل:\npip install requests beautifulsoup4"
                self.category_info_text.delete(1.0, tk.END)
                self.category_info_text.insert(tk.END, error_msg)
                messagebox.showerror("خطأ في المكتبات", error_msg)
                return
            
            # إنشاء مستخرج الأقسام
            extractor = CategoryExtractor()
            
            # تحديث واجهة المستخدم
            self.category_info_text.delete(1.0, tk.END)
            self.category_info_text.insert(tk.END, f"🔍 جاري فحص {len(categories)} قسم...\n")
            self.root.update()
            
            # معلومات مجمعة عن الأقسام
            all_info_text = ""
            total_books = 0
            
            for category_id in categories:
                try:
                    # استخراج معلومات القسم
                    books = extractor.extract_category_books(category_id)
                    category_name = extractor._extract_category_name(category_id)
                    
                    # إضافة معلومات القسم
                    all_info_text += f"📚 القسم {category_id} - {category_name}: {len(books)} كتاب\n"
                    total_books += len(books)
                    
                    # إيقاف قصير لتجنب التحميل الزائد
                    time.sleep(0.2)
                    
                except Exception as e:
                    all_info_text += f"❌ خطأ في القسم {category_id}: {str(e)}\n"
            
            # عرض النتائج المجمعة
            summary_text = f"📊 ملخص فحص الأقسام:\n"
            summary_text += f"👉 عدد الأقسام: {len(categories)}\n"
            summary_text += f"📚 إجمالي الكتب: {total_books}\n\n"
            summary_text += all_info_text
            
            self.category_info_text.delete(1.0, tk.END)
            self.category_info_text.insert(tk.END, summary_text)
            
            # إظهار رسالة نجاح
            messagebox.showinfo("تم الفحص", f"تم العثور على {total_books} كتاب في {len(categories)} قسم")
                
        except Exception as e:
            error_msg = f"❌ خطأ في فحص الأقسام المتعددة: {str(e)}"
            self.category_info_text.delete(1.0, tk.END)
            self.category_info_text.insert(tk.END, error_msg)
            messagebox.showerror("خطأ", error_msg)
    
    def start_category_extraction(self):
        """بدء استخراج كتب الأقسام"""
        if self.category_mode_var.get() == "single":
            self.start_single_category_extraction()
        else:
            self.start_multiple_category_extraction()
    
    def start_single_category_extraction(self):
        """بدء استخراج قسم واحد"""
        category_id = self.category_id_var.get().strip()
        if not category_id:
            messagebox.showerror("خطأ", "يرجى إدخال رقم القسم")
            return
        
        # التأكد من إعدادات قاعدة البيانات
        if not self.validate_database_settings():
            return
        
        # بدء العملية في خيط منفصل
        self.start_category_thread([category_id])
    
    def start_multiple_category_extraction(self):
        """بدء استخراج أقسام متعددة"""
        category_list = self.category_list_var.get().strip()
        if not category_list:
            messagebox.showerror("خطأ", "يرجى إدخال قائمة الأقسام")
            return
        
        try:
            # تحويل قائمة الأقسام
            categories = [cat.strip() for cat in category_list.split(',') if cat.strip()]
            if not categories:
                messagebox.showerror("خطأ", "قائمة الأقسام فارغة")
                return
        except:
            messagebox.showerror("خطأ", "تنسيق قائمة الأقسام غير صحيح")
            return
        
        # التأكد من إعدادات قاعدة البيانات
        if not self.validate_database_settings():
            return
        
        # بدء العملية في خيط منفصل
        self.start_category_thread(categories)
    
    def start_category_thread(self, categories):
        """بدء خيط استخراج الأقسام"""
        # تحديث حالة الواجهة
        self.is_running = True
        self.start_time = time.time()
        self.start_extraction_btn.configure(state=tk.DISABLED)
        self.stop_category_btn.configure(state=tk.NORMAL)
        self.shared_progress_bar.start()
        self.shared_status_label.configure(text="🔄 بدء استخراج الأقسام...")
        
        # مسح قائمة الكتب السابقة
        self.clear_books_list()
        
        # بدء الخيط
        self.category_thread = threading.Thread(
            target=self.extract_categories_worker,
            args=(categories,)
        )
        self.category_thread.daemon = True
        self.category_thread.start()
    
    def extract_categories_worker(self, categories):
        """العامل الرئيسي لاستخراج الأقسام"""
        try:
            # التحقق من توفر المكتبات
            if not CATEGORY_EXTRACTION_AVAILABLE:
                error_msg = "المكتبات المطلوبة غير متوفرة"
                self.root.after(0, lambda: self.category_extraction_error(error_msg))
                return
            
            extractor = CategoryExtractor()
            max_books = None
            
            # تحديد الحد الأقصى للكتب
            if self.max_books_per_category_var.get().strip():
                try:
                    max_books = int(self.max_books_per_category_var.get().strip())
                except:
                    pass
            
            # استخراج قائمة الكتب من الأقسام
            total_books_extracted = 0
            
            for category_id in categories:
                try:
                    # تحديث الحالة
                    self.root.after(0, lambda cat=category_id: 
                                   self.shared_status_label.configure(text=f"🔍 فحص القسم {cat}..."))
                    
                    # استخراج كتب القسم
                    books = extractor.extract_category_books(category_id)
                    category_name = extractor._extract_category_name(category_id)
                    
                    if max_books and len(books) > max_books:
                        books = books[:max_books]
                    
                    self.root.after(0, lambda cat=category_id, name=category_name, count=len(books): 
                                   self.log_message(f"📚 القسم {cat} ({name}): تم العثور على {count} كتاب"))
                    
                    # استخراج كل كتاب باستخدام enhanced_runner.py
                    for i, book_id in enumerate(books, 1):
                        if not self.is_running:  # فحص إذا تم إيقاف العملية
                            break
                            
                        # تحديث الحالة
                        self.root.after(0, lambda cat=category_id, curr=i, total=len(books), bid=book_id: 
                                       self.shared_status_label.configure(text=f"📖 القسم {cat}: كتاب {curr}/{total} - رقم {bid}"))
                        
                        # إضافة الكتاب للقائمة
                        self.root.after(0, lambda bid=book_id: 
                                       self.add_book_to_list(bid, f"كتاب {bid}", "🔄 جاري الاستخراج"))
                        
                        # تشغيل enhanced_runner.py لاستخراج الكتاب
                        success, book_title = self.extract_single_book_from_category(book_id, category_name)
                        
                        # تحديث حالة الكتاب مع العنوان إن وُجد
                        display_title = book_title if book_title else f"كتاب {book_id}"
                        status = "✅ تم بنجاح" if success else "❌ فشل"
                        self.root.after(0, lambda bid=book_id, title=display_title, s=status: 
                                       self.update_book_status(bid, title, s))
                        
                        if success:
                            total_books_extracted += 1
                        
                        # إيقاف قصير
                        time.sleep(1)
                
                except Exception as e:
                    error_msg = f"خطأ في معالجة القسم {category_id}: {str(e)}"
                    self.root.after(0, lambda msg=error_msg: self.log_message(f"❌ {msg}"))
            
            # إنهاء العملية
            self.root.after(0, lambda: self.category_extraction_completed_with_stats(total_books_extracted))
            
        except Exception as e:
            error_msg = f"خطأ في استخراج الأقسام: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self.category_extraction_error(msg))
    
    def extract_single_book_from_category(self, book_id, category_name=None):
        """استخراج كتاب واحد باستخدام enhanced_runner.py"""
        book_title = None  # متغير لحفظ عنوان الكتاب
        
        try:
            # تحديد نوع العملية المختار
            operation_type = self.category_operation_var.get()
            
            # تحديد مجلد الإخراج الأساسي
            base_output_dir = self.category_output_dir_var.get().strip()
            if not base_output_dir:
                # استخدام مجلد افتراضي إذا لم يتم تحديد مجلد
                base_output_dir = os.path.join(current_dir, "enhanced_books", "categories")
            
            # إنشاء مجلد القسم إذا كان اسم القسم متوفر
            category_folder = None
            if category_name and operation_type == "extract_only":
                # تنظيف اسم القسم ليصبح صالح كاسم مجلد
                clean_category_name = self.clean_category_name_for_folder(category_name)
                category_folder = os.path.join(base_output_dir, clean_category_name)
                
                # إنشاء المجلد إذا لم يكن موجود
                try:
                    os.makedirs(category_folder, exist_ok=True)
                    self.root.after(0, lambda: self.log_message(f"📁 تم إنشاء/التأكد من مجلد القسم: {category_folder}"))
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"⚠️ تعذر إنشاء مجلد القسم، سيتم الحفظ في المجلد الافتراضي: {e}"))
                    category_folder = base_output_dir
            
            # إذا كان الوضع استخراج ورفع، التحقق من وجود الكتاب في قاعدة البيانات أولاً
            if operation_type == "extract_and_database":
                # أولاً: التحقق من وجود الكتاب في قاعدة البيانات
                check_command = [
                    sys.executable,
                    os.path.join(current_dir, "enhanced_runner.py"),
                    "check",
                    str(book_id),
                    "--db-host", self.db_host_var.get() or "localhost",
                    "--db-port", self.db_port_var.get() or "3306",
                    "--db-user", self.db_user_var.get() or "root",
                    "--db-name", self.db_name_var.get() or "bms",
                    "--db-password", self.db_password_var.get() or ""
                ]
                
                # إعداد متغيرات البيئة
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                env['PYTHONUTF8'] = '1'
                
                # التحقق من وجود الكتاب
                check_result = subprocess.run(
                    check_command,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=current_dir,
                    env=env,
                    timeout=30  # 30 ثانية كافية للتحقق
                )
                
                # إذا كان الكتاب موجود (رمز الخروج = 0)، تخطي الاستخراج
                if check_result.returncode == 0:
                    self.root.after(0, lambda: self.log_message(f"⏭️ كتاب {book_id}: موجود مسبقًا في قاعدة البيانات - تم تخطيه"))
                    
                    # تحديث حالة الكتاب في واجهة المستخدم
                    if hasattr(self, 'files_listbox') and hasattr(self, 'update_file_status_in_listbox'):
                        try:
                            # ابحث عن الكتاب في القائمة وحدّث حالته
                            for i in range(self.files_listbox.size()):
                                if str(book_id) in self.files_listbox.get(i):
                                    self.root.after(0, lambda idx=i: self.update_file_status_in_listbox(idx, "⏭️ موجود مسبقًا"))
                                    break
                        except:
                            pass
                    
                    return True  # اعتبر العملية نجحت لأننا تخطينا الكتاب الموجود
                
                # إذا لم يكن الكتاب موجود، استخرجه
                self.root.after(0, lambda: self.log_message(f"🔍 كتاب {book_id}: غير موجود - بدء الاستخراج والرفع..."))
                
                # إعداد الأمر - نستخدم extract مع معاملات قاعدة البيانات لتفعيل الحفظ في قاعدة البيانات
                command = [
                    sys.executable,
                    os.path.join(current_dir, "enhanced_runner.py"),
                    "extract",
                    str(book_id)
                ]
                
                # إضافة معاملات قاعدة البيانات بشكل صريح (نجبر استخدام قاعدة البيانات)
                command.extend([
                    "--db-host", self.db_host_var.get() or "localhost",
                    "--db-port", self.db_port_var.get() or "3306",
                    "--db-user", self.db_user_var.get() or "root",
                    "--db-name", self.db_name_var.get() or "bms",
                    "--db-password", self.db_password_var.get() or ""
                ])
                
            else:  # operation_type == "extract_only"
                # وضع الاستخراج فقط - استخدم enhanced_shamela_scraper.py مباشرة
                self.root.after(0, lambda: self.log_message(f"🔍 كتاب {book_id}: بدء الاستخراج فقط..."))
                
                # أولاً: استخراج عنوان الكتاب لاستخدامه في التسمية
                self.root.after(0, lambda: self.log_message(f"📚 كتاب {book_id}: جاري استخراج العنوان للتسمية..."))
                book_title = self.extract_book_title(book_id)
                
                if book_title:
                    self.root.after(0, lambda: self.log_message(f"✅ كتاب {book_id}: تم استخراج العنوان بنجاح: '{book_title}'"))
                else:
                    self.root.after(0, lambda: self.log_message(f"⚠️ كتاب {book_id}: فشل في استخراج العنوان، سيتم استخدام التسمية الافتراضية"))
                
                command = [
                    sys.executable,
                    os.path.join(current_dir, "enhanced_shamela_scraper.py"),
                    str(book_id),
                    "--max-pages", "50"  # حد أدنى من الصفحات للاختبار السريع
                ]
                
                # إضافة مجلد الإخراج مع التسمية المناسبة
                output_filename = None
                if book_title:
                    # استخدام عنوان الكتاب في التسمية
                    cleaned_title = self.clean_book_title_for_filename(book_title)
                    output_filename = f"{cleaned_title}.json"
                    self.root.after(0, lambda: self.log_message(f"📝 اسم الملف المبني على العنوان: {output_filename}"))
                else:
                    # استخدام التسمية القديمة كاحتياطي
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_filename = f"book_{book_id}_{timestamp}.json"
                    self.root.after(0, lambda: self.log_message(f"⚠️ استخدام الاسم الافتراضي: {output_filename}"))
                
                # تحديد مسار الحفظ الكامل
                if category_folder and os.path.exists(category_folder):
                    output_path = os.path.join(category_folder, output_filename)
                else:
                    # إذا لم يتم تحديد مجلد أو فشل إنشاؤه، استخدم المجلد الأساسي
                    output_path = os.path.join(base_output_dir, output_filename)
                
                command.extend(["--output", output_path])
                self.root.after(0, lambda: self.log_message(f"� المسار الكامل للحفظ: {output_path}"))
            
            # إعداد متغيرات البيئة
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            
            # تشغيل الأمر
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=current_dir,
                env=env,
                timeout=3600  # 60 دقيقة timeout
            )
            
            # تسجيل المخرجات
            if result.stdout:
                stdout = result.stdout.strip()
                self.root.after(0, lambda: self.log_message(f"📖 كتاب {book_id}: {stdout}"))
            
            if result.stderr:
                self.root.after(0, lambda: self.log_message(f"⚠️ كتاب {book_id}: {result.stderr.strip()}"))
            
            return result.returncode == 0, book_title
            
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.log_message(f"⏰ انتهت مهلة استخراج الكتاب {book_id}"))
            return False, book_title
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"❌ خطأ في استخراج الكتاب {book_id}: {str(e)}"))
            return False, book_title
    
    def category_extraction_completed_with_stats(self, total_extracted):
        """إنهاء عملية استخراج الأقسام مع الإحصائيات"""
        self.is_running = False
        self.start_extraction_btn.configure(state=tk.NORMAL)
        self.stop_category_btn.configure(state=tk.DISABLED)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text=f"✅ تم إنهاء الاستخراج - {total_extracted} كتاب")
        
        messagebox.showinfo("تم الإنهاء", f"تم إنهاء عملية استخراج الأقسام بنجاح\n\nإجمالي الكتب المستخرجة: {total_extracted}")
        
        # تسجيل الإحصائيات النهائية
        self.log_message(f"📊 إحصائيات نهائية: تم استخراج {total_extracted} كتاب بنجاح")
    
    def add_book_to_list(self, book_id, title, status):
        """إضافة كتاب لقائمة الكتب"""
        self.books_tree.insert("", "end", values=(book_id, title, status))
        self.books_tree.see(self.books_tree.get_children()[-1])
        
        # تحديث عداد الكتب
        book_count = len(self.books_tree.get_children())
        self.books_counter_label.configure(text=f"عدد الكتب: {book_count}")
    
    def update_book_status(self, book_id, title, status):
        """تحديث حالة كتاب في القائمة"""
        for item in self.books_tree.get_children():
            values = self.books_tree.item(item, 'values')
            if values[0] == str(book_id):
                self.books_tree.item(item, values=(book_id, title, status))
                break
    
    def category_extraction_completed(self):
        """إنهاء عملية استخراج الأقسام"""
        self.is_running = False
        self.start_extraction_btn.configure(state=tk.NORMAL)
        self.stop_category_btn.configure(state=tk.DISABLED)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="✅ تم إنهاء استخراج الأقسام")
        
        messagebox.showinfo("تم الإنهاء", "تم إنهاء عملية استخراج الأقسام بنجاح")
    
    def category_extraction_error(self, error_msg):
        """معالجة خطأ في استخراج الأقسام"""
        self.is_running = False
        self.start_extraction_btn.configure(state=tk.NORMAL)
        self.stop_category_btn.configure(state=tk.DISABLED)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="❌ خطأ في استخراج الأقسام")
        
        self.log_message(error_msg)
        messagebox.showerror("خطأ", error_msg)
    
    def clear_books_list(self):
        """مسح قائمة الكتب"""
        for item in self.books_tree.get_children():
            self.books_tree.delete(item)
        
        # إعادة تعيين عداد الكتب
        self.books_counter_label.configure(text="عدد الكتب: 0")
    
    def export_books_list(self):
        """تصدير قائمة الكتب"""
        try:
            import csv
            from tkinter import filedialog
            
            # اختيار مكان الحفظ
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="حفظ قائمة الكتب"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(["رقم الكتاب", "العنوان", "الحالة"])
                    
                    for item in self.books_tree.get_children():
                        values = self.books_tree.item(item, 'values')
                        writer.writerow(values)
                
                messagebox.showinfo("تم الحفظ", f"تم حفظ قائمة الكتب في:\n{filename}")
        except Exception as e:
            messagebox.showerror("خطأ", f"خطأ في حفظ الملف: {str(e)}")
    
    def validate_database_settings(self):
        """التحقق من صحة إعدادات قاعدة البيانات"""
        if not self.db_host_var.get().strip():
            messagebox.showerror("خطأ", "يرجى إدخال عنوان الخادم")
            return False
        if not self.db_user_var.get().strip():
            messagebox.showerror("خطأ", "يرجى إدخال اسم المستخدم")
            return False
        if not self.db_name_var.get().strip():
            messagebox.showerror("خطأ", "يرجى إدخال اسم قاعدة البيانات")
            return False
        return True
    
    def extraction_completed(self, success):
        """معالجة انتهاء الاستخراج"""
        self.is_running = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.shared_progress_bar.stop()
        
        if success:
            self.shared_status_label.configure(text="تم الاستخراج بنجاح! ✅", style='Success.TLabel')
            self.log_message("🎉 تم الانتهاء من الاستخراج بنجاح!")
            messagebox.showinfo("نجح الاستخراج", "تم استخراج الكتاب بنجاح!")
        else:
            self.shared_status_label.configure(text="فشل الاستخراج ❌", style='Error.TLabel')
            self.log_message("❌ فشل في عملية الاستخراج")
            messagebox.showerror("فشل الاستخراج", "حدث خطأ أثناء الاستخراج")
    
    def database_operation_completed(self, success, operation_type):
        """معالجة انتهاء عملية قاعدة البيانات"""
        self.is_running = False
        self.shared_progress_bar.stop()
        
        # إعادة تفعيل الأزرار المناسبة
        if operation_type == "upload":
            self.upload_btn.configure(state=tk.NORMAL)
        elif operation_type == "create_tables":
            self.create_tables_btn.configure(state=tk.NORMAL)
        elif operation_type == "stats":
            self.show_stats_btn.configure(state=tk.NORMAL)
        
        if success:
            self.shared_status_label.configure(text="تمت العملية بنجاح! ✅", style='Success.TLabel')
            self.log_message("🎉 تمت عملية قاعدة البيانات بنجاح!")
            
            operation_names = {
                "upload": "رفع البيانات",
                "create_tables": "إنشاء الجداول",
                "stats": "عرض الإحصائيات"
            }
            messagebox.showinfo("نجحت العملية", f"تمت عملية {operation_names.get(operation_type, 'قاعدة البيانات')} بنجاح!")
        else:
            self.shared_status_label.configure(text="فشلت العملية ❌", style='Error.TLabel')
            self.log_message("❌ فشلت عملية قاعدة البيانات")
            messagebox.showerror("فشلت العملية", "حدث خطأ أثناء تنفيذ العملية")
    
    def extraction_error(self, error_msg):
        """معالجة أخطاء الاستخراج"""
        self.is_running = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="خطأ في الاستخراج ❌", style='Error.TLabel')
        self.log_message(f"❌ خطأ: {error_msg}")
        messagebox.showerror("خطأ", f"حدث خطأ في الاستخراج:\n{error_msg}")
    
    def database_operation_error(self, error_msg, operation_type):
        """معالجة أخطاء عمليات قاعدة البيانات"""
        self.is_running = False
        self.shared_progress_bar.stop()
        
        # إعادة تفعيل الأزرار المناسبة
        if operation_type == "upload":
            self.upload_btn.configure(state=tk.NORMAL)
        elif operation_type == "create_tables":
            self.create_tables_btn.configure(state=tk.NORMAL)
        elif operation_type == "stats":
            self.show_stats_btn.configure(state=tk.NORMAL)
        
        self.shared_status_label.configure(text="خطأ في العملية ❌", style='Error.TLabel')
        self.log_message(f"❌ خطأ: {error_msg}")
        messagebox.showerror("خطأ", f"حدث خطأ في العملية:\n{error_msg}")
    
    def operation_stopped(self):
        """معالجة إيقاف العملية"""
        self.is_running = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.upload_btn.configure(state=tk.NORMAL)
        self.upload_multiple_btn.configure(state=tk.NORMAL)
        self.scan_files_btn.configure(state=tk.NORMAL)
        self.create_tables_btn.configure(state=tk.NORMAL)
        self.show_stats_btn.configure(state=tk.NORMAL)
        self.start_extraction_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.stop_category_btn.configure(state=tk.DISABLED)
        self.shared_progress_bar.stop()
        self.shared_status_label.configure(text="تم إيقاف العملية", style='Warning.TLabel')

def main():
    """الوظيفة الرئيسية"""
    root = tk.Tk()
    app = EnhancedRunnerGUI(root)
    
    # إعداد إغلاق التطبيق
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("إنهاء التطبيق", "هناك عملية جارية. هل تريد إنهاء التطبيق؟"):
                if app.current_process:
                    app.current_process.terminate()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # بدء التطبيق
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
