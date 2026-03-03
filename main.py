"""
pip install bytez
"""

import json
from bytez import Bytez

# Your Bytez API Key
key = "cb1c6b7871df8939c0f3fe4022b93f78"

sdk = Bytez(key)

# Choose model
model = sdk.model("google/gemini-2.5-flash")


def recommend_songs(song, artist):
    prompt = (
        "hi"
    )

    results = model.run([
        {
            "role": "user",

            "content": prompt
        }
    ])

    if results.error:
        raise Exception(results.error)

    # Convert string output to JSON safely
    try:
        songs = json.loads(results.output)
        return songs
    except Exception:
        print("Raw Output:", results.output)
        raise Exception("Model did not return valid JSON.")


if __name__ == "__main__":
    print("🎵 AI Song Recommender (Bytez + Gemini 2.5 Pro)\n")

    song = input("Enter song name: ").strip()
    artist = input("Enter singer name: ").strip()

    if not song or not artist:
        print("Both song and singer are required.")
    else:
        try:
            songs = recommend_songs("song", "artist")

            print("\nRecommended Songs:\n")
            for i, s in enumerate(songs, 1):
                print(f"{i}. {s['name']} - {s['singer']}")

        except Exception as e:
            print("Error:", e)

            