from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/security')
def security():
    return "Security page under construction!"  # Replace with your security view template later


@app.route('/thermal')
def thermal():
    return "Thermal Comfort page under construction!"  # Replace with your thermal view template later


@app.route('/settings')
def settings():
    return "Settings page under construction!"  # Replace with your settings view template later


if __name__ == "__main__":
    app.run(debug=True)
