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

        # 1. Retrieve last check session baseline for this stock
        last_check = snapshot_service.get_last_check_session(db, thesis.watchlistItemId, thesis.watchlist_item.symbol)
        last_checked_at = last_check.checkedAt if last_check else None

        # 2. Capture snapshots for historical baseline tracking
        snapshot_service.capture_market_snapshot(db, thesis.watchlist_item.symbol, quote, technicals.volatility)
        snapshot_service.capture_fundamental_snapshot(db, thesis.watchlist_item.symbol, fundamentals)

        # 3. Get signal definitions for this thesis
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

        # 4. Detect objective changes across market, fundamental, and news against last check baseline
        detected_changes = []
        detected_changes.extend(change_detection_engine.detect_market_changes(quote, last_check, technicals))
        detected_changes.extend(change_detection_engine.detect_fundamental_changes(fundamentals, last_check))
        detected_changes.extend(change_detection_engine.detect_news_changes(news.relevantNews))

        # 5. Build Layer 1: Objective Meaningful Changes & Layer 2: Thesis-Aware Evidence
        from backend.app.schemas.evidence import ObjectiveChangeResponse
        objective_changes: List[ObjectiveChangeResponse] = []
        supporting_evidence: List[EvidenceResponse] = []
        contradicting_evidence: List[EvidenceResponse] = []
        neutral_evidence: List[EvidenceResponse] = []

        # Clear old transient evidence for this evaluation cycle
        db.query(Evidence).filter(Evidence.thesisId == thesis.id).delete()

        meaningful_changes = [c for c in detected_changes if c.is_meaningful]
        has_meaningful_change = len(meaningful_changes) > 0

        for change in detected_changes:
            # Classify thesis impact (Layer 2)
            ev = evidence_classifier.classify_change(change, thesis.text, thesis.category, signals_dicts)
            ev.thesisId = thesis.id
            ev.symbol = thesis.watchlist_item.symbol

            # Create Layer 1 Objective Change item
            obj_change = ObjectiveChangeResponse(
                id=ev.id,
                signalName=change.signal_name,
                category=change.category,
                sourceType=change.source_type,
                previousValue=change.previous_value,
                currentValue=change.current_value,
                changeValue=change.change_value,
                changePercentage=change.change_percentage,
                magnitude=change.magnitude or (f"{change.change_percentage:+.1f}%" if change.change_percentage is not None else None),
                isMeaningful=change.is_meaningful,
                significanceReason=change.significance_reason or "Material change detected against baseline",
                thesisImpact=ev.classification
            )
            if change.is_meaningful:
                objective_changes.append(obj_change)

            # Only persist and count evidence for thesis if meaningful or specifically relevant
            if change.is_meaningful:
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

        # 6. Synthesize Status & Explainability Summary
        num_sup = len(supporting_evidence)
        num_con = len(contradicting_evidence)
        num_neu = len(neutral_evidence)
        num_obj_meaningful = len(objective_changes)

        if num_con > 0:
            status = "THESIS_NEEDS_ATTENTION"
            summary = f"Your thesis needs attention because {num_con} contradictory signal{'s' if num_con > 1 else ''} emerged against your investment premise."
            if num_sup > 0:
                summary += f" ({num_sup} supporting signal{'s' if num_sup > 1 else ''} also detected)."
        elif num_sup > 0:
            status = "THESIS_STRENGTHENING"
            summary = f"Your thesis is strengthening: {num_sup} real-world signal{'s' if num_sup > 1 else ''} actively confirm and support your premise."
        elif has_meaningful_change:
            status = "MEANINGFUL_CHANGE"
            summary = f"{num_obj_meaningful} meaningful change{'s' if num_obj_meaningful > 1 else ''} detected since your last check, but none materially alter your core thesis."
        else:
            status = "NO_MEANINGFUL_CHANGE"
            summary = "No meaningful shifts detected in fundamental ratios, guidance, company news, or price volatility since your last check."

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

        # Persist CheckSession so future checks compare against this observation
        latest_headline = news.relevantNews[0].title if (news and news.relevantNews) else None
        snapshot_service.record_check_session(
            db=db,
            watchlistItemId=thesis.watchlistItemId,
            symbol=thesis.watchlist_item.symbol,
            price=quote.price,
            change=quote.change,
            percentageChange=quote.percentageChange,
            volume=quote.volume,
            volatility=technicals.volatility if technicals else None,
            pe=fundamentals.pe if fundamentals else None,
            pb=fundamentals.pb if fundamentals else None,
            eps=fundamentals.eps if fundamentals else None,
            roe=fundamentals.roe if fundamentals else None,
            margin=fundamentals.margin if fundamentals else None,
            revenue=fundamentals.revenue if fundamentals else None,
            profit=fundamentals.profit if fundamentals else None,
            debt=fundamentals.debt if fundamentals else None,
            latestHeadline=latest_headline,
            newsCount=len(news.relevantNews) if news else 0,
            overallStatus=status,
            hasMeaningfulChange=has_meaningful_change,
            meaningfulChangeCount=num_obj_meaningful,
            supportingCount=num_sup,
            contradictingCount=num_con,
            neutralCount=num_neu
        )

        db.commit()
        db.refresh(thesis)

        return WhatChangedResponse(
            symbol=thesis.watchlist_item.symbol,
            companyName=thesis.watchlist_item.companyName,
            thesisId=thesis.id,
            thesisText=thesis.text,
            thesisCategory=thesis.category,
            status=status,
            hasMeaningfulChange=has_meaningful_change,
            meaningfulChangeCount=num_obj_meaningful,
            supportingCount=num_sup,
            contradictingCount=num_con,
            neutralCount=num_neu,
            summary=summary,
            lastCheckedAt=last_checked_at or now,
            lastEvaluatedAt=now,
            objectiveChanges=objective_changes,
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
            st = "NO_MEANINGFUL_CHANGE"
            if item.thesis:
                st = item.thesis.status or "NO_MEANINGFUL_CHANGE"
            
            # Map statuses according to specifications:
            # THESIS CHANGED = stocks where user's thesis-relevant state has materially changed
            # NEEDS ATTENTION = stocks where meaningful changes require investigation or work against thesis
            # NO CHANGE = stocks with no meaningful changes since previous check
            if st in ("THESIS_NEEDS_ATTENTION", "NEEDS_ATTENTION"):
                needs_attention += 1
            elif st in ("THESIS_STRENGTHENING", "STRENGTHENING", "MEANINGFUL_CHANGE"):
                thesis_changed += 1
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
