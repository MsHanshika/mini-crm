import datetime
import os
import json
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
# IMPORTANT: Set a secret key for session management and flashing messages
app.secret_key = 'mini-crm-secret-key-123'  

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -----------------------------------------------------------------------------
# MOCK DATA STORE
# -----------------------------------------------------------------------------
customers = [
    {'name': 'Alice Smith', 'company': 'Tech Corp', 'email': 'alice@tech.com', 'status': 'Active', 'date': datetime.datetime.now(), 'id': 1},
    {'name': 'Bob Jones', 'company': 'Design Co', 'email': 'bob@design.com', 'status': 'Inactive', 'date': datetime.datetime.now(), 'id': 2}
]

sales = [
    {'id': 101, 'customer': 'Alice Smith', 'amount': 1200.00, 'status': 'Completed', 'date': '2023-10-25'},
    {'id': 102, 'customer': 'Bob Jones', 'amount': 450.50, 'status': 'Pending', 'date': '2023-10-28'},
    {'id': 103, 'customer': 'Alice Smith', 'amount': 3000.00, 'status': 'Completed', 'date': '2023-11-01'},
]

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
def get_stats():
    total_customers = len(customers)
    active_customers = len([c for c in customers if c['status'] == 'Active'])
    total_revenue = sum(s['amount'] for s in sales if s['status'] == 'Completed')
    pending_sales_value = sum(s['amount'] for s in sales if s['status'] == 'Pending')
    
    # Mock "New This Week" logic
    new_this_week = len(customers) 

    return {
        "total": total_customers,
        "active": active_customers,
        "new": new_this_week,
        "revenue": total_revenue,
        "pending_value": pending_sales_value
    }

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# -----------------------------------------------------------------------------
# ROUTES
# -----------------------------------------------------------------------------

@app.route('/')
def dashboard():
    return render_template('dashboard.html', active_page='dashboard', stats=get_stats(), customers=customers)

@app.route('/customers')
def customers_list():
    return render_template('customers.html', active_page='customers', customers=customers)

@app.route('/sales')
def sales_tracking():
    # Pass all customers to the template so the modal form can list them
    return render_template('sales.html', active_page='sales', sales=sales, 
                           total_sales=get_stats()['revenue'], 
                           pending_sales=get_stats()['pending_value'],
                           all_customers=customers)

@app.route('/add-sale', methods=['POST'])
def add_sale():
    try:
        new_sale = {
            'id': max(s['id'] for s in sales) + 1 if sales else 101,
            'customer': request.form.get('customer_name'),
            'amount': float(request.form.get('amount')),
            'status': request.form.get('status'),
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        sales.insert(0, new_sale)
        flash(f'Sale of ${new_sale["amount"]:.2f} logged for {new_sale["customer"]}.', 'success')
    except Exception as e:
        flash(f'Error logging sale: Please ensure amount is a valid number. ({e})', 'error')
        
    return redirect(url_for('sales_tracking'))


@app.route('/add', methods=['GET', 'POST'])
def add_customer():
    # Retrieve pre-filled data if available from image scan
    prefill_param = request.args.get('prefill', '{}')
    
    prefill_data = {}
    if prefill_param:
        try:
            # We expect a JSON string, so we must parse it
            prefill_data = json.loads(prefill_param)
        except json.JSONDecodeError:
            print(f"Error decoding JSON prefill data: {prefill_param}")
            flash('Failed to process image data. Please enter details manually.', 'error')

    if request.method == 'POST':
        new_customer = {
            'name': request.form.get('name'),
            'company': request.form.get('company'),
            'email': request.form.get('email'),
            'status': request.form.get('status'),
            'date': datetime.datetime.now(),
            'id': len(customers) + 1
        }
        customers.insert(0, new_customer)
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers_list'))
    
    # Render form, passing prefill data
    return render_template('add_customer.html', active_page='customers', prefill=prefill_data)

@app.route('/upload-scan', methods=['POST'])
def upload_scan():
    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('add_customer'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('add_customer'))
        
    if file and allowed_file(file.filename):
        # In a real application, you would send the file to an OCR service here.
        # For this demo, we save it (optional) and provide mock extracted data.
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # ---------------------------------------------------------
        # MOCK OCR LOGIC (SIMULATION)
        # ---------------------------------------------------------
        extracted_data = {
            'name': 'Extracted Contact Name', 
            'company': 'Mock Solutions Inc.', 
            'email': 'contact@mocksolutions.com',
            'status': 'Active'
        }
        
        flash('Image scanned and details extracted successfully!', 'success')
        
        # Pass extracted data back to the add_customer route as a JSON string
        return redirect(url_for('add_customer', prefill=json.dumps(extracted_data)))

    flash('Invalid file type. Only PNG, JPG, JPEG are allowed.', 'error')
    return redirect(url_for('add_customer'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)