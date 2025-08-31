@echo off
chcp 65001 > nul
echo ================================================
echo Enhanced Shamela Runner GUI
echo واجهة رسومية محسنة لتشغيل المكتبة الشاملة
echo ================================================
echo.

echo جاري تشغيل الواجهة الرسومية...
echo Starting GUI application...
echo.

python enhanced_runner_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo خطأ في تشغيل التطبيق. تأكد من:
    echo Error running application. Please check:
    echo - Python مثبت ومتاح في PATH
    echo - جميع المكتبات المطلوبة مثبتة
    echo - ملف enhanced_runner_gui.py موجود
    echo.
    pause
)
