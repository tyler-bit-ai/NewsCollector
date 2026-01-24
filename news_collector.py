import requests
import datetime
import urllib.parse
from email.utils import parsedate_to_datetime
from config import (
    GOOGLE_API_KEY, SEARCH_ENGINE_ID,
    NAVER_CLIENT_ID, NAVER_CLIENT_SECRET,
    BLACKLIST_DOMAINS, EXCLUDED_KEYWORDS,
    NAVER_SEARCH_KEYWORDS, NAVER_VOC_KEYWORDS, NAVER_COMPETITOR_KEYWORDS,
    MARKET_KEYWORDS_QUERY,
    GOOGLE_GLOBAL_QUERIES, COMMUNITY_SITES
)
from smart_filter import SmartFilter


class CategoryClassifier:
    """키워드 기반 간단 카테고리 분류기"""

    # 카테고리별 키워드 정의
    CATEGORY_KEYWORDS = {
        'market_culture': [
            '입국자', '출국자', '출입국자', '입국자수', '출국자수',
            'K-POP', '케이팝', '한류', '한국 여행', '일본 여행', '중국 여행',
            '베트남 여행', '필리핀 여행', '해외 여행객', '여행객수', '관광객'
        ],
        'global_trend': [
            # global 타입 기사는 나중에 처리
        ],
        'competitors': [
            'KT 로밍', 'KT 데이터', 'KT 로밍 요금제', 'kt 로밍', 'kt 데이터',
            'LGU+ 로밍', 'LG유플러스 로밍', 'lgu+ 로밍', 'lg유플러스',
            'KT 통신', 'LGU+ 통신'
        ],
        'esim_products': [
            '도시락 esim', '도시락이심', '도시락 프로모션', '도시락 할인',
            '말톡 esim', '말톡이심', '말톡 프로모션', '말톡 할인',
            '유심사', '이지이심', '핀다이렉트', 'eSIM 프로모션', 'esim 프로모션'
        ],
        'voc_roaming': [
            '로밍 후기', '로밍 리뷰', '로밍 추천', '로밍 재구매',
            '로밍 사용기', '로밍 사용법', '로밍 추천'
        ],
        'voc_esim': [
            'eSIM 후기', 'esim 후기', 'eSIM 리뷰', 'esim 리뷰',
            'eSIM 추천', 'esim 추천', 'eSIM 재구매', 'esim 재구매',
            '도시락 후기', '말톡 후기', '유심사 후기', '이지이심 후기'
        ]
    }

    @classmethod
    def classify_article(cls, article: dict) -> str:
        """
        기사를 키워드 기반으로 카테고리 분류

        Returns:
            카테고리 키 (market_culture, global_trend, competitors, esim_products, voc_roaming, voc_esim, other)
        """
        title = article.get('title', '').lower()
        snippet = article.get('snippet', '').lower()
        combined = f"{title} {snippet}"

        # Global 기사는 type으로 확인
        if article.get('type') == 'global':
            return 'global_trend'

        # 각 카테고리 키워드 확인 (우선순위대로)
        priority_order = ['competitors', 'voc_roaming', 'voc_esim', 'esim_products', 'market_culture']

        for category in priority_order:
            keywords = cls.CATEGORY_KEYWORDS[category]
            for keyword in keywords:
                if keyword.lower() in combined:
                    return category

        return 'other'  # 분류되지 않은 기사


class NewsCollector:
    def __init__(self, debug_mode=False):
        # Google Keys
        self.google_api_key = GOOGLE_API_KEY
        self.google_cse_id = SEARCH_ENGINE_ID
        self.google_base_url = "https://www.googleapis.com/customsearch/v1"
        self.google_quota_exceeded = False

        # Naver Keys
        self.naver_client_id = NAVER_CLIENT_ID
        self.naver_client_secret = NAVER_CLIENT_SECRET
        self.naver_base_url = "https://openapi.naver.com/v1/search"

        # Debug Mode
        self.debug_mode = debug_mode

        # Smart Filter
        self.smart_filter = SmartFilter(debug_mode=debug_mode)

    def clean_naver_link(self, link: str, category: str) -> str:
        """
        네이버 링크에서 리디렉트/랜딩 페이지 제거
        실제 기사/블로그 글 원본 링크로 변환
        """
        if not link:
            return link

        # 이미 정상적인 링크 형태이면 그대로 반환
        # 정상 형태: news.naver.com/..., blog.naver.com/아이디/번호
        if '/blog.naver.com/' in link and '/Promotion' not in link:
            return link
        if 'news.naver.com/' in link and 'view.nhn' in link:
            return link

        # 블로그 프로모션/랜딩 페이지 처리
        if '/blog.naver.com/' in link and ('/Promotion' in link or 'blogId=' in link):
            # blogId와 logNo 추출 시도
            parsed = urllib.parse.urlparse(link)
            params = urllib.parse.parse_qs(parsed.query)

            blog_id = params.get('blogId', [''])[0]
            log_no = params.get('logNo', [''])[0]

            if blog_id and log_no:
                return f"https://blog.naver.com/{blog_id}/{log_no}"

        # 그 외 경우는 원본 링크 반환
        return link

    def validate_article(self, article):
        """
        [Strict Validation]
        Filters out games, finance, irrelevant content, and blacklist domains.
        """
        link = article.get('link', '')
        title = article.get('title', '').lower()
        snippet = article.get('snippet', '').lower()

        # 1. URL Pattern Check
        if any(blocked in link for blocked in BLACKLIST_DOMAINS):
            if self.debug_mode:
                print(f"[FILTERED] URL Blacklist: {title[:50]}...")
            return None

        # 2. Strict Keyword Exclusion (Game, Finance, etc.)
        # Check Title & Snippet
        combined_text = f"{title} {snippet}"
        for bad_word in EXCLUDED_KEYWORDS:
            if bad_word.lower() in combined_text:
                if self.debug_mode:
                    print(f"[FILTERED] Keyword '{bad_word}': {title[:50]}...")
                return None

        # Check Link for bad words (sometimes helpful)
        if any(bad_word.lower() in link.lower() for bad_word in EXCLUDED_KEYWORDS):
            if self.debug_mode:
                print(f"[FILTERED] Link Keyword: {title[:50]}...")
            return None

        return article

    def deduplicate(self, articles):
        """Removes duplicates based on normalized Title and URL"""
        unique_articles = []
        seen_titles = set()
        seen_links = set()

        for article in articles:
            # Simple normalization: remove spaces, lowercase
            clean_title = article['title'].replace(' ', '').replace('<b>', '').replace('</b>', '').replace('&quot;', '').lower()
            
            if clean_title in seen_titles:
                continue
            if article['link'] in seen_links:
                continue

            # Clean up HTML tags in title/snippet for final output
            article['title'] = article['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            article['snippet'] = article['snippet'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')

            unique_articles.append(article)
            seen_titles.add(clean_title)
            seen_links.add(article['link'])
            
        return unique_articles

    def check_time_validity(self, pub_date_obj):
        """
        Checks if the datetime object is within the recent 24 hours.
        Expects a datetime object (offset-aware preferably).
        """
        if not pub_date_obj:
            return True # Fallback if parsing fails but source is trusted "recent"

        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Ensure pub_date_obj is timezone aware for comparison
        if pub_date_obj.tzinfo is None:
            # Assume local time if naive, or UTC?? Naver usually gives local KST but in string format.
            # Ideally we parsed it to aware datetime.
            # If naive, assume it's close enough or safe to compare if we make now naive (bad practice)
            # Let's attach UTC if naive just to prevent crash, though it might be off by 9h.
            pub_date_obj = pub_date_obj.replace(tzinfo=datetime.timezone.utc)

        diff = now - pub_date_obj
        # Strict 24 hours
        return diff < datetime.timedelta(hours=24)

    def collect_from_naver(self, query, categories=['news', 'blog', 'cafearticle']):
        """
        Collects from Naver Open API.
        categories: list of 'news', 'blog', 'cafearticle'
        """
        print(f"[Naver] Searching: {query} in {categories}")
        
        headers = {
            "X-Naver-Client-Id": self.naver_client_id,
            "X-Naver-Client-Secret": self.naver_client_secret
        }
        
        all_items = []

        for category in categories:
            url = f"{self.naver_base_url}/{category}.json"
            params = {
                "query": query,
                "display": 50, # Maximize fetch to allow filtering
                "sort": "date" # Sort by date to get newest
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.status_code != 200:
                    print(f"[ERROR] Naver API ({category}) failed: {response.status_code}")
                    continue
                
                data = response.json()
                items = data.get('items', [])
                
                for item in items:
                    # Date Handling
                    # News: "pubDate": "Mon, 19 Jan 2026 12:00:00 +0900"
                    # Blog/Cafe: "postdate": "20260119" (YYYYMMDD) - No time!
                    
                    pub_date_obj = None
                    raw_date = item.get('pubDate') or item.get('postdate')
                    
                    if raw_date:
                        try:
                            if category == 'news':
                                pub_date_obj = parsedate_to_datetime(raw_date)
                            else:
                                # Blog/Cafe returns YYYYMMDD
                                pub_date_obj = datetime.datetime.strptime(raw_date, "%Y%m%d")
                                # Set time to 00:00 KST roughly? Or just accept if date is today/yesterday.
                                # Let's make it offset specific if possible, or naive. 
                                # Better: just convert to date and compare with today's date for strictness?
                                # Requirement: Recent 24 hours. "20260119" -> covers 00:00 to 23:59.
                                # If today is 20th 09:00, 19th is within 24h? Maybe.
                                # Let's attach KST timezone to be safe if comparing with NOW.
                                kst = datetime.timezone(datetime.timedelta(hours=9))
                                pub_date_obj = pub_date_obj.replace(tzinfo=kst)

                        except Exception:
                            pass # Keep None
                    
                    # Validate Time (Strict 24h)
                    if not self.check_time_validity(pub_date_obj):
                         # For Blog/Cafe which implies "Day" granularity, we might be lenient
                         # If it's today or yesterday, we accept.
                         # check_time_validity is strict timedelta. 
                         # If '20260118' (yesterday) and now is '20260119 20:00', delta is > 24h (from 00:00).
                         # We might lose valid posts. 
                         # Refine: If blog/cafe, allow 'yesterday' even if technically > 24h from 00:00
                         if category in ['blog', 'cafearticle'] and raw_date:
                             # Simple string check: today or yesterday
                             today_str = datetime.datetime.now().strftime("%Y%m%d")
                             yesterday_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")
                             if raw_date != today_str and raw_date != yesterday_str:
                                 continue
                         else:
                             continue # Strict time check failed for news
                    
                    # Link Cleaning: Remove Naver redirect/landing pages
                    raw_link = item.get('link', '')
                    clean_link = self.clean_naver_link(raw_link, category)

                    # Standardization
                    article = {
                        'title': item.get('title'),
                        'link': clean_link,
                        'snippet': item.get('description'),
                        'source': f"Naver {category.capitalize()}",
                        'published': raw_date,
                        'type': 'domestic' # default type, refined later
                    }
                    
                    if self.validate_article(article):
                        all_items.append(article)
                        
            except Exception as e:
                print(f"[ERROR] Naver API Exception: {e}")
                continue

        return self.deduplicate(all_items)

    def collect_from_google(self, queries, num=10):
        """
        Collects from Google Custom Search API.
        Used for Global Trends & Backup.
        """
        if self.google_quota_exceeded:
            return []
            
        print(f"[Google] Searching: {len(queries)} queries...")
        all_items = []
        
        for query in queries:
            try:
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cse_id,
                    'q': query,
                    'dateRestrict': 'd1', # API level 24h restrict
                    'sort': 'date',
                    'num': num
                }
                response = requests.get(self.google_base_url, params=params)
                if response.status_code == 429:
                    self.google_quota_exceeded = True
                    break
                
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        article = {
                            'title': item.get('title'),
                            'link': item.get('link'),
                            'snippet': item.get('snippet'),
                            'source': item.get('displayLink'),
                            'type': 'global'
                        }
                        if self.validate_article(article):
                            all_items.append(article)
                            
            except Exception as e:
                print(f"[ERROR] Google API Exception: {e}")
                continue
                
        return self.deduplicate(all_items)

    def collect_hybrid(self):
        """
        Master method to collect from all sources.
        """
        print("=== Starting Hybrid Data Collection ===")

        # 1. Domestic & Market (Naver priority)
        # Combine predefined keywords into a single efficient query loop or specific calls
        domestic_articles = []

        # A. Core Keywords -> News, Blog, Cafe
        for keyword in NAVER_SEARCH_KEYWORDS:
            domestic_articles.extend(self.collect_from_naver(keyword, categories=['news', 'blog', 'cafearticle']))

        # B. Market/Culture Keywords -> News, Blog
        domestic_articles.extend(self.collect_from_naver(MARKET_KEYWORDS_QUERY, categories=['news', 'blog']))

        # C. VOC Keywords -> Blog, Cafe (Community focus for customer reviews)
        for keyword in NAVER_VOC_KEYWORDS:
            domestic_articles.extend(self.collect_from_naver(keyword, categories=['blog', 'cafearticle']))

        # D. Competitor Keywords -> News
        for keyword in NAVER_COMPETITOR_KEYWORDS:
            domestic_articles.extend(self.collect_from_naver(keyword, categories=['news']))

        # 2. Global (Google)
        global_articles = self.collect_from_google(GOOGLE_GLOBAL_QUERIES, num=10)

        return {
            'domestic': self.deduplicate(domestic_articles),
            'global': global_articles
        }
