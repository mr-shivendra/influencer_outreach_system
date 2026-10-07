import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
yt = build("youtube", "v3", developerKey=os.getenv("YOUTUBE_API_KEY"))

KEYWORDS = ["skincare routine", "makeup tutorial", "fashion haul",
            "outfit ideas", "beauty review", "hair care routine"]

def discover_channels(keywords, per_keyword=40):
    channel_ids = set()
    for kw in keywords:
        token = None
        fetched = 0
        while fetched < per_keyword:
            resp = yt.search().list(
                q=kw, type="channel", part="snippet",
                maxResults=20, pageToken=token).execute()
            for item in resp["items"]:
                channel_ids.add(item["snippet"]["channelId"])
            fetched += 20
            token = resp.get("nextPageToken")
            if not token:
                break
    return list(channel_ids)

def get_channel_details(ids):
    rows = []
    for i in range(0, len(ids), 50):          # API allows 50 per call
        resp = yt.channels().list(
            id=",".join(ids[i:i+50]),
            part="snippet,statistics,contentDetails").execute()
        for c in resp["items"]:
            s = c["statistics"]
            rows.append({
                "channel_id": c["id"],
                "name": c["snippet"]["title"],
                "description": c["snippet"]["description"],
                "country": c["snippet"].get("country", "Not Found"),
                "followers": int(s.get("subscriberCount", 0)),
                "video_count": int(s.get("videoCount", 0)),
                "uploads_playlist": c["contentDetails"]["relatedPlaylists"]["uploads"],
                "profile_url": f"https://www.youtube.com/channel/{c['id']}",
                "platform": "YouTube",
            })
    return rows


if __name__ == "__main__":
    ids = discover_channels(KEYWORDS)
    print(f"Found {len(ids)} unique channels")
    rows = get_channel_details(ids)
    pd.DataFrame(rows).to_csv("data/raw_channels.csv", index=False)
    print("Saved to data/raw_channels.csv")