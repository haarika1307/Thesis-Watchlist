import logging
import urllib.parse
from datetime import datetime, timezone
from typing import List
import httpx
import yfinance as yf
from bs4 import BeautifulSoup

from backend.app.core.config import settings
from backend.app.schemas.news import NewsArticleResponse
from backend.app.services.news.base import NewsProvider
from backend.app.services.market_data.cache import cache

logger = logging.getLogger(__name__)

class YahooAndRssNewsProvider(NewsProvider):
    """Fetches real articles from Yahoo Finance and Google News RSS."""

    @property
    def provider_name(self) -> str:
        return "yahoo_and_rss"

    def get_company_news(self, symbol: str, company_name: str = "") -> List[NewsArticleResponse]:
        """Fetch live company news."""
        cache_key = f"news:{symbol.upper()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        articles: List[NewsArticleResponse] = []
        seen_titles = set()

        # 1. Fetch from yfinance ticker news
        norm_symbol = symbol.strip().upper()
        if not norm_symbol.endswith(".NS") and not norm_symbol.endswith(".BO") and "." not in norm_symbol:
            norm_symbol = f"{norm_symbol}.NS"

        try:
            ticker = yf.Ticker(norm_symbol)
            yf_news = ticker.news or []
            for item in yf_news:
                content = item.get("content", {}) or item
                title = content.get("title") or item.get("title")
                if not title or title.strip() in seen_titles:
                    continue
                seen_titles.add(title.strip())

                # URL resolution
                click_url = content.get("canonicalUrl", {}).get("url") or item.get("link") or ""
                pub_provider = content.get("provider", {}).get("displayName") or item.get("publisher") or "Yahoo Finance"
                summary = content.get("summary") or item.get("summary") or title

                pub_time = None
                pub_ts = content.get("pubDate") or item.get("providerPublishTime")
                if isinstance(pub_ts, int):
                    pub_time = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
                elif isinstance(pub_ts, str):
                    try:
                        pub_time = datetime.fromisoformat(pub_ts.replace("Z", "+00:00"))
                    except Exception:
                        pub_time = datetime.now(timezone.utc)
                else:
                    pub_time = datetime.now(timezone.utc)

                articles.append(NewsArticleResponse(
                    symbol=symbol,
                    title=title.strip(),
                    source=pub_provider,
                    url=click_url,
                    summary=summary.strip(),
                    publishedAt=pub_time
                ))
        except Exception as e:
            logger.warning(f"Yahoo News fetch error for {symbol}: {e}")

        # 2. Fetch from Google News RSS for Indian & global market coverage
        try:
            query_name = company_name if company_name else symbol.split(".")[0]
            clean_term = urllib.parse.quote(f"{query_name} stock share news")
            rss_url = f"https://news.google.com/rss/search?q={clean_term}&hl=en-IN&gl=IN&ceid=IN:en"

            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with httpx.Client(timeout=5.0) as client:
                res = client.get(rss_url, headers=headers)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "xml")
                    items = soup.find_all("item")
                    for item in items[:10]:
                        t = item.find("title")
                        title_text = t.text if t else ""
                        if not title_text or title_text.strip() in seen_titles:
                            continue
                        seen_titles.add(title_text.strip())

                        link_tag = item.find("link")
                        link_text = link_tag.text if link_tag else ""

                        source_tag = item.find("source")
                        source_text = source_tag.text if source_tag else "Financial Press"

                        pub_tag = item.find("pubDate")
                        pub_time = datetime.now(timezone.utc)
                        if pub_tag:
                            try:
                                # Example: Sat, 05 Sep 2026 06:12:00 GMT
                                from email.utils import parsedate_to_datetime
                                pub_time = parsedate_to_datetime(pub_tag.text)
                            except Exception:
                                pass

                        articles.append(NewsArticleResponse(
                            symbol=symbol,
                            title=title_text.strip(),
                            source=source_text.strip(),
                            url=link_text.strip(),
                            summary=title_text.strip(),
                            publishedAt=pub_time
                        ))
        except Exception as e:
            logger.warning(f"Google News RSS fetch error for {symbol}: {e}")

        # Sort by publishedAt descending
        articles.sort(key=lambda a: a.publishedAt or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

        cache.set(cache_key, articles, ttl_seconds=settings.NEWS_CACHE_TTL_SECONDS)
        return articles
