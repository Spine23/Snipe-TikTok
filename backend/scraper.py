# scraper.py
import json
import time
from TikTokApi import TikTokApi

hashtags = ["news", "usa", "uk", "event"]
max_results = 20
output_file = "captions.json"

def is_non_influencer(user):
    return user.get("verified") is False and user.get("followerCount", 0) < 10000

def is_early_viral(stats):
    return (
        stats.get("playCount", 0) < 500
        and stats.get("diggCount", 0) > 20
        and stats.get("shareCount", 0) >= 10
        and stats.get("commentCount", 0) < 10
    )

def fetch_tiktoks():
    api = TikTokApi()
    collected = []

    for tag in hashtags:
        try:
            results = api.hashtag(name=tag).videos(count=max_results)
            for video in results:
                if not video or not video.as_dict:
                    continue

                data = video.as_dict
                desc = data.get("desc", "")
                stats = data.get("stats", {})
                author = data.get("author", {})

                if not is_non_influencer(author) or not is_early_viral(stats):
                    continue

                print("✅ Found:", desc)
                collected.append(desc)

        except Exception as e:
            print("❌ Error scraping:", e)

    return collected

def save_to_json(captions):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(captions, f, indent=2)

if __name__ == "__main__":
    print("🚀 Running TikTok Scraper...")
    captions = fetch_tiktoks()
    save_to_json(captions)
    print(f"✅ Saved {len(captions)} captions to {output_file}")
