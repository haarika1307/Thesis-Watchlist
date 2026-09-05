import re
import logging
from typing import List, Tuple
from datetime import datetime, timezone

from backend.app.schemas.news import NewsArticleResponse, NewsListResponse
from backend.app.services.news.yahoo_news_provider import YahooAndRssNewsProvider

logger = logging.getLogger(__name__)

class NewsService:
    def __init__(self):
        self.provider = YahooAndRssNewsProvider()

    def get_ranked_news_for_thesis(
        self,
        symbol: str,
        company_name: str,
        thesis_text: str = "",
        signals: List[dict] = None
    ) -> NewsListResponse:
        """Fetch real news and partition/rank into Relevant to Thesis vs All News."""
        all_articles = self.provider.get_company_news(symbol, company_name)
        if not all_articles:
            return NewsListResponse(symbol=symbol, relevantNews=[], allNews=[])

        if not thesis_text and not signals:
            return NewsListResponse(symbol=symbol, relevantNews=[], allNews=all_articles)

        # Build keywords list from thesis and signals
        keywords = set()
        # Clean words from thesis
        raw_words = re.findall(r'\b[A-Za-z]{3,}\b', thesis_text.lower())
        stop_words = {"this", "that", "with", "from", "have", "will", "think", "because", "stock", "company"}
        for w in raw_words:
            if w not in stop_words:
                keywords.add(w)

        signal_keywords = set()
        if signals:
            for s in signals:
                topic = s.get("topic", "").lower()
                name = s.get("signalName", "").lower()
                desc = s.get("description", "").lower()
                for w in re.findall(r'\b[A-Za-z]{3,}\b', f"{topic} {name} {desc}"):
                    if w not in stop_words:
                        signal_keywords.add(w)

        positive_sentiment_terms = {
            "surge", "surges", "jump", "jumps", "growth", "grow", "profit", "gain", "gains",
            "deal", "wins", "order", "contract", "beats", "record", "strong", "recovery",
            "expansion", "rallies", "upgrade", "outperform", "bullish", "higher", "positive"
        }
        negative_sentiment_terms = {
            "plunge", "fall", "falls", "drop", "drops", "slump", "loss", "losses", "cautious",
            "warning", "misses", "weak", "slowdown", "headwind", "margin", "decline",
            "downgrade", "pressure", "underperform", "bearish", "lower", "negative", "investigation"
        }

        relevant_list: List[NewsArticleResponse] = []
        regular_list: List[NewsArticleResponse] = []

        for art in all_articles:
            text_corpus = f"{art.title} {art.summary or ''}".lower()
            
            # Score matches
            thesis_matches = sum(1 for kw in keywords if kw in text_corpus)
            signal_matches = sum(1 for kw in signal_keywords if kw in text_corpus)
            
            relevance_score = (thesis_matches * 1.5) + (signal_matches * 2.0)
            
            if relevance_score > 0:
                pos_hits = sum(1 for t in positive_sentiment_terms if t in text_corpus)
                neg_hits = sum(1 for t in negative_sentiment_terms if t in text_corpus)

                if pos_hits > neg_hits:
                    classification = "SUPPORTING"
                    reason = f"Reported positive momentum matching thesis themes ({', '.join([k for k in keywords if k in text_corpus][:2])})"
                elif neg_hits > pos_hits:
                    classification = "CONTRADICTING"
                    reason = f"Headwinds or cautionary signals detected relating to thesis parameters ({', '.join([k for k in keywords if k in text_corpus][:2])})"
                else:
                    classification = "NEUTRAL"
                    reason = "Directly mentions key thesis themes with balanced or informational context."

                art_copy = NewsArticleResponse(
                    id=art.id,
                    symbol=art.symbol,
                    title=art.title,
                    source=art.source,
                    url=art.url,
                    summary=art.summary,
                    publishedAt=art.publishedAt,
                    relevanceScore=round(relevance_score, 1),
                    classification=classification,
                    reason=reason
                )
                relevant_list.append(art_copy)
            else:
                regular_list.append(art)

        # Sort relevant news by score descending
        relevant_list.sort(key=lambda a: (a.relevanceScore or 0), reverse=True)

        return NewsListResponse(
            symbol=symbol,
            relevantNews=relevant_list,
            allNews=all_articles
        )

news_service = NewsService()
