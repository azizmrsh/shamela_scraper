-- إصلاح حقل edition في جدول books
-- تحويل من INTEGER إلى VARCHAR(255)

-- فحص الهيكل الحالي
DESCRIBE books;

-- إصلاح حقل edition
ALTER TABLE books MODIFY COLUMN edition VARCHAR(255) NULL;

-- فحص النتيجة
DESCRIBE books;
