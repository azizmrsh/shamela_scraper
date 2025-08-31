# -*- coding: utf-8 -*-
"""
Enhanced Shamela Database Manager - مدير قاعدة بيانات محسن للكتب المستخرجة من الشاملة
يدعم الميزات الجديدة والجداول المحسنة

الميزات الجديدة:
- جدول الناشرين المنفصل
- جدول أقسام الكتب
- دعم الترقيم الأصلي للصفحات
- دعم روابط المجلدات
- ترتيب الفصول المحسن
- دعم التواريخ الهجرية

تحسينات الأداء:
- دعم العمليات المجمعة (batch operations)
- تحسين الاستعلامات مع فهارس محسنة
- تجمع الاتصالات (connection pooling)
- تحسين معاملات قاعدة البيانات
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor

try:
    import mysql.connector
    from mysql.connector import Error
    from mysql.connector.pooling import MySQLConnectionPool
except ImportError:
    print("تحتاج لتثبيت mysql-connector-python:")
    print("pip install mysql-connector-python")
    exit(1)

import sys
import os
sys.path.append(os.path.dirname(__file__))
from enhanced_shamela_scraper import (
    Book, Author, Publisher, BookSection, Volume, 
    Chapter, PageContent, VolumeLink, PerformanceConfig
)

logger = logging.getLogger(__name__)

class EnhancedShamelaDatabaseManager:
    """مدير قاعدة البيانات المحسن للكتب المستخرجة من الشاملة"""
    
    def __init__(self, db_config: Dict[str, Any], performance_config: PerformanceConfig = None):
        """
        إنشاء مدير قاعدة البيانات المحسن
        
        Args:
            db_config: إعدادات قاعدة البيانات
            performance_config: إعدادات الأداء
        """
        self.config = db_config
        self.performance_config = performance_config or PerformanceConfig()
        self.connection = None
        self.cursor = None
        
        # تجمع الاتصالات للعمليات المتوازية
        if self.performance_config.max_workers > 1:
            pool_config = db_config.copy()
            pool_config['pool_name'] = 'enhanced_shamela_pool'
            pool_config['pool_size'] = min(self.performance_config.max_workers + 2, 10)
            pool_config['pool_reset_session'] = True
            
            try:
                self.connection_pool = MySQLConnectionPool(**pool_config)
                logger.info(f"تم إنشاء تجمع اتصالات بحجم {pool_config['pool_size']}")
            except Error as e:
                logger.warning(f"فشل في إنشاء تجمع الاتصالات: {e}")
                self.connection_pool = None
        else:
            self.connection_pool = None
        
        # أسماء الجداول المحسنة
        self.tables = {
            'books': 'books',
            'authors': 'authors', 
            'publishers': 'publishers',
            'book_sections': 'book_sections',
            'author_book': 'author_book',
            'volumes': 'volumes',
            'chapters': 'chapters',
            'pages': 'pages',
            'volume_links': 'volume_links'
        }
        
        # تخزين مؤقت للكائنات المحفوظة
        self._cached_authors = {}
        self._cached_publishers = {}
        self._cached_sections = {}
    
    def connect(self) -> None:
        """الاتصال بقاعدة البيانات"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database'],
                charset=self.config.get('charset', 'utf8mb4'),
                use_unicode=True,
                autocommit=False
            )
            self.cursor = self.connection.cursor(dictionary=True)
            logger.info("تم الاتصال بقاعدة البيانات المحسنة بنجاح")
        except Error as e:
            logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
            raise
    
    def disconnect(self) -> None:
        """قطع الاتصال بقاعدة البيانات"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("تم قطع الاتصال بقاعدة البيانات")
    
    def close(self) -> None:
        """إغلاق الاتصال بقاعدة البيانات"""
        self.disconnect()
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.connection.rollback()
        self.disconnect()
    
    def execute_query(self, query: str, params: tuple = None) -> Any:
        """تنفيذ استعلام SQL"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.fetchall()
        except Error as e:
            logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
            logger.error(f"الاستعلام: {query}")
            logger.error(f"المعاملات: {params}")
            raise
    
    def execute_batch_insert(self, query: str, data_batch: List[tuple]) -> List[int]:
        """تنفيذ عملية إدراج مجمعة وإرجاع قائمة IDs"""
        if not data_batch:
            return []
        
        try:
            # تقسيم الدفعة إلى أجزاء أصغر إذا لزم الأمر
            batch_size = min(self.performance_config.batch_size, len(data_batch))
            inserted_ids = []
            
            for i in range(0, len(data_batch), batch_size):
                batch = data_batch[i:i + batch_size]
                
                # تنفيذ الدفعة
                self.cursor.executemany(query, batch)
                
                # جمع IDs المدرجة
                first_id = self.cursor.lastrowid
                if first_id:
                    batch_ids = list(range(first_id, first_id + len(batch)))
                    inserted_ids.extend(batch_ids)
            
            logger.debug(f"تم إدراج {len(inserted_ids)} عنصر بدفعات")
            return inserted_ids
            
        except Error as e:
            logger.error(f"خطأ في الإدراج المجمع: {e}")
            logger.error(f"الاستعلام: {query}")
            logger.error(f"عدد العناصر: {len(data_batch)}")
            raise
    
    def get_pooled_connection(self):
        """الحصول على اتصال من التجمع"""
        if self.connection_pool:
            try:
                return self.connection_pool.get_connection()
            except Error as e:
                logger.warning(f"فشل في الحصول على اتصال من التجمع: {e}")
                return None
        return None
    
    def execute_parallel_batch(self, operation_func, data_batches: List[List], max_workers: int = None) -> List[Any]:
        """تنفيذ عمليات مجمعة بشكل متوازي"""
        if not data_batches or not self.connection_pool:
            # تنفيذ تسلسلي إذا لم يتوفر تجمع الاتصالات
            results = []
            for batch in data_batches:
                results.extend(operation_func(batch))
            return results
        
        max_workers = max_workers or min(self.performance_config.max_workers, len(data_batches))
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {
                executor.submit(self._execute_batch_with_pooled_connection, operation_func, batch): batch
                for batch in data_batches
            }
            
            for future in future_to_batch:
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                except Exception as e:
                    logger.error(f"فشل في تنفيذ دفعة متوازية: {e}")
        
        return results
    
    def _execute_batch_with_pooled_connection(self, operation_func, batch):
        """تنفيذ عملية مجمعة باستخدام اتصال من التجمع"""
        connection = self.get_pooled_connection()
        if not connection:
            return []
        
        try:
            # إنشاء مدير مؤقت باتصال من التجمع
            temp_manager = EnhancedShamelaDatabaseManager(self.config, self.performance_config)
            temp_manager.connection = connection
            temp_manager.cursor = connection.cursor(dictionary=True)
            
            results = operation_func(temp_manager, batch)
            connection.commit()
            return results
            
        except Exception as e:
            connection.rollback()
            logger.error(f"خطأ في العملية المجمعة المتوازية: {e}")
            return []
        finally:
            if connection:
                connection.close()
    
    def save_pages_batch(self, pages: List[PageContent], book_id: int, volume_ids: Dict[int, int] = None) -> List[int]:
        """حفظ الصفحات مجمعة للأداء المحسن"""
        if not pages:
            return []
        
        volume_ids = volume_ids or {}
        
        # تحضير البيانات للإدراج المجمع
        pages_data = []
        for page in pages:
            # تحديد الجزء للصفحة
            volume_id = None
            if page.volume_number and page.volume_number in volume_ids:
                volume_id = volume_ids[page.volume_number]
            
            page_data = (
                book_id,
                page.page_number,
                page.internal_index,
                page.content,
                page.html_content,
                page.word_count,
                volume_id,
                None,  # chapter_id - سيتم تحديده لاحقاً
                page.original_page_number,
                page.page_index_internal,
                page.printed_missing,
                datetime.now(),
                datetime.now()
            )
            pages_data.append(page_data)
        
        # تقسيم البيانات إلى دفعات
        batch_size = self.performance_config.batch_size
        batches = [pages_data[i:i + batch_size] for i in range(0, len(pages_data), batch_size)]
        
        # استعلام الإدراج المجمع
        insert_query = f"""
            INSERT INTO {self.tables['pages']} 
            (book_id, page_number, internal_index, content, html_content, word_count, 
             volume_id, chapter_id, original_page_number, page_index_internal, 
             printed_missing, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        all_page_ids = []
        
        if self.performance_config.max_workers > 1 and len(batches) > 1:
            # تنفيذ متوازي للدفعات الكبيرة
            logger.info(f"حفظ {len(pages)} صفحة في {len(batches)} دفعة متوازية")
            
            def batch_insert_func(manager, batch):
                return manager.execute_batch_insert(insert_query, batch)
            
            all_page_ids = self.execute_parallel_batch(batch_insert_func, batches)
        else:
            # تنفيذ تسلسلي
            logger.info(f"حفظ {len(pages)} صفحة في {len(batches)} دفعة تسلسلية")
            for batch in batches:
                page_ids = self.execute_batch_insert(insert_query, batch)
                all_page_ids.extend(page_ids)
        
        logger.info(f"تم حفظ {len(all_page_ids)} صفحة بنجاح")
        return all_page_ids
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """تنفيذ استعلام INSERT وإرجاع ID الجديد"""
        try:
            self.cursor.execute(query, params or ())
            return self.cursor.lastrowid
        except Error as e:
            logger.error(f"خطأ في تنفيذ INSERT: {e}")
            logger.error(f"الاستعلام: {query}")
            logger.error(f"المعاملات: {params}")
            raise
    
    def create_enhanced_tables(self) -> None:
        """
        إنشاء الجداول المحسنة إذا لم تكن موجودة
        """
        logger.info("إنشاء الجداول المحسنة...")
        
        # جدول الناشرين
        publishers_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['publishers']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) NULL,
                location VARCHAR(255) NULL,
                description TEXT NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY publishers_slug_unique (slug),
                INDEX publishers_name_index (name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول أقسام الكتب
        book_sections_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['book_sections']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) NULL,
                parent_id BIGINT UNSIGNED NULL,
                description TEXT NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY book_sections_slug_unique (slug),
                INDEX book_sections_name_index (name),
                FOREIGN KEY (parent_id) REFERENCES {self.tables['book_sections']}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول المؤلفين المحسن
        authors_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['authors']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                slug VARCHAR(255) NULL,
                biography TEXT NULL,
                madhhab VARCHAR(100) NULL,
                birth_date VARCHAR(50) NULL,
                death_date VARCHAR(50) NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY authors_slug_unique (slug),
                INDEX authors_full_name_index (full_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول الكتب المحسن
        books_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['books']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                slug VARCHAR(255) NULL,
                shamela_id VARCHAR(50) NOT NULL,
                publisher_id BIGINT UNSIGNED NULL,
                book_section_id BIGINT UNSIGNED NULL,
                edition VARCHAR(255) NULL,
                edition_number INT NULL,
                publication_year INT NULL,
                edition_date_hijri VARCHAR(50) NULL,
                edition_DATA INT NULL,
                pages_count INT NULL,
                volumes_count INT NULL,
                description LONGTEXT NULL,
                language VARCHAR(10) DEFAULT 'ar',
                source_url VARCHAR(500) NULL,
                has_original_pagination BOOLEAN DEFAULT FALSE,
                status VARCHAR(20) DEFAULT 'published',
                visibility VARCHAR(20) DEFAULT 'public',
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY books_shamela_id_unique (shamela_id),
                UNIQUE KEY books_slug_unique (slug),
                INDEX books_title_index (title),
                INDEX books_publication_year_index (publication_year),
                INDEX books_status_index (status),
                FOREIGN KEY (publisher_id) REFERENCES {self.tables['publishers']}(id) ON DELETE SET NULL,
                FOREIGN KEY (book_section_id) REFERENCES {self.tables['book_sections']}(id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # إضافة الحقول المفقودة إذا لم تكن موجودة
        alter_books_table = f"""
            ALTER TABLE {self.tables['books']} 
            ADD COLUMN IF NOT EXISTS has_original_pagination BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS edition_DATA INT NULL,
            ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'published',
            ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) DEFAULT 'public'
        """
        
        # تحديث جدول الفصول لجعل volume_id يقبل NULL
        alter_chapters_table = f"""
            ALTER TABLE {self.tables['chapters']} 
            MODIFY COLUMN volume_id BIGINT UNSIGNED NULL
        """
        
        # تحديث جدول الصفحات لإضافة الحقول المفقودة
        alter_pages_table = f"""
            ALTER TABLE {self.tables['pages']} 
            ADD COLUMN IF NOT EXISTS original_page_number INT NULL,
            ADD COLUMN IF NOT EXISTS word_count INT NULL,
            ADD COLUMN IF NOT EXISTS html_content LONGTEXT NULL,
            ADD COLUMN IF NOT EXISTS printed_missing BOOLEAN DEFAULT FALSE
        """
        
        # جدول ربط المؤلفين بالكتب
        author_book_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['author_book']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                book_id BIGINT UNSIGNED NOT NULL,
                author_id BIGINT UNSIGNED NOT NULL,
                role VARCHAR(50) DEFAULT 'author',
                is_main BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY author_book_unique (book_id, author_id),
                FOREIGN KEY (book_id) REFERENCES {self.tables['books']}(id) ON DELETE CASCADE,
                FOREIGN KEY (author_id) REFERENCES {self.tables['authors']}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول الأجزاء المحسن
        volumes_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['volumes']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                book_id BIGINT UNSIGNED NOT NULL,
                number INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                page_start INT NULL,
                page_end INT NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX volumes_book_id_index (book_id),
                UNIQUE KEY volumes_book_number_unique (book_id, number),
                FOREIGN KEY (book_id) REFERENCES {self.tables['books']}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول الفصول المحسن
        chapters_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['chapters']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                volume_id BIGINT UNSIGNED NULL,
                book_id BIGINT UNSIGNED NOT NULL,
                chapter_number VARCHAR(20) NULL,
                title VARCHAR(255) NOT NULL,
                parent_id BIGINT UNSIGNED NULL,
                order_number INT DEFAULT 0,
                page_start INT NULL,
                page_end INT NULL,
                level INT DEFAULT 0,
                chapter_type ENUM('main', 'sub') DEFAULT 'main',
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX chapters_book_id_index (book_id),
                INDEX chapters_order_index (order_number),
                FOREIGN KEY (volume_id) REFERENCES {self.tables['volumes']}(id) ON DELETE CASCADE,
                FOREIGN KEY (book_id) REFERENCES {self.tables['books']}(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES {self.tables['chapters']}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول الصفحات المحسن
        pages_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['pages']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                book_id BIGINT UNSIGNED NOT NULL,
                volume_id BIGINT UNSIGNED NULL,
                chapter_id BIGINT UNSIGNED NULL,
                page_number INT NOT NULL,
                original_page_number INT NULL,
                internal_index INT NULL,
                content LONGTEXT NULL,
                html_content LONGTEXT NULL,
                word_count INT NULL,
                content_type VARCHAR(20) DEFAULT 'text',
                content_hash VARCHAR(64) NULL,
                character_count INT NULL,
                has_footnotes BOOLEAN DEFAULT FALSE,
                has_images BOOLEAN DEFAULT FALSE,
                has_tables BOOLEAN DEFAULT FALSE,
                formatting_info JSON NULL,
                plain_text LONGTEXT NULL,
                reading_time_minutes INT NULL,
                printed_missing BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX pages_book_id_index (book_id),
                INDEX pages_page_number_index (page_number),
                INDEX pages_internal_index_index (internal_index),
                UNIQUE KEY pages_book_page_unique (book_id, page_number),
                FOREIGN KEY (book_id) REFERENCES {self.tables['books']}(id) ON DELETE CASCADE,
                FOREIGN KEY (volume_id) REFERENCES {self.tables['volumes']}(id) ON DELETE CASCADE,
                FOREIGN KEY (chapter_id) REFERENCES {self.tables['chapters']}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # جدول روابط المجلدات
        volume_links_table = f"""
            CREATE TABLE IF NOT EXISTS {self.tables['volume_links']} (
                id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                book_id BIGINT UNSIGNED NOT NULL,
                volume_number INT NOT NULL,
                title VARCHAR(255) NOT NULL,
                url VARCHAR(500) NOT NULL,
                page_start INT NULL,
                page_end INT NULL,
                created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX volume_links_book_id_index (book_id),
                UNIQUE KEY volume_links_book_volume_unique (book_id, volume_number),
                FOREIGN KEY (book_id) REFERENCES {self.tables['books']}(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        # تنفيذ إنشاء الجداول
        tables_sql = [
            publishers_table,
            book_sections_table,
            authors_table,
            books_table,
            author_book_table,
            volumes_table,
            chapters_table,
            pages_table,
            volume_links_table
        ]
        
        for table_sql in tables_sql:
            try:
                self.cursor.execute(table_sql)
                logger.info(f"تم إنشاء/التحقق من الجدول بنجاح")
            except Error as e:
                logger.error(f"خطأ في إنشاء الجدول: {e}")
                raise
        
        # تنفيذ تحديث جدول الكتب لإضافة الحقول المفقودة
        try:
            self.cursor.execute(alter_books_table)
            logger.info("تم تحديث جدول الكتب بالحقول المفقودة")
        except Error as e:
            # تجاهل الخطأ إذا كانت الحقول موجودة بالفعل
            if "Duplicate column name" not in str(e):
                logger.warning(f"تحذير في تحديث جدول الكتب: {e}")
        
        # تنفيذ تحديث جدول الفصول
        try:
            self.cursor.execute(alter_chapters_table)
            logger.info("تم تحديث جدول الفصول لجعل volume_id يقبل NULL")
        except Error as e:
            logger.warning(f"تحذير في تحديث جدول الفصول: {e}")
        
        # تنفيذ تحديث جدول الصفحات
        try:
            self.cursor.execute(alter_pages_table)
            logger.info("تم تحديث جدول الصفحات بالحقول المفقودة")
        except Error as e:
            if "Duplicate column name" not in str(e):
                logger.warning(f"تحذير في تحديث جدول الصفحات: {e}")
        
        self.connection.commit()
        logger.info("تم إنشاء جميع الجداول المحسنة بنجاح")
    
    def save_publisher(self, publisher: Publisher) -> int:
        """حفظ الناشر وإرجاع ID"""
        if not publisher or not publisher.name:
            return None
            
        # البحث عن الناشر الموجود
        query = f"SELECT id FROM {self.tables['publishers']} WHERE name = %s LIMIT 1"
        result = self.execute_query(query, (publisher.name,))
        
        if result:
            publisher_id = result[0]['id']
            # تحديث البيانات إذا كانت متوفرة
            update_query = f"""
                UPDATE {self.tables['publishers']} 
                SET slug = %s, description = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                publisher.slug, publisher.description,
                datetime.now(), publisher_id
            ))
            logger.info(f"تم تحديث الناشر: {publisher.name}")
        else:
            # إدراج ناشر جديد
            insert_query = f"""
                INSERT INTO {self.tables['publishers']} 
                (name, slug, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            publisher_id = self.execute_insert(insert_query, (
                publisher.name, publisher.slug, publisher.description,
                datetime.now(), datetime.now()
            ))
            logger.info(f"تم إدراج ناشر جديد: {publisher.name} (ID: {publisher_id})")
        
        return publisher_id
    
    def save_book_section(self, book_section: BookSection) -> int:
        """حفظ قسم الكتاب وإرجاع ID"""
        if not book_section or not book_section.name:
            return None
            
        # البحث عن القسم الموجود
        query = f"SELECT id FROM {self.tables['book_sections']} WHERE name = %s LIMIT 1"
        result = self.execute_query(query, (book_section.name,))
        
        if result:
            section_id = result[0]['id']
            # تحديث البيانات
            update_query = f"""
                UPDATE {self.tables['book_sections']} 
                SET slug = %s, description = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                book_section.slug, book_section.description,
                datetime.now(), section_id
            ))
            logger.info(f"تم تحديث قسم الكتاب: {book_section.name}")
        else:
            # إدراج قسم جديد
            insert_query = f"""
                INSERT INTO {self.tables['book_sections']} 
                (name, slug, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            section_id = self.execute_insert(insert_query, (
                book_section.name, book_section.slug, book_section.description,
                datetime.now(), datetime.now()
            ))
            logger.info(f"تم إدراج قسم جديد: {book_section.name} (ID: {section_id})")
        
        return section_id
    
    def save_author(self, author: Author) -> int:
        """حفظ مؤلف وإرجاع ID"""
        # البحث عن المؤلف الموجود
        query = f"SELECT id FROM {self.tables['authors']} WHERE full_name = %s LIMIT 1"
        result = self.execute_query(query, (author.name,))
        
        if result:
            author_id = result[0]['id']
            # تحديث البيانات
            update_query = f"""
                UPDATE {self.tables['authors']} 
                SET slug = %s, biography = %s, madhhab = %s, 
                    birth_date = %s, death_date = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                author.slug, author.biography, author.madhhab,
                author.birth_date, author.death_date, 
                datetime.now(), author_id
            ))
            logger.info(f"تم تحديث المؤلف: {author.name}")
        else:
            # إدراج مؤلف جديد
            insert_query = f"""
                INSERT INTO {self.tables['authors']} 
                (full_name, slug, biography, madhhab, birth_date, death_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            author_id = self.execute_insert(insert_query, (
                author.name, author.slug, author.biography, author.madhhab,
                author.birth_date, author.death_date, 
                datetime.now(), datetime.now()
            ))
            logger.info(f"تم إدراج مؤلف جديد: {author.name} (ID: {author_id})")
        
        return author_id
    
    def save_enhanced_book(self, book: Book) -> int:
        """حفظ كتاب محسن وإرجاع ID"""
        # البحث عن الكتاب الموجود
        query = f"SELECT id FROM {self.tables['books']} WHERE shamela_id = %s LIMIT 1"
        result = self.execute_query(query, (book.shamela_id,))
        
        # حفظ الناشر والحصول على ID
        publisher_id = self.save_publisher(book.publisher) if book.publisher else None
        
        # حفظ قسم الكتاب والحصول على ID
        book_section_id = self.save_book_section(book.book_section) if book.book_section else None
        
        # تحويل edition_date_hijri إلى رقم
        edition_data_int = None
        if hasattr(book, 'edition_date_hijri') and book.edition_date_hijri:
            try:
                # استخراج الأرقام من النص
                import re
                numbers = re.findall(r'\d+', str(book.edition_date_hijri))
                if numbers:
                    edition_data_int = int(numbers[0])
            except (ValueError, AttributeError):
                edition_data_int = None
        
        if result:
            book_id = result[0]['id']
            # تحديث الكتاب الموجود
            update_query = f"""
                UPDATE {self.tables['books']} 
                SET title = %s, slug = %s, publisher_id = %s, book_section_id = %s,
                    edition = %s, edition_number = %s, edition_DATA = %s, pages_count = %s, volumes_count = %s,
                    description = %s, source_url = %s, has_original_pagination = %s, status = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                book.title, book.slug, publisher_id, book_section_id,
                book.edition, book.edition_number, edition_data_int, book.page_count, book.volume_count,
                book.description, book.source_url, book.has_original_pagination, 'published', datetime.now(), book_id
            ))
            logger.info(f"تم تحديث الكتاب: {book.title}")
        else:
            # إدراج كتاب جديد
            insert_query = f"""
                INSERT INTO {self.tables['books']} 
                (title, slug, shamela_id, publisher_id, book_section_id,
                 edition, edition_number, edition_DATA, pages_count, volumes_count, 
                 description, source_url, has_original_pagination, status, visibility, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            book_id = self.execute_insert(insert_query, (
                book.title, book.slug, book.shamela_id, publisher_id, book_section_id,
                book.edition, book.edition_number, edition_data_int, book.page_count, book.volume_count,
                book.description, book.source_url, book.has_original_pagination, 'published', 'public', 
                datetime.now(), datetime.now()
            ))
            logger.info(f"تم إدراج كتاب جديد: {book.title} (ID: {book_id})")
        
        return book_id
    
    def save_volume_link(self, volume_link: VolumeLink, book_id: int) -> int:
        """حفظ رابط المجلد وإرجاع ID"""
        # البحث عن الرابط الموجود
        query = f"""
            SELECT id FROM {self.tables['volume_links']} 
            WHERE book_id = %s AND volume_number = %s LIMIT 1
        """
        result = self.execute_query(query, (book_id, volume_link.volume_number))
        
        if result:
            link_id = result[0]['id']
            # تحديث الرابط
            update_query = f"""
                UPDATE {self.tables['volume_links']} 
                SET title = %s, url = %s, page_start = %s, page_end = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                volume_link.title, volume_link.url, volume_link.page_start,
                volume_link.page_end, datetime.now(), link_id
            ))
            logger.debug(f"تم تحديث رابط المجلد: {volume_link.title}")
        else:
            # إدراج رابط جديد
            insert_query = f"""
                INSERT INTO {self.tables['volume_links']} 
                (book_id, volume_number, title, url, page_start, page_end, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            link_id = self.execute_insert(insert_query, (
                book_id, volume_link.volume_number, volume_link.title, volume_link.url,
                volume_link.page_start, volume_link.page_end, datetime.now(), datetime.now()
            ))
            logger.debug(f"تم إدراج رابط مجلد جديد: {volume_link.title} (ID: {link_id})")
        
        return link_id
    
    def save_enhanced_chapter(self, chapter: Chapter, book_id: int, volume_id: Optional[int] = None, 
                             parent_id: Optional[int] = None) -> int:
        """حفظ فصل محسن وإرجاع ID"""
        # البحث عن الفصل الموجود
        query = f"""
            SELECT id FROM {self.tables['chapters']} 
            WHERE book_id = %s AND title = %s AND `order` = %s LIMIT 1
        """
        result = self.execute_query(query, (book_id, chapter.title, chapter.order))
        
        if result:
            chapter_id = result[0]['id']
            # تحديث الفصل (بدون chapter_type لأنه محفوظ في JSON فقط)
            update_query = f"""
                UPDATE {self.tables['chapters']} 
                SET volume_id = %s, page_start = %s, page_end = %s, parent_id = %s,
                    level = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                volume_id, chapter.page_number, chapter.page_end, parent_id,
                chapter.level, datetime.now(), chapter_id
            ))
            logger.debug(f"تم تحديث الفصل: {chapter.title}")
        else:
            # إدراج فصل جديد
            insert_query = f"""
                INSERT INTO {self.tables['chapters']} 
                (book_id, volume_id, title, page_start, page_end, parent_id,
                 `order`, level, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            chapter_id = self.execute_insert(insert_query, (
                book_id, volume_id, chapter.title, chapter.page_number, chapter.page_end,
                parent_id, chapter.order, chapter.level,
                datetime.now(), datetime.now()
            ))
            logger.debug(f"تم إدراج فصل جديد: {chapter.title} (ID: {chapter_id})")
        
        return chapter_id
    
    def save_enhanced_page(self, page: PageContent, book_id: int, volume_id: Optional[int] = None, 
                          chapter_id: Optional[int] = None) -> int:
        """حفظ صفحة محسنة وإرجاع ID"""
        # البحث عن الصفحة الموجودة
        query = f"""
            SELECT id FROM {self.tables['pages']} 
            WHERE book_id = %s AND page_number = %s LIMIT 1
        """
        result = self.execute_query(query, (book_id, page.page_number))
        
        # استخراج البيانات الإضافية من PageContent
        internal_index = getattr(page, 'page_index_internal', None) or getattr(page, 'internal_index', None)
        original_page_number = getattr(page, 'original_page_number', None)
        word_count = getattr(page, 'word_count', None)
        html_content = getattr(page, 'html_content', None)
        printed_missing = getattr(page, 'printed_missing', False)
        
        if result:
            page_id = result[0]['id']
            # تحديث الصفحة
            update_query = f"""
                UPDATE {self.tables['pages']} 
                SET volume_id = %s, chapter_id = %s, content = %s, internal_index = %s, 
                    original_page_number = %s, word_count = %s, html_content = %s, 
                    printed_missing = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                volume_id, chapter_id, page.content, internal_index,
                original_page_number, word_count, html_content, 
                printed_missing, datetime.now(), page_id
            ))
            logger.debug(f"تم تحديث الصفحة: {page.page_number}")
        else:
            # إدراج صفحة جديدة
            insert_query = f"""
                INSERT INTO {self.tables['pages']} 
                (book_id, volume_id, chapter_id, page_number, content, internal_index,
                 original_page_number, word_count, html_content, printed_missing, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            page_id = self.execute_insert(insert_query, (
                book_id, volume_id, chapter_id, page.page_number, page.content, internal_index,
                original_page_number, word_count, html_content, printed_missing,
                datetime.now(), datetime.now()
            ))
            logger.debug(f"تم إدراج صفحة جديدة: {page.page_number} (ID: {page_id})")
        
        return page_id
    
    def save_complete_enhanced_book(self, book: Book) -> Dict[str, Any]:
        """حفظ كتاب كامل محسن مع جميع بياناته"""
        logger.info(f"بدء حفظ الكتاب المحسن الكامل: {book.title}")
        
        # التأكد من وجود الاتصال
        if not self.connection:
            self.connect()
        
        try:
            # بدء المعاملة
            self.connection.start_transaction()
            
            # 0. حساب internal_index للصفحات
            self.calculate_internal_index_for_pages(book)
            
            # 1. حفظ الكتاب المحسن
            book_id = self.save_enhanced_book(book)
            
            # 2. حفظ المؤلفين وربطهم بالكتاب
            author_ids = []
            for author in book.authors:
                author_id = self.save_author(author)
                author_ids.append(author_id)
                self.save_author_book_relation(book_id, author_id)
            
            # 3. حفظ الأجزاء
            volume_ids = {}
            for volume in book.volumes:
                volume_id = self.save_volume(volume, book_id)
                volume_ids[volume.number] = volume_id
            
            # 4. حفظ روابط المجلدات
            volume_link_ids = []
            for volume_link in book.volume_links:
                link_id = self.save_volume_link(volume_link, book_id)
                volume_link_ids.append(link_id)
            
            # 5. حفظ الفصول المحسنة
            def save_enhanced_chapters_recursive(chapters: List[Chapter], parent_id: Optional[int] = None):
                chapter_ids = []
                for chapter in chapters:
                    # تحديد الجزء للفصل
                    volume_id = None
                    if chapter.volume_number and chapter.volume_number in volume_ids:
                        volume_id = volume_ids[chapter.volume_number]
                    
                    chapter_id = self.save_enhanced_chapter(chapter, book_id, volume_id, parent_id)
                    chapter_ids.append(chapter_id)
                    
                    # حفظ الفصول الفرعية
                    if chapter.children:
                        child_ids = save_enhanced_chapters_recursive(chapter.children, chapter_id)
                        chapter_ids.extend(child_ids)
                
                return chapter_ids
            
            chapter_ids = save_enhanced_chapters_recursive(book.index)
            
            # 6. حفظ الصفحات المحسنة بطريقة مجمعة محسنة
            if book.pages:
                if self.performance_config.batch_size > 1 and len(book.pages) > self.performance_config.batch_size:
                    # استخدام الحفظ المجمع للكتب الكبيرة
                    logger.info(f"حفظ {len(book.pages)} صفحة باستخدام العمليات المجمعة")
                    page_ids = self.save_pages_batch(book.pages, book_id, volume_ids)
                else:
                    # حفظ تقليدي للكتب الصغيرة
                    logger.info(f"حفظ {len(book.pages)} صفحة بطريقة تقليدية")
                    page_ids = []
                    for page in book.pages:
                        # تحديد الجزء للصفحة
                        volume_id = None
                        if page.volume_number and page.volume_number in volume_ids:
                            volume_id = volume_ids[page.volume_number]
                        
                        # تحديد الفصل للصفحة
                        chapter_id = self.find_chapter_for_page(book_id, page.page_number)
                        
                        page_id = self.save_enhanced_page(page, book_id, volume_id, chapter_id)
                        page_ids.append(page_id)
            else:
                page_ids = []
            
            # تأكيد المعاملة
            self.connection.commit()
            
            result = {
                'book_id': book_id,
                'author_ids': author_ids,
                'volume_ids': list(volume_ids.values()),
                'volume_link_ids': volume_link_ids,
                'chapter_ids': chapter_ids,
                'page_ids': page_ids,
                'total_pages': len(page_ids),
                'total_chapters': len(chapter_ids),
                'total_authors': len(author_ids),
                'total_volumes': len(volume_ids),
                'total_volume_links': len(volume_link_ids),
                'has_original_pagination': book.has_original_pagination,
                'publisher': book.publisher.name if book.publisher else None,
                'book_section': book.book_section.name if book.book_section else None
            }
            
            logger.info(f"تم حفظ الكتاب المحسن بنجاح: {book.title}")
            logger.info(f"إحصائيات الحفظ المحسنة: {result}")
            
            return result
            
        except Exception as e:
            # التراجع عن المعاملة في حالة الخطأ
            if self.connection:
                self.connection.rollback()
            logger.error(f"خطأ في حفظ الكتاب المحسن: {e}")
            raise
    
    def save_volume(self, volume: Volume, book_id: int) -> int:
        """حفظ جزء وإرجاع ID"""
        # البحث عن الجزء الموجود
        query = f"""
            SELECT id FROM {self.tables['volumes']} 
            WHERE book_id = %s AND number = %s LIMIT 1
        """
        result = self.execute_query(query, (book_id, volume.number))
        
        if result:
            volume_id = result[0]['id']
            # تحديث الجزء
            update_query = f"""
                UPDATE {self.tables['volumes']} 
                SET title = %s, page_start = %s, page_end = %s, updated_at = %s
                WHERE id = %s
            """
            self.cursor.execute(update_query, (
                volume.title, volume.page_start, volume.page_end,
                datetime.now(), volume_id
            ))
            logger.debug(f"تم تحديث الجزء: {volume.title}")
        else:
            # إدراج جزء جديد
            insert_query = f"""
                INSERT INTO {self.tables['volumes']} 
                (book_id, number, title, page_start, page_end, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            volume_id = self.execute_insert(insert_query, (
                book_id, volume.number, volume.title, volume.page_start, volume.page_end,
                datetime.now(), datetime.now()
            ))
            logger.debug(f"تم إدراج جزء جديد: {volume.title} (ID: {volume_id})")
        
        return volume_id
    
    def save_author_book_relation(self, book_id: int, author_id: int, role: str = 'author', is_main: bool = True) -> None:
        """حفظ علاقة المؤلف بالكتاب"""
        # التحقق من وجود العلاقة
        query = f"""
            SELECT id FROM {self.tables['author_book']} 
            WHERE book_id = %s AND author_id = %s LIMIT 1
        """
        result = self.execute_query(query, (book_id, author_id))
        
        if not result:
            insert_query = f"""
                INSERT INTO {self.tables['author_book']} 
                (book_id, author_id, role, is_main, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            self.execute_insert(insert_query, (
                book_id, author_id, role, is_main,
                datetime.now(), datetime.now()
            ))
            logger.debug(f"تم ربط المؤلف {author_id} بالكتاب {book_id}")
    
    def find_chapter_for_page(self, book_id: int, page_number: int) -> Optional[int]:
        """العثور على الفصل المناسب للصفحة"""
        query = f"""
            SELECT id FROM {self.tables['chapters']} 
            WHERE book_id = %s AND page_start IS NOT NULL AND page_start <= %s
            ORDER BY page_start DESC LIMIT 1
        """
        result = self.execute_query(query, (book_id, page_number))
        return result[0]['id'] if result else None
    
    def calculate_internal_index_for_pages(self, book: Book) -> None:
        """حساب internal_index للصفحات بناءً على has_original_pagination
        
        المنطق المعكوس:
        - page_number: الرقم التسلسلي (1, 2, 3, ...)
        - internal_index: رقم الصفحة الفعلي/الأصلي
        """
        if not book.has_original_pagination:
            # إذا لم يكن هناك ترقيم أصلي، internal_index = page_number الأصلي
            for i, page in enumerate(book.pages, 1):
                # حفظ الرقم الأصلي في internal_index
                original_page_num = page.page_number
                if not hasattr(page, 'internal_index') or page.internal_index is None:
                    page.internal_index = original_page_num
                if not hasattr(page, 'page_index_internal') or page.page_index_internal is None:
                    page.page_index_internal = original_page_num
                # تحديث page_number ليكون الرقم التسلسلي
                page.page_number = i
        else:
            # إذا كان هناك ترقيم أصلي، internal_index = الرقم الأصلي، page_number = التسلسلي
            for i, page in enumerate(book.pages, 1):
                # حفظ الرقم الأصلي في internal_index
                original_page_num = page.page_number
                if not hasattr(page, 'internal_index') or page.internal_index is None:
                    page.internal_index = original_page_num
                if not hasattr(page, 'page_index_internal') or page.page_index_internal is None:
                    page.page_index_internal = original_page_num
                # تحديث page_number ليكون الرقم التسلسلي
                page.page_number = i
        
        logger.info(f"تم حساب internal_index لـ {len(book.pages)} صفحة (has_original_pagination: {book.has_original_pagination})")
        logger.info(f"المنطق المعكوس: page_number = تسلسلي، internal_index = رقم فعلي")
    
    def get_enhanced_book_stats(self, book_id: int) -> Dict[str, Any]:
        """الحصول على إحصائيات الكتاب المحسنة"""
        stats = {}
        
        # معلومات الكتاب الأساسية المحسنة
        book_query = f"""
            SELECT b.title, b.shamela_id, b.edition, b.edition_number,
                   b.publication_year, b.edition_date_hijri, b.pages_count, 
                   b.volumes_count, b.has_original_pagination,
                   p.name as publisher_name, s.name as section_name
            FROM {self.tables['books']} b
            LEFT JOIN {self.tables['publishers']} p ON b.publisher_id = p.id
            LEFT JOIN {self.tables['book_sections']} s ON b.book_section_id = s.id
            WHERE b.id = %s
        """
        book_result = self.execute_query(book_query, (book_id,))
        if book_result:
            stats['book'] = book_result[0]
        
        # عدد المؤلفين
        authors_query = f"""
            SELECT COUNT(*) as count FROM {self.tables['author_book']} 
            WHERE book_id = %s
        """
        authors_result = self.execute_query(authors_query, (book_id,))
        stats['authors_count'] = authors_result[0]['count'] if authors_result else 0
        
        # عدد الأجزاء
        volumes_query = f"""
            SELECT COUNT(*) as count FROM {self.tables['volumes']} 
            WHERE book_id = %s
        """
        volumes_result = self.execute_query(volumes_query, (book_id,))
        stats['volumes_count'] = volumes_result[0]['count'] if volumes_result else 0
        
        # عدد الفصول
        chapters_query = f"""
            SELECT COUNT(*) as count FROM {self.tables['chapters']} 
            WHERE book_id = %s
        """
        chapters_result = self.execute_query(chapters_query, (book_id,))
        stats['chapters_count'] = chapters_result[0]['count'] if chapters_result else 0
        
        # عدد الصفحات
        pages_query = f"""
            SELECT COUNT(*) as count, SUM(word_count) as total_words
            FROM {self.tables['pages']} WHERE book_id = %s
        """
        pages_result = self.execute_query(pages_query, (book_id,))
        if pages_result:
            stats['pages_count'] = pages_result[0]['count']
            stats['total_words'] = pages_result[0]['total_words'] or 0
        
        # عدد روابط المجلدات
        volume_links_query = f"""
            SELECT COUNT(*) as count FROM {self.tables['volume_links']} 
            WHERE book_id = %s
        """
        volume_links_result = self.execute_query(volume_links_query, (book_id,))
        stats['volume_links_count'] = volume_links_result[0]['count'] if volume_links_result else 0
        
        return stats

# ========= وظائف مساعدة محسنة =========
def load_enhanced_book_from_json(json_path: str) -> Book:
    """تحميل كتاب محسن من ملف JSON"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # تحويل البيانات إلى كائنات محسنة
    authors = [Author(**author_data) for author_data in data.get('authors', [])]
    
    publisher = None
    if data.get('publisher'):
        publisher = Publisher(**data['publisher'])
    
    book_section = None
    if data.get('book_section'):
        book_section = BookSection(**data['book_section'])
    
    volumes = [Volume(**volume_data) for volume_data in data.get('volumes', [])]
    volume_links = [VolumeLink(**vl_data) for vl_data in data.get('volume_links', [])]
    
    # تحويل الفصول المحسنة
    def convert_enhanced_chapters(chapters_data):
        chapters = []
        for chapter_data in chapters_data:
            chapter = Chapter(
                title=chapter_data['title'],
                order=chapter_data.get('order', 0),
                page_number=chapter_data.get('page_number'),
                page_end=chapter_data.get('page_end'),
                volume_number=chapter_data.get('volume_number'),
                level=chapter_data.get('level', 0),
                chapter_type=chapter_data.get('chapter_type', 'main'),
                children=convert_enhanced_chapters(chapter_data.get('children', []))
            )
            chapters.append(chapter)
        return chapters
    
    index = convert_enhanced_chapters(data.get('index', []))
    
    # تحويل الصفحات المحسنة
    pages = []
    for page_data in data.get('pages', []):
        page = PageContent(
            page_number=page_data['page_number'],
            content=page_data['content'],
            html_content=page_data.get('html_content'),
            volume_number=page_data.get('volume_number'),
            word_count=page_data.get('word_count'),
            original_page_number=page_data.get('original_page_number')
        )
        pages.append(page)
    
    # إنشاء كائن الكتاب المحسن
    book = Book(
        title=data['title'],
        shamela_id=data['shamela_id'],
        slug=data.get('slug'),
        authors=authors,
        publisher=publisher,
        book_section=book_section,
        edition=data.get('edition'),
        edition_number=data.get('edition_number'),
        publication_year=data.get('publication_year'),
        edition_date_hijri=data.get('edition_date_hijri'),
        page_count=data.get('page_count'),
        volume_count=data.get('volume_count'),
        categories=data.get('categories', []),
        description=data.get('description'),
        language=data.get('language', 'ar'),
        source_url=data.get('source_url'),
        has_original_pagination=data.get('has_original_pagination', False),
        index=index,
        volumes=volumes,
        volume_links=volume_links,
        pages=pages
    )
    
    return book

def save_enhanced_json_to_database(json_path: str, db_config: Dict[str, Any], 
                                  performance_config: PerformanceConfig = None) -> Dict[str, Any]:
    """حفظ كتاب محسن من ملف JSON إلى قاعدة البيانات مع تحسينات الأداء"""
    if performance_config is None:
        performance_config = PerformanceConfig()
    
    logger.info(f"تحميل الكتاب المحسن من {json_path}")
    book = load_enhanced_book_from_json(json_path)
    
    start_time = time.time()
    
    with EnhancedShamelaDatabaseManager(db_config, performance_config) as db:
        # إنشاء الجداول إذا لم تكن موجودة
        db.create_enhanced_tables()
        result = db.save_complete_enhanced_book(book)
    
    elapsed_time = time.time() - start_time
    
    # إضافة إحصائيات الأداء للنتيجة
    result['performance'] = {
        'elapsed_time': elapsed_time,
        'pages_per_second': result['total_pages'] / elapsed_time if elapsed_time > 0 else 0,
        'batch_size': performance_config.batch_size,
        'max_workers': performance_config.max_workers,
        'parallel_enabled': performance_config.max_workers > 1
    }
    
    logger.info(f"تم حفظ الكتاب المحسن في قاعدة البيانات في {elapsed_time:.2f} ثانية")
    logger.info(f"معدل الأداء: {result['performance']['pages_per_second']:.2f} صفحة/ثانية")
    
    return result

# ========= واجهة سطر الأوامر المحسنة =========
def main():
    """الوظيفة الرئيسية المحسنة لسطر الأوامر"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="إدارة قاعدة البيانات المحسنة للكتب المستخرجة من الشاملة"
    )
    
    parser.add_argument('action', choices=['save', 'stats', 'create-tables'], 
                       help='العملية المطلوبة')
    parser.add_argument('--json', help='مسار ملف JSON للكتاب')
    parser.add_argument('--book-id', type=int, help='معرف الكتاب في قاعدة البيانات')
    parser.add_argument('--db-host', default='localhost', help='عنوان قاعدة البيانات')
    parser.add_argument('--db-port', type=int, default=3306, help='منفذ قاعدة البيانات')
    parser.add_argument('--db-user', default='root', help='اسم المستخدم')
    parser.add_argument('--db-password', help='كلمة المرور')
    parser.add_argument('--db-name', default='bms', help='اسم قاعدة البيانات')
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'user': args.db_user,
        'password': args.db_password or input("كلمة مرور قاعدة البيانات: "),
        'database': args.db_name
    }
    
    try:
        if args.action == 'create-tables':
            with EnhancedShamelaDatabaseManager(db_config) as db:
                db.create_enhanced_tables()
            print("✓ تم إنشاء الجداول المحسنة بنجاح!")
        
        elif args.action == 'save':
            if not args.json:
                print("خطأ: يجب تحديد مسار ملف JSON")
                return
            
            result = save_enhanced_json_to_database(args.json, db_config)
            print(f"✓ تم حفظ الكتاب المحسن بنجاح!")
            print(f"معرف الكتاب: {result['book_id']}")
            print(f"عدد الصفحات: {result['total_pages']}")
            print(f"عدد الفصول: {result['total_chapters']}")
            print(f"عدد المؤلفين: {result['total_authors']}")
            print(f"عدد الأجزاء: {result['total_volumes']}")
            print(f"عدد روابط المجلدات: {result['total_volume_links']}")
            print(f"الناشر: {result['publisher'] or 'غير محدد'}")
            print(f"القسم: {result['book_section'] or 'غير محدد'}")
            print(f"ترقيم أصلي: {'نعم' if result['has_original_pagination'] else 'لا'}")
        
        elif args.action == 'stats':
            if not args.book_id:
                print("خطأ: يجب تحديد معرف الكتاب")
                return
            
            with EnhancedShamelaDatabaseManager(db_config) as db:
                stats = db.get_enhanced_book_stats(args.book_id)
            
            book = stats.get('book', {})
            print(f"إحصائيات الكتاب المحسن {args.book_id}:")
            print(f"العنوان: {book.get('title', 'غير محدد')}")
            print(f"معرف الشاملة: {book.get('shamela_id', 'غير محدد')}")
            print(f"الطبعة: {book.get('edition', 'غير محددة')} (رقم: {book.get('edition_number', 'غير محدد')})")
            print(f"سنة النشر: {book.get('publication_year', 'غير محددة')} م ({book.get('edition_date_hijri', 'غير محددة')} هـ)")
            print(f"الناشر: {book.get('publisher_name', 'غير محدد')}")
            print(f"القسم: {book.get('section_name', 'غير محدد')}")
            print(f"ترقيم أصلي: {'نعم' if book.get('has_original_pagination') else 'لا'}")
            print(f"عدد الصفحات: {stats.get('pages_count', 0)}")
            print(f"عدد الفصول: {stats.get('chapters_count', 0)}")
            print(f"عدد المؤلفين: {stats.get('authors_count', 0)}")
            print(f"عدد الأجزاء: {stats.get('volumes_count', 0)}")
            print(f"عدد روابط المجلدات: {stats.get('volume_links_count', 0)}")
            print(f"إجمالي الكلمات: {stats.get('total_words', 0):,}")
    
    except Exception as e:
        logger.error(f"خطأ: {e}")
        print(f"❌ خطأ: {e}")

if __name__ == "__main__":
    main()
