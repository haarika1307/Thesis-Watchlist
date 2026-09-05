import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import httpx
import yfinance as yf
import pandas as pd
import numpy as np

from backend.app.core.config import settings
from backend.app.schemas.market import (
    StockSearchResult,
    QuoteResponse,
    HistoryResponse,
    HistoryCandle,
    FundamentalsResponse,
    FinancialPeriod,
    TechnicalsResponse
)
from backend.app.services.market_data.base import MarketDataProvider
from backend.app.services.market_data.cache import cache

logger = logging.getLogger(__name__)

class YahooMarketDataProvider(MarketDataProvider):
    """Production Yahoo Finance Market Data Provider with caching, symbol normalization, and technical calculations."""

    @property
    def provider_name(self) -> str:
        return "yahoo"

    def _normalize_symbol(self, symbol: str, exchange: str = "NSE") -> str:
        """Normalize symbol for Yahoo Finance, adding exchange suffix if needed."""
        symbol = symbol.strip().upper()
        if "." in symbol:
            return symbol
        if exchange.upper() == "NSE":
            return f"{symbol}.NS"
        elif exchange.upper() == "BSE":
            return f"{symbol}.BO"
        # If exchange is US or not specified, leave as is
        return symbol

    def _clean_symbol_display(self, symbol: str) -> str:
        """Strip .NS or .BO for clean display."""
        if symbol.endswith(".NS") or symbol.endswith(".BO"):
            return symbol.split(".")[0]
        return symbol

    def search(self, query: str) -> List[StockSearchResult]:
        """Search real stocks using Yahoo Finance autocomplete API."""
        query = query.strip()
        if not query:
            return []

        cache_key = f"search:{query.lower()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        results: List[StockSearchResult] = []
        try:
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=12&newsCount=0"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            with httpx.Client(timeout=6.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    quotes = data.get("quotes", [])
                    for q in quotes:
                        quote_type = q.get("quoteType", "")
                        if quote_type not in ["EQUITY", "ETF"]:
                            continue
                        
                        sym = q.get("symbol", "")
                        disp_name = q.get("shortname") or q.get("longname") or sym
                        exch = q.get("exchange", "")
                        
                        # Normalize exchange name
                        norm_exch = "NSE" if ".NS" in sym or exch in ["NSI", "NSE"] else ("BSE" if ".BO" in sym or exch in ["BSE"] else exch)
                        currency = "INR" if norm_exch in ["NSE", "BSE"] else "USD"

                        results.append(StockSearchResult(
                            symbol=sym,
                            name=disp_name,
                            exchange=norm_exch,
                            currency=currency,
                            type=quote_type
                        ))
        except Exception as e:
            logger.warning(f"Yahoo search error: {e}")

        # Fallback to direct symbol lookup if search returned nothing
        if not results and len(query) <= 12:
            sym_clean = query.upper()
            try:
                candidate = f"{sym_clean}.NS"
                ticker = yf.Ticker(candidate)
                info = ticker.fast_info
                if info and info.last_price:
                    results.append(StockSearchResult(
                        symbol=candidate,
                        name=sym_clean,
                        exchange="NSE",
                        currency="INR"
                    ))
            except Exception:
                pass

        cache.set(cache_key, results, ttl_seconds=300)
        return results

    def get_quote(self, symbol: str) -> QuoteResponse:
        """Fetch current real-time or delayed quote for a stock."""
        norm_symbol = self._normalize_symbol(symbol)
        cache_key = f"quote:{norm_symbol}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        ticker = yf.Ticker(norm_symbol)
        now = datetime.now(timezone.utc)

        try:
            fast = ticker.fast_info
            last_price = getattr(fast, "last_price", None)
            prev_close = getattr(fast, "previous_close", None)
            currency = getattr(fast, "currency", "INR") or "INR"

            if last_price is None:
                # Try regular info fallback
                info = ticker.info or {}
                last_price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
                prev_close = info.get("previousClose") or last_price
                company_name = info.get("shortName") or info.get("longName") or self._clean_symbol_display(symbol)
                day_high = info.get("dayHigh")
                day_low = info.get("dayLow")
                w52_high = info.get("fiftyTwoWeekHigh")
                w52_low = info.get("fiftyTwoWeekLow")
                mkt_cap = info.get("marketCap")
                vol = info.get("volume") or info.get("regularMarketVolume")
                pe_val = info.get("trailingPE")
                exchange = info.get("exchange", "NSE")
            else:
                info = {}
                try:
                    info = ticker.info or {}
                except Exception:
                    pass
                company_name = info.get("shortName") or info.get("longName") or self._clean_symbol_display(symbol)
                day_high = getattr(fast, "day_high", None) or info.get("dayHigh")
                day_low = getattr(fast, "day_low", None) or info.get("dayLow")
                w52_high = getattr(fast, "year_high", None) or info.get("fiftyTwoWeekHigh")
                w52_low = getattr(fast, "year_low", None) or info.get("fiftyTwoWeekLow")
                mkt_cap = getattr(fast, "market_cap", None) or info.get("marketCap")
                vol = getattr(fast, "last_volume", None) or info.get("volume")
                pe_val = info.get("trailingPE")
                exchange = "NSE" if ".NS" in norm_symbol else ("BSE" if ".BO" in norm_symbol else info.get("exchange", "NSE"))

            price = float(last_price) if last_price is not None else 0.0
            prev = float(prev_close) if prev_close is not None and prev_close > 0 else price
            change = round(price - prev, 2)
            pct_change = round(((price - prev) / prev) * 100, 2) if prev > 0 else 0.0

            quote = QuoteResponse(
                symbol=norm_symbol,
                companyName=company_name,
                price=round(price, 2),
                change=change,
                percentageChange=pct_change,
                currency="₹" if currency == "INR" else ("$" if currency == "USD" else currency),
                exchange=exchange,
                dayHigh=round(float(day_high), 2) if day_high is not None else None,
                dayLow=round(float(day_low), 2) if day_low is not None else None,
                fiftyTwoWeekHigh=round(float(w52_high), 2) if w52_high is not None else None,
                fiftyTwoWeekLow=round(float(w52_low), 2) if w52_low is not None else None,
                marketCap=float(mkt_cap) if mkt_cap is not None else None,
                volume=int(vol) if vol is not None else None,
                pe=round(float(pe_val), 2) if pe_val is not None else None,
                marketStatus="OPEN",
                freshness="DELAYED (15 min)" if ".NS" in norm_symbol or ".BO" in norm_symbol else "LIVE",
                provider="yahoo",
                timestamp=now
            )
            cache.set(cache_key, quote, ttl_seconds=settings.MARKET_CACHE_TTL_SECONDS)
            return quote
        except Exception as e:
            logger.error(f"Error fetching quote for {norm_symbol}: {e}")
            # Return baseline quote with error indication
            return QuoteResponse(
                symbol=norm_symbol,
                companyName=self._clean_symbol_display(symbol),
                price=0.0,
                change=0.0,
                percentageChange=0.0,
                currency="INR",
                exchange="NSE",
                marketStatus="CLOSED",
                freshness="UNAVAILABLE",
                provider="yahoo",
                timestamp=now
            )

    def get_history(self, symbol: str, range_str: str = "1M") -> HistoryResponse:
        """Fetch historical price candles."""
        norm_symbol = self._normalize_symbol(symbol)
        range_clean = range_str.upper()
        cache_key = f"history:{norm_symbol}:{range_clean}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Map range to yfinance period and interval
        range_mapping = {
            "1D": ("1d", "5m"),
            "1W": ("5d", "15m"),
            "1M": ("1mo", "1d"),
            "6M": ("6mo", "1d"),
            "1Y": ("1y", "1d"),
            "5Y": ("5y", "1wk"),
            "ALL": ("max", "1mo")
        }
        period, interval = range_mapping.get(range_clean, ("1mo", "1d"))

        candles: List[HistoryCandle] = []
        try:
            ticker = yf.Ticker(norm_symbol)
            df = ticker.history(period=period, interval=interval)
            if df is not None and not df.empty:
                for idx, row in df.iterrows():
                    ts_str = idx.strftime("%Y-%m-%d %H:%M") if hasattr(idx, "strftime") else str(idx)
                    candles.append(HistoryCandle(
                        timestamp=ts_str,
                        open=round(float(row["Open"]), 2),
                        high=round(float(row["High"]), 2),
                        low=round(float(row["Low"]), 2),
                        close=round(float(row["Close"]), 2),
                        volume=int(row["Volume"]) if "Volume" in row and not pd.isna(row["Volume"]) else 0
                    ))
        except Exception as e:
            logger.error(f"Error fetching history for {norm_symbol}: {e}")

        resp = HistoryResponse(symbol=norm_symbol, range=range_clean, candles=candles)
        cache.set(cache_key, resp, ttl_seconds=settings.HISTORY_CACHE_TTL_SECONDS)
        return resp

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        """Fetch real financial statements, ratios, and fundamentals."""
        norm_symbol = self._normalize_symbol(symbol)
        cache_key = f"fundamentals:{norm_symbol}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = datetime.now(timezone.utc)
        ticker = yf.Ticker(norm_symbol)

        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        # Extract real fundamentals
        pe = info.get("trailingPE") or info.get("forwardPE")
        pb = info.get("priceToBook")
        eps = info.get("trailingEps") or info.get("forwardEps")
        roe = info.get("returnOnEquity")
        if roe is not None:
            roe = round(roe * 100, 2)  # format as percentage
        mkt_cap = info.get("marketCap")
        div_yield = info.get("dividendYield")
        if div_yield is not None:
            div_yield = round(div_yield * 100, 2)
        revenue = info.get("totalRevenue")
        profit = info.get("netIncomeToCommon") or info.get("netIncome")
        ebitda = info.get("ebitda")
        margin = info.get("operatingMargins")
        if margin is not None:
            margin = round(margin * 100, 2)
        debt = info.get("totalDebt")
        fcf = info.get("freeCashflow")

        # ROCE calculation if available: EBIT / (Total Assets - Current Liabilities)
        roce = None
        try:
            ebit = info.get("ebitda")
            if ebit and mkt_cap and debt:
                capital_employed = mkt_cap + debt
                if capital_employed > 0:
                    roce = round((ebit / capital_employed) * 100, 2)
        except Exception:
            pass

        # Extract quarterly history if available
        financial_history: List[FinancialPeriod] = []
        try:
            q_fin = ticker.quarterly_financials
            if q_fin is not None and not q_fin.empty:
                for col in q_fin.columns[:4]:
                    col_name = col.strftime("%b %Y") if hasattr(col, "strftime") else str(col)[:7]
                    rev = float(q_fin.loc["Total Revenue", col]) if "Total Revenue" in q_fin.index and not pd.isna(q_fin.loc["Total Revenue", col]) else None
                    ni = float(q_fin.loc["Net Income", col]) if "Net Income" in q_fin.index and not pd.isna(q_fin.loc["Net Income", col]) else None
                    op_inc = float(q_fin.loc["Operating Income", col]) if "Operating Income" in q_fin.index and not pd.isna(q_fin.loc["Operating Income", col]) else None
                    op_margin = round((op_inc / rev) * 100, 2) if rev and op_inc and rev > 0 else None

                    financial_history.append(FinancialPeriod(
                        period=col_name,
                        revenue=rev,
                        netIncome=ni,
                        operatingMargin=op_margin
                    ))
        except Exception as e:
            logger.debug(f"Quarterly financials note for {norm_symbol}: {e}")

        resp = FundamentalsResponse(
            symbol=norm_symbol,
            companyName=info.get("shortName") or info.get("longName") or self._clean_symbol_display(symbol),
            marketCap=float(mkt_cap) if mkt_cap is not None else None,
            pe=round(float(pe), 2) if pe is not None else None,
            pb=round(float(pb), 2) if pb is not None else None,
            roe=roe,
            roce=roce,
            eps=round(float(eps), 2) if eps is not None else None,
            dividendYield=div_yield,
            revenue=float(revenue) if revenue is not None else None,
            profit=float(profit) if profit is not None else None,
            ebitda=float(ebitda) if ebitda is not None else None,
            margin=margin,
            debt=float(debt) if debt is not None else None,
            freeCashFlow=float(fcf) if fcf is not None else None,
            financialHistory=financial_history,
            freshness="AS OF LATEST SEC/MCA FILING",
            provider="yahoo",
            timestamp=now
        )
        cache.set(cache_key, resp, ttl_seconds=settings.FUNDAMENTALS_CACHE_TTL_SECONDS)
        return resp

    def get_technicals(self, symbol: str) -> TechnicalsResponse:
        """Compute real technical indicators (RSI, MACD, SMAs, Volatility) from price history."""
        norm_symbol = self._normalize_symbol(symbol)
        cache_key = f"technicals:{norm_symbol}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        now = datetime.now(timezone.utc)
        ticker = yf.Ticker(norm_symbol)

        # Default fallback
        rsi_val = None
        macd_val = None
        macd_signal_val = None
        macd_hist_val = None
        sma20_val = None
        sma50_val = None
        sma200_val = None
        volatility_val = None
        trend = "NEUTRAL"
        current_price = 0.0
        volume = 0

        try:
            df = ticker.history(period="1y", interval="1d")
            if df is not None and not df.empty and len(df) >= 15:
                closes = df["Close"]
                current_price = round(float(closes.iloc[-1]), 2)
                volume = int(df["Volume"].iloc[-1]) if "Volume" in df and not pd.isna(df["Volume"].iloc[-1]) else 0

                # 1. RSI (14 days)
                delta = closes.diff()
                gain = delta.clip(lower=0)
                loss = -1 * delta.clip(upper=0)
                avg_gain = gain.rolling(window=14, min_periods=14).mean()
                avg_loss = loss.rolling(window=14, min_periods=14).mean()
                rs = avg_gain / avg_loss.replace(0, np.nan)
                rsi_series = 100 - (100 / (1 + rs))
                if not pd.isna(rsi_series.iloc[-1]):
                    rsi_val = round(float(rsi_series.iloc[-1]), 1)

                # 2. Moving Averages
                if len(closes) >= 20:
                    sma20_val = round(float(closes.rolling(window=20).mean().iloc[-1]), 2)
                if len(closes) >= 50:
                    sma50_val = round(float(closes.rolling(window=50).mean().iloc[-1]), 2)
                if len(closes) >= 200:
                    sma200_val = round(float(closes.rolling(window=200).mean().iloc[-1]), 2)

                # 3. MACD (12, 26, 9)
                ema12 = closes.ewm(span=12, adjust=False).mean()
                ema26 = closes.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                hist = macd_line - signal_line

                macd_val = round(float(macd_line.iloc[-1]), 2)
                macd_signal_val = round(float(signal_line.iloc[-1]), 2)
                macd_hist_val = round(float(hist.iloc[-1]), 2)

                # 4. Volatility (Annualized standard deviation of 20-day returns)
                log_ret = np.log(closes / closes.shift(1)).dropna()
                if len(log_ret) >= 20:
                    vol_20 = log_ret.tail(20).std() * math.sqrt(252) * 100
                    volatility_val = round(float(vol_20), 1)

                # 5. Trend interpretation
                if sma50_val and current_price > sma50_val and (rsi_val is None or rsi_val >= 50):
                    trend = "BULLISH"
                elif sma50_val and current_price < sma50_val and (rsi_val is None or rsi_val < 50):
                    trend = "BEARISH"
                else:
                    trend = "NEUTRAL"
        except Exception as e:
            logger.error(f"Error computing technicals for {norm_symbol}: {e}")

        resp = TechnicalsResponse(
            symbol=norm_symbol,
            price=current_price,
            volume=volume,
            rsi=rsi_val,
            macd=macd_val,
            macdSignal=macd_signal_val,
            macdHist=macd_hist_val,
            sma20=sma20_val,
            sma50=sma50_val,
            sma200=sma200_val,
            volatility=volatility_val,
            trend=trend,
            timestamp=now
        )
        cache.set(cache_key, resp, ttl_seconds=settings.HISTORY_CACHE_TTL_SECONDS)
        return resp
