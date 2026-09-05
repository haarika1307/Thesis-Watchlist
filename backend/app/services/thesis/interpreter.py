import re
import logging
from typing import List, Optional
from backend.app.core.config import settings
from backend.app.schemas.thesis import (
    StructuredThesisProfile,
    SignalDefinition
)

logger = logging.getLogger(__name__)

class ThesisInterpreter:
    """Interprets free-form thesis text and category into a structured profile with relevant signals and data requirements."""

    def __init__(self):
        # Domain dictionaries for business units, themes, and metrics
        self.themes = {
            "growth": {
                "theme": "Growth & Expansion",
                "default_signals": [
                    SignalDefinition(
                        signalName="Revenue Growth",
                        topic="Financial Performance",
                        description="Year-over-year top-line revenue expansion",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="revenueGrowth",
                        newsKeywords=["revenue", "sales", "topline", "growth", "expansion"]
                    ),
                    SignalDefinition(
                        signalName="Operating Margin",
                        topic="Profitability",
                        description="Operating margin stability or expansion under higher volume",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="operatingMargin",
                        newsKeywords=["margin", "ebitda margin", "operating profit"]
                    ),
                    SignalDefinition(
                        signalName="Order Book / Deal Wins",
                        topic="Business Pipeline",
                        description="New customer additions, contract wins, or order book growth",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="dealWins",
                        newsKeywords=["deal", "contract", "order", "bookings", "client win"]
                    ),
                    SignalDefinition(
                        signalName="Earnings Per Share (EPS)",
                        topic="Earnings Power",
                        description="Growth in net earnings per share",
                        direction="POSITIVE",
                        importance="MEDIUM",
                        targetMetric="eps",
                        newsKeywords=["earnings", "eps", "net profit", "pat"]
                    )
                ]
            },
            "valuation": {
                "theme": "Value & Multiple Re-rating",
                "default_signals": [
                    SignalDefinition(
                        signalName="Price-to-Earnings (P/E)",
                        topic="Valuation Multiple",
                        description="Valuation multiple compared to historical range and industry peers",
                        direction="NEGATIVE",  # Lower multiple or reasonable multiple preferred
                        importance="HIGH",
                        targetMetric="pe",
                        newsKeywords=["p/e", "valuation", "undervalued", "cheap", "multiple"]
                    ),
                    SignalDefinition(
                        signalName="Price-to-Book (P/B)",
                        topic="Asset Valuation",
                        description="Stock price relative to book value per share",
                        direction="NEGATIVE",
                        importance="HIGH",
                        targetMetric="pb",
                        newsKeywords=["p/b", "book value", "net worth"]
                    ),
                    SignalDefinition(
                        signalName="Free Cash Flow Yield",
                        topic="Cash Generation",
                        description="Robust cash flow generation supporting intrinsic valuation",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="freeCashFlow",
                        newsKeywords=["free cash flow", "fcf", "cash generation", "cash flow"]
                    ),
                    SignalDefinition(
                        signalName="Return on Equity (ROE)",
                        topic="Capital Efficiency",
                        description="Management efficiency in compounding shareholder equity",
                        direction="POSITIVE",
                        importance="MEDIUM",
                        targetMetric="roe",
                        newsKeywords=["roe", "return on equity", "roce"]
                    )
                ]
            },
            "demand": {
                "theme": "Demand Recovery & Utilization",
                "default_signals": [
                    SignalDefinition(
                        signalName="Revenue Growth",
                        topic="Demand Velocity",
                        description="Top-line inflection signaling demand resumption",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="revenueGrowth",
                        newsKeywords=["demand", "sales", "volume", "recovery", "orders"]
                    ),
                    SignalDefinition(
                        signalName="Large Deal Wins",
                        topic="Commercial Momentum",
                        description="Large deals signed during the quarter indicating customer spend",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="dealWins",
                        newsKeywords=["large deal", "megadeal", "wins", "contract", "pipeline"]
                    ),
                    SignalDefinition(
                        signalName="Operating Margin",
                        topic="Operating Leverage",
                        description="Margin recovery as utilization rates rise",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="operatingMargin",
                        newsKeywords=["margin", "utilization", "operating margin", "headwind"]
                    ),
                    SignalDefinition(
                        signalName="Management Guidance / Commentary",
                        topic="Forward Visibility",
                        description="Management tone regarding upcoming pipeline and client caution",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="managementCommentary",
                        newsKeywords=["guidance", "commentary", "outlook", "management", "cautious", "optimistic"]
                    )
                ]
            },
            "margin": {
                "theme": "Margin Expansion & Profitability",
                "default_signals": [
                    SignalDefinition(
                        signalName="Operating Margin",
                        topic="Margin Expansion",
                        description="Operating margin improvement via pricing or cost optimization",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="operatingMargin",
                        newsKeywords=["margin expansion", "ebitda", "operating margin", "cost cut"]
                    ),
                    SignalDefinition(
                        signalName="Net Profit Margin",
                        topic="Bottom Line",
                        description="Conversion of revenue into net profit",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="profit",
                        newsKeywords=["profit margin", "pat margin", "net profit"]
                    ),
                    SignalDefinition(
                        signalName="EBITDA Growth",
                        topic="Core Earnings",
                        description="Expansion of cash operating earnings before interest and taxes",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="ebitda",
                        newsKeywords=["ebitda", "operational earnings", "cash operating profit"]
                    )
                ]
            },
            "debt": {
                "theme": "Deleveraging & Balance Sheet",
                "default_signals": [
                    SignalDefinition(
                        signalName="Total Debt Reduction",
                        topic="Balance Sheet Health",
                        description="Reduction in gross and net debt obligations",
                        direction="NEGATIVE",  # Lower debt is better
                        importance="HIGH",
                        targetMetric="debt",
                        newsKeywords=["debt", "deleveraging", "debt reduction", "repayment", "interest"]
                    ),
                    SignalDefinition(
                        signalName="Free Cash Flow",
                        topic="Cash Flow",
                        description="Cash available to fund debt service or growth internally",
                        direction="POSITIVE",
                        importance="HIGH",
                        targetMetric="freeCashFlow",
                        newsKeywords=["free cash flow", "cash flow", "fcf"]
                    )
                ]
            }
        }

    def interpret(self, thesis_text: str, category: str = "Growth", company_name: str = "") -> StructuredThesisProfile:
        """Interpret user's thesis text and category into a rich StructuredThesisProfile."""
        text_lower = thesis_text.lower()
        cat_lower = category.lower()

        # 1. Identify specific business entity / unit mentioned in text
        # e.g., "Jio", "EV", "Cloud", "Retail", "Semiconductor", "Defense", "Renewable", "IT Demand"
        business_unit = None
        entity_patterns = [
            r"\b(jio)\b", r"\b(retail)\b", r"\b(cloud)\b", r"\b(ev|electric vehicle)\b",
            r"\b(defense|defence)\b", r"\b(solar|renewable|green hydrogen)\b",
            r"\b(digital)\b", r"\b(ai|artificial intelligence)\b",
            r"\b(suv|automotive)\b", r"\b(semiconductor|chips)\b",
            r"\b(it demand|tech demand|software)\b", r"\b(telecom|5g)\b"
        ]
        for pat in entity_patterns:
            m = re.search(pat, text_lower)
            if m:
                business_unit = m.group(1).title()
                break

        # 2. Match theme
        selected_theme_key = "growth"
        if any(w in text_lower for w in ["undervalued", "valuation", "cheap", "pe multiple", "p/e", "margin of safety", "discount"]) or "valuation" in cat_lower:
            selected_theme_key = "valuation"
        elif any(w in text_lower for w in ["demand", "recover", "recovery", "deal wins", "bookings", "it demand", "client spend"]) or "industry" in cat_lower:
            selected_theme_key = "demand"
        elif any(w in text_lower for w in ["margin", "profitability", "ebitda margin", "operating leverage"]) or "business performance" in cat_lower:
            selected_theme_key = "margin"
        elif any(w in text_lower for w in ["debt", "deleveraging", "debt reduction", "balance sheet"]):
            selected_theme_key = "debt"
        elif "risk" in cat_lower:
            selected_theme_key = "debt"
        else:
            selected_theme_key = "growth"

        base_config = self.themes[selected_theme_key]
        signals: List[SignalDefinition] = list(base_config["default_signals"])

        # 3. Add entity-specific signals if identified
        if business_unit and business_unit.lower() == "jio":
            signals.insert(0, SignalDefinition(
                signalName="Jio Subscriber Growth & ARPU",
                topic="Business Unit Metric",
                description="Average Revenue Per User (ARPU) and net active subscriber additions in telecom",
                direction="POSITIVE",
                importance="HIGH",
                targetMetric="arpu",
                newsKeywords=["jio", "arpu", "telecom", "subscriber growth", "5g tariff"]
            ))
        elif business_unit and "ev" in business_unit.lower():
            signals.insert(0, SignalDefinition(
                signalName="EV Deliveries & Market Share",
                topic="EV Adoption",
                description="Monthly electric vehicle deliveries and penetration rate",
                direction="POSITIVE",
                importance="HIGH",
                targetMetric="evDeliveries",
                newsKeywords=["ev", "electric vehicle", "battery", "deliveries", "tata ev"]
            ))
        elif business_unit and "cloud" in business_unit.lower():
            signals.insert(0, SignalDefinition(
                signalName="Cloud & Digital Deal Pipeline",
                topic="Cloud Growth",
                description="Revenue from hyperscaler partnerships and cloud migrations",
                direction="POSITIVE",
                importance="HIGH",
                targetMetric="cloudRevenue",
                newsKeywords=["cloud", "digital transformation", "ai revenue"]
            ))

        # Ensure market price movement is also a monitored signal
        signals.append(SignalDefinition(
            signalName="Market Price & Trend Confirmation",
            topic="Price Action",
            description="Market price trajectory aligning with thesis expectation",
            direction="POSITIVE",
            importance="MEDIUM",
            targetMetric="priceChange",
            newsKeywords=["stock", "shares", "rally", "target price"]
        ))

        return StructuredThesisProfile(
            business=business_unit,
            theme=base_config["theme"],
            rationale=thesis_text,
            signals=signals
        )

thesis_interpreter = ThesisInterpreter()
