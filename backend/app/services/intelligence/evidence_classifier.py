import logging
from typing import List, Dict, Optional
from datetime import datetime, timezone

from backend.app.schemas.evidence import EvidenceResponse
from backend.app.schemas.thesis import ThesisResponse, ThesisSignalResponse
from backend.app.services.change_detection.detector import DetectedChange

logger = logging.getLogger(__name__)

class EvidenceClassifier:
    """Classifies detected real-world changes as SUPPORTING, CONTRADICTING, NEUTRAL, or UNCERTAIN based on user thesis signals."""

    def classify_change(
        self,
        change: DetectedChange,
        thesis_text: str,
        category: str,
        signals: List[Dict]
    ) -> EvidenceResponse:
        """Evaluate a single detected change against the thesis and relevant signals."""
        now = datetime.now(timezone.utc)
        sig_map = {s.get("signalName", "").lower(): s for s in signals}
        metric_map = {s.get("targetMetric", "").lower(): s for s in signals if s.get("targetMetric")}

        # Find matching signal definition
        matched_sig = None
        change_name_l = change.signal_name.lower()
        if change_name_l in sig_map:
            matched_sig = sig_map[change_name_l]
        elif change.metric_key.lower() in metric_map:
            matched_sig = metric_map[change.metric_key.lower()]
        else:
            # Partial match
            for k, v in sig_map.items():
                if k in change_name_l or change_name_l in k:
                    matched_sig = v
                    break

        expected_dir = matched_sig.get("direction", "POSITIVE") if matched_sig else "POSITIVE"
        target_metric = change.metric_key

        classification = "NEUTRAL"
        confidence = 0.85
        explanation = ""

        # 1. Price movement classification
        if target_metric == "priceChange":
            pct = change.change_percentage or 0.0
            if pct > 0:
                classification = "SUPPORTING"
                explanation = f"Price positive momentum (+{pct:.1f}%) aligns with affirmative thesis outlook."
            elif pct < -1.5:
                classification = "CONTRADICTING"
                explanation = f"Price decline of {pct:.1f}% indicates market resistance to the thesis expectations."
            else:
                classification = "NEUTRAL"
                explanation = f"Price movement ({pct:+.1f}%) is within normal trading consolidation."

        # 2. Operating margin
        elif target_metric == "operatingMargin":
            pct = change.change_percentage
            val_f = float(change.current_value.replace("%", "")) if "%" in change.current_value else 0.0
            if pct is not None:
                if pct > 0:
                    classification = "SUPPORTING" if expected_dir == "POSITIVE" else "CONTRADICTING"
                    explanation = f"Operating margin improved by {pct:+.2f}%, demonstrating healthy operational leverage."
                elif pct < 0:
                    classification = "CONTRADICTING" if expected_dir == "POSITIVE" else "SUPPORTING"
                    explanation = f"Operating margin contracted by {abs(pct):.2f}%, indicating margin pressure or cost inflation."
                else:
                    classification = "NEUTRAL"
                    explanation = f"Operating margin stable at {change.current_value}."
            else:
                classification = "SUPPORTING" if val_f >= 15.0 else "NEUTRAL"
                explanation = f"Reported operating margin of {change.current_value} provides healthy baseline."

        # 3. Revenue growth
        elif target_metric == "revenueGrowth":
            pct = change.change_percentage or 0.0
            if pct > 0:
                classification = "SUPPORTING" if expected_dir == "POSITIVE" else "CONTRADICTING"
                explanation = f"Top-line revenue expanded by {pct:+.1f}%, directly verifying business growth."
            elif pct < 0:
                classification = "CONTRADICTING" if expected_dir == "POSITIVE" else "SUPPORTING"
                explanation = f"Top-line contracted by {pct:.1f}%, working against revenue growth expectations."
            else:
                classification = "NEUTRAL"
                explanation = "Top-line revenue remained flat."

        # 4. Valuation (P/E or P/B)
        elif target_metric in ["pe", "pb"]:
            if "details" in change.__dict__ and "pe" in change.details:
                pe_val = change.details["pe"]
                if pe_val:
                    if pe_val < 25.0:
                        classification = "SUPPORTING"
                        explanation = f"P/E ratio of {pe_val:.1f}x supports reasonable or attractive valuation thesis."
                    elif pe_val > 50.0:
                        classification = "CONTRADICTING"
                        explanation = f"Elevated P/E multiple of {pe_val:.1f}x stretches valuation margin of safety."
                    else:
                        classification = "NEUTRAL"
                        explanation = f"P/E multiple at {pe_val:.1f}x aligns with average market pricing."
            else:
                classification = "NEUTRAL"
                explanation = f"Valuation multiple at {change.current_value} evaluated against historical baseline."

        # 5. News / Management Commentary / Deal Wins
        elif change.source_type == "NEWS":
            pre_classified = change.details.get("classification")
            if pre_classified in ["SUPPORTING", "CONTRADICTING"]:
                classification = pre_classified
                explanation = change.change_value
            else:
                classification = "NEUTRAL"
                explanation = f"Event context from {change.details.get('source', 'Press')}: {change.current_value}"

        # 6. Fallback
        else:
            classification = "NEUTRAL"
            explanation = change.significance_reason or f"Signal monitored: {change.current_value}"

        return EvidenceResponse(
            id=f"ev_{int(now.timestamp() * 1000)}_{change.metric_key}",
            thesisId="",
            symbol="",
            signalName=change.signal_name,
            sourceType=change.source_type,
            sourceId=change.source_id,
            previousValue=change.previous_value,
            currentValue=change.current_value,
            changeValue=change.change_value,
            changePercentage=change.change_percentage,
            classification=classification,
            confidence=confidence,
            explanation=explanation,
            timestamp=now
        )

evidence_classifier = EvidenceClassifier()
