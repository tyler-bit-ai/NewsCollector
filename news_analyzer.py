from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL_BASIC, OPENAI_MODEL_ADVANCED, OPENAI_BASE_URL
from smart_filter import SmartFilter
from news_collector import CategoryClassifier
import time
import random
import json

class NewsAnalyzer:
    def __init__(self):
        if not OPENAI_API_KEY:
             print("[WARNING] OpenAI API Key is not set.")
             self.client = None
        else:
            self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
            
        # Define models
        self.model_basic = OPENAI_MODEL_BASIC      # gpt-4o-mini-2024-07-18
        self.model_advanced = OPENAI_MODEL_ADVANCED # gpt-5-2025-08-07

    def _call_ai(self, messages, model, response_format={"type": "json_object"}):
        """Helper to call AI with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    response_format=response_format
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                print(f"[AI Error] Attempt {attempt+1} ({model}): {e}")
                time.sleep(2)
        raise Exception(f"AI call failed for {model} after retries.")

    def analyze_and_summarize(self, raw_data):
        """
        Two-step Analysis:
        1. Basic Model: Classify and Summarize raw text.
        2. Advanced Model: Generate Insights and Executive Summary.
        """
        domestic_items = raw_data.get('domestic', [])
        global_items = raw_data.get('global', [])

        if not domestic_items and not global_items:
            return {"error": "수집된 데이터가 없습니다."}

        # --- Smart Filter 적용 (토큰 최적화) ---
        print("   [Analyzer] Applying Smart Filter for token optimization...")
        smart_filter = SmartFilter(debug_mode=False)

        # 점수 기반 필터링 (임계값 30) - 필터링 정보도 함께 반환
        domestic_filtered, domestic_filter_info = smart_filter.filter_articles_for_ai(domestic_items, threshold=30)
        global_filtered, global_filter_info = smart_filter.filter_articles_for_ai(global_items, threshold=30)

        print(f"   [Smart Filter] Domestic: {len(domestic_items)} → {len(domestic_filtered)}")
        print(f"   [Smart Filter] Global: {len(global_items)} → {len(global_filtered)}")

        # 필터링된 데이터로 분석
        domestic_items = domestic_filtered
        global_items = global_filtered

        # --- 카테고리별 분류 (키워드 기반) ---
        print("   [Analyzer] Classifying articles by category...")
        classified = {
            'market_culture': [],
            'global_trend': [],
            'competitors': [],
            'esim_products': [],
            'voc_roaming': [],
            'voc_esim': [],
            'other': []
        }

        # Domestic 기사 분류
        for article in domestic_items:
            category = CategoryClassifier.classify_article(article)
            classified[category].append(article)

        # Global 기사는 모두 global_trend로
        for article in global_items:
            classified['global_trend'].append(article)

        # 분류 결과 출력
        for cat, items in classified.items():
            if items:
                print(f"   {cat}: {len(items)} articles")

        # --- 각 카테고리별 최신 10개씩 선택 ---
        def sort_by_date(items):
            return sorted(items, key=lambda x: (x.get('published') is None, x.get('published') or ''), reverse=True)

        max_per_category = 10
        domestic_by_category = {}
        for cat in ['market_culture', 'competitors', 'esim_products', 'voc_roaming', 'voc_esim']:
            sorted_items = sort_by_date(classified[cat])
            domestic_by_category[cat] = sorted_items[:max_per_category]

        global_limited = sort_by_date(classified['global_trend'])[:max_per_category]

        # --- STEP 1: Summarization (GPT-4o-mini) ---
        print("   [Analyzer] Step 1: Summarizing with Basic Model...")

        def format_items(items):
            text = ""
            for idx, item in enumerate(items, 1):
                text += f"{idx}. [{item.get('source')}] {item.get('title')}\n"
                text += f"   Link: {item.get('link')}\n"
            return text

        # 카테고리별 기사를 모두 합쳐서 텍스트 생성
        all_domestic = []
        for cat_items in domestic_by_category.values():
            all_domestic.extend(cat_items)

        domestic_text = format_items(all_domestic)
        global_text = format_items(global_limited)

        prompt_basic = f"""
        당신은 SKT 로밍팀 데이터 분석가입니다.
        제공된 기사 목록을 분석하여 지정된 섹션으로 분류하고 요약하세요.
        전략적 인사이트는 아직 도출하지 마세요. 오직 팩트 기반의 요약과 분류만 수행합니다.

        [Data Sources]
        === DOMESTIC DATA (최신 {len(all_domestic)}개) ===
        {domestic_text}

        === GLOBAL DATA (최신 {len(global_limited)}개) ===
        {global_text}

        [Classification Rules - 6 Categories]
        0. **Market & Culture (Macro)**: 한국 방문객(입국자), K-Culture, K-POP, 한류, 출국자 수 통계/추이, 여행 시장 동향.

        1. **Global Roaming Trend**: 해외 기사 중 eSIM 및 로밍 산업에 관한 영어 기사. 글로벌 로밍/eSIM/통신 기술 트렌드(Starlink, 6G 등).

        2. **SKT & Competitors (KT/LGU+)**: SKT 바로로밍, KT 로밍, LGU+ 로밍 관련 기사. **(중요: SK텔레콤(SKT) 단독 뉴스는 절대 포함하지 마세요. KT/LGU+ 내용이 주가 되는 기사만 분류)**.

        3. **eSIM**: eSIM 대표 업체(도시락, 말톡, 유심사, 이지에심, 핀다이렉트 등) 관련 기사와 eSIM 사업자들의 프로모션/광고 관련 기사.

        4. **로밍 Voice**: 로밍 사업에 대한 긍정/부정 후기 (커뮤니티, 블로그 소스). "ㅠㅠ", "ㅋㅋ", "후기", "리뷰", "재구매", "추천" 등 개인 사용 경험글.

        5. **eSIM VoC**: eSIM 사업에 대한 긍정/부정 후기 (커뮤니티, 블로그 소스). eSIM/도시락/말톡 등의 고객 후기, "후기", "리뷰", "ㅠㅠ", "ㅋㅋ", "재구매", "추천" 등 개인 경험 표현.

        [Output Limits]
- Market & Culture (Macro): 최대 5개
- Global Roaming Trend: 최대 5개
- SKT & Competitors (KT/LGU+): 최대 5개
- eSIM: 최대 5개 (프로모션/기사/출시 소식만)
- 로밍 Voice: 최대 5개 (고객 후기/리뷰)
- eSIM VoC: 최대 5개 (고객 후기/리뷰)

        [Noise Filtering]
        - 게임, 금융, 광고, 이벤트 관련 내용은 제외.

        [Output JSON Structure]
        {{
            "section_market_culture": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_global_trend": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_competitors": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_esim_products": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_voc_roaming": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_voc_esim": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ]
        }}

        **중요**: "link" 필드는 반드시 위 기사 목록에 제공된 실제 링크(URL)를 그대로 복사해서 사용하세요. 절대 가짜 링크(example.com 등)를 생성하지 마세요.
        """

        try:
            summ_data = self._call_ai(
                messages=[
                    {"role": "system", "content": "You are a concise summarizer. Output JSON."},
                    {"role": "user", "content": prompt_basic}
                ],
                model=self.model_basic
            )
        except Exception as e:
            return {"error": f"Summarization Step Failed: {e}"}

        # --- STEP 2: Insights (GPT-5) ---
        print("   [Analyzer] Step 2: Generating Insights with Advanced Model...")
        
        # Serialize step 1 output to be input for step 2
        context_json = json.dumps(summ_data, ensure_ascii=False, indent=2)

        prompt_advanced = f"""
        당신은 'SKT 로밍팀 전략 IT 컨설턴트'입니다.
        아래 정리된 시장 동향 데이터를 바탕으로, 핵심 전략 인사이트와 경영진 보고용 요약을 작성하세요.

        [Analyzed Market Data]
        {context_json}

        [Task]
        1. **Email Summary**: 전체를 관통하는 핵심 인사이트 1개와 메가 트렌드 2개를 3줄 내외로 요약(반드시 `• ` 글머리 기호 사용).
        2. **Strategic Insights**:
           - **Insight 1 (Technology)**: 기술 우위(품질/속도/CS)를 활용한 마케팅 방안. VOC의 불만을 해소할 포인트.
           - **Insight 2 (Demand)**: 여행/문화 트렌드와 연계한 수요 선점 및 상품 대응 전략.

        [Output JSON Structure]
        {{
            "email_top_summary": "• (핵심 인사이트)\\n• (트렌드 1)\\n• (트렌드 2)",
            "strategic_insight": "1. [기술 초격차 마케팅] ...\\n2. [시장 수요 선점] ..."
        }}
        """

        try:
            insight_data = self._call_ai(
                messages=[
                    {"role": "system", "content": "You are a top-tier strategy consultant. Output JSON."},
                    {"role": "user", "content": prompt_advanced}
                ],
                model=self.model_advanced
            )
        except Exception as e:
            return {"error": f"Insight Step Failed: {e}"}

        # Merge Results
        final_result = summ_data.copy()
        final_result.update(insight_data)

        # 필터링 정보 추가 (디버그용)
        final_result['filter_info'] = {
            'domestic': domestic_filter_info,
            'global': global_filter_info
        }

        return final_result
