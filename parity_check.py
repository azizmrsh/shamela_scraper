# -*- coding: utf-8 -*-
"""
Parity Check - فحص تطابق النتائج
يقارن نتائج النسخة المحسنة مع الأصلية للتأكد من عدم تغيير المنطق

التحقق من:
- نفس عدد الصفحات/الفصول/المجلدات/المؤلفين
- نفس محتوى كل صفحة (hash)
- نفس page_number و internal_index
- نفس بيانات الكتاب الأساسية
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
import argparse
import sys
import os

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    print("تحتاج لتثبيت mysql-connector-python:")
    print("pip install mysql-connector-python")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParityChecker:
    """فاحص التطابق للنتائج"""
    
    def __init__(self, baseline_db_config: Dict[str, Any], optimized_db_config: Dict[str, Any]):
        self.baseline_config = baseline_db_config
        self.optimized_config = optimized_db_config
        self.baseline_conn = None
        self.optimized_conn = None
        
    def connect_databases(self):
        """الاتصال بقواعد البيانات"""
        try:
            self.baseline_conn = mysql.connector.connect(**self.baseline_config)
            self.optimized_conn = mysql.connector.connect(**self.optimized_config)
            logger.info("تم الاتصال بقواعد البيانات بنجاح")
        except Error as e:
            logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
            raise
            
    def disconnect_databases(self):
        """قطع الاتصال بقواعد البيانات"""
        if self.baseline_conn:
            self.baseline_conn.close()
        if self.optimized_conn:
            self.optimized_conn.close()
    
    def get_book_counts(self, connection, book_id: int) -> Dict[str, int]:
        """جلب أعداد العناصر لكتاب معين"""
        cursor = connection.cursor(dictionary=True)
        
        counts = {}
        
        # عدد الصفحات
        cursor.execute("SELECT COUNT(*) as count FROM pages WHERE book_id = %s", (book_id,))
        counts['pages'] = cursor.fetchone()['count']
        
        # عدد الفصول
        cursor.execute("SELECT COUNT(*) as count FROM chapters WHERE book_id = %s", (book_id,))
        counts['chapters'] = cursor.fetchone()['count']
        
        # عدد المجلدات
        cursor.execute("SELECT COUNT(*) as count FROM volumes WHERE book_id = %s", (book_id,))
        counts['volumes'] = cursor.fetchone()['count']
        
        # عدد المؤلفين
        cursor.execute("SELECT COUNT(*) as count FROM author_book WHERE book_id = %s", (book_id,))
        counts['authors'] = cursor.fetchone()['count']
        
        # عدد روابط المجلدات
        cursor.execute("SELECT COUNT(*) as count FROM volume_links WHERE book_id = %s", (book_id,))
        counts['volume_links'] = cursor.fetchone()['count']
        
        # مجموع الكلمات
        cursor.execute("SELECT SUM(COALESCE(word_count, 0)) as total_words FROM pages WHERE book_id = %s", (book_id,))
        result = cursor.fetchone()
        counts['total_words'] = result['total_words'] or 0
        
        cursor.close()
        return counts
    
    def get_pages_data(self, connection, book_id: int) -> List[Dict[str, Any]]:
        """جلب بيانات الصفحات مع hash للمحتوى"""
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                page_number,
                internal_index,
                content,
                COALESCE(html_content, '') as html_content,
                word_count,
                volume_number,
                original_page_number
            FROM pages 
            WHERE book_id = %s 
            ORDER BY internal_index
        """
        
        cursor.execute(query, (book_id,))
        pages = cursor.fetchall()
        
        # حساب hash للمحتوى
        for page in pages:
            content_hash = hashlib.sha256(
                (page['content'] or '').encode('utf-8')
            ).hexdigest()
            html_hash = hashlib.sha256(
                (page['html_content'] or '').encode('utf-8')
            ).hexdigest()
            
            page['content_hash'] = content_hash
            page['html_hash'] = html_hash
        
        cursor.close()
        return pages
    
    def get_book_metadata(self, connection, book_id: int) -> Dict[str, Any]:
        """جلب بيانات الكتاب الأساسية"""
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT 
                title,
                shamela_id,
                edition,
                edition_number,
                publication_year,
                edition_date_hijri,
                has_original_pagination,
                language,
                status
            FROM books 
            WHERE id = %s
        """
        
        cursor.execute(query, (book_id,))
        result = cursor.fetchone()
        cursor.close()
        return result or {}
    
    def compare_counts(self, baseline_counts: Dict[str, int], 
                      optimized_counts: Dict[str, int]) -> List[str]:
        """مقارنة الأعداد"""
        differences = []
        
        for key, baseline_value in baseline_counts.items():
            optimized_value = optimized_counts.get(key, 0)
            if baseline_value != optimized_value:
                differences.append(
                    f"{key}: baseline={baseline_value}, optimized={optimized_value}"
                )
        
        return differences
    
    def compare_pages(self, baseline_pages: List[Dict[str, Any]], 
                     optimized_pages: List[Dict[str, Any]]) -> List[str]:
        """مقارنة الصفحات"""
        differences = []
        
        if len(baseline_pages) != len(optimized_pages):
            differences.append(
                f"عدد الصفحات: baseline={len(baseline_pages)}, optimized={len(optimized_pages)}"
            )
            return differences
        
        for i, (baseline_page, optimized_page) in enumerate(zip(baseline_pages, optimized_pages)):
            page_num = baseline_page['page_number']
            
            # مقارنة الحقول الأساسية
            if baseline_page['page_number'] != optimized_page['page_number']:
                differences.append(
                    f"صفحة {i}: page_number مختلف - baseline={baseline_page['page_number']}, optimized={optimized_page['page_number']}"
                )
            
            if baseline_page['internal_index'] != optimized_page['internal_index']:
                differences.append(
                    f"صفحة {page_num}: internal_index مختلف - baseline={baseline_page['internal_index']}, optimized={optimized_page['internal_index']}"
                )
            
            # مقارنة hash المحتوى
            if baseline_page['content_hash'] != optimized_page['content_hash']:
                differences.append(
                    f"صفحة {page_num}: محتوى مختلف (content hash مختلف)"
                )
            
            if baseline_page['html_hash'] != optimized_page['html_hash']:
                differences.append(
                    f"صفحة {page_num}: HTML مختلف (html hash مختلف)"
                )
            
            # مقارنة الحقول الإضافية
            for field in ['word_count', 'volume_number', 'original_page_number']:
                if baseline_page[field] != optimized_page[field]:
                    differences.append(
                        f"صفحة {page_num}: {field} مختلف - baseline={baseline_page[field]}, optimized={optimized_page[field]}"
                    )
        
        return differences
    
    def compare_metadata(self, baseline_meta: Dict[str, Any], 
                        optimized_meta: Dict[str, Any]) -> List[str]:
        """مقارنة بيانات الكتاب الأساسية"""
        differences = []
        
        fields_to_compare = [
            'title', 'shamela_id', 'edition', 'edition_number', 
            'publication_year', 'edition_date_hijri', 'has_original_pagination',
            'language', 'status'
        ]
        
        for field in fields_to_compare:
            baseline_value = baseline_meta.get(field)
            optimized_value = optimized_meta.get(field)
            
            if baseline_value != optimized_value:
                differences.append(
                    f"{field}: baseline='{baseline_value}', optimized='{optimized_value}'"
                )
        
        return differences
    
    def check_book_parity(self, book_id: int) -> Dict[str, Any]:
        """فحص تطابق كتاب محدد"""
        logger.info(f"فحص تطابق الكتاب {book_id}...")
        
        try:
            self.connect_databases()
            
            # جلب الأعداد
            baseline_counts = self.get_book_counts(self.baseline_conn, book_id)
            optimized_counts = self.get_book_counts(self.optimized_conn, book_id)
            
            # جلب الصفحات
            baseline_pages = self.get_pages_data(self.baseline_conn, book_id)
            optimized_pages = self.get_pages_data(self.optimized_conn, book_id)
            
            # جلب بيانات الكتاب
            baseline_meta = self.get_book_metadata(self.baseline_conn, book_id)
            optimized_meta = self.get_book_metadata(self.optimized_conn, book_id)
            
            # مقارنة البيانات
            count_diffs = self.compare_counts(baseline_counts, optimized_counts)
            page_diffs = self.compare_pages(baseline_pages, optimized_pages)
            meta_diffs = self.compare_metadata(baseline_meta, optimized_meta)
            
            all_differences = count_diffs + page_diffs + meta_diffs
            
            result = {
                'book_id': book_id,
                'baseline_counts': baseline_counts,
                'optimized_counts': optimized_counts,
                'total_differences': len(all_differences),
                'differences': all_differences,
                'is_identical': len(all_differences) == 0
            }
            
            return result
            
        finally:
            self.disconnect_databases()
    
    def print_parity_report(self, result: Dict[str, Any]):
        """طباعة تقرير التطابق"""
        print("=" * 60)
        print(f"تقرير فحص التطابق - كتاب {result['book_id']}")
        print("=" * 60)
        
        if result['is_identical']:
            print("✅ النتائج متطابقة تماماً - 0 اختلافات")
        else:
            print(f"❌ وجدت {result['total_differences']} اختلافات")
        
        print("\nالأعداد:")
        print("-" * 30)
        for key in result['baseline_counts']:
            baseline = result['baseline_counts'][key]
            optimized = result['optimized_counts'][key]
            status = "✅" if baseline == optimized else "❌"
            print(f"{status} {key}: baseline={baseline}, optimized={optimized}")
        
        if result['differences']:
            print("\nالاختلافات المفصلة:")
            print("-" * 30)
            for diff in result['differences'][:10]:  # أول 10 اختلافات فقط
                print(f"• {diff}")
            
            if len(result['differences']) > 10:
                print(f"... و {len(result['differences']) - 10} اختلافات أخرى")
        
        print("\n" + "=" * 60)
        
        return result['is_identical']

def main():
    parser = argparse.ArgumentParser(description='فحص تطابق النتائج بين النسخة الأصلية والمحسنة')
    parser.add_argument('--book-id', type=int, required=True, help='معرف الكتاب للفحص')
    parser.add_argument('--baseline-host', default='localhost', help='خادم قاعدة البيانات الأصلية')
    parser.add_argument('--baseline-db', required=True, help='اسم قاعدة البيانات الأصلية')
    parser.add_argument('--baseline-user', required=True, help='مستخدم قاعدة البيانات الأصلية')
    parser.add_argument('--baseline-password', required=True, help='كلمة المرور الأصلية')
    parser.add_argument('--optimized-host', default='localhost', help='خادم قاعدة البيانات المحسنة')
    parser.add_argument('--optimized-db', required=True, help='اسم قاعدة البيانات المحسنة')
    parser.add_argument('--optimized-user', required=True, help='مستخدم قاعدة البيانات المحسنة')
    parser.add_argument('--optimized-password', required=True, help='كلمة المرور المحسنة')
    
    args = parser.parse_args()
    
    baseline_config = {
        'host': args.baseline_host,
        'database': args.baseline_db,
        'user': args.baseline_user,
        'password': args.baseline_password,
        'charset': 'utf8mb4',
        'use_unicode': True
    }
    
    optimized_config = {
        'host': args.optimized_host,
        'database': args.optimized_db,
        'user': args.optimized_user,
        'password': args.optimized_password,
        'charset': 'utf8mb4',
        'use_unicode': True
    }
    
    checker = ParityChecker(baseline_config, optimized_config)
    
    try:
        result = checker.check_book_parity(args.book_id)
        is_identical = checker.print_parity_report(result)
        
        sys.exit(0 if is_identical else 1)
        
    except Exception as e:
        logger.error(f"فشل فحص التطابق: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
