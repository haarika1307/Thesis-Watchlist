import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.thesis import Thesis
from backend.app.models.thesis_signal import ThesisSignal
from backend.app.models.evidence import Evidence
from backend.app.models.evaluation import Evaluation, WatchlistEvaluation
from backend.app.models.watchlist import Watchlist
from backend.app.models.watchlist_item import WatchlistItem
from backend.app.schemas.evidence import EvidenceResponse, WhatChangedResponse
from backend.app.schemas.market import QuoteResponse, FundamentalsResponse, TechnicalsResponse
from backend.app.schemas.news import NewsListResponse
from backend.app.services.change_detection.detector import change_detection_engine
from backend.app.services.intelligence.evidence_classifier import evidence_classifier
from backend.app.services.snapshot.snapshot_service import snapshot_service

logger = logging.getLogger(__name__)

class ThesisEvaluator:
    """Evaluates thesis health by executing change detection, evidence classification, and status synthesis."""

    def evaluate_thesis(
        self,
        db: Session,
        thesis: Thesis,
        quote: QuoteResponse,
        fundamentals: FundamentalsResponse,
        technicals: TechnicalsResponse,
        news: NewsListResponse
    ) -> WhatChangedResponse:
        """Run full evaluation pipeline on a thesis and persist the evaluation and evidence."""
        now = datetime.now(timezone.utc)

        # 1. Take snapshots for historical baseline tracking
        snapshot_service.capture_market_snapshot(db, thesis.watchlist_item.symbol, quote, technicals.volatility)
        snapshot_service.capture_fundamental_snapshot(db, thesis.watchlist_item.symbol, fundamentals)

        # 2. Get signal definitions for this thesis
        signals_db = db.query(ThesisSignal).filter(ThesisSignal.thesisId == thesis.id).all()
        signals_dicts = [
            {
                "signalName": s.signalName,
                "topic": s.topic,
                "direction": s.direction,
                "importance": s.importance,
                "targetMetric": s.description
            }
            for s in signals_db
        ]

        # 3. Detect changes across market, fundamental, and news
        detected_changes = []
        detected_changes.extend(change_detection_engine.detect_market_changes(quote, None, technicals))
        detected_changes.extend(change_detection_engine.detect_fundamental_changes(fundamentals, None))
        detected_changes.extend(change_detection_engine.detect_news_changes(news.relevantNews))

        # 4. Filter for meaningful changes & classify each
        supporting_evidence: List[EvidenceResponse] = []
        contradicting_evidence: List[EvidenceResponse] = []
        neutral_evidence: List[EvidenceResponse] = []

        # Clear old transient evidence for this evaluation cycle or keep historical
        db.query(Evidence).filter(Evidence.thesisId == thesis.id).delete()

        for change in detected_changes:
            if not change.is_meaningful:
                continue

            ev = evidence_classifier.classify_change(change, thesis.text, thesis.category, signals_dicts)
            ev.thesisId = thesis.id
            ev.symbol = thesis.watchlist_item.symbol

            # Persist Evidence row
            db_ev = Evidence(
                thesisId=thesis.id,
                symbol=thesis.watchlist_item.symbol,
                signalName=ev.signalName,
                sourceType=ev.sourceType,
                sourceId=ev.sourceId,
                previousValue=ev.previousValue,
                currentValue=ev.currentValue,
                changeValue=ev.changeValue,
                changePercentage=ev.changePercentage,
                classification=ev.classification,
                confidence=ev.confidence,
                explanation=ev.explanation,
                timestamp=now
            )
            db.add(db_ev)

            if ev.classification == "SUPPORTING":
                supporting_evidence.append(ev)
            elif ev.classification == "CONTRADICTING":
                contradicting_evidence.append(ev)
            else:
                neutral_evidence.append(ev)

        # Update signal current values in DB
        for s in signals_db:
            for ev in (supporting_evidence + contradicting_evidence + neutral_evidence):
                if s.signalName.lower() in ev.signalName.lower() or ev.signalName.lower() in s.signalName.lower():
                    s.previousValue = s.currentValue
                    s.currentValue = ev.currentValue
                    break

        # 5. Synthesize Status & Explainability Summary
        num_sup = len(supporting_evidence)
        num_con = len(contradicting_evidence)
        num_neu = len(neutral_evidence)

        if num_con > 0 and num_sup > 0:
            status = "NEEDS_ATTENTION"
            summary = f"Your thesis needs attention because {num_sup} relevant signal{'s' if num_sup > 1 else ''} strengthened while {num_con} relevant signal{'s' if num_con > 1 else ''} weakened."
        elif num_con > 0 and num_sup == 0:
            status = "NEEDS_ATTENTION"
            summary = f"Your thesis needs attention because {num_con} contradictory signal{'s' if num_con > 1 else ''} emerged against your initial expectations."
        elif num_sup > 0 and num_con == 0:
            status = "STRENGTHENING"
            summary = f"Your thesis is strengthening: {num_sup} real-world signal{'s' if num_sup > 1 else ''} actively confirm and support your premise."
        else:
            status = "NO_CHANGE"
            summary = "No meaningful shifts detected in fundamental ratios, guidance, or price volatility since last observation."

        # Update Thesis status
        thesis.status = status
        thesis.lastEvaluatedAt = now

        # Create Evaluation Record
        eval_record = Evaluation(
            thesisId=thesis.id,
            status=status,
            supportingCount=num_sup,
            contradictingCount=num_con,
            neutralCount=num_neu,
            confidence=0.88,
            summary=summary,
            evaluatedAt=now
        )
        db.add(eval_record)
        db.commit()
        db.refresh(thesis)

        return WhatChangedResponse(
            symbol=thesis.watchlist_item.symbol,
            companyName=thesis.watchlist_item.companyName,
            thesisId=thesis.id,
            thesisText=thesis.text,
            thesisCategory=thesis.category,
            status=status,
            supportingCount=num_sup,
            contradictingCount=num_con,
            neutralCount=num_neu,
            summary=summary,
            lastEvaluatedAt=now,
            supportingEvidence=supporting_evidence,
            contradictingEvidence=contradicting_evidence,
            neutralEvidence=neutral_evidence
        )

    def evaluate_watchlist(self, db: Session, watchlist_id: str) -> WatchlistEvaluation:
        """Calculate aggregate watchlist status counts."""
        watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
        if not watchlist:
            raise ValueError("Watchlist not found")

        items = db.query(WatchlistItem).filter(WatchlistItem.watchlistId == watchlist_id).all()
        now = datetime.now(timezone.utc)

        thesis_changed = 0
        needs_attention = 0
        no_change = 0

        for item in items:
            if item.thesis:
                st = item.thesis.status
                if st == "STRENGTHENING":
                    thesis_changed += 1
                elif st == "NEEDS_ATTENTION":
                    needs_attention += 1
                else:
                    no_change += 1
            else:
                no_change += 1

        w_eval = WatchlistEvaluation(
            watchlistId=watchlist_id,
            lastCheckedAt=now,
            thesisChangedCount=thesis_changed,
            needsAttentionCount=needs_attention,
            noChangeCount=no_change
        )
        db.add(w_eval)
        db.commit()
        db.refresh(w_eval)
        return w_eval

thesis_evaluator = ThesisEvaluator()
