import pandas as pd
from datetime import datetime, timezone

from discovery import discover_channels, get_channel_details, KEYWORDS
from enrichment import get_recent_videos, engagement_rate, find_email
from filtering import evaluate
from personalize import get_themes, generate_valid
from sender import send_email, already_sent, log_outreach, init_log

BEAUTY_TERMS = ["skincare", "makeup", "beauty", "hair", "cosmetic"]
FASHION_TERMS = ["fashion", "outfit", "style", "haul", "wardrobe"]


def classify_niche(text):
    text = text.lower()
    b = sum(t in text for t in BEAUTY_TERMS)
    f = sum(t in text for t in FASHION_TERMS)
    if b == 0 and f == 0:
        return "Other"
    return "Beauty" if b >= f else "Fashion"


def days_since(date_str):
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - d).days
    except Exception:
        return None


def main():
    # Stage 1: Discovery
    print("Stage 1: discovering channels...")
    ids = discover_channels(KEYWORDS)
    channels = get_channel_details(ids)
    pd.DataFrame(channels).to_csv("data/raw_channels.csv", index=False)
    print(f"  {len(channels)} channels found")
    channels = channels[:10]
    # Stage 2: Enrichment
    print("Stage 2: enriching profiles...")
    for ch in channels:
        try:
            titles, dates, stats = get_recent_videos(ch["uploads_playlist"])
            ch["titles"] = titles
            ch["engagement"] = engagement_rate(stats)
            ch["days_since_last_post"] = days_since(dates[0]) if dates else None
        except Exception as e:
            print(f"  enrichment failed for {ch['name']}: {e}")
            ch["titles"] = []
            ch["engagement"] = None
            ch["days_since_last_post"] = None
        ch["email"] = find_email(ch["description"])
        ch["niche"] = classify_niche(ch["description"] + " " + " ".join(ch["titles"]))

    # Stage 3: Filtering
    print("Stage 3: filtering...")
    for ch in channels:
        ch["status"], ch["reason"] = evaluate(ch)
    passed = [c for c in channels if c["status"] == "PASS"]
    print(f"  {len(passed)} passed, {len(channels) - len(passed)} failed")
    passed=passed[:5]

    # Stage 4: AI personalization (PASS only)
    print("Stage 4: generating messages...")
    for ch in passed:
        ch["themes"] = get_themes(ch["titles"])
        msgs = generate_valid(ch)
        ch["email_msg"] = msgs["email"] if msgs else "Generation failed"
        ch["dm_msg"] = msgs["dm"] if msgs else "Generation failed"

    print("Stage 5: generating messages...")
    init_log()
    # Save the dataset (all channels, with pass/fail and reason)
    out = pd.DataFrame(channels)
    out["titles"] = out["titles"].apply(lambda t: " | ".join(t))
    out.to_csv("data/influencers.csv", index=False)

    # Save the messages for shortlisted influencers
    pd.DataFrame([{
        "name": c["name"], "email": c["email"],
        "email_message": c["email_msg"], "instagram_dm": c["dm_msg"],
    } for c in passed]).to_csv("data/messages.csv", index=False)

    # Stage 5: Sending layer
    print("Stage 5: sending (simulated)...")
    dm_queue = []
    for ch in passed:
        if ch["email_msg"] == "Generation failed":
            log_outreach(ch["name"], ch["email"], "No", "No", "Skipped - Generation Failed")
        elif ch["email"] == "Not Found":
            log_outreach(ch["name"], ch["email"], "Yes", "No", "Skipped - No Email")
        elif already_sent(ch["email"]):
            print(f"  duplicate skipped: {ch['email']}")
        else:
            try:
                status = send_email(ch["email"],
                                    f"Collaboration idea for {ch['name']}",
                                    ch["email_msg"])
                log_outreach(ch["name"], ch["email"], "Yes", "Yes", status)
            except Exception as e:
                log_outreach(ch["name"], ch["email"], "Yes", "No", f"Failed: {e}")
        # Instagram DMs are never automated, only queued for manual sending
        dm_queue.append({"name": ch["name"], "dm": ch["dm_msg"], "sent_manually": "No"})

    pd.DataFrame(dm_queue).to_csv("data/manual_dm_queue.csv", index=False)
    print("Done. Check the data/ folder.")


if __name__ == "__main__":
    main()