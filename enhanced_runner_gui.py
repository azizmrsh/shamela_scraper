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

# إضافة المجلد الحالي للـ path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

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
        
        # متغيرات قاعدة البيانات
        self.db_host_var = tk.StringVar(value="srv1800.hstgr.io")
        self.db_port_var = tk.StringVar(value="3306")
        self.db_user_var = tk.StringVar(value="u994369532_test")
        self.db_password_var = tk.StringVar(value="Test20205")
        self.db_name_var = tk.StringVar(value="u994369532_test")
        
        # متغيرات التحكم
        self.operation_var = tk.StringVar(value="extract")
        self.progress_var = tk.DoubleVar()
        
    def setup_styles(self):
        """إعداد أنماط الواجهة"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # أنماط مخصصة
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), foreground='#2c3e50')
        style.configure('Heading.TLabel', font=('Arial', 10, 'bold'), foreground='#34495e')
        style.configure('Success.TLabel', foreground='#27ae60')
        style.configure('Error.TLabel', foreground='#e74c3c')
        style.configure('Warning.TLabel', foreground='#f39c12')
        style.configure('Accent.TButton', font=('Arial', 9, 'bold'))
        
    def create_widgets(self):
        """إنشاء عناصر الواجهة"""
        # إنشاء النوافذ المبوبة
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # التبويبات
        self.create_extract_tab()
        self.create_database_tab()
        self.create_management_tab()
        self.create_logs_tab()
        
        # شريط الحالة
        self.create_status_bar()
        
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
        
        # شريط التقدم
        self.create_progress_section(extract_frame)
        
    def create_database_tab(self):
        """إنشاء تبويب قاعدة البيانات"""
        db_frame = ttk.Frame(self.notebook)
        self.notebook.add(db_frame, text="🗄️ قاعدة البيانات")
        
        # عنوان رئيسي
        title_label = ttk.Label(db_frame, text="🗄️ إدارة قاعدة البيانات", style='Title.TLabel')
        title_label.pack(pady=(10, 20))
        
        # إطار رفع الملفات
        upload_frame = ttk.LabelFrame(db_frame, text="📤 رفع ملف JSON إلى قاعدة البيانات", padding="10")
        upload_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # اختيار ملف JSON
        ttk.Label(upload_frame, text="ملف JSON:", style='Heading.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        json_entry = ttk.Entry(upload_frame, textvariable=self.json_file_var, width=50, font=('Arial', 9))
        json_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        browse_json_btn = ttk.Button(upload_frame, text="تصفح", command=self.browse_json_file)
        browse_json_btn.grid(row=0, column=2, sticky=tk.W)
        
        upload_frame.columnconfigure(1, weight=1)
        
        # أزرار قاعدة البيانات
        db_control_frame = ttk.Frame(upload_frame)
        db_control_frame.grid(row=1, column=0, columnspan=3, pady=(15, 0))
        
        self.upload_btn = ttk.Button(db_control_frame, text="📤 رفع إلى قاعدة البيانات", 
                                    command=self.upload_to_database, style='Accent.TButton')
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.create_tables_btn = ttk.Button(db_control_frame, text="🏗️ إنشاء الجداول", 
                                           command=self.create_database_tables)
        self.create_tables_btn.pack(side=tk.LEFT, padx=(0, 10))
        
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
        
    def create_logs_tab(self):
        """إنشاء تبويب السجلات"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="📋 السجلات والمخرجات")
        
        # عنوان رئيسي
        title_label = ttk.Label(logs_frame, text="📋 سجلات العمليات والمخرجات", style='Title.TLabel')
        title_label.pack(pady=(10, 10))
        
        # إطار التحكم في السجلات
        logs_control_frame = ttk.Frame(logs_frame)
        logs_control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(logs_control_frame, text="🔄 تحديث", command=self.refresh_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(logs_control_frame, text="🗑️ مسح السجل", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(logs_control_frame, text="💾 حفظ السجل", command=self.save_logs).pack(side=tk.LEFT)
        
        # منطقة عرض السجلات
        self.logs_text = scrolledtext.ScrolledText(logs_frame, height=25, font=('Consolas', 9))
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
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
        ttk.Label(db_frame, text="كلمة المرور:", style='Heading.TLabel').grid(
            row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(10, 0))
        password_entry = ttk.Entry(db_frame, textvariable=self.db_password_var, show="*", width=20)
        password_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 20), pady=(10, 0))
        
        # زر اختبار الاتصال
        test_btn = ttk.Button(db_frame, text="🔌 اختبار الاتصال", command=self.test_database_connection)
        test_btn.grid(row=2, column=2, columnspan=2, sticky=tk.W, pady=(10, 0))
        
    def create_progress_section(self, parent):
        """إنشاء قسم شريط التقدم"""
        progress_frame = ttk.LabelFrame(parent, text="📊 تقدم العملية", padding="10")
        progress_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # شريط التقدم
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # تسميات الحالة
        status_frame = ttk.Frame(progress_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="جاهز للبدء", style='Heading.TLabel')
        self.status_label.pack(side=tk.LEFT)
        
        self.time_label = ttk.Label(status_frame, text="", style='Heading.TLabel')
        self.time_label.pack(side=tk.RIGHT)
        
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
    
    def browse_json_file(self):
        """تصفح ملف JSON"""
        file_path = filedialog.askopenfilename(
            title="اختر ملف JSON",
            filetypes=[("JSON files", "*.json"), ("Compressed JSON", "*.json.gz"), ("All files", "*.*")]
        )
        if file_path:
            self.json_file_var.set(file_path)
    
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
        self.status_label.configure(text="جاري الاستخراج...", style='Success.TLabel')
        self.progress_bar.start()
        
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
                "--db-password", self.db_password_var.get(),
                "--db-name", self.db_name_var.get()
            ])
        
        return command
    
    def run_extraction(self, command):
        """تشغيل عملية الاستخراج"""
        try:
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                cwd=current_dir
            )
            
            # قراءة المخرجات
            while True:
                output = self.current_process.stdout.readline()
                if output == '' and self.current_process.poll() is not None:
                    break
                if output:
                    self.log_message(output.strip())
            
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
            "--db-password", self.db_password_var.get(),
            "--db-name", self.db_name_var.get()
        ]
        
        # تحديث الواجهة
        self.is_running = True
        self.upload_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="جاري الرفع...", style='Success.TLabel')
        self.progress_bar.start()
        
        # تشغيل العملية
        threading.Thread(target=self.run_database_operation, args=(command, "upload")).start()
    
    def create_database_tables(self):
        """إنشاء جداول قاعدة البيانات"""
        command = [
            "python", "enhanced_runner.py", "create-tables",
            "--db-host", self.db_host_var.get(),
            "--db-port", self.db_port_var.get(),
            "--db-user", self.db_user_var.get(),
            "--db-password", self.db_password_var.get(),
            "--db-name", self.db_name_var.get()
        ]
        
        # تحديث الواجهة
        self.is_running = True
        self.create_tables_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="جاري إنشاء الجداول...", style='Success.TLabel')
        self.progress_bar.start()
        
        # تشغيل العملية
        threading.Thread(target=self.run_database_operation, args=(command, "create_tables")).start()
    
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
            "--db-password", self.db_password_var.get(),
            "--db-name", self.db_name_var.get()
        ]
        
        # تحديث الواجهة
        self.is_running = True
        self.show_stats_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="جاري جلب الإحصائيات...", style='Success.TLabel')
        self.progress_bar.start()
        
        # تشغيل العملية
        threading.Thread(target=self.run_database_operation, args=(command, "stats")).start()
    
    def run_database_operation(self, command, operation_type):
        """تشغيل عملية قاعدة البيانات"""
        try:
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                cwd=current_dir
            )
            
            # قراءة المخرجات
            while True:
                output = self.current_process.stdout.readline()
                if output == '' and self.current_process.poll() is not None:
                    break
                if output:
                    self.log_message(output.strip())
            
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
            
            connection = mysql.connector.connect(
                host=self.db_host_var.get(),
                port=int(self.db_port_var.get()),
                user=self.db_user_var.get(),
                password=self.db_password_var.get(),
                database=self.db_name_var.get()
            )
            
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
    
    def log_message(self, message):
        """إضافة رسالة للسجل"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.logs_text.insert(tk.END, formatted_message)
        self.logs_text.see(tk.END)
        
        # تحديث شريط الحالة
        self.status_text.configure(text=message[:100])
    
    def monitor_progress(self):
        """مراقبة التقدم"""
        if self.is_running:
            elapsed = time.time() - self.start_time
            elapsed_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            self.time_label.configure(text=f"الوقت المنقضي: {elapsed_str}")
            
            # جدولة التحديث التالي
            self.root.after(1000, self.monitor_progress)
    
    def extraction_completed(self, success):
        """معالجة انتهاء الاستخراج"""
        self.is_running = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress_bar.stop()
        
        if success:
            self.status_label.configure(text="تم الاستخراج بنجاح! ✅", style='Success.TLabel')
            self.log_message("🎉 تم الانتهاء من الاستخراج بنجاح!")
            messagebox.showinfo("نجح الاستخراج", "تم استخراج الكتاب بنجاح!")
        else:
            self.status_label.configure(text="فشل الاستخراج ❌", style='Error.TLabel')
            self.log_message("❌ فشل في عملية الاستخراج")
            messagebox.showerror("فشل الاستخراج", "حدث خطأ أثناء الاستخراج")
    
    def database_operation_completed(self, success, operation_type):
        """معالجة انتهاء عملية قاعدة البيانات"""
        self.is_running = False
        self.progress_bar.stop()
        
        # إعادة تفعيل الأزرار المناسبة
        if operation_type == "upload":
            self.upload_btn.configure(state=tk.NORMAL)
        elif operation_type == "create_tables":
            self.create_tables_btn.configure(state=tk.NORMAL)
        elif operation_type == "stats":
            self.show_stats_btn.configure(state=tk.NORMAL)
        
        if success:
            self.status_label.configure(text="تمت العملية بنجاح! ✅", style='Success.TLabel')
            self.log_message("🎉 تمت عملية قاعدة البيانات بنجاح!")
            
            operation_names = {
                "upload": "رفع البيانات",
                "create_tables": "إنشاء الجداول",
                "stats": "عرض الإحصائيات"
            }
            messagebox.showinfo("نجحت العملية", f"تمت عملية {operation_names.get(operation_type, 'قاعدة البيانات')} بنجاح!")
        else:
            self.status_label.configure(text="فشلت العملية ❌", style='Error.TLabel')
            self.log_message("❌ فشلت عملية قاعدة البيانات")
            messagebox.showerror("فشلت العملية", "حدث خطأ أثناء تنفيذ العملية")
    
    def extraction_error(self, error_msg):
        """معالجة أخطاء الاستخراج"""
        self.is_running = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress_bar.stop()
        self.status_label.configure(text="خطأ في الاستخراج ❌", style='Error.TLabel')
        self.log_message(f"❌ خطأ: {error_msg}")
        messagebox.showerror("خطأ", f"حدث خطأ في الاستخراج:\n{error_msg}")
    
    def database_operation_error(self, error_msg, operation_type):
        """معالجة أخطاء عمليات قاعدة البيانات"""
        self.is_running = False
        self.progress_bar.stop()
        
        # إعادة تفعيل الأزرار المناسبة
        if operation_type == "upload":
            self.upload_btn.configure(state=tk.NORMAL)
        elif operation_type == "create_tables":
            self.create_tables_btn.configure(state=tk.NORMAL)
        elif operation_type == "stats":
            self.show_stats_btn.configure(state=tk.NORMAL)
        
        self.status_label.configure(text="خطأ في العملية ❌", style='Error.TLabel')
        self.log_message(f"❌ خطأ: {error_msg}")
        messagebox.showerror("خطأ", f"حدث خطأ في العملية:\n{error_msg}")
    
    def operation_stopped(self):
        """معالجة إيقاف العملية"""
        self.is_running = False
        self.extract_btn.configure(state=tk.NORMAL)
        self.upload_btn.configure(state=tk.NORMAL)
        self.create_tables_btn.configure(state=tk.NORMAL)
        self.show_stats_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.progress_bar.stop()
        self.status_label.configure(text="تم إيقاف العملية", style='Warning.TLabel')

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
