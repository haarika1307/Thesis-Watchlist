import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from backend.app.schemas.market import QuoteResponse, FundamentalsResponse, TechnicalsResponse
from backend.app.schemas.news import NewsArticleResponse

logger = logging.getLogger(__name__)

@dataclass
class DetectedChange:
    signal_name: str
    metric_key: str
    source_type: str  # MARKET, FUNDAMENTAL, NEWS, MANAGEMENT, EVENT
    source_id: Optional[str]
    previous_value: Optional[str]
    current_value: str
    change_value: Optional[str]
    change_percentage: Optional[float]
    is_meaningful: bool
    significance_reason: str
    details: Dict[str, Any]

class ChangeDetectionEngine:
    """Evaluates current market, fundamental, and news data against baseline/historical snapshots to isolate meaningful changes."""

    # Significance thresholds
    PRICE_CHANGE_MEANINGFUL_PCT = 2.5  # Daily change > 2.5% is meaningful
    PE_CHANGE_MEANINGFUL_PCT = 5.0      # Multiple expansion/contraction > 5%
    MARGIN_CHANGE_MEANINGFUL_BPS = 0.5  # 50 bps margin change
    REVENUE_GROWTH_THRESHOLD_PCT = 3.0  # 3% revenue variance

    def detect_market_changes(
        self,
        quote: QuoteResponse,
        previous_quote: Optional[QuoteResponse] = None,
        technicals: Optional[TechnicalsResponse] = None
    ) -> List[DetectedChange]:
        """Detect meaningful market and price action changes."""
        changes: List[DetectedChange] = []

        price_pct = quote.percentageChange or 0.0
        abs_pct = abs(price_pct)
        is_meaningful = abs_pct >= self.PRICE_CHANGE_MEANINGFUL_PCT
        
        sig_reason = (
            f"Abnormal daily price swing of {price_pct:+.1f}% exceeds threshold ({self.PRICE_CHANGE_MEANINGFUL_PCT}%)"
            if is_meaningful
            else f"Normal daily price fluctuation ({price_pct:+.1f}%) within typical baseline"
        )

        prev_price_str = f"{quote.currency}{round(quote.price - quote.change, 2)}" if quote.change else None

        changes.append(DetectedChange(
            signal_name="Market Price & Trend Confirmation",
            metric_key="priceChange",
            source_type="MARKET",
            source_id=f"quote_{quote.symbol}",
            previous_value=prev_price_str,
            current_value=f"{quote.currency}{quote.price:,.2f}",
            change_value=f"{quote.change:+.2f} ({price_pct:+.2f}%)",
            change_percentage=price_pct,
            is_meaningful=is_meaningful,
            significance_reason=sig_reason,
            details={"volume": quote.volume, "pe": quote.pe}
        ))

        # Check technical indicator changes (RSI overbought/oversold)
        if technicals and technicals.rsi is not None:
            rsi = technicals.rsi
            rsi_meaningful = rsi >= 70 or rsi <= 35
            rsi_sig = (
                f"RSI indicator at {rsi} indicates extreme momentum ({'overbought' if rsi >= 70 else 'oversold'})"
                if rsi_meaningful else f"RSI at {rsi} in balanced range"
            )
            changes.append(DetectedChange(
                signal_name="Momentum / RSI Oscillator",
                metric_key="rsi",
                source_type="MARKET",
                source_id="technicals_rsi",
                previous_value="50.0",
                current_value=f"{rsi}",
                change_value=f"{rsi - 50.0:+.1f} pts",
                change_percentage=round(((rsi - 50) / 50) * 100, 1),
                is_meaningful=rsi_meaningful,
                significance_reason=rsi_sig,
                details={"rsi": rsi, "trend": technicals.trend}
            ))

        return changes

    def detect_fundamental_changes(
        self,
        current_fund: FundamentalsResponse,
        prev_fund: Optional[FundamentalsResponse] = None
    ) -> List[DetectedChange]:
        """Detect quarterly fundamental and ratio changes."""
        changes: List[DetectedChange] = []

        # 1. Operating Margin
        if current_fund.margin is not None:
            curr_margin = current_fund.margin
            prev_margin = prev_fund.margin if (prev_fund and prev_fund.margin is not None) else None
            
            if prev_margin is not None:
                diff = curr_margin - prev_margin
                meaningful = abs(diff) >= self.MARGIN_CHANGE_MEANINGFUL_BPS
                sig = f"Operating margin shifted by {diff:+.2f}% (from {prev_margin:.1f}% to {curr_margin:.1f}%)"
            else:
                diff = None
                meaningful = True
                sig = f"Current operating margin verified at {curr_margin:.1f}%"

            changes.append(DetectedChange(
                signal_name="Operating Margin",
                metric_key="operatingMargin",
                source_type="FUNDAMENTAL",
                source_id="sec_filing_margin",
                previous_value=f"{prev_margin:.1f}%" if prev_margin else None,
                current_value=f"{curr_margin:.1f}%",
                change_value=f"{diff:+.2f}%" if diff is not None else None,
                change_percentage=diff,
                is_meaningful=meaningful,
                significance_reason=sig,
                details={"margin": curr_margin}
            ))

        # 2. P/E Valuation Multiple
        if current_fund.pe is not None:
            curr_pe = current_fund.pe
            prev_pe = prev_fund.pe if (prev_fund and prev_fund.pe is not None) else None
            
            if prev_pe is not None:
                pe_pct = round(((curr_pe - prev_pe) / prev_pe) * 100, 1)
                meaningful = abs(pe_pct) >= self.PE_CHANGE_MEANINGFUL_PCT
                sig = f"P/E ratio shifted by {pe_pct:+.1f}% to {curr_pe:.1f}x"
            else:
                pe_pct = None
                meaningful = True
                sig = f"Current P/E multiple established at {curr_pe:.1f}x"

            changes.append(DetectedChange(
                signal_name="Price-to-Earnings (P/E)",
                metric_key="pe",
                source_type="FUNDAMENTAL",
                source_id="sec_filing_pe",
                previous_value=f"{prev_pe:.1f}x" if prev_pe else None,
                current_value=f"{curr_pe:.1f}x",
                change_value=f"{curr_pe - prev_pe:+.1f}x" if prev_pe else None,
                change_percentage=pe_pct,
                is_meaningful=meaningful,
                significance_reason=sig,
                details={"pe": curr_pe}
            ))

        # 3. Revenue Growth from quarterly history if available
        if current_fund.financialHistory and len(current_fund.financialHistory) >= 2:
            q_latest = current_fund.financialHistory[0]
            q_prior = current_fund.financialHistory[1]
            if q_latest.revenue and q_prior.revenue and q_prior.revenue > 0:
                rev_growth = round(((q_latest.revenue - q_prior.revenue) / q_prior.revenue) * 100, 1)
                meaningful = abs(rev_growth) >= self.REVENUE_GROWTH_THRESHOLD_PCT
                sig = f"Quarter-over-Quarter revenue growth changed by {rev_growth:+.1f}%"

                changes.append(DetectedChange(
                    signal_name="Revenue Growth",
                    metric_key="revenueGrowth",
                    source_type="FUNDAMENTAL",
                    source_id="quarterly_filing_revenue",
                    previous_value=f"₹{q_prior.revenue / 1e7:,.1f} Cr" if q_prior.revenue > 1e7 else f"{q_prior.revenue:,.0f}",
                    current_value=f"₹{q_latest.revenue / 1e7:,.1f} Cr" if q_latest.revenue > 1e7 else f"{q_latest.revenue:,.0f}",
                    change_value=f"{rev_growth:+.1f}%",
                    change_percentage=rev_growth,
                    is_meaningful=meaningful,
                    significance_reason=sig,
                    details={"latest_period": q_latest.period, "revenue": q_latest.revenue}
                ))

        # 4. Debt & Free Cash Flow
        if current_fund.debt is not None:
            changes.append(DetectedChange(
                signal_name="Total Debt Reduction",
                metric_key="debt",
                source_type="FUNDAMENTAL",
                source_id="balance_sheet_debt",
                previous_value=None,
                current_value=f"₹{current_fund.debt / 1e7:,.1f} Cr" if current_fund.debt > 1e7 else f"{current_fund.debt:,.0f}",
                change_value=None,
                change_percentage=None,
                is_meaningful=True,
                significance_reason="Reported total debt on active balance sheet",
                details={"debt": current_fund.debt}
            ))

        return changes

    def detect_news_changes(
        self,
        news_articles: List[NewsArticleResponse]
    ) -> List[DetectedChange]:
        """Convert highly relevant news items (deal wins, guidance, commentary) into detected changes."""
        changes: List[DetectedChange] = []
        for art in news_articles[:4]:  # Top relevant news
            if not art.classification or art.classification == "NEUTRAL":
                continue

            # Detect specific signal from headline/summary
            sig_name = "Company Developments & Guidance"
            metric = "news_event"
            title_l = art.title.lower()
            if "deal" in title_l or "contract" in title_l or "order" in title_l or "win" in title_l:
                sig_name = "Order Book / Deal Wins"
                metric = "dealWins"
            elif "guidance" in title_l or "commentary" in title_l or "outlook" in title_l or "demand" in title_l:
                sig_name = "Management Guidance / Commentary"
                metric = "managementCommentary"
            elif "arpu" in title_l or "subscriber" in title_l or "jio" in title_l:
                sig_name = "Jio Subscriber Growth & ARPU"
                metric = "arpu"
            elif "ev" in title_l or "electric" in title_l:
                sig_name = "EV Deliveries & Market Share"
                metric = "evDeliveries"

            changes.append(DetectedChange(
                signal_name=sig_name,
                metric_key=metric,
                source_type="NEWS",
                source_id=art.url or art.id,
                previous_value="Previous guidance / baseline",
                current_value=art.title,
                change_value=art.reason or "Fresh operational development reported",
                change_percentage=None,
                is_meaningful=True,
                significance_reason=f"High-impact publication from {art.source}",
                details={"url": art.url, "source": art.source, "classification": art.classification}
            ))
        return changes

change_detection_engine = ChangeDetectionEngine()
