import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = 'mini-crm-secret-key-123'

# -----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------
# This creates a file named 'crm.db' in an 'instance' folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# DATABASE MODELS (Tables)
# -----------------------------------------------------------------------------
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='Active')
    phone = db.Column(db.String(20))
    date_joined = db.Column(db.DateTime, default=datetime.datetime.now)

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False) # Storing name for simplicity
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.datetime.now)

# Create the database tables if they don't exist
with app.app_context():
    db.create_all()

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def get_stats():
    # Query the database for counts and sums
    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(status='Active').count()
    
    # Calculate revenue (completed sales)
    completed_sales = Sale.query.filter_by(status='Completed').all()
    total_revenue = sum(sale.amount for sale in completed_sales)
    
    # Calculate pending value
    pending_sales = Sale.query.filter_by(status='Pending').all()
    pending_value = sum(sale.amount for sale in pending_sales)
    
    # Mock "New This Week" (for now, just returns total to keep it simple)
    new_this_week = total_customers 

    return {
        "total": total_customers,
        "active": active_customers,
        "new": new_this_week,
        "revenue": total_revenue,
        "pending_value": pending_value
    }

# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------

@app.route('/')
def dashboard():
    # Fetch recent customers (limit 5)
    recent_customers = Customer.query.order_by(Customer.id.desc()).limit(5).all()
    return render_template('dashboard.html', active_page='dashboard', stats=get_stats(), customers=recent_customers)

@app.route('/customers')
def customers_list():
    # Get the search query from the URL (e.g., ?search=John)
    search_query = request.args.get('search')
    
    # Start with a base query
    query = Customer.query

    # If a search term exists, filter the results
    if search_query:
        # ilike is case-insensitive (e.g., "tech" matches "Tech Corp")
        query = query.filter(or_(
            Customer.name.ilike(f'%{search_query}%'),
            Customer.company.ilike(f'%{search_query}%'),
            Customer.email.ilike(f'%{search_query}%')
        ))
    
    # Execute the query
    customers = query.order_by(Customer.id.desc()).all()
    
    return render_template('customers.html', active_page='customers', customers=customers)
@app.route('/sales')
def sales_tracking():
    # Fetch all sales and all customers (for the dropdown)
    all_sales = Sale.query.order_by(Sale.date.desc()).all()
    all_customers = Customer.query.order_by(Customer.name).all()
    
    # Format dates for display (optional, but makes it look nice)
    for sale in all_sales:
        # We add a temporary attribute 'formatted_date' or just replace the string in the template
        # For simplicity, the template expects a string or object. 
        # The datetime object works fine, but we can format it in Jinja or here.
        pass

    return render_template('sales.html', active_page='sales', sales=all_sales, 
                           total_sales=get_stats()['revenue'], 
                           pending_sales=get_stats()['pending_value'],
                           all_customers=all_customers)

@app.route('/add-sale', methods=['POST'])
def add_sale():
    try:
        new_sale = Sale(
            customer_name=request.form.get('customer_name'),
            amount=float(request.form.get('amount')),
            status=request.form.get('status'),
            date=datetime.datetime.now()
        )
        db.session.add(new_sale)
        db.session.commit()
        flash(f'Sale of ${new_sale.amount:.2f} logged for {new_sale.customer_name}.', 'success')
    except Exception as e:
        flash(f'Error logging sale: {e}', 'error')
        
    return redirect(url_for('sales_tracking'))

@app.route('/add', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        new_customer = Customer(
            name=request.form.get('name'),
            company=request.form.get('company'),
            email=request.form.get('email'),
            status=request.form.get('status'),
            phone=request.form.get('phone')
        )
        db.session.add(new_customer)
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers_list'))
    
    return render_template('add_customer.html', active_page='customers')

if __name__ == '__main__':
    app.run(debug=True, port=5000)