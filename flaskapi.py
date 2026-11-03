from flask import Flask, jsonify, request, session, redirect, url_for, render_template
import bleach

app = Flask(__name__)

app.secret_key = "very-secret-key-change-me"

app.config["SESSION_COOKIE_HTTPONLY"] = False

user_logins = [
    {"username": "abc", "password": "123", "balance": "50,000"},
    {"username": "def", "password": "456", "balance": "10,000"}
]

comments = []  # fake database for stored XSS

# @app.after_request
# def set_csp(response):
#     response.headers["Content-Security-Policy"] = "script-src 'self'"
#     return response


# ---------------- HOME ----------------
@app.route("/home")
def home():
    if "user" in session:
        return render_template(
            "home.html",
            username=session["user"],
            balance=session["balance"]
        )
    return redirect(url_for("login"))


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate credentials
        for user in user_logins:
            if user["username"] == username and user["password"] == password:
                session["user"] = username
                session["balance"] = user["balance"]
                return redirect(url_for("home"))

        return render_template(
            "login.html",
            error="Invalid username or password"
        )

    return render_template("login.html")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- SEARCH (Reflected XSS demo) ----------------
@app.route("/search")
def search():
    q = request.args.get("q", "")
    # intentionally vulnerable
    q = bleach.clean(q)
    return render_template("search.html", query=q)


# ---------------- STORED XSS COMMENTS PAGE ----------------
@app.route("/comments", methods=["GET", "POST"])
def comments_page():
    global comments

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        comment = request.form.get("comment", "")

        # ❌ INTENTIONALLY VULNERABLE STORED XSS
        # We store raw HTML/JS without sanitizing
        comments.append(comment)

        return redirect(url_for("comments_page"))

    # Display all comments (unsafe)
    return render_template(
        "comments.html",
        comments=comments,
        username=session["user"]
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

