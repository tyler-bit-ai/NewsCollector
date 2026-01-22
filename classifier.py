class DataClassifier:
    def __init__(self):
        # 1. Hard Filtering Domains
        self.COMMUNITY_DOMAINS = [
            'cafe.naver.com', 'ppomppu.co.kr', 'clien.net', 
            'theqoo.net', 'fmkorea.com', 'ruliweb.com', 
            'instiz.net', 'dcinside.com', 'threads.net', 'threads.com'
        ]
        
        self.NEWS_DOMAINS = [
            'news.naver.com', 'v.daum.net', 'yna.co.kr', 
            'zdnet.co.kr', 'bloter.net', 'etnews.com',
            'hankyung.com', 'mk.co.kr', 'mt.co.kr',
            'newsis.com', 'news1.kr'
        ]

    def classify_item(self, item):
        """
        Classifies an item into 'news' or 'community'.
        Priority:
        1. Hard Domain Match (URL)
        2. Content/Title Soft Match (Keywords)
        """
        link = item.get('link', '')
        title = item.get('title', '')
        snippet = item.get('snippet', '')
        
        # 1. Hard Domain Check
        for domain in self.COMMUNITY_DOMAINS:
            if domain in link:
                return 'community'
                
        for domain in self.NEWS_DOMAINS:
            if domain in link:
                return 'news'

        # 2. Soft Content Check
        # Keywords typically found in news
        news_keywords = ["기자", "밝혔다", "발표했다", "뉴스", "보도", "출시", "공개"]
        # Keywords typically found in community posts
        community_keywords = ["해요", "했음", "추천좀", "질문", "후기", "ㅠㅠ", "ㅋㅋ", "ㅎㅎ"]

        combined_text = (title + " " + snippet)
        
        # Check for news style
        if any(k in combined_text for k in news_keywords):
            # Additional check: Does it look like a formal article?
            return 'news'
            
        # Check for community style
        if any(k in combined_text for k in community_keywords):
            return 'community'
            
        # Default fallback (conservative approach)
        # If the source domain is a known portal like 'n.news.naver.com' it might have slipped through
        if 'news' in link or 'article' in link:
            return 'news'
            
        return 'community' # Default to community if unsure, or maybe add 'unknown'

    def process_and_deduplicate(self, items):
        """
        Classifies items and deduplicates them.
        Returns: {'news': [...], 'community': [...]}
        """
        classified_data = {
            'news': [],
            'community': []
        }
        
        seen_links = set()
        
        for item in items:
            link = item.get('link')
            if link in seen_links:
                continue
            seen_links.add(link)
            
            category = self.classify_item(item)
            
            # Add category-specific metadata if needed
            if category == 'news':
                classified_data['news'].append(item)
            else:
                classified_data['community'].append(item)
        
        # TODO: Implement more advanced deduplication logic here if needed
        # e.g., Fuzzy matching for titles to remove same news from different outlets
        
        return classified_data
