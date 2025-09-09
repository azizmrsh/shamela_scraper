#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إصلاح حقل edition في جدول books
تحويل حقل edition من INTEGER إلى VARCHAR(255)
"""

import mysql.connector
import sys
import os

def fix_edition_column():
    """إصلاح حقل edition في جدول books"""
    
    # إعدادات قاعدة البيانات
    db_config = {
        'host': '145.223.98.97',
        'port': 3306,
        'user': 'bms_db',
        'database': 'bms_db',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'auth_plugin': 'mysql_native_password'
    }
    
    try:
        print("🔌 الاتصال بقاعدة البيانات...")
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        print("🔍 فحص هيكل الجدول الحالي...")
        cursor.execute("DESCRIBE books")
        columns = cursor.fetchall()
        
        # البحث عن حقل edition
        edition_column = None
        for column in columns:
            if column[0] == 'edition':
                edition_column = column
                break
        
        if edition_column:
            print(f"📋 حقل edition الحالي: {edition_column[1]}")
            
            # فحص إذا كان النوع INTEGER
            if 'int' in edition_column[1].lower():
                print("⚠️ حقل edition من نوع INTEGER - يحتاج إصلاح!")
                
                print("🔧 تحويل حقل edition إلى VARCHAR(255)...")
                alter_query = """
                ALTER TABLE books 
                MODIFY COLUMN edition VARCHAR(255) NULL
                """
                cursor.execute(alter_query)
                connection.commit()
                print("✅ تم تحويل حقل edition بنجاح!")
                
            else:
                print("✅ حقل edition من النوع الصحيح")
        else:
            print("❌ حقل edition غير موجود")
        
        # فحص الهيكل الجديد
        print("\n🔍 فحص الهيكل بعد التعديل...")
        cursor.execute("DESCRIBE books")
        columns = cursor.fetchall()
        
        for column in columns:
            if column[0] == 'edition':
                print(f"✅ حقل edition الجديد: {column[1]}")
                break
        
        cursor.close()
        connection.close()
        print("\n🎉 تم إصلاح قاعدة البيانات بنجاح!")
        
    except mysql.connector.Error as e:
        print(f"❌ خطأ في قاعدة البيانات: {e}")
        return False
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 بدء إصلاح حقل edition في جدول books")
    print("=" * 50)
    
    success = fix_edition_column()
    
    if success:
        print("\n✅ تم الإصلاح بنجاح!")
        print("يمكنك الآن إعادة محاولة رفع ملفات JSON")
    else:
        print("\n❌ فشل في الإصلاح")
    
    input("\nاضغط Enter للخروج...")
