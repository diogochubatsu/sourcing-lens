"""
AI Verdict Service
Rule-based scoring that produces a sell/don't-sell recommendation.
No LLM needed for MVP — pure logic on available data.
"""
from models import Verdict, MarginEntry, MatchResult, MarketPulse


def compute_verdict(
    margins: list[MarginEntry],
    matches: list[MatchResult],
    pulse: MarketPulse | None,
    source_product: dict | None = None,
) -> Verdict:
    """
    Generate a rule-based verdict on whether to sell this product.
    
    Scoring:
    - Margin > 50% on any platform: +3
    - Margin 30-50%: +1
    - Margin < 30%: -1
    - Margin < 0%: -3
    - Best confidence match > 90%: +2 (easy to source)
    - Competition "low": +2
    - Competition "medium": +1
    - Competition "high": -1
    - Velocity "hot": +2
    - Velocity "warm": +1
    - Velocity "cool": -1
    - Velocity "dead": -3
    """
    score = 0
    pros = []
    cons = []

    # --- Margin scoring ---
    best_margin = max((m.margin_pct for m in margins), default=0)
    best_platform = ""
    best_qty = 0
    for m in margins:
        if m.margin_pct == best_margin:
            best_platform = m.sell_platform
            best_qty = m.quantity
            break

    if best_margin > 60:
        score += 3
        pros.append(f"{best_margin}% margin on {best_platform} with {best_qty}-unit order — excellent")
    elif best_margin > 50:
        score += 2
        pros.append(f"{best_margin}% margin on {best_platform} — strong")
    elif best_margin > 30:
        score += 1
        pros.append(f"{best_margin}% margin on {best_platform} — decent")
    elif best_margin > 0:
        score -= 1
        cons.append(f"Best margin is only {best_margin}% — thin margins")
    else:
        score -= 3
        cons.append(f"Negative margin ({best_margin}%) — losing money")

    # --- Match confidence scoring ---
    if matches:
        best_conf = max(m.confidence for m in matches)
        if best_conf > 0.90:
            score += 2
            pros.append(f"{best_conf*100:.0f}% source match found — easy to source")
        elif best_conf > 0.70:
            score += 1
            pros.append(f"{best_conf*100:.0f}% source match — likely same product")
        else:
            cons.append(f"Best source match is only {best_conf*100:.0f}% — uncertain sourcing")
    
    if len(matches) < 2:
        cons.append("Few source options — limited supplier diversity")
    elif len(matches) >= 5:
        pros.append(f"{len(matches)} source options — good supplier diversity")

    # --- Pulse scoring ---
    if pulse:
        if pulse.velocity == "hot":
            score += 2
            pros.append("Product is trending hot right now")
        elif pulse.velocity == "warm":
            score += 1
            pros.append("Product demand is steady")
        elif pulse.velocity == "cool":
            score -= 1
            cons.append("Product demand is cooling")
        elif pulse.velocity == "dead":
            score -= 3
            cons.append("Product trend has died — avoid")

        if pulse.competition == "low":
            score += 2
            pros.append("Low competition — room for entry")
        elif pulse.competition == "medium":
            score += 1
            pros.append("Moderate competition — manageable")
        elif pulse.competition == "high":
            score -= 1
            cons.append("High competition — margins may compress")
        elif pulse.competition == "saturated":
            score -= 2
            cons.append("Market is saturated — very hard to compete")

    # --- Overall rating ---
    if score >= 6:
        rating = "strong"
    elif score >= 3:
        rating = "moderate"
    elif score >= 0:
        rating = "weak"
    else:
        rating = "avoid"

    # --- Recommendation ---
    rec_parts = []
    if rating == "strong":
        rec_parts.append("Strong opportunity.")
        if best_margin > 50:
            rec_parts.append(f"Start with {best_qty} units on {best_platform}.")
        if pulse and pulse.velocity == "hot":
            rec_parts.append("Act fast — trend may peak soon.")
    elif rating == "moderate":
        rec_parts.append("Decent opportunity with caveats.")
        rec_parts.append("Test with a small batch first (50 units).")
        if pulse and pulse.competition in ("high", "saturated"):
            rec_parts.append("Differentiate on listing quality or bundles.")
    elif rating == "weak":
        rec_parts.append("Proceed with caution.")
        rec_parts.append("Margins are thin or competition is stiff.")
        rec_parts.append("Only worth it at scale (500+ units).")
    else:
        rec_parts.append("Not recommended right now.")
        if best_margin <= 0:
            rec_parts.append("You would lose money at current prices.")
        if pulse and pulse.velocity in ("cool", "dead"):
            rec_parts.append("The trend has passed.")

    summary = " ".join(rec_parts)

    # Limit pros/cons to top 5 each
    return Verdict(
        rating=rating,
        summary=summary,
        pros=pros[:5],
        cons=cons[:5],
        recommendation=summary,
    )
