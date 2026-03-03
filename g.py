from flask import Flask, request, render_template_string
from bytez import Bytez

app = Flask(__name__)

# Your Bytez API Key
key = "cb1c6b7871df8939c0f3fe4022b93f78"

sdk = Bytez(key)
model = sdk.model("google/gemini-2.5-flash")


@app.route("/", methods=["GET", "POST"])
def home():
    response_text = None
    error_message = None

    if request.method == "POST":
        song = request.form.get("song", "").strip()
        artist = request.form.get("artist", "").strip()

        if not song or not artist:
            error_message = "Please enter both song and artist."
        else:
            prompt = f"Recommend exactly 10 songs similar to '{song}' by '{artist}'. Match genre, mood, tempo, instrumentation, and lyrical theme.\n\n Return ONLY a JSON array like this:\n[{{\"name\":\"Song Title\",\"singer\":\"Artist Name\"}}]\nDo NOT explain. Do NOT add text."

            try:
                results = model.run([
                    {
                        "role": "user",
                        "content": prompt
                    }
                ])
                print("========== MODEL RESPONSE ==========")
                print("Type:", type(results.output))
                print("Raw Output:")
                print(results.output)
                print("====================================")

                if results.error:
                    error_message = results.error
                else:
                    response_text = results.output

            except Exception as e:
                error_message = str(e)

    return render_template_string("""
        <h2>🎵 Simple AI Song Recommender</h2>
        <form method="POST">
            Song: <input type="text" name="song"><br><br>
            Artist: <input type="text" name="artist"><br><br>
            <button type="submit">Recommend</button>
        </form>

        {% if error_message %}
            <p style="color:red;">Error: {{ error_message }}</p>
        {% endif %}

        {% if response_text %}
            <h3>Recommendations:</h3>
            <pre>{{ response_text }}</pre>
        {% endif %}
    """, response_text=response_text, error_message=error_message)


if __name__ == "__main__":
    app.run(debug=True)