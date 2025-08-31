import re, json, time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from bs4 import BeautifulSoup

# ========= اضبط هالثوابت لتطابق جداولك =========
# books
BOOKS_PAGES_COL   = "pages_count"     # غيّر إلى "page_count" لو عندك هيك
BOOKS_VOLUMES_COL = "volumes_count"   # غيّر إلى "volume_count" لو عندك هيك
# chapters
CHAPTERS_PAGE_COL = "page_number"     # غيّر إلى "page_start" لو جدولك هيك
# pages
PAGES_TABLE       = "pages"
PAGES_PAGE_COL    = "page_number"
PAGES_CONTENT_COL = "content"

BASE_URL = "https://shamela.ws"
# HEADERS  = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"}
REQ_TIMEOUT   = 30
REQUEST_DELAY = 0.35  # احترام الخادم

try:
    from slugify import slugify
except ImportError:
    import unicodedata
    def slugify(text: str) -> str:
        text = unicodedata.normalize("NFKC", text or "").strip()
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"[^\w\-]+", "", text, flags=re.U)
        return text.strip("-").lower()

# ========= نماذج البيانات =========
@dataclass
class Author:
    name: str
    slug: Optional[str] = None
    biography: Optional[str] = None
    madhhab: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    def ensure_slug(self):
        if not self.slug and self.name:
            self.slug = slugify(self.name)

@dataclass
class Chapter:
    title: str
    page_number: Optional[int] = None
    children: List["Chapter"] = field(default_factory=list)
    volume_number: Optional[int] = None  # يُملأ لاحقًا

@dataclass
class Volume:
    number: int
    title: str
    page_start: Optional[int] = None
    page_end: Optional[int] = None

@dataclass
class Book:
    title: str
    shamela_id: str
    authors: List[Author] = field(default_factory=list)
    publisher: Optional[str] = None
    edition: Optional[str] = None
    publication_year: Optional[int] = None
    page_count: Optional[int] = None
    volume_count: Optional[int] = None
    categories: List[str] = field(default_factory=list)
    index: List[Chapter] = field(default_factory=list)
    volumes: List[Volume] = field(default_factory=list)

class ShamelaScraperError(Exception):
    pass


# ========= بطاقة الكتاب + الفهرس =========
def _parse_info_page(book_id: str, soup: BeautifulSoup) -> Tuple[Book, BeautifulSoup]:
    # Check for empty book content indicator
    if "محتوى الكتاب غير متوفر حالياً" in soup.get_text() or "No article found" in soup.get_text():
        raise ShamelaScraperError("الكتاب فارغ أو لا يحتوي على محتوى.")

    title_tag = soup.select_one("section.page-header h1 a")
    title = (title_tag.get_text(strip=True) if title_tag else "").strip()
    if not title:
        raise ShamelaScraperError("تعذّر استخراج عنوان الكتاب")

    authors: List[Author] = []
    for a in soup.select("section.page-header .container a[href*=\"/author/\"]"):
        name = a.get_text(strip=True)
        if name:
            au = Author(name=name); au.ensure_slug(); authors.append(au)

    cats: List[str] = []
    for a in soup.select("ol.breadcrumb a"):
        txt = a.get_text(strip=True)
        if txt and txt not in ("الرئيسية", "أقسام الكتب"):
            cats.append(txt)

    publisher = edition = None
    publication_year = None
    pages_or_parts = None  # ("pages"| "parts", value)

    nass = soup.select_one("div.nass") or soup
    lines = []
    for el in nass.find_all(["p", "li", "div", "span"], recursive=True):
        t = el.get_text(" ", strip=True)
        if ":" in t and len(t) < 200:
            lines.append(t)

    for line in lines:
        key, val = [s.strip() for s in line.split(":", 1)]
        if not val:
            continue
        if key in ("الناشر", "دار النشر"): publisher = val
        elif key in ("الطبعة", "الطبعةُ"):  edition = val
        elif key in ("سنة النشر", "عام النشر"):
            m = re.search(r"(\d{3,4})", val)
            if m:
                try: publication_year = int(m.group(1))
                except: pass
        elif key in ("عدد الصفحات",):
            m = re.search(r"(\d+)", val); 
            if m: pages_or_parts = ("pages", int(m.group(1)))
        elif key in ("عدد الأجزاء","الأجزاء"):
            m = re.search(r"(\d+)", val); 
            if m: pages_or_parts = ("parts", int(m.group(1)))

    book = Book(
        title=title,
        shamela_id=str(book_id),
        authors=authors,
        publisher=publisher,
        edition=edition,
        publication_year=publication_year,
        page_count=pages_or_parts[1] if (pages_or_parts and pages_or_parts[0]=="pages") else None,
        volume_count=pages_or_parts[1] if (pages_or_parts and pages_or_parts[0]=="parts") else None,
        categories=cats
    )
    return book, soup

def _pick_title_and_page(anchor, book_id: str) -> Tuple[str, Optional[int]]:
    if not anchor:
        return "", None
    title = anchor.get_text(strip=True)
    href  = anchor.get("href") or ""
    if f"/book/{book_id}/" in href:
        m = re.search(rf"/book/{book_id}/(\d+)", href)
        page = int(m.group(1)) if m else None
    else:
        page = None
    return title, page

def _parse_chapter_list(ul_tag, book_id: str) -> List[Chapter]:
    chapters: List[Chapter] = []
    for li in ul_tag.find_all("li", recursive=False):
        anchor = None
        for a in li.find_all("a", href=True):
            if f"/book/{book_id}/" in (a.get("href") or ""):
                anchor = a; break
        if anchor is None:
            anchor = li.find("a")

        title, page = _pick_title_and_page(anchor, book_id)
        if title in ("نسخ الرابط", "نشر لفيسيوك", "نشر لتويتر"):
            continue
        title = title.lstrip("-").strip()

        child_ul = li.find("ul")
        children = _parse_chapter_list(child_ul, book_id) if child_ul else []
        if title:
            chapters.append(Chapter(title=title, page_number=page, children=children))
    return chapters

def _parse_index_from_info_page(book_id: str, soup: BeautifulSoup) -> List[Chapter]:
    c = soup.select_one("div.betaka-index")
    if not c: return []
    ul = c.find("ul")
    if not ul: return []
    return _parse_chapter_list(ul, book_id)

# ========= آخر صفحة =========
def _detect_last_page(book_id: str, soup: BeautifulSoup) -> Optional[int]:
    # soup is now passed directly from the browser tool interaction
    max_page = 1
    for a in soup.select("a[href*=\"/book/\"]"):
        href = a.get("href") or ""
        m = re.search(rf"/book/{book_id}/(\d+)", href)
        if m:
            pg = int(m.group(1))
            if pg > max_page: max_page = pg
    for a in soup.select("ul.pagination a, .pagination a"):
        txt = (a.get_text() or "").strip()
        if txt in ("الأخير", ">>", "آخر"):
            m = re.search(rf"/book/{book_id}/(\d+)", a.get("href") or "")
            if m:
                pg = int(m.group(1))
                if pg > max_page: max_page = pg
    return max_page if max_page >= 1 else None

# ========= كشف الأجزاء ونطاقاتها من صفحة 1 =========
def _detect_parts_ranges(book_id: str, soup: BeautifulSoup) -> Tuple[List[Volume], Optional[int]]:
    # soup is now passed directly from the browser tool interaction

    last_page = 1
    for a in soup.select("a[href*=\"/book/\"]"):
        href = a.get("href") or ""
        m = re.search(rf"/book/{book_id}/(\d+)", href)
        if m:
            pg = int(m.group(1))
            if pg > last_page: last_page = pg
    if last_page < 1:
        last_page = None

    parts_links = []
    parts_links += soup.select("#fld_part_top ~ div ul[role=\"menu\"] li a[href]")
    if not parts_links:
        parts_links += soup.select("div.dropdown-menu a[href]")
    if not parts_links:
        for a in soup.select("a[href*=\"/book/\"]"):
            if "الجزء" in (a.get_text(strip=True) or ""):
                parts_links.append(a)

    parts: List[Tuple[str, Optional[int]]] = []
    for a in parts_links:
        label = a.get_text(strip=True)
        href  = a.get("href") or ""
        m = re.search(rf"/book/{book_id}/(\d+)", href)
        pstart = int(m.group(1)) if m else None
        if label and "الجزء" in label:
            parts.append((label, pstart))

    parts = [(t, p) for (t, p) in parts if t]
    parts.sort(key=lambda x: (x[1] if x[1] is not None else 10**9))

    volumes: List[Volume] = []
    if parts:
        for i, (label, pstart) in enumerate(parts):
            if pstart is None: continue
            if i+1 < len(parts):
                nstart = parts[i+1][1] or pstart
                pend   = (nstart - 1) if (nstart and nstart > pstart) else None
            else:
                pend   = last_page
            volumes.append(Volume(number=i+1, title=label, page_start=pstart, page_end=pend))
    else:
        volumes.append(Volume(number=1, title="المجلد", page_start=1, page_end=(last_page if last_page and last_page>1 else None)))

    return volumes, (last_page if last_page and last_page > 1 else None)

def _assign_chapters_to_volumes(chapters: List[Chapter], volumes: List[Volume]) -> None:
    def vol_for_page(pg: Optional[int]) -> Optional[int]:
        if pg is None: return None
        for v in volumes:
            s = v.page_start or 1
            e = v.page_end or 10**9
            if s <= pg <= e:
                return v.number
        return None
    def walk(nodes: List[Chapter]):
        for ch in nodes:
            ch.volume_number = vol_for_page(ch.page_number)
            if ch.children:
                walk(ch.children)
    walk(chapters)

# ========= API رئيسي =========
def parse_book_page(book_id: str, soup_info_page: BeautifulSoup, soup_first_page: BeautifulSoup) -> Book:
    book, _ = _parse_info_page(book_id, soup_info_page)
    book.index = _parse_index_from_info_page(book_id, soup_info_page)

    vols, last_page = _detect_parts_ranges(book_id, soup_first_page)
    # حدّث إجمالي الصفحات إن وجدنا أكبر صفحة
    last_page2 = _detect_last_page(book_id, soup_first_page)
    if last_page2 and (not last_page or last_page2 > last_page):
        last_page = last_page2

    if last_page and (not book.page_count or book.page_count < last_page):
        book.page_count = last_page

    # لا نُخفّض العدد إن البطاقة قالت >1
    if vols and len(vols) > 1:
        book.volumes = vols
        book.volume_count = len(vols)
    else:
        if (book.volume_count or 0) > 1:
            book.volumes = [Volume(number=i+1, title=f"الجزء {i+1}") for i in range(book.volume_count)]
        else:
            book.volume_count = 1
            book.volumes = [Volume(number=1, title="المجلد", page_start=1, page_end=last_page)]

    _assign_chapters_to_volumes(book.index, book.volumes)
    return book

# ========= SQL: books/authors/volumes/chapters =========
def flatten_chapters(chs: List[Chapter], level: int = 0) -> List[Dict]:
    rows = []
    for ch in chs:
        rows.append({
            "title": ch.title.strip(),
            "page_number": ch.page_number,
            "level": level,
            "volume_number": ch.volume_number
        })
        if ch.children:
            rows.extend(flatten_chapters(ch.children, level+1))
    return rows

def mysql_escape(val: Optional[str]) -> str:
    if val is None: return "NULL"
    # Escape backslashes and double quotes for SQL string literals
    return "\"" + str(val).replace("\\", "\\\\").replace("\"", "\\\"") + "\""

def generate_insert_sql(book: Book) -> str:
    bslug = slugify(book.title or f"book-{book.shamela_id}")
    cats  = json.dumps(book.categories or [], ensure_ascii=False)

    lines = []
    lines.append("START TRANSACTION;")
    lines.append("SET NAMES utf8mb4;")
    lines.append("SET @book_id := 0;")

    # books
    lines.append("-- books")
    lines.append(f"""
INSERT INTO books (title, slug, publisher, edition, publication_year, {BOOKS_PAGES_COL}, {BOOKS_VOLUMES_COL}, shamela_id, categories, source_url)
VALUES ({mysql_escape(book.title)}, {mysql_escape(bslug)}, {mysql_escape(book.publisher)}, {mysql_escape(book.edition)},
        {book.publication_year if book.publication_year else "NULL"},
        {book.page_count if book.page_count else "NULL"},
        {book.volume_count if book.volume_count else "NULL"},
        {mysql_escape(book.shamela_id)},
        {mysql_escape(cats)},
        {mysql_escape(f"{BASE_URL}/book/{book.shamela_id}")})
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id),
    title=VALUES(title), publisher=VALUES(publisher), edition=VALUES(edition),
    publication_year=VALUES(publication_year), {BOOKS_PAGES_COL}=VALUES({BOOKS_PAGES_COL}),
    {BOOKS_VOLUMES_COL}=VALUES({BOOKS_VOLUMES_COL}), categories=VALUES(categories), source_url=VALUES(source_url);
SET @book_id := LAST_INSERT_ID();
""".strip())

    # authors + author_book
    lines.append("-- authors + author_book")
    for a in (book.authors or []):
        a.ensure_slug()
        lines.append("SET @a_id := 0;")
        lines.append(f"""
INSERT INTO authors (name, slug, biography, madhhab, birth_date, death_date)
VALUES ({mysql_escape(a.name)}, {mysql_escape(a.slug)}, {mysql_escape(a.biography)}, {mysql_escape(a.madhhab)}, {mysql_escape(a.birth_date)}, {mysql_escape(a.death_date)})
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), name=VALUES(name);
SET @a_id := LAST_INSERT_ID();
INSERT IGNORE INTO author_book (book_id, author_id, role, is_main) VALUES (@book_id, @a_id, 'author', 1);
""".strip())

    # volumes
    lines.append("-- volumes")
    for v in (book.volumes or [Volume(1, "المجلد")]):
        lines.append(f"""
INSERT INTO volumes (book_id, number, title, page_start, page_end)
VALUES (@book_id, {v.number}, {mysql_escape(v.title)}, {v.page_start if v.page_start else "NULL"}, {v.page_end if v.page_end else "NULL"})
ON DUPLICATE KEY UPDATE id = LAST_INSERT_ID(id), title=VALUES(title), page_start=VALUES(page_start), page_end=VALUES(page_end);
""".strip())

    # chapters
    lines.append("-- chapters")
    flat = flatten_chapters(book.index or [])
    for ch in flat:
        vol_no = ch["volume_number"]
        vol_id_expr = "NULL"
        if vol_no:
            vol_id_expr = f"(SELECT id FROM volumes WHERE book_id=@book_id AND number={vol_no} LIMIT 1)"
        page_expr = ch["page_number"] if ch["page_number"] else "NULL"
        lines.append(f"""
INSERT INTO chapters (book_id, volume_id, title, {CHAPTERS_PAGE_COL}, page_end, parent_id, level)
VALUES (@book_id, {vol_id_expr}, {mysql_escape(ch['title'])}, {page_expr}, NULL, NULL, {ch['level']});
""".strip())

    lines.append("COMMIT;")
    return "\n".join(lines)

# ========= الصفحات: جلب وتوليد SQL =========
def fetch_page_content(book_id: str, page_no: int, soup: BeautifulSoup, as_html: bool = False) -> str:
    # soup is now passed directly from the browser tool interaction

    candidates = [
        soup.find(id="book"),
        soup.select_one("div#text"),
        soup.select_one("article"),
        soup.select_one("div.reader-text"),
        soup.select_one("div.col-md-9")
    ]
    main = next((c for c in candidates if c), None) or soup.find("body") or soup

    # تنظيف عناصر مزعجة
    for bad in main.select("script, style, nav, .share, .social, .ad, .navbar, .pagination"):
        bad.decompose()

    if as_html:
        return main.decode()

    text = main.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def fetch_pages_for_book(book: Book, get_soup_wrapper: callable, as_html: bool = False) -> List[Tuple[int, str]]:
    # get_soup_wrapper is a callable that takes url and returns soup
    last_page = book.page_count or _detect_last_page(book.shamela_id, get_soup_wrapper(f"{BASE_URL}/book/{book.shamela_id}/1")) or 1
    vols = book.volumes or [Volume(1, "المجلد", 1, last_page)]

    def vol_for_page(pg):
        for v in vols:
            s, e = v.page_start or 1, v.page_end or 10**9
            if s <= pg <= e:
                return v.number
        return None

    pages = []
    for p in range(1, last_page + 1):
        page_url = f"{BASE_URL}/book/{book.shamela_id}/{p}"
        soup = get_page_soup_func(page_url)
        txt = fetch_page_content(book.shamela_id, p, soup, as_html=as_html)
        pages.append({"page_number": p, "volume_number": vol_for_page(p), "content": txt})
    return pages

def generate_pages_insert_sql(book: Book, pages: List[Dict]) -> str:
    """
    INSERT لجدول الصفحات:
    - book_id من books
    - volume_id عبر (book_id, number)
    - chapter_id: أقرب فصل يبدأ قبل/عند الصفحة (subquery)
    """
    lines = []
    lines.append("START TRANSACTION;")
    lines.append("SET NAMES utf8mb4;")
    lines.append(f"SET @book_id := (SELECT id FROM books WHERE shamela_id=\"{book.shamela_id}\" LIMIT 1);")
    lines.append("SET @vol_id := NULL;")
    lines.append("SET @chap_id := NULL;")

    for page in pages:
        vol_no = page["volume_number"]
        page_no = page["page_number"]
        content = page["content"]

        vol_id_expr = "NULL"
        if vol_no:
            vol_id_expr = f"(SELECT id FROM volumes WHERE book_id=@book_id AND number={vol_no} LIMIT 1)"

        # Find the closest chapter_id that starts before or at the current page_no
        chapter_id_expr = f"(SELECT id FROM chapters WHERE book_id=@book_id AND {CHAPTERS_PAGE_COL} <= {page_no} ORDER BY {CHAPTERS_PAGE_COL} DESC LIMIT 1)"

        lines.append(f"""
INSERT INTO {PAGES_TABLE} (book_id, volume_id, chapter_id, {PAGES_PAGE_COL}, {PAGES_CONTENT_COL})
VALUES (@book_id, {vol_id_expr}, {chapter_id_expr}, {page_no}, {mysql_escape(content)})
ON DUPLICATE KEY UPDATE {PAGES_CONTENT_COL}=VALUES({PAGES_CONTENT_COL});
""".strip())

    lines.append("COMMIT;")
    return "\n".join(lines)

# New functions for category scraping using browser tools
def _extract_book_ids_from_browser_page(soup: BeautifulSoup) -> List[str]:
    book_ids = []
    # Select all <a> tags with href containing "/book/" and extract the book ID
    # The links are typically within the main content area, not necessarily div.col-md-9
    for a in soup.select("a[href*=\"/book/\"]"):
        href = a.get("href")
        if href:
            m = re.search(r"/book/(\d+)", href)
            if m and m.group(1) not in book_ids:
                book_ids.append(m.group(1))
    return book_ids

def _extract_category_links_from_browser_page(soup: BeautifulSoup) -> List[str]:
    category_links = []
    # Category links are usually in <a> tags with href containing "/categories?categoryId="
    for a in soup.select("a[href*=\"/categories?categoryId=\"]"):
        href = a.get("href")
        if href and href.startswith("/categories?categoryId=") and href not in category_links:
            category_links.append(href)
    return category_links

def get_all_book_ids_in_category_browser(category_url: str, get_soup_wrapper: callable) -> List[str]:
    all_book_ids = []
    visited_urls = set()
    urls_to_visit = [category_url]

    while urls_to_visit:
        current_url = urls_to_visit.pop(0)
        full_current_url = current_url if current_url.startswith("http") else BASE_URL + current_url

        if full_current_url in visited_urls:
            continue
        visited_urls.add(full_current_url)

        print(f"Navigating to: {full_current_url}")
        try:
            soup = get_soup_wrapper(full_current_url)
        except Exception as e:
            print(f"Error fetching {full_current_url}: {e}")
            continue

        # Extract book IDs from the current page
        all_book_ids.extend(_extract_book_ids_from_browser_page(soup))

        # Find pagination links and add them to urls_to_visit
        # On web.mutakamela.org, pagination is usually in the form of ?page=X in the URL
        # We need to check if there\'s a next page link or if we can infer it.
        # For now, let\'s assume all books are on one page for a category, or we need to scroll.
        # Since there are no explicit pagination links, we\'ll rely on initial load.
        # If a category has many books, we might need to scroll down to load more.
        # For now, we\'ll only process the initially loaded page.
        
        # Find sub-category links and add them to urls_to_visit (recursive part)
        # This part is crucial for navigating through the category tree.
        for link in _extract_category_links_from_browser_page(soup):
            if BASE_URL + link not in visited_urls:
                urls_to_visit.append(BASE_URL + link)

    # Remove duplicates and return
    return sorted(list(set(all_book_ids)))

# Example usage (for testing purposes, will be integrated into main script)
if __name__ == '__main__':
    # This part will be removed or modified to be called from a main script
    pass


