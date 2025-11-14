from flask import Flask, render_template


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="assests",
    static_url_path="/assests",
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/news")
def news():
    return render_template("news.html")


@app.route("/weather")
def weather():
    return render_template("weatherApp.html")


@app.route("/about")
def about():
    return render_template("About.html")


if __name__ == "__main__":
    app.run(debug=True)