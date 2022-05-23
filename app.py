
from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from io import StringIO, BytesIO
from datetime import datetime
import csv
import urllib.request, json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"  # relative path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Create model for Products with the following attributes.
class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100), nullable=False)  # must have a name
    quantity = db.Column(db.Integer, default=1) # must be an integer
    comments = db.Column(db.String(200))
    city = db.Column(db.String(20), nullable=False)

    def __init__(self, product, city ):
        self.product = product
        self.city = city
# Creates the SQLite database (db).
@app.before_first_request
def create_table():
    db.create_all()

latAndLong = {
    'Austin' : [30.26, -97.73],
    'Toronto' : [43.65, -79.34],
    'San Diego': [32.71, -117.16],
    'New York': [40.73, -73.93],
    'Las Vegas': [36.11, -115.17]
}

weatherAPI = "https://api.openweathermap.org/data/3.0/onecall?lat=%f&lon=%f&exclude=hourly,daily,minutely,alerts&appid=%s&units=metric"

@app.route("/", methods=["POST", "GET"])
def index():
    columns = [column.name for column in Products.__mapper__.columns if column.name != "id" and column.name != "city"]
    # Add new product to the db
    if request.method == "POST":
        # Check if it has a name and city
        if not request.form['product'] or not request.form['city']:
             return redirect("/noNameOrCity")
        # Check if quantity is valid
        if not request.form['quantity'].isdigit():
             return redirect("/notInt")
        new_task = Products(product = request.form['product'], city = request.form['city'])
        for column in columns:
            if column == 'city' or column == 'product':
                continue
            else:
                setattr(new_task, column, request.form[column])
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect("/")
        except:
            return "There was an issue creating this product"

    # List all products.
    else:
        
        products = Products.query.all()
        # Stores weather conditions from the API, then sent to the frontend
        weather = {}
        # Fetch the API key, here it's just stored in a text file, but in real applications, it should be stored securely
        f = open("./templates/APIkey.txt")
        API_key = f.readline()
        for product in products:
            location = getattr(product, 'city')
            if location in weather:
                continue
            else:
                try:
                    city_coords = latAndLong[location]
                    api_response = urllib.request.urlopen(weatherAPI%(city_coords[0], city_coords[1], API_key))
                    api_data = api_response.read()
                    api_dict = json.loads(api_data)
                    weather_description = '%d Celsius Degree'%api_dict.get('current').get('temp') + ', ' + api_dict.get('current').get('weather')[0].get('main') + ': ' + api_dict.get('current').get('weather')[0].get('description')
                    weather[location] = weather_description
                except:
                    weather[location] = "There is some errot fetching the weather data"
        return render_template("index.html", products=products, columns=columns, city = 'city', weather = weather)

@app.route("/delete/<int:id>")
def delete(id):
    # Delete product with given id value from the db.
    product_to_delete = Products.query.get_or_404(id)
    try:
        db.session.delete(product_to_delete)
        db.session.commit()
        return redirect("/")
    except:
        return "There was an issue deleting that product"


@app.route("/update/<int:id>", methods=["POST", "GET"])
def update(id):
    columns = [column.name for column in Products.__mapper__.columns if column.name != "id" and column.name != "city"]
    product_to_update = Products.query.get_or_404(id)

    # Update the info of a product.
    if request.method == "POST":
        # Check if it has a name and city
        if not request.form['product'] or not request.form['city']:
             return redirect("/noNameOrCity")
        # Check if quantity is valid
        if not request.form['quantity'].isdigit():
             return redirect("/notInt")
        for column in columns:
            setattr(product_to_update, column, request.form[column])
        setattr(product_to_update, 'city', request.form['city'])
        try:
            db.session.commit()
            return redirect("/")
        except:
            return "There was an issue updating that product"

    else:
        return render_template("update.html", product=product_to_update, columns=columns, city = 'city')

@app.route("/export")
def export():
    # Exports inventory data to a CSV.
    # Creates CSV in memory via StringIO and converts buffer into a file-like object via BytesIO.
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)

    first_row = [column.name for column in Products.__mapper__.columns]
    writer.writerow(first_row)

    for record in Products.query.all():
        row = []
        for column in Products.__mapper__.columns:
            row.append(getattr(record, column.name))
        writer.writerow(row)

    csv_obj = BytesIO()
    csv_obj.write(csv_buffer.getvalue().encode())
    csv_obj.seek(0)

    return send_file(
        path_or_file=csv_obj,
        as_attachment=True,
        download_name=f"Inventory_data_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    )

@app.route("/noNameOrCity")
def warning():

    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("noNameOrCity.html")

@app.route("/notInt")
def notInt():

    if request.method == "POST":
        return redirect("/")
    else:
        return render_template("notInt.html")