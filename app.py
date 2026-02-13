from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/service")
def service():
    return render_template("service.html")

@app.route("/project")
def project():
    return render_template("project.html")

@app.route("/blog")
def blog():
    return render_template("blog.html")

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/testimonial")
def testimonial():
    return render_template("testimonial.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")
@app.route("/error")
def error():
    return render_template("404.html")
@app.route("/admin")
def admin():
    return render_template("admin/dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
