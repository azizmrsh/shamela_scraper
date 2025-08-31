# Benchmark Script for Windows - سكربت قياس الأداء لـ Windows

Write-Host "======================================" -ForegroundColor Green
Write-Host "قياس أداء سكربت المكتبة الشاملة المحسن" -ForegroundColor Green
Write-Host "Enhanced Shamela Scraper Benchmark" -ForegroundColor Green  
Write-Host "======================================" -ForegroundColor Green

# متغيرات الاختبار
$BookId = "1221"  # كتاب صغير للاختبار السريع
$MaxPages = 20
$OutputDir = "benchmark_results"

# إنشاء مجلد النتائج
if (!(Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

Write-Host ""
Write-Host "📊 بدء القياس..." -ForegroundColor Yellow
Write-Host "📖 الكتاب: $BookId" -ForegroundColor Cyan
Write-Host "📄 الصفحات: $MaxPages" -ForegroundColor Cyan
Write-Host ""

# قياس الأداء
Write-Host "⏱️ قياس الأداء..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$OutputDir\performance_test_$timestamp.log"

try {
    python test_performance.py --book-id $BookId --pages $MaxPages 2>&1 | Tee-Object -FilePath $logFile
    
    Write-Host ""
    Write-Host "✅ انتهى القياس. النتائج محفوظة في $OutputDir\" -ForegroundColor Green
    Write-Host ""
    Write-Host "لعرض النتائج:" -ForegroundColor Cyan
    Write-Host "Get-ChildItem $OutputDir\" -ForegroundColor Gray
    Write-Host ""
    Write-Host "لعرض آخر نتيجة:" -ForegroundColor Cyan
    Write-Host "Get-Content $logFile -Tail 20" -ForegroundColor Gray
    
}
catch {
    Write-Host "❌ فشل في تنفيذ الاختبار: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "تأكد من وجود Python والملفات المطلوبة" -ForegroundColor Red
}
