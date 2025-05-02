import os
from flask import Flask, request, session, redirect, url_for, render_template
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")
        if password == os.getenv("LOGIN_PASSWORD"):
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Wrong password!")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("home"))


@app.before_request
def restrict_access():
    allowed_routes = ["home", "login", "static"]

    if request.endpoint is None:
        return

    if not session.get("logged_in") and request.endpoint not in allowed_routes:
        return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
