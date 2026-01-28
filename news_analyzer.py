from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL_BASIC, OPENAI_MODEL_ADVANCED, OPENAI_BASE_URL
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
        1. Basic Model: Summarize pre-categorized articles (categories assigned at collection time).
        2. Advanced Model: Generate Insights and Executive Summary.
        """
        domestic_items = raw_data.get('domestic', [])
        global_items = raw_data.get('global', [])

        if not domestic_items and not global_items:
            return {"error": "수집된 데이터가 없습니다."}

        # --- Use categories assigned at collection time ---
        print("   [Analyzer] Using pre-assigned categories from collection...")
        classified = {
            'market_culture': [],
            'global_trend': [],
            'competitors': [],
            'esim_products': [],
            'voc_roaming': [],
            'voc_esim': [],
            'other': []
        }

        # Domestic 기사: collection 단계에서 assigned된 category 사용
        for article in domestic_items:
            category = article.get('category', 'other')
            classified[category].append(article)

        # Global 기사는 모두 global_trend로
        for article in global_items:
            classified['global_trend'].append(article)

        # 분류 결과 출력
        for cat, items in classified.items():
            if items:
                print(f"   {cat}: {len(items)} articles")

        # 필터링 정보 (빈 값으로 설정)
        domestic_filter_info = {}
        global_filter_info = []

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

        # 각 카테고리별 입력된 기사 수 계산
        category_counts = {}
        for cat in ['market_culture', 'global_trend', 'competitors', 'esim_products', 'voc_roaming', 'voc_esim']:
            if cat == 'global_trend':
                category_counts[cat] = len(global_limited)
            else:
                category_counts[cat] = len(domestic_by_category.get(cat, []))

        # 동적 출력 한계 생성
        def get_output_limit(cat_name, count):
            if count <= 5:
                return f"- {cat_name}: {count}개 (모두 요약)"
            else:
                return f"- {cat_name}: 정확히 5개 (반드시 5개 선택)"

        output_limits = "\n".join([
            get_output_limit("Market & Culture (Macro)", category_counts['market_culture']),
            get_output_limit("Global Roaming Trend", category_counts['global_trend']),
            get_output_limit("SKT & Competitors (KT/LGU+)", category_counts['competitors']),
            get_output_limit("eSIM", category_counts['esim_products']),
            get_output_limit("로밍 VoC", category_counts['voc_roaming']),
            get_output_limit("eSIM VoC", category_counts['voc_esim'])
        ])

        prompt_basic = f"""
        당신은 SKT 로밍팀 데이터 분석가입니다.
        제공된 기사 목록을 요약하세요.

        **중요**: 기사들은 수집 단계에서 이미 카테고리별로 정확히 분류되었습니다. 절대 재분류하지 말고, 각 카테고리에 해당하는 기사들을 그대로 요약하세요.

        [Data Sources]
        === DOMESTIC DATA (최신 {len(all_domestic)}개) ===
        {domestic_text}

        === GLOBAL DATA (최신 {len(global_limited)}개) ===
        {global_text}

        [Category Description]
        0. **Market & Culture (Macro)**: 한국 방문객(입국자), K-Culture, K-POP, 한류, 출국자 수 통계/추이, 여행 시장 동향.

        1. **Global Roaming Trend**: 해외 기사 중 eSIM 및 로밍 산업에 관한 영어 기사. 글로벌 로밍/eSIM/통신 기술 트렌드(Starlink, 6G 등).

        2. **SKT & Competitors (KT/LGU+)**: SKT 바로로밍, KT 로밍, LGU+ 로밍 관련 기사. **(중요: SK텔레콤(SKT) 단독 뉴스는 절대 포함하지 마세요. KT/LGU+ 내용이 주가 되는 기사만 요약하세요.)**

        3. **eSIM**: eSIM 대표 업체(도시락, 말톡, 유심사, 이지이심, 핀다이렉트 등) 관련 기사와 eSIM 사업자들의 프로모션/광고 관련 기사. **(중요: 블로그/카페 후기/리뷰는 절대 포함하지 마세요. 오직 언론사 뉴스만 요약하세요.)**

        4. **로밍 VoC**: 로밍 사업에 대한 긍정/부정 후기 (커뮤니티, 블로그 소스). "ㅠㅠ", "ㅋㅋ", "후기", "리뷰", "재구매", "추천" 등 개인 사용 경험글. **(중요: eSIM/이심 관련 내용은 제외하고 순수 로밍 서비스 후기만 요약하세요.)**

        5. **eSIM VoC**: eSIM 사업에 대한 긍정/부정 후기 (커뮤니티, 블로그 소스). eSIM/도시락/말톡 등의 고객 후기, "후기", "리뷰", "ㅠㅠ", "ㅋㅋ", "재구매", "추천" 등 개인 경험 표현. **(중요: 모든 블로그/카페 후기/리뷰는 이 카테고리만을 위해 요약하세요.)**

        [Output Limits]
{output_limits}

        [Output JSON Structure]
        {{
            "section_market_culture": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_global_trend": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_competitors": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_esim_products": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_voc_roaming": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ],
            "section_voc_esim": [ {{ "title": "...", "summary": "• ...", "link": "...", "source": "..." }} ]
        }}

        **중요**:
        1. "link" 필드는 반드시 위 기사 목록에 제공된 실제 링크(URL)를 그대로 복사해서 사용하세요. 절대 가짜 링크(example.com 등)를 생성하지 마세요.
        2. 반드시 **모든 6개 카테고리**를 JSON으로 출력하세요. 빈 배열이라도 출력해야 합니다.
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
