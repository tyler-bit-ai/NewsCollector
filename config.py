import os
from dotenv import load_dotenv

load_dotenv()

# Google Custom Search API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

# Naver Search API
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY").strip() if os.getenv("OPENAI_API_KEY") else None
OPENAI_BASE_URL = "https://api.platform.a15t.com/v1"
OPENAI_MODEL_BASIC = "openai/gpt-4o-mini-2024-07-18"
OPENAI_MODEL_ADVANCED = "openai/gpt-5-2025-08-07"

# --- Hybrid Search Strategy & Queries ---

# 1. Domestic Channels (Naver News/Blog/Cafe)
# Note: Removed NAVER_SEARCH_KEYWORDS - keywords are now category-specific

# 1.1 eSIM Products (Companies) - For eSIM category (Naver News)
# eSIM 사업자/프로모션 관련 키워드
NAVER_ESIM_PRODUCTS_KEYWORDS = [
    "유심사", "말톡", "핀다이렉트", "도시락 eSIM", "로밍 도깨비"
]

# 1.2 Roaming VOC Keywords - For 로밍 VoC category (Naver Blog, Cafe)
# 로밍 관련 고객 후기/리뷰
NAVER_ROAMING_VOC_KEYWORDS = [
    "로밍 후기", "로밍 리뷰", "로밍 추천", "로밍 재구매"
]

# 1.3 eSIM VOC Keywords - For eSIM VoC category (Naver Blog, Cafe)
# eSIM 관련 고객 후기/리뷰
NAVER_ESIM_VOC_KEYWORDS = [
    "도시락 eSIM후기", "도시락eSIM 리뷰", "도시락eSIM 추천",
    "말톡 후기", "말톡 리뷰", "말톡 추천",
    "유심사 후기", "유심사 리뷰",
    "이지이심 후기", "이지이심 리뷰",
    "eSIM 후기", "eSIM 리뷰", "eSIM 추천", "eSIM 재구매",
    "로밍도깨비 후기", "로밍도깨비 추천",
    "핀다이렉트 eSIM후기", "핀다이렉트 eSIM 추천"
]

# 1.4 Competitor-Specific Keywords
# For SKT & Competitors category (Naver News)
NAVER_COMPETITOR_KEYWORDS = [
    "KT 로밍", "KT 데이터 로밍", "KT 로밍 요금제",
    "LGU+ 로밍", "LG유플러스 로밍", "LGU+ 데이터 로밍",
    "SKT 바로 로밍",  # For comparison
    "SKT baro", "SKT 바로"
]

# 2. Travel/Culture (Naver & Google Hybrid)
# Market & Culture Keywords - For Market & Culture category (Naver News, Blog)
# 여행/문화 관련 키워드
NAVER_MARKET_CULTURE_KEYWORDS = [
    "일본 여행", "중국 여행", "베트남 여행", "필리핀 여행", "한국 여행",
    "케이팝", "K-POP", "한류",
    "출국자수", "입국자수", "출입국자수", "출국자 동향", "입국자 동향", "해외 여행객수"
]

# 3. Global Channels (Google Only)
# Comprehensive keywords: roaming business, global eSIM industry, travel connectivity market
# Strategic keywords (trends): travel eSIM trends 2026, roaming market outlook, MVNO roaming services
# Technical keywords (insights): 5G SA roaming, satellite cellular convergence, SGP.32 eSIM, Starlink roaming
GOOGLE_GLOBAL_QUERIES = [
    "roaming business",
    "global eSIM industry",
    "travel connectivity market",
    "travel eSIM trends 2026",
    "roaming market outlook",
    "MVNO roaming services",
    "5G SA roaming",
    "satellite cellular convergence",
    "SGP.32 eSIM",
    "Starlink roaming"
]

# Community Sites (for potential Google fallback or VOC classification)
COMMUNITY_SITES = ["ppomppu.co.kr", "clien.net", "cafe.naver.com", "theqoo.net", "fmkorea.com", "ruliweb.com", "instiz.net", "dcinside.com", "threads.net", "threads.com"]

# Filter Settings (Strict Noise Reduction)
BLACKLIST_DOMAINS = [
    'list.php', 'search', 'category', 'tag', 'bbs/board.php', 'main.php', '/index', 
    'view_all', 'login', 'deal', 'promo', 'membership', 'profile', 'attendance'
]

EXCLUDED_KEYWORDS = [
    # Game Blocking (Strict)
    "game", "게임", "게이밍", "롤", "LoL", "배그", "RPG", "MMORPG", "서버 로밍", "Zone", "리그오브레전드", "PUBG", "아이템", "서버이동", "던파", "메이플",
    # Finance/Ads Blocking
    "트래블로그", "트래블월렛", "환전", "수수료", "이벤트", "광고", "지급", "쿠폰", "당첨", "사전예약", "카드", "적금"
]

# Email Settings
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

DEFAULT_RECIPIENTS = [
    "sib1979@sk.com",
    "minchaekim@sk.com",
    "hyunju11.kim@sk.com",
    "jieun.baek@sk.com",
    "yjwon@sk.com",
    "letigon@sk.com",
    "lsm0787@sk.com",
    "maclogic@sk.com",
    "jungjaehoon@sk.com",
    "hw.cho@sk.com",
    "chlskdud0623@sk.com",
    "youngmin.choi@sk.com",
    "jinyeol.han@sk.com",
    "jeongwoo.hwang@sk.com",
    "funda@sk.com"
]
