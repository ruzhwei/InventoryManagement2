from os import name
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"  # relative path
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Create model for Products and Warehouses with the following attributes.
# Warehouse and Product are in one-to-many relationship
class Warehouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    def __repr__(self):
        return self.name
    
class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product = db.Column(db.String(100), nullable=False)  # must have a name
    quantity = db.Column(db.Integer, default=1)
    comments = db.Column(db.String(200))
    ware_id = db.Column(db.Integer, db.ForeignKey("warehouse.id"))
    warehouse = db.relationship('Warehouse', backref=db.backref('products', lazy = 'dynamic'))

    def __init__(self, product, warehouse ):
        self.product = product
        self.warehouse = warehouse
    def __repr__(self):
        return '<Products %r>' % self.product
# Creates the SQLite database (db).
@app.before_first_request
def create_table():
    db.create_all()


@app.route("/", methods=["POST", "GET"])
def index():
    columns = [column.name for column in Products.__mapper__.columns if column.name != "id" and column.name != "ware_id"]
    columns.append('warehouse')
    # Add new product to the db
    if request.method == "POST":
        new_warehouse_name = request.form['warehouse']
        new_warehouse = Warehouse.query.filter_by(name = str(new_warehouse_name)).first()
        # if not specified or the warehouse user input does not exist, warehouse will be "None", we can update this attr later   
        new_task = Products(product = request.form['product'], warehouse= new_warehouse)
        for column in columns:
            if column == 'warehouse' or column == 'product':
                continue
            else:
                setattr(new_task, column, request.form[column])
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect("/")
        except:
            return "There was an issue creating this product"

    # List all.
    else:
        
        products = Products.query.all()
        warehouse = Warehouse.query.all()
        return render_template("index.html", products=products, columns=columns, warehouse = warehouse)


@app.route("/manageWare", methods=["POST", "GET"])
def manageWare():
    
    if request.method == "POST":
        # This is to add new warehouses
        new_task = Warehouse(name = request.form['Warehouse Name'])

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect("/manageWare")
        except:
            return "There was an issue creating this warehouse"

    # List all.
    else:
        warehouse = Warehouse.query.all()
        return render_template("manageWare.html", warehouse = warehouse)

@app.route("/manageWare/delete/<int:id>")
def deleteWare(id):
    # Delete warehouse with given id value from the db.
    warehouse_to_delete = Warehouse.query.get_or_404(id)
    try:
        db.session.delete(warehouse_to_delete)
        db.session.commit()
        return redirect("/manageWare")
    except:
        return "There was an issue deleting this warehouse"

@app.route("/manageWare/rename/<int:id>", methods=["POST", "GET"])
def rename(id):
    warehouse_to_rename = Warehouse.query.get_or_404(id)

    # Rename this warehouse with given id
    if request.method == "POST":
        setattr(warehouse_to_rename, "name", request.form['Warehouse Name'])
        print(warehouse_to_rename, warehouse_to_rename.name)
        try:
            db.session.commit()
            return redirect("/manageWare")
        except:
            return "There was an issue rename this warehouse"

    else:
        return render_template("rename.html", house=warehouse_to_rename)

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
    columns = [column.name for column in Products.__mapper__.columns if column.name != "id" and column.name != "ware_id"]
    columns.append('warehouse')
    product_to_update = Products.query.get_or_404(id)

    # Update the info of a product.
    if request.method == "POST":
        for column in columns:
            if column == 'warehouse':
                new_warehouse_name = request.form[column]
                new_warehouse = Warehouse.query.filter_by(name = str(new_warehouse_name)).first()
                # if not specified or the warehouse user input does not exist, warehouse will be "None", we can update this attr later   
                product_to_update.warehouse = new_warehouse
            else:
                setattr(product_to_update, column, request.form[column])
        try:
            db.session.commit()
            return redirect("/")
        except:
            return "There was an issue updating that product"

    else:
        return render_template("update.html", product=product_to_update, columns=columns)