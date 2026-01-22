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
# Core Keywords: 로밍, eSIM, SKT 바로, 도시락 eSIM, 말톡, 유심사, 이지에심, 핀다이렉트
# Tech/Quality: 스타링크, 로밍 속도, 로밍 불만, 로밍 품질, 로밍 불편, 5G SA 로밍, eSIM 장점, eSIM 속도, eSIM 편리
NAVER_SEARCH_KEYWORDS = [
    "로밍", "eSIM", "SKT 바로", "도시락 eSIM", "말톡", "유심사", "이지에심", "핀다이렉트",
    "로밍 속도", "로밍 불만", "로밍 품질", "로밍 불편",
    "eSIM 장점", "eSIM 속도", "eSIM 편리"
]

# 2. Travel/Culture (Naver & Google Hybrid)
# Keywords: (Reference only, used in logic): (로밍 OR eSIM) ("일본 여행" OR "중국 여행" OR "베트남 여행" OR "필리핀 여행" OR "한국 여행" OR "케이팝" OR "K-POP" OR "한류")
# Market: 출국자수, 입국자수, 출입국자수, 출국자 동향, 입국자 동향, 해외 여행객수
MARKET_KEYWORDS_QUERY = '(로밍 OR eSIM) ("일본 여행" OR "중국 여행" OR "베트남 여행" OR "필리핀 여행" OR "한국 여행" OR "케이팝" OR "K-POP" OR "한류" OR "출국자수" OR "입국자수" OR "출입국자수" OR "출국자 동향" OR "입국자 동향" OR "해외 여행객수")'

# 3. Global Channels (Google Only)
# Keywords: ("Roaming industry" OR "eSIM market") ("trends" OR "analysis" OR "future")
GOOGLE_GLOBAL_QUERIES = [
    '("Roaming industry" OR "eSIM market") ("trends" OR "analysis" OR "future")'
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
