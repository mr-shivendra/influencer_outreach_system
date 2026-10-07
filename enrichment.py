import re
from discovery import yt

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

def find_email(description):
    match = EMAIL_RE.search(description or "")
    return match.group(0) if match else "Not Found"

def get_recent_videos(uploads_playlist, n=10):
    resp = yt.playlistItems().list(
        playlistId=uploads_playlist, part="contentDetails,snippet",
        maxResults=n).execute()
    video_ids = [v["contentDetails"]["videoId"] for v in resp["items"]]
    titles = [v["snippet"]["title"] for v in resp["items"]]
    dates = [v["contentDetails"].get("videoPublishedAt") for v in resp["items"]]
    stats = yt.videos().list(id=",".join(video_ids), part="statistics").execute()
    return titles, dates, stats["items"]

def engagement_rate(video_stats):
    rates = []
    for v in video_stats:
        s = v["statistics"]
        views = int(s.get("viewCount", 0))
        if views > 0:
            likes = int(s.get("likeCount", 0))
            comments = int(s.get("commentCount", 0))
            rates.append((likes + comments) / views * 100)
    return round(sum(rates) / len(rates), 2) if rates else None