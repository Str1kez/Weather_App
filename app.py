from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
import requests
import sys


API = "c4d89c55db85dfdacddf3e0589ed23d8"
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
app.secret_key = "wtf"
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)

    def __repr__(self):
        return "%s" % self.name


db.create_all()
db.session.commit()


def get_request(city):
    return requests.get("http://api.openweathermap.org/data/2.5/weather",
                        params={'q': city, 'units': 'metric', 'appid': API}).json()


def is_day(d):
    if d["sys"]["sunrise"] < d["dt"] < d["sys"]["sunset"]:
        return True
    return False


def get_id():
    query_id = 0
    while City.query.get(query_id):
        query_id += 1
    return query_id


@app.route('/')
def index():
    city_list = []
    for city in City.query.all():
        weather = {}
        r = get_request(city)
        weather['day'] = is_day(r)
        weather['temp'] = round(r["main"]["temp"])
        weather['state'] = r["weather"][0]["main"]
        weather['city'] = r["name"].upper()
        weather['id'] = city.id
        city_list.append(weather)
    return render_template("index.html", city_list=city_list[::-1])


@app.route('/remove', methods=['POST'])
def remove_city():
    city_id = request.form['id']
    db.session.delete(City.query.get(city_id))
    db.session.commit()
    return redirect('/')


@app.route("/login")
def login():
    return "Login page"


@app.route("/home")
def home():
    return "Home page"


@app.route("/add", methods=["POST"])
def add_city():
    city_name = request.form['city_name']
    if get_request(city_name)['cod'] != 200:
        flash("The city doesn't exist!")
        return redirect('/')
    try:
        city_id = get_id()
        db.session.add(City(id=city_id, name=city_name.upper()))
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        flash("The city has already been added to the list!")
    return redirect('/')


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
