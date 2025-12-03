import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = 'mini-crm-secret-key-123'


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


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
    customer_name = db.Column(db.String(100), nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    date = db.Column(db.DateTime, default=datetime.datetime.now)


with app.app_context():
    db.create_all()


def get_stats():

    total_customers = Customer.query.count()
    active_customers = Customer.query.filter_by(status='Active').count()
    
    
    completed_sales = Sale.query.filter_by(status='Completed').all()
    total_revenue = sum(sale.amount for sale in completed_sales)
    
  
    pending_sales = Sale.query.filter_by(status='Pending').all()
    pending_value = sum(sale.amount for sale in pending_sales)
    

    new_this_week = total_customers 

    return {
        "total": total_customers,
        "active": active_customers,
        "new": new_this_week,
        "revenue": total_revenue,
        "pending_value": pending_value
    }



@app.route('/')
def dashboard():
    
    recent_customers = Customer.query.order_by(Customer.id.desc()).limit(5).all()
    return render_template('dashboard.html', active_page='dashboard', stats=get_stats(), customers=recent_customers)

@app.route('/customers')
def customers_list():
   
    search_query = request.args.get('search')
    
   
    query = Customer.query

   
    if search_query:
        
        query = query.filter(or_(
            Customer.name.ilike(f'%{search_query}%'),
            Customer.company.ilike(f'%{search_query}%'),
            Customer.email.ilike(f'%{search_query}%')
        ))
    
   
    customers = query.order_by(Customer.id.desc()).all()
    
    return render_template('customers.html', active_page='customers', customers=customers)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting customer: {e}', 'error')
    return redirect(url_for('customers_list'))

@app.route('/sales')
def sales_tracking():
    
    all_sales = Sale.query.order_by(Sale.date.desc()).all()
    all_customers = Customer.query.order_by(Customer.name).all()
    
   
    for sale in all_sales:

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