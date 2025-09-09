#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Category Book Extractor - مستخرج كتب الأقسام
استخراج جميع كتب قسم معين من موقع الشاملة
"""

import requests
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class CategoryExtractor:
    """مستخرج كتب الأقسام من موقع الشاملة"""
    
    def __init__(self):
        self.base_url = "https://shamela.ws"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def extract_category_books(self, category_id, progress_callback=None):
        """
        استخراج جميع كتب قسم معين
        
        Args:
            category_id (int): رقم القسم
            progress_callback (function): دالة لتحديث التقدم
            
        Returns:
            dict: قاموس يحتوي على معلومات الكتب
        """
        try:
            category_url = f"{self.base_url}/category/{category_id}"
            
            if progress_callback:
                progress_callback(f"🔗 جاري الاتصال بقسم رقم {category_id}...")
            
            response = self.session.get(category_url, timeout=30)
            response.raise_for_status()
            
            if progress_callback:
                progress_callback("📄 جاري تحليل محتوى الصفحة...")
            
            # استخراج أرقام الكتب من الروابط
            book_pattern = r'https://shamela\.ws/book/(\d+)'
            book_ids = re.findall(book_pattern, response.text)
            
            # إزالة التكرارات والتأكد من أن القائمة فريدة
            unique_book_ids = list(dict.fromkeys(book_ids))
            
            if not unique_book_ids:
                if progress_callback:
                    progress_callback(f"❌ لم يتم العثور على كتب في القسم {category_id}")
                return {
                    'category_id': category_id,
                    'category_name': 'غير معروف',
                    'books_count': 0,
                    'book_ids': [],
                    'status': 'no_books_found'
                }
            
            # استخراج اسم القسم من عنوان الصفحة
            category_name = self._extract_category_name(response.text)
            
            if progress_callback:
                progress_callback(f"✅ تم العثور على {len(unique_book_ids)} كتاب في قسم '{category_name}'")
            
            return {
                'category_id': category_id,
                'category_name': category_name,
                'books_count': len(unique_book_ids),
                'book_ids': [int(book_id) for book_id in unique_book_ids],
                'status': 'success'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ خطأ في الاتصال: {str(e)}"
            if progress_callback:
                progress_callback(error_msg)
            return {
                'category_id': category_id,
                'category_name': 'خطأ',
                'books_count': 0,
                'book_ids': [],
                'status': 'connection_error',
                'error': str(e)
            }
        except Exception as e:
            error_msg = f"❌ خطأ غير متوقع: {str(e)}"
            if progress_callback:
                progress_callback(error_msg)
            return {
                'category_id': category_id,
                'category_name': 'خطأ',
                'books_count': 0,
                'book_ids': [],
                'status': 'error',
                'error': str(e)
            }
    
    def _extract_category_name(self, html_content):
        """استخراج اسم القسم من محتوى HTML"""
        try:
            # البحث عن العنوان في الصفحة
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # محاولة العثور على عنوان القسم
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text().strip()
                # استخراج اسم القسم من العنوان
                if '|' in title_text:
                    category_name = title_text.split('|')[0].strip()
                else:
                    category_name = title_text.replace('المكتبة الشاملة', '').strip()
                return category_name if category_name else 'قسم غير معروف'
            
            # محاولة أخرى للبحث عن العنوان في h1
            h1_tag = soup.find('h1')
            if h1_tag:
                return h1_tag.get_text().strip()
            
            return 'قسم غير معروف'
            
        except Exception:
            return 'قسم غير معروف'
    
    def extract_multiple_categories(self, category_ids, progress_callback=None):
        """
        استخراج كتب عدة أقسام
        
        Args:
            category_ids (list): قائمة أرقام الأقسام
            progress_callback (function): دالة لتحديث التقدم
            
        Returns:
            list: قائمة بمعلومات جميع الأقسام
        """
        results = []
        total_categories = len(category_ids)
        
        for i, category_id in enumerate(category_ids, 1):
            if progress_callback:
                progress_callback(f"📚 معالجة القسم {i}/{total_categories}: رقم {category_id}")
            
            result = self.extract_category_books(category_id, progress_callback)
            results.append(result)
            
            # توقف قصير بين الطلبات لتجنب الحظر
            if i < total_categories:
                time.sleep(1)
        
        return results

def test_category_extractor():
    """اختبار مستخرج أقسام الكتب"""
    extractor = CategoryExtractor()
    
    def progress_print(message):
        print(message)
    
    # اختبار قسم العقيدة (رقم 1)
    result = extractor.extract_category_books(1, progress_print)
    
    print("\n📊 نتائج الاستخراج:")
    print(f"رقم القسم: {result['category_id']}")
    print(f"اسم القسم: {result['category_name']}")
    print(f"عدد الكتب: {result['books_count']}")
    print(f"الحالة: {result['status']}")
    
    if result['book_ids']:
        print(f"أول 10 كتب: {result['book_ids'][:10]}")

if __name__ == "__main__":
    test_category_extractor()
