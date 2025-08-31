#!/bin/bash
# Benchmark Script - سكربت قياس الأداء الأساسي

echo "======================================"
echo "قياس أداء سكربت المكتبة الشاملة المحسن"
echo "Enhanced Shamela Scraper Benchmark"
echo "======================================"

# متغيرات الاختبار
BOOK_ID="1221"  # كتاب صغير للاختبار السريع
MAX_PAGES=20
OUTPUT_DIR="benchmark_results"

# إنشاء مجلد النتائج
mkdir -p "$OUTPUT_DIR"

echo ""
echo "📊 بدء القياس..."
echo "📖 الكتاب: $BOOK_ID"
echo "📄 الصفحات: $MAX_PAGES"
echo ""

# قياس الأداء
echo "⏱️ قياس الأداء..."
python test_performance.py --book-id "$BOOK_ID" --pages "$MAX_PAGES" > "$OUTPUT_DIR/performance_test_$(date +%Y%m%d_%H%M%S).log" 2>&1

# عرض النتائج
echo ""
echo "✅ انتهى القياس. النتائج محفوظة في $OUTPUT_DIR/"
echo ""
echo "لعرض النتائج:"
echo "ls -la $OUTPUT_DIR/"
echo ""
echo "لعرض آخر نتيجة:"
echo "tail -n 20 $OUTPUT_DIR/*.log"
