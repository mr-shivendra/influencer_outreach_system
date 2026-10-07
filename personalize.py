# personalize.py
import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3.8-flash"   # if "model not found", check Google AI Studio for the current name


def ask_llm_json(prompt):
    """Send a prompt to Gemini and return the parsed JSON response."""
    resp = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )
    time.sleep(4)   # stay under the free-tier rate limit
    text = resp.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)


def get_themes(titles):
    """Summarize recent video titles into 3 content themes."""
    prompt = (
        f"Recent video titles:\n{titles}\n\n"
        "Return 3 short content themes as a JSON list of strings."
    )
    try:
        return ask_llm_json(prompt)
    except Exception as e:
        print("Theme generation failed:", e)
        return ["Not Found"]


def generate_messages(inf):
    """Generate a personalized email and Instagram DM for one influencer."""
    recent_title = inf["titles"][0] if inf.get("titles") else "your recent content"
    prompt = f"""You write outreach for GlowLeaf, a clean skincare brand.
Influencer: {inf['name']}
Niche: {inf['niche']}
Content themes: {inf['themes']}
Recent video: {recent_title}

Return JSON with two keys:
"email": 60-90 words. Reference their recent video and audience, propose ONE collaboration angle (affiliate, UGC, or barter), include a clear value proposition. Natural tone, no hype.
"dm": 15-30 words, short and casual, personalized to their content."""
    return ask_llm_json(prompt)


def words(text):
    """Count words in a piece of text."""
    return len(text.split())


def generate_valid(inf, retries=3):
    """Generate messages and retry until word limits are met."""
    for attempt in range(retries):
        try:
            out = generate_messages(inf)
            if 60 <= words(out["email"]) <= 90 and 15 <= words(out["dm"]) <= 30:
                return out
            print(f"Attempt {attempt + 1}: word count out of range, retrying...")
        except Exception as e:
            print("Message generation error:", e)
    return None   # log as "Generation failed"


if __name__ == "__main__":
    test = {
        "name": "Sarah Glow",
        "niche": "Beauty",
        "themes": ["Skincare routines", "Makeup tutorials"],
        "titles": ["My 5-step night routine"],
    }
    print("Themes:", get_themes(test["titles"]))
    out = generate_valid(test)
    print(out)
    if out:
        print("Email words:", words(out["email"]), "| DM words:", words(out["dm"]))