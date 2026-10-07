# Automated Micro-Influencer Outreach System

An end-to-end pipeline that discovers micro-influencers on YouTube, filters and classifies them, enriches their profiles, generates personalized outreach messages with an LLM, and runs a (simulated) sending layer with duplicate prevention and an outreach log.

**Niche:** Fashion & Beauty
**Platform:** YouTube
**Brand used for outreach:** GlowLeaf, a *fictional* clean-skincare brand used only to demonstrate personalization.

```
Discovery -> Data Collection -> Filtering -> Enrichment -> AI Personalization -> Sending -> Tracking
```

---

## Technology Stack

| Purpose | Tool |
|---|---|
| Language | Python 3 |
| Discovery and metrics | YouTube Data API v3 (`google-api-python-client`) |
| Data processing and storage | `pandas`, CSV files |
| AI personalization | Google Gemini API (`google-genai`) |
| Email sending | `smtplib` (Gmail SMTP), simulated by default |
| Secrets | `python-dotenv` (`.env` file) |

## APIs and Tools Used

- **YouTube Data API v3**: channel search, channel statistics, recent videos, video statistics
- **Google Gemini API**: content-theme extraction and message generation (model set in `personalize.py`)
- **Gmail SMTP** (optional, disabled by default): real email delivery

## Data Sources

All data comes from the official YouTube Data API and from text that channels publish publicly (channel descriptions and video titles). No scraping of Instagram or any other platform is performed, and no platform restrictions are bypassed.

---

## Project Structure

```
influencer-outreach/
├── discovery.py       # search channels and fetch channel details
├── enrichment.py      # recent videos, engagement rate, email extraction
├── filtering.py       # PASS/FAIL rules with reasons
├── personalize.py     # Gemini: themes, email pitch, Instagram DM
├── sender.py          # send/simulate email, duplicate check, outreach log
├── main.py            # orchestrator that runs the full pipeline
├── data/
│   ├── raw_channels.csv       # all discovered channels
│   ├── influencers.csv        # full dataset with PASS/FAIL + reason
│   ├── messages.csv           # email + DM for shortlisted influencers
│   ├── outreach_log.csv       # outreach tracker
│   └── manual_dm_queue.csv    # Instagram DMs for manual sending
├── .env.example
├── requirements.txt
└── README.md
```

---

## Discovery Methodology

1. A list of keywords (for example "skincare routine", "makeup tutorial", "fashion haul", "outfit ideas", "beauty review", "hair care routine") is searched through the YouTube search endpoint with `type=channel`.
2. Results are paginated and de-duplicated using a set of channel IDs.
3. Channel details (name, description, country, subscriber count, video count, uploads playlist) are fetched in batches of 50 IDs per request to save API quota.
4. All discovered channels are saved to `data/raw_channels.csv`, including ones outside the micro-influencer range, so the dataset shows who passed and who failed and why.

## Filtering Logic

Each channel is evaluated by `filtering.py` and receives a `PASS` or `FAIL` status plus a human-readable reason.

| Criterion | Rule |
|---|---|
| Follower count | 5,000 to 100,000 subscribers |
| Engagement rate | At least 2% (average of the last 10 videos) |
| Content relevance | Fashion/beauty keywords found in the channel description or recent video titles |
| Activity | Last upload within 90 days |
| Missing data | Missing engagement data is a FAIL with the reason "engagement not available" |

Niche classification (`Beauty`, `Fashion`, or `Other`) is done by counting beauty versus fashion keywords in the channel description and recent titles.

Example reasons: `followers 1460000 outside 5k-100k`, `engagement 1.16% < 2%`, `inactive > 90 days`.

## Enrichment Process

For every discovered channel the system collects:

| Field | How it is obtained |
|---|---|
| Name, platform, profile URL | YouTube API |
| Follower count | YouTube API (`subscriberCount`) |
| Engagement rate | `(likes + comments) / views * 100`, averaged over the last 10 videos |
| Category / niche | Keyword-based classification |
| Content themes | Gemini summarizes recent video titles into 3 themes (shortlisted influencers only) |
| Contact email | Regex search on the public channel description. If none is found it is recorded as `Not Found` |
| Country | YouTube API if the channel set one, otherwise `Not Found` |
| Audience age / gender / geography | **Not available** from public YouTube data, so not collected |

Emails are never guessed or generated. If no public email is visible, the record says `Not Found`.

## AI Model and Prompt

- **Model:** Google Gemini, configured through the `MODEL` variable in `personalize.py`.
- **Output format:** JSON (`response_mime_type="application/json"`) so responses are parsed reliably.

Prompt used for message generation:

```
You write outreach for GlowLeaf, a clean skincare brand.
Influencer: {name}
Niche: {niche}
Content themes: {themes}
Recent video: {most recent video title}

Return JSON with two keys:
"email": 60-90 words. Reference their recent video title and niche, propose ONE
collaboration angle (affiliate, UGC, or barter), include a clear value proposition.
Natural tone, no hype.
"dm": 15-30 words, short and casual, personalized to their content.
Do not mention any email.

Rules: use ONLY the details given above. Do not invent facts about the influencer,
their audience, or their videos beyond what is listed. Do not claim any earlier contact.
```

## Personalization Logic

- Messages are generated per influencer, not from a single fixed template.
- Each prompt contains that influencer's name, niche, extracted content themes, and most recent video title.
- The model chooses one collaboration angle (affiliate, UGC, or barter) that fits the creator.
- **Validation loop:** the code counts words and regenerates (up to 3 attempts) if the email is outside 60-90 words or the DM is outside 15-30 words. If all attempts fail, the record is marked `Generation failed` rather than filled with fake content.
- Temporary API errors (HTTP 503/429) are retried automatically with increasing wait times.
- Messages are only generated for influencers who passed filtering, which saves API quota.

## Sending Mechanism

Implemented in `sender.py`:

1. Select shortlisted influencers with a valid contact email.
2. Retrieve their personalized email.
3. Send via Gmail SMTP, or **simulate** sending (default: `SIMULATE = True`, which prints the message instead of sending).
4. Record the status in `data/outreach_log.csv`.
5. **Duplicate prevention:** an email address already present in the log is skipped.

Possible statuses: `Sent`, `Simulated`, `Skipped - No Email`, `Skipped - Generation Failed`, `Failed: <reason>`.

**Instagram DMs are never sent automatically.** To respect platform rules, generated DMs are written to `data/manual_dm_queue.csv` with a `sent_manually` column for a manual workflow.

To enable real email sending, set `SIMULATE = False` in `sender.py` and add `GMAIL_USER` and `GMAIL_APP_PASSWORD` to `.env`.

## Outreach Tracker Fields

`data/outreach_log.csv` columns: `influencer`, `email`, `message_generated`, `sent`, `date`, `status`.

---

## Setup Instructions

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd influencer-outreach

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the data folder
mkdir data

# 5. Add API keys
cp .env.example .env              # then edit .env
```

`.env` contents:

```
YOUTUBE_API_KEY=your_youtube_key
GEMINI_API_KEY=your_gemini_key
```

How to get the keys:
- **YouTube:** Google Cloud Console, create a project, enable *YouTube Data API v3*, create an API key.
- **Gemini:** Google AI Studio, create an API key.

Run the full pipeline:

```bash
python main.py
```

Run stages individually for testing:

```bash
python discovery.py     # saves data/raw_channels.csv
python personalize.py   # tests Gemini message generation
```

Run `main.py` a second time to see duplicate prevention (`duplicate skipped`) in action.

---

## Results of the Test Run

> Fill these in from your own run. Do not estimate.

| Metric | Value |
|---|---|
| Channels discovered | `<number>` |
| Channels in 5k-100k range | `<number>` |
| Passed filtering | `<number>` |
| Failed filtering | `<number>` |
| Shortlisted with public email | `<number>` |
| Emails simulated | `<number>` |

---

## Error Handling

- Per-channel `try/except` in enrichment, so one failing channel does not stop the run.
- Missing values are recorded as `Not Found` or `None` instead of being invented.
- Retries with backoff for temporary Gemini errors.
- Failed message generation is logged, not hidden.
- Raw data is saved after discovery so the YouTube quota is not spent twice.

## Limitations

- **Audience demographics** (age, gender, geography) are not available from public YouTube data and are marked unavailable.
- **Many creators do not publish an email**, so a large share of shortlisted influencers are logged as `Skipped - No Email`.
- **Engagement rate** is based on only the last 10 videos, so it is an estimate.
- **Niche classification is keyword-based**, so it can misclassify channels with ambiguous descriptions.
- **Regex email extraction** can occasionally match text that is not a real address.
- **YouTube API quota** (10,000 units per day by default) limits how many searches can be run per day; each search call costs 100 units.
- **Gemini free tier** has rate limits and occasional temporary outages.
- **Instagram DMs** are manual by design.
- Only YouTube is implemented. Other platforms would need separate, permitted data sources.

## Scalability (50 to 500+ influencers)

- **Pagination and batching:** already used for search and for 50-ID channel lookups; extend with more keywords and pages.
- **Caching:** store raw API responses so reruns do not consume quota.
- **Quota management:** request a quota increase or rotate projects/keys for larger runs.
- **Storage:** replace CSV files with SQLite or PostgreSQL for indexing, deduplication, and resumable runs.
- **Concurrency:** process enrichment and message generation in parallel batches with rate limiting.
- **Queue-based sending:** use a job queue (for example Celery or a cloud queue) with throttling for real email delivery.
- **Orchestration:** schedule runs with cron, n8n, or Airflow.
- **Human review:** add an approval step before sending, which the workflow already allows through `messages.csv`.

## Ethical and Data Integrity Notes

- No fabricated influencer data, no guessed emails, and no fake metrics.
- Unavailable data is explicitly marked.
- Emails are sent only in simulation mode by default.
- Only publicly visible contact information from official API data is used.
