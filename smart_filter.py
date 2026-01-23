"""
Smart Filter for Roaming News Bot
- Score-based relevance calculation
- Context-aware keyword filtering
- Token optimization for AI analysis
"""

import re
import datetime
from typing import Dict, Optional


class SmartFilter:
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode

        # 핵심 키워드 및 가중치
        self.CORE_KEYWORDS = {
            "로밍": 10,
            "eSIM": 10,
            "esim": 8,
            "SKT 바로": 15,
            "도시락 eSIM": 12,
            "말톡": 10,
            "유심사": 10,
            "이지에심": 10,
            "핀다이렉트": 10
        }

        # 2차 키워드
        self.SECONDARY_KEYWORDS = {
            "KT": 8,
            "LGU+": 8,
            "LG유플러스": 8,
            "스타링크": 7,
            "5G SA": 7,
            "데이터 로밍": 9,
            "해외 데이터": 8,
            "여행 SIM": 8
        }

        # 게임 관련 키워드 (문맥 분석용)
        self.GAME_KEYWORDS = {
            "리그오브레전드", "롤체", "롤드컵", "티어", "랭크",
            "챔피언", "소환사의 협곡", "LoL", "PUBG", "배그",
            "MMORPG", "RPG", "서버 이동", "서버 로밍", "던파", "메이플"
        }

        # 통신 관련 문맥 키워드
        self.TELECOM_CONTEXT = {
            "통신", "이동통신", "요금제", "데이터", "네트워크",
            "속도", "품질", "커버리지", "해외", "여행", "출국"
        }

        # 출처 신뢰도 점수
        self.SOURCE_CREDIBILITY = {
            # 주요 언론사
            "yna.co.kr": 100,
            "newsis.com": 95,
            "news1.kr": 95,
            "hankyung.com": 95,
            "mk.co.kr": 95,
            "mt.co.kr": 95,
            # IT 전문지
            "zdnet.co.kr": 90,
            "bloter.net": 90,
            "etnews.com": 90,
            # 포털
            "news.naver.com": 85,
            "v.daum.net": 85,
            # 기본값
            "default": 60
        }

        # 블로그/카페 패턴
        self.BLOG_PATTERNS = ["blog.naver.com", "tistory.com", "brunch.co.kr"]
        self.CAFE_PATTERNS = ["cafe.naver.com", "cafe.daum.net"]

        # 커뮤니티 패턴 (낮은 신뢰도)
        self.COMMUNITY_PATTERNS = [
            "ppomppu.co.kr", "clien.net", "theqoo.net",
            "fmkorea.com", "ruliweb.com", "instiz.net", "dcinside.com"
        ]

    def calculate_keyword_density_score(self, title: str, snippet: str) -> float:
        """
        키워드 밀도 기반 점수 계산 (0~100)
        """
        combined_text = f"{title} {snippet}".lower()
        text_length = len(combined_text)

        if text_length == 0:
            return 0.0

        total_score = 0

        # 핵심 키워드 검색
        for keyword, weight in self.CORE_KEYWORDS.items():
            count = combined_text.count(keyword.lower())
            if count > 0:
                # 빈도수 × 가중치 (최대 3회까지 인정)
                total_score += min(count, 3) * weight

        # 2차 키워드 검색
        for keyword, weight in self.SECONDARY_KEYWORDS.items():
            count = combined_text.count(keyword.lower())
            if count > 0:
                total_score += min(count, 2) * weight * 0.7  # 2차 키워드는 70% 가중치

        # 텍스트 길이로 정규화 (길이가 너무 길면 점수 감소)
        normalized_score = (total_score / text_length) * 500

        return min(normalized_score, 100)  # 최대 100점 제한

    def calculate_source_credibility(self, link: str) -> float:
        """
        출처 기반 신뢰도 점수 (0~100)
        """
        # 신뢰도 높은 언론사 체크
        for domain, score in self.SOURCE_CREDIBILITY.items():
            if domain != "default" and domain in link:
                return score

        # 블로그/카페 체크
        for pattern in self.BLOG_PATTERNS + self.CAFE_PATTERNS:
            if pattern in link:
                return 60

        # 커뮤니티 체크
        for pattern in self.COMMUNITY_PATTERNS:
            if pattern in link:
                return 40

        return self.SOURCE_CREDIBILITY["default"]

    def calculate_freshness_score(self, published: Optional[str]) -> float:
        """
        날짜 기반 Freshness 점수 (0~100)
        """
        if not published:
            return 50  # 날짜 없는 경우 기본 점수

        try:
            # 다양한 날짜 형식 파싱
            if "T" in published or "+" in published:
                # ISO 8601 format: 2026-01-19T12:00:00+0900
                from dateutil import parser
                pub_date = parser.parse(published)
            elif len(published) == 8 and published.isdigit():
                # YYYYMMDD format
                pub_date = datetime.datetime.strptime(published, "%Y%m%d")
            else:
                # RFC 2822 format
                from email.utils import parsedate_to_datetime
                pub_date = parsedate_to_datetime(published)

            now = datetime.datetime.now(pub_date.tzinfo if pub_date.tzinfo else datetime.timezone.utc)
            diff = now - pub_date

            # 시간 차이를 시간 단위로 변환
            hours_ago = diff.total_seconds() / 3600

            if hours_ago <= 6:
                return 100
            elif hours_ago <= 12:
                return 80
            elif hours_ago <= 24:
                return 60
            elif hours_ago <= 48:
                return 40
            else:
                return 20

        except Exception as e:
            if self.debug_mode:
                # 에러 메시지도 안전하게 출력
                safe_error = str(e).encode('cp949', 'ignore').decode('cp949')
                print(f"[DEBUG] Date parsing error: {safe_error}")
            return 50

    def calculate_competitor_bonus(self, title: str, snippet: str) -> float:
        """
        경쟁사 관련 가중치 계산
        - KT, LGU+ 포함: +30점
        - SKT도 포함: -10점 (SKT 단독 기사 방지)
        """
        combined_text = f"{title} {snippet}".lower()

        has_kt = "kt" in combined_text or "kt-" in combined_text
        has_lgu = "lgu+" in combined_text or "lg유플러스" in combined_text
        has_skt = "skt" in combined_text or "sk텔레콤" in combined_text

        bonus = 0
        if has_kt or has_lgu:
            bonus += 30

        if has_skt:
            bonus -= 10

        return max(bonus, 0)  # 음수 방지

    def contextual_keyword_check(self, title: str, snippet: str, keyword: str) -> bool:
        """
        문맥 인지 키워드 체크
        특정 키워드가 실제로 해당 주제와 관련이 있는지 확인
        """
        combined_text = f"{title} {snippet}".lower()

        # "롤" 키워드 특수 처리
        if keyword == "롤":
            # 게임 문맥 키워드
            has_game_context = any(
                game_kw in combined_text
                for game_kw in ["리그오브레전드", "롤체", "롤드컵", "티어", "랭크", "챔피언", "소환사"]
            )
            # 통신 문맥 키워드
            has_telecom_context = any(
                telecom_kw in combined_text
                for telecom_kw in self.TELECOM_CONTEXT
            )

            # 게임 문맥이 있고 통신 문맥이 없으면 필터링
            if has_game_context and not has_telecom_context:
                return False
            # 통신 문맥이 있으면 보존
            elif has_telecom_context:
                return True

        # 그 외 키워드는 기본적으로 True
        return True

    def is_game_related(self, title: str, snippet: str) -> bool:
        """
        게임 관련 기사인지 판별 (문맥 인지)
        """
        combined_text = f"{title} {snippet}".lower()

        # 강력한 게임 신호
        strong_game_signals = [
            "리그오브레전드", "롤드컵", "롤체전", "LoL", "PUBG", "배그",
            "MMORPG", "서버 이동", "소환사의 협곡"
        ]

        for signal in strong_game_signals:
            if signal.lower() in combined_text:
                # 통신 문맥이 있는지 확인
                has_telecom = any(kw in combined_text for kw in self.TELECOM_CONTEXT)
                if not has_telecom:
                    return True

        # "롤" 단독 사용 체크
        if "롤" in combined_text:
            # 주변 단어 확인 (단순 문자열 매칭 방지)
            words = combined_text.split()
            for i, word in enumerate(words):
                if "롤" in word:
                    # 앞뒤 단어 확인
                    context_words = []
                    if i > 0:
                        context_words.append(words[i-1])
                    if i < len(words) - 1:
                        context_words.append(words[i+1])

                    context = " ".join(context_words)

                    # 게임 관련 문맥이면 필터링
                    if any(game_kw in context for game_kw in ["챔피언", "티어", "랭크", "게임"]):
                        return True

        return False

    def calculate_relevance_score(self, article: Dict) -> float:
        """
        종합 관련성 점수 계산 (0~100)

        수식: (키워드 밀도 × 0.4) + (출처 신뢰도 × 0.3) + (Freshness × 0.2) + (경쟁사 가중치 × 0.1)
        """
        title = article.get('title', '')
        snippet = article.get('snippet', '')
        link = article.get('link', '')
        published = article.get('published')

        # 게임 관련 기사는 우선 필터링 (문맥 인지)
        if self.is_game_related(title, snippet):
            if self.debug_mode:
                safe_title = title[:50].encode('cp949', 'ignore').decode('cp949') if title else ''
                print(f"[FILTER] Game-related: {safe_title}...")
            return 0

        # 1. 키워드 밀도 점수
        keyword_score = self.calculate_keyword_density_score(title, snippet)

        # 2. 출처 신뢰도 점수
        source_score = self.calculate_source_credibility(link)

        # 3. Freshness 점수
        freshness_score = self.calculate_freshness_score(published)

        # 4. 경쟁사 가중치
        competitor_bonus = self.calculate_competitor_bonus(title, snippet)

        # 가중 평균 계산
        total_score = (
            keyword_score * 0.4 +
            source_score * 0.3 +
            freshness_score * 0.2 +
            competitor_bonus * 0.1
        )

        if self.debug_mode:
            # 인코딩 문제 방지를 위해 안전한 출력
            safe_title = title[:40].encode('cp949', 'ignore').decode('cp949') if title else ''
            print(f"[SCORE] {safe_title}... | Keyword: {keyword_score:.1f} | "
                  f"Source: {source_score:.1f} | Fresh: {freshness_score:.1f} | "
                  f"Bonus: {competitor_bonus:.1f} | Total: {total_score:.1f}")

        return min(total_score, 100)  # 최대 100점 제한

    def should_include_for_ai(self, article: Dict, threshold: float = 30) -> tuple:
        """
        AI 분석 포함 여부 결정

        Args:
            article: 기사 딕셔너리
            threshold: 최소 관련성 점수 임계값

        Returns:
            (bool, dict) - (포함 여부, 필터링 사유 정보)
        """
        title = article.get('title', '')
        snippet = article.get('snippet', '')
        link = article.get('link', '')
        published = article.get('published')

        # 1. 게임 관련 기사 필터링
        if self.is_game_related(title, snippet):
            return False, {
                "filtered": True,
                "reason": "게임 관련 기사",
                "score": 0,
                "details": "리그오브레전드, LoL, PUBG 등 게임 키워드 감지"
            }

        # 2. 점수 계산
        keyword_score = self.calculate_keyword_density_score(title, snippet)
        source_score = self.calculate_source_credibility(link)
        freshness_score = self.calculate_freshness_score(published)
        competitor_bonus = self.calculate_competitor_bonus(title, snippet)

        total_score = (
            keyword_score * 0.4 +
            source_score * 0.3 +
            freshness_score * 0.2 +
            competitor_bonus * 0.1
        )
        total_score = min(total_score, 100)

        # 3. 경쟁사 기사 확인
        is_competitor = any(kw in title.lower() for kw in ["kt", "lgu+", "lg유플러스"])
        adjusted_threshold = 20 if is_competitor else threshold

        # 4. 필터링 여부 결정
        if total_score >= adjusted_threshold:
            return True, {
                "filtered": False,
                "reason": "통과",
                "score": round(total_score, 2),
                "details": self._get_pass_reason(keyword_score, source_score, freshness_score, competitor_bonus)
            }
        else:
            return False, {
                "filtered": True,
                "reason": "관련성 점수 미달",
                "score": round(total_score, 2),
                "details": self._get_fail_reason(keyword_score, source_score, freshness_score, competitor_bonus, adjusted_threshold)
            }

    def _get_pass_reason(self, keyword_score, source_score, freshness_score, competitor_bonus):
        """통과 사유 생성"""
        reasons = []
        if keyword_score > 20:
            reasons.append(f"핵심 키워드 포함 ({keyword_score:.1f}점)")
        if source_score > 80:
            reasons.append(f"신뢰도 높은 출처 ({source_score:.1f}점)")
        if freshness_score > 60:
            reasons.append(f"최신 기사 ({freshness_score:.1f}점)")
        if competitor_bonus > 0:
            reasons.append(f"경쟁사 관련 기사 (+{competitor_bonus:.1f}점)")
        return ", ".join(reasons) if reasons else "종합 점수 합격"

    def _get_fail_reason(self, keyword_score, source_score, freshness_score, competitor_bonus, threshold):
        """필터링 사유 생성"""
        reasons = []
        if keyword_score < 15:
            reasons.append(f"관련 키워드 부족 ({keyword_score:.1f}점)")
        if source_score < 50:
            reasons.append(f"신뢰도 낮은 출처 ({source_score:.1f}점)")
        if freshness_score < 40:
            reasons.append(f"오래된 기사 ({freshness_score:.1f}점)")
        fail_msg = f"점수 미달 (합격선: {threshold}점)"
        return f"{fail_msg} - " + ", ".join(reasons) if reasons else fail_msg

    def filter_articles_for_ai(self, articles: list, threshold: float = 30) -> tuple:
        """
        기사 목록에서 AI 분석에 포함할 기사만 필터링

        Args:
            articles: 기사 딕셔너리 리스트
            threshold: 최소 관련성 점수 임계값

        Returns:
            (필터링된 기사 리스트, 필터링 정보 리스트)
        """
        filtered = []
        filter_info = []

        for article in articles:
            should_include, info = self.should_include_for_ai(article, threshold)

            # 필터링 정보에 기사 제목/링크 추가
            info['title'] = article.get('title', '')[:60]
            info['link'] = article.get('link', '')
            info['source'] = article.get('source', '')
            filter_info.append(info)

            if should_include:
                filtered.append(article)

        if self.debug_mode:
            passed = sum(1 for f in filter_info if not f['filtered'])
            print(f"\n[FILTER SUMMARY] Original: {len(articles)} → Passed: {passed} → Filtered: {len(articles) - passed}")

        return filtered, filter_info


# ========================================
# 테스트 시나리오
# ========================================

def run_test_scenarios():
    """
    Smart Filter 테스트 시나리오 5개
    """
    filter = SmartFilter(debug_mode=True)

    print("=" * 80)
    print("SMART FILTER TEST SCENARIOS")
    print("=" * 80)

    # 테스트 케이스 1: 경쟁사 기사 (KT)
    test_case_1 = {
        'title': 'KT, 해외 로밍 요금제 50% 인하... eSIM 경쟁 본격화',
        'link': 'https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=105&oid=029&aid=0001234567',
        'snippet': 'KT가 19일 해외 로밍 요금제를 대폭 인하한다고 발표했다. 기존보다 최대 50% 저렴해진 이번 요금제는...',
        'source': 'Naver News',
        'published': 'Mon, 19 Jan 2026 12:00:00 +0900',
        'type': 'domestic'
    }

    # 테스트 케이스 2: 게임 기사 (롤/LoL)
    test_case_2 = {
        'title': '롤드컵 2024, 리그오브레전드 서버 로밍으로 인한 지연 현상 발생',
        'link': 'https://www.inven.co.kr/webzine/news/?news=12345',
        'snippet': '리그오브레전드 롤드컵 경기 중 서버 로밍 기능으로 인한 핑 문제가 발생했다. 선수들은...',
        'source': 'Inven',
        'published': 'Mon, 19 Jan 2026 14:30:00 +0900',
        'type': 'domestic'
    }

    # 테스트 케이스 3: SKT 단독 기사
    test_case_3 = {
        'title': 'SKT, 스타링크 로밍 서비스 출시... 위성 통신 시대 개막',
        'link': 'https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=105&oid=029&aid=0001234568',
        'snippet': 'SK텔레콤이 스페이스X의 스타링크와 제휴해 위성 기반 로밍 서비스를 출시한다. 빈 지역에서도...',
        'source': 'Naver News',
        'published': 'Mon, 19 Jan 2026 10:00:00 +0900',
        'type': 'domestic'
    }

    # 테스트 케이스 4: eSIM 대체재 기사
    test_case_4 = {
        'title': '도시락 eSIM, 일본 여행객 대상 프로모션 진행... "로밍비 80% 절감"',
        'link': 'https://blog.naver.com/dosirak_esim/2212345678',
        'snippet': '도시락 eSIM이 일본 여행객을 대상으로 특별 프로모션을 진행한다고 밝혔다. 기존 로밍 서비스 대비...',
        'source': 'Naver Blog',
        'published': '20260119',
        'type': 'domestic'
    }

    # 테스트 케이스 5: 통신사 관련 "롤" 기사 (거짓 양성 테스트)
    test_case_5 = {
        'title': 'SKT, 5G 데이터 로밍 서비스 개선... "롤" 네트워크 품질 향상',
        'link': 'https://news.naver.com/main/read.nhn?mode=LSD&mid=shm&sid1=105&oid=029&aid=0001234569',
        'snippet': 'SK텔레콤이 5G 데이터 로밍 품질을 개선한다. 롤(로밍) 서비스 이용 시 데이터 속도가 기존보다 2배 향상될 예정이다...',
        'source': 'Naver News',
        'published': 'Mon, 19 Jan 2026 09:00:00 +0900',
        'type': 'domestic'
    }

    test_cases = [
        ("Case 1: KT 경쟁사 기사", test_case_1, True, 70),
        ("Case 2: 게임 기사 (롤/LoL)", test_case_2, False, 0),
        ("Case 3: SKT 단독 기사", test_case_3, True, 75),
        ("Case 4: eSIM 대체재 기사", test_case_4, True, 65),
        ("Case 5: 통신 '롤' 기사 (거짓 양성 방지)", test_case_5, True, 70)
    ]

    results = []

    for name, article, expected, min_score in test_cases:
        print(f"\n{'─' * 80}")
        print(f"TEST: {name}")
        print(f"{'─' * 80}")
        print(f"Title: {article['title']}")
        print(f"Expected: {'AI 포함' if expected else '필터링'} (예상 점수: {min_score}+)")

        score = filter.calculate_relevance_score(article)
        should_include = filter.should_include_for_ai(article, threshold=30)

        print(f"\nResult:")
        print(f"  - Score: {score:.2f} / 100")
        print(f"  - AI Include: {'YES' if should_include else 'NO'}")
        print(f"  - Match Expected: {'[PASS]' if should_include == expected else '[FAIL]'}")

        results.append({
            'name': name,
            'score': score,
            'expected_include': expected,
            'actual_include': should_include,
            'pass': should_include == expected
        })

    # 요약 출력
    print(f"\n{'=' * 80}")
    print("TEST SUMMARY")
    print(f"{'=' * 80}")

    for r in results:
        status = "[PASS]" if r['pass'] else "[FAIL]"
        print(f"{status} | {r['name']:30s} | Score: {r['score']:5.1f} | "
              f"Expected: {'YES' if r['expected_include'] else 'NO':3s} | "
              f"Actual: {'YES' if r['actual_include'] else 'NO':3s}")

    pass_count = sum(1 for r in results if r['pass'])
    print(f"\nTotal: {pass_count}/{len(results)} tests passed")
    print(f"{'=' * 80}")

    return results


if __name__ == "__main__":
    # 테스트 실행
    run_test_scenarios()
