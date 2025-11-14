from flask import Flask, render_template


app = Flask(
    __name__,
    template_folder="templates",
    static_folder="assests",
    static_url_path="/assests",
)


@app.route("/")
def home():
    return render_template("home.html", active_page="home")


@app.route("/news")
def news():
    return render_template("news.html", active_page="news")


@app.route("/weather")
def weather():
    return render_template("weather_app.html", active_page="weather")


@app.route("/about")
def about():
    return render_template("about.html", active_page="about")

if __name__ == "__main__":
    app.run(debug=True)