FASHION_BEAUTY_TERMS = ["skincare", "makeup", "beauty", "fashion", "outfit",
                        "hair", "style", "haul", "cosmetic"]

def evaluate(row):
    reasons = []
    if not (5000 <= row["followers"] <= 100000):
        reasons.append(f"followers {row['followers']} outside 5k-100k")
    if row["engagement"] is None:
        reasons.append("engagement not available")
    elif row["engagement"] < 2.0:
        reasons.append(f"engagement {row['engagement']}% < 2%")
    text = (row["description"] + " " + " ".join(row["titles"])).lower()
    if not any(t in text for t in FASHION_BEAUTY_TERMS):
        reasons.append("content not fashion/beauty related")
    if row["days_since_last_post"] is not None and row["days_since_last_post"] > 90:
        reasons.append("inactive > 90 days")
    return ("PASS", "All criteria met") if not reasons else ("FAIL", "; ".join(reasons))