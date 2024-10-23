"""
This is Python script to build a Server for Library application
"""
from datetime import datetime, timedelta
import enum
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from sqlalchemy import func


app = Flask(__name__)
CORS(app,resources={r"/*":{"origins":"*","methods":["GET","POST","PUT","DELETE"],"allow_headers":"*"}})
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Logging setup:
logging.basicConfig(filename='library.log', level=logging.INFO)
logger = app.logger

#---- Helper functions: to post actions info to the logger file,
#---- but also to the DataBase table so the User admin can track his employess actions --------

def log_action(action):
    log_entry = LogEntry(action=action)
    db.session.add(log_entry)
    db.session.commit()
    # logging.info(f"{action} performed at {datetime.now()}")
# ----------------------------------------------------------------------------------------

# Enums:
class BookType(enum.Enum):
    TYPE_1 = 1  # up to 10 days
    TYPE_2 = 2  # up to 5 days
    TYPE_3 = 3  # up to 2 days

class BookCategory(enum.Enum):
    SCIFI = 'Science Fiction'
    HORROR = 'Horror'
    ROMANCE = 'Romance'
    MYSTERY = 'Mystery'
    FANTASY = 'Fantasy'
    BIOGRAPHY = 'Biography'
    HISTORY = 'History'
    COMEDY = 'Comedy'

# Models ---- TABLES FOR THE DATA BASE:
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year_published = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum(BookType), nullable=False)
    category = db.Column(db.Enum(BookCategory), nullable=False)
    is_out_of_stock = db.Column(db.Boolean, default=False)
    book_quantity = db.Column(db.Integer, default=1)

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String(11), nullable=False)
    is_deactivated = db.Column(db.Boolean, default=False)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    cust_name = db.Column(db.String(30), db.ForeignKey('customer.name'), nullable=False)
    cust_phonenumber = db.Column(db.String(11), db.ForeignKey('customer.phone_number'), nullable=False)
    book_name = db.Column(db.String(30), db.ForeignKey('book.name'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    loan_date = db.Column(db.DateTime, nullable=False,  default=datetime.now)
    return_due_date = db.Column(db.DateTime, nullable=False)

class LogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)

class ReturnedBooks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String, nullable=False)
    cust_name = db.Column(db.String, nullable=False)
    cust_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)
    cust_phonenumber = db.Column(db.String(11), db.ForeignKey('customer.phone_number'), nullable=False)
    loan_date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    returned_date = db.Column(db.DateTime)




# API Routes:
# ===========

# -------MAIN PAGE STARTER METHOD ==========================
# ==========================================================
@app.route('/')
def serve_frontend():
    try:
# Query for late loans to alert the staff:
        current_date = datetime.now()
        late_loans = Loan.query.filter(Loan.return_due_date < current_date, Loan.return_due_date.isnot(None) ).all()
# Initiate alert variable as None to prevent an error in cases where no late loans exist: 
        alert_message = None
        if late_loans:
# As stated in the top -- Log_Action would be part of the rest of the Code for the store administrators to track actions in the store:
            log_action("User started the application and <mark><u>late loans</u></mark> were found.")    
# alert message to pass to the frontend through the Headers:
            alert_message = "There are late loans. Please check the ''Late Loans'' section. <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<===================================================================="
# Sends the HTML along with the alert message:
        response = send_file('index.html')
# can set a cookie, or use query parameters in JS to pass the alert message:
        if alert_message:
            response.headers['X-Alert-Message'] = alert_message
# Logging the output info into the logger file for tracking:
        logging.info(f""" Outcome Activated -> Response to index page {"with alert message" if alert_message else "without alert message"}""") 
        return response
# Catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error opening home page: {str(e)} ")
        log_action(f"Error opening home page: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500
# ----------------------------------------------------------------------------------------------
# ////////////////////////////////////////////////////////////////////////////////////



# -------------- CUSTOMER RELATED METHODS =========================================== !!!!!!!!!!!!!!!!!!!!   SOME RETURN MESSAGES ARE ON PERPOUSE IN DIFFERENT STYLE 
# =================================================================================== !!!!!!!!!!!!!!!!!!!!   FOR PERPOUSE OF TRYING TO CREATE ALERTNESS FOR THE LIBRARY WORKERS

@app.route('/add_customer', methods=['POST'])
def add_customer():
    try: 
# Requesting conditions from the User:
        data = request.json
# Check if a customer with the same phone number and age already exists:
        existing_customer = Customer.query.filter_by(phone_number=data['phone_number']).first()
# If customer already exists, return an error message:
        if existing_customer:
# Log to the logger file:
            logging.info(" Outcome Activated -> Error: customer already exists, matched by phone number ") 
# logging infromation into the DataBase logger for the Store to use:
            log_action(f""" <b>User</b> tried to add 
                        <br> a new Customer 
                        <br> with a phone number that already exists in Database<b>:</b>
                    <br><br> <b>[ {data['phone_number']} ]</b> 
                    <br><br> which belongs to user with <b>ID:({existing_customer.id})</b> """)
# Return Data to the front:
            return jsonify({ "error_cust_exist": existing_customer.id }), 400

# loading the new customer variable with the new customer information:  
        new_customer = Customer(name=data['name'], city=data['city'], age=data['age'], phone_number=data['phone_number'])
# adding them to the DataBase and closing the session:
        db.session.add(new_customer)
        db.session.commit()
# Adding the information into the logger file:
        logging.info(" Outcome Activated -> Success: New customer added successfuly")
# logging infromation into the DataBase logger for the Store to use:
        log_action(f""" <mark>Added</mark> new customer: 
                        <br> <b>[</b> {new_customer.name} <b>],</b> 
                        <br> ID: {new_customer.id} """)
# Return Data to the front:
        return jsonify({"success": {"cust_name": new_customer.name, "cust_id": new_customer.id} }), 201
    
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error adding customer: {str(e)}") 
        log_action(f"Error adding customer: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/search_customers', methods=['GET'])
def search_customers():
    try:
# requesting and getting the parameters from the User:
        cust_id = request.args.get('id')
        name = request.args.get('name')
        phone_number = request.args.get('phone_number')
        is_deactivated = request.args.get('is_deactivated')

# Open a query requst to build the query:
        query = Customer.query
# filters the query with "if" query chains based on provided parameters:
        if cust_id:
            cust_id = int(cust_id)
            query = query.filter(Customer.id == cust_id)      
        if name:
            query = query.filter(Customer.name.ilike(f'%{name}%'))
        if phone_number:
            query = query.filter(Customer.phone_number.ilike(f'%{phone_number}%'))
        if is_deactivated:
            if is_deactivated.lower() in ['true', 'false']:
                is_deactivated_bool = is_deactivated.lower() == 'true'
                query = query.filter(Customer.is_deactivated == is_deactivated_bool)
            else:
                logging.info(" Outcome Activated -> Error: Invalid value in Deactivated (true or false)") 
                return jsonify({"error": "Invalid value in Deactivated. Use 'true' or 'false'."}), 400

# Execute query request and close the session:
        customers = query.all()
# case when no customers are found:
        if not customers:
# Log to the action logger file:
            logging.info(" Outcome Activated -> Error: User searched customers - Non were found ") 
# Log to the Admin database log:
            log_action(f""" User searched for Customers.
                    <br><br>     No customers found matching the search criteria <b>--->></b> 
                    <br><br> <b> ID</b>: [ {cust_id if cust_id else '?'} ]
                        <br> <b> Name</b>: [{name if name else '?'}]
                        <br> <b> Phone Number</b>: [{phone_number if phone_number else '?'}]
                        <br> <b> Deactivation Status</b>: [{is_deactivated if is_deactivated else '?'}] """)
# Retrun data to the front:
            return jsonify({"error_customer_not_found":
                                {   "name": name if name else '?',
                                    "customer_id": cust_id if cust_id else '?', 
                                    "phone_number": phone_number if phone_number else '?',
                                    "active_status": 'Not Active' if is_deactivated == 'true' else 'Active' if is_deactivated == 'false' else '?' }}), 404

# In case when customers WERE found:
# Log to the action logger file, log it to the database admin log, and return data to front:
        logging.info(f" Outcome Activated -> Success: User searched customers ") 
        log_action(f""" User searched Customers with filters<b>:</b> 
                    <br><br> <b> ID</b>: [ {cust_id if cust_id else '?'} ]
                        <br> <b> Name</b>: [{name if name else '?'}]
                        <br> <b> Phone Number</b>: [{phone_number if phone_number else '?'}]
                        <br> <b> Deactivation Status</b>: [{is_deactivated if is_deactivated else '?'}]
                    <br><br> <span style="font-size: 18px;">I</span>f all <b>'?'</b> then User would get full unfiltered list. """)
        return jsonify([{
            'Name': customer.name,
            'Id': customer.id,
            'City': customer.city,
            'Age': customer.age,
            'Phone_number': customer.phone_number,
            'Deactivated_status': customer.is_deactivated} for customer in customers]), 200
# catching unexpected error for gracious error handle:
    except Exception as e:
            logging.info(f" Outcome Activated -> Error searching customer: {str(e)}") 
            log_action(f" Error searching customer: {str(e)}")
            return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/remove_customer/<int:id>', methods=['PUT'])
def remove_customer(id):
# Check in the database if customer requested by the user exists:
    customer = db.session.get(Customer, id)
    try:  
# If customer exists and already deactivated:
        if customer:
            if customer.is_deactivated == True:
# Log to the action logger file, log it to the database admin log, and return data to front:
                logging.info(" Outcome Activated -> Error: Customer Already Deactivated, matched by ID ") 
                log_action(f"""  <span style="font-size: 18px;">U</span>ser tried to Deactivate Customer: <b>[</b>{customer.name}<b>]</b> -
                            <br> <span style="font-size: 18px;">I</span>D Number: <b>(</b> {customer.id} <b>)</b> 
                            <br>--------------------- 
                            <br> <span style="font-size: 18px;">B</span>ut they are Already Deactivated """)
                return jsonify({"errorDeactivated": {"customer_name": customer.name, "customer_id": customer.id} }), 400
# If the customer isnt deactivated change it to deactivated and commit and push the change:
            customer.is_deactivated = True
            db.session.commit()
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Success: Customer deactivated") 
            log_action(f"""      <span style="font-size: 18px;">U</span>ser <mark>Deactivated</mark> Customer named: <b>[</b>{customer.name}<b>]</b> - 
                        <br><br> <span style="font-size: 18px;">C</span>ustomer <span style="font-size: 18px;">I</span>D Number: {customer.id}  """)
            return jsonify({"success": {"customer_name":customer.name, "customer_id":customer.id}}), 200
# If customer wasnt found --> return to the Frontend the "Customer not found" JSON data:
# Log to the action logger file, log it to the database admin log, and return data to front:
        logging.info(" Outcome Activated -> Error: Customer wasnt found, matched by ID ") 
        log_action(f"""  <span style="font-size: 18px;">U</span>ser searched for Customer on ID <span style="font-size: 18px;">N</span>umber:<b>(</b>{id}<b>)</b>,
                    <br> for Deactivation process.
                <br><br> <span style="font-size: 18px;">C</span>ustomer with that ID Number wasn't found. """)
        return jsonify({"error_id": id}), 404
# catching unexpected error for gracious error handle:
    except ValueError as e:
        logging.info(f" Outcome Activated -> ValueError occurred: {str(e)} during deactivating customer with ID: {id}") 
        log_action(f" ValueError occurred: {str(e)} during deactivating customer with ID: {id}")
        return jsonify({"error": "A value error occurred in the removing process. Please check the data you entered and try again."}), 400
    except Exception as e:
        logging.info(f" Outcome Activated -> Error removing customer: {str(e)}") 
        log_action(f" Error removing customer: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/activate_customer/<int:id>', methods=['PUT'])
def activate_customer(id):
# Get the user id parameter: 
    customer = db.session.get(Customer, id)
    try:
        if not customer: # if customer with the ID wasnt found
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: No customer was found, matched by ID") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser tried to Activate a Customer with ID: {id}.
                    <br><br> <span style="font-size: 18px;">N</span>o such Customer found.  """)
            return jsonify({"errorExist": id }), 404
# If the customer exist and is deactivated - activate it and push the change into the DataBase:
        if customer and customer.is_deactivated == True:
            customer.is_deactivated = False
            db.session.commit()
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Success: Customer activated ") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser <mark>Activated</mark> Customer:
                    <br><br> <b>[</b>{customer.name}<b>]</b>,
                        <br> <span style="font-size: 18px;">I</span>D: <b>(</b> {customer.id} <b>)</b>  """)
            return jsonify({"success": { "name": customer.name, "id": customer.id } }), 200

# If customer exists and isnt deactivated:
        if customer and customer.is_deactivated == False:
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: Customer is already activated, matched by ID") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser tried to Activate Customer:
                    <br><br> <b>[</b>{customer.name}<b>]</b>,
                        <br> ID: {customer.id}.
                    <br><br> <span style="font-size: 18px;">T</span>hat Customer is Already Activated """)
            return jsonify({"errorActive": { "name": customer.name, "id": customer.id } }), 400

# catching unexpected error for gracious error handle:
    except ValueError as e:
        logging.info(f" Outcome Activated -> ValueError occurred: {str(e)} during activating customer with ID: {id}") 
        log_action(f" ValueError occurred: {str(e)} during activating customer with ID: {id}")
        return jsonify({"error": "A value error occurred in the activating process. Please check the data you entered and try again."}), 400
    except Exception as e:
        logging.info(f" Outcome Activated -> Error activating customer: {str(e)}") 
        log_action(f" Error activating customer: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500


# ------------------ BOOK RELATED METHODS ============================================
# ====================================================================================

@app.route('/add_book', methods=['POST'])
def add_book():
# Asking the user for permeters to add books and writing exceptions if error occuers:
    try:  
        data = request.json
# Check if all required fields are present:
        missing_fields = []
        if 'name' not in data:
            missing_fields.append('name')
        if 'author' not in data:
            missing_fields.append('author')
        if 'year_published' not in data:
            missing_fields.append('year_published')
        if 'type' not in data:
            missing_fields.append('type')
        if 'category' not in data:
            missing_fields.append('category')
# If any fields are missing, raise a BadRequest exception with detailed info:
        if missing_fields:
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(f" Outcome Activated -> Error: User tries to add a book to DataBase- Missing required fields: {', '.join(missing_fields)} ") 
            log_action(f" User tries to add a book to DataBase- Error Missing required fields: {', '.join(missing_fields)} ")
            raise BadRequest(f"Missing required fields: {', '.join(missing_fields)}")

# Check if a book with the same name already exists (case-insensitive):
        existing_book = Book.query.filter(func.lower(Book.name) == func.lower(data['name'])).first()
        if existing_book:
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: Book already exists, Matched by using book name") 
            log_action(f""" <span style="font-size: 18px;">U</span>ser tried to add a book that <span style="font-size: 17px;">a</span>lready exists:
                            ' {existing_book.name} ', ID:{existing_book.id} """)
            return jsonify({"error_book_Exist": { "book_name": existing_book.name, "book_id":existing_book.id } }), 400

# Prepearing the Data Dump variables:
        new_book = Book (
            name=data['name'],
            author=data['author'],
            year_published=int(data['year_published']),
            type=BookType(int(data['type'])),
            category=BookCategory(data['category']) )
        
        db.session.add(new_book) #prepearing to adding the data to the databse
        db.session.commit() #pushing the data to the database and closing session 
# Log to the action logger file, log it to the database admin log, and return data to front:
        logging.info(" Outcome Activated -> Success: New Book added succesfuly") 
        log_action(f"""  <mark><span style="font-size: 18px;">A</span>dded</mark> new book:
                    <br> <b>[</b> {new_book.name}<b> ]</b>
                <br><br> <span style="font-size: 18px;">B</span>ook ID: {new_book.id} """)
        return jsonify({"success": {"name": new_book.name, "id": new_book.id} }), 201

# catching unexpected error for gracious error handle:
    except ValueError as e:    
        logging.info(f" Outcome Activated -> Invalid input: {str(e)}") 
        logger.error(f" Invalid input: {str(e)}")
        return jsonify({"error": f"Invalid input: {str(e)}. Check that 'Type' is 1, 2, or 3, and 'Category' is valid."}), 400
    except BadRequest as e:
        logging.info(f" Outcome Activated -> Bad request: {str(e)}") 
        logger.error(f" Bad request: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.info(f" Outcome Activated -> Error adding book: {str(e)}") 
        log_action(f" Error adding book: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/update_book_quantity', methods=['PUT'])
def update_book_quantity():
    try:
# Get the data from the request body:
        data = request.json  
        book_id = data.get('book_id')
        new_quantity = data.get('quantity')
# Making sure both fields are filled:
        if not all(key in data for key in ['book_id', 'quantity']): 
# Log to the action logger file:
            logging.info("  Outcome Activated -> Error: Missing required fields, 'book_id' or 'quantity' or both")
            raise BadRequest("Missing required fields, 'book_id' or 'quantity' or both ")
# Check if the book exists - starting with puting a query request into a variable:
        book = db.session.get(Book, book_id)
# If it doesnt exist the query variable would be 'None' (None = empty):
        if not book: 
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: Book wasnt found - matched by using book ID") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser tried to enter <mark>Book quantity</mark> change for Book ID:<b>(</b>{book_id}<b>)</b>
                    <br><br> <span style="font-size: 18px;">B</span>ook was not found.""")
            return jsonify({"errorFoundid": book_id}), 404
# Get the quantity value and catch possible error to the libraries book stock importent part:
        try:
            new_quantity = int(new_quantity)
        except (ValueError, TypeError):
# Log to the action logger file and return data to the front:
            logging.info(" Outcome Activated -> Quantity value error: Invalid quantity. Please provide a valid integer") 
            return jsonify({"error": "Invalid quantity. Please provide a valid integer."}), 400

# Ensure the new quantity is valid, meaning - not a negative number:
        if  new_quantity < 0:
# It might Seem redundent but logging this action would allow the library owner to see if his employee tries to mess with the stock numbers:
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: Book quantity change failed - negative number was entered ") 
            log_action(f""" User tried to enter invalid number: ( {new_quantity} ). 
                            if tried too much in short time it might indicate a problematic employee """) 
            return jsonify({"error_quantity": f" {new_quantity} is Invalid quantity number." }), 400

# Update the book quantity - starting by putting into variables the previous quantity and saving the new quantity:
        previous_quantity = book.book_quantity
        book.book_quantity = new_quantity
# Checking if new quantity changed to 0 so the program would update the book to "out of stock":
        if new_quantity == 0:
            book.is_out_of_stock = True
# Log the actions:
            logging.info(" Outcome Activated -> Success: Book quantity changed to 0 succesfuly, book went out of stock") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser updated Book <b>[</b>{book.name}<b>]</b> 
                            and <mark>marked as out of stock</mark> due to quantity updated to <span style="font-size: 18px;">0</span>.
                    <br><br> Quantity updated from amount of: {previous_quantity} To {new_quantity}. """)
# Check if Book quantity was changed from 0, in order to notify the Admin and user that book is in stock - but not activated: 
        elif previous_quantity == 0 and new_quantity > 0:
# Log the actions:
            logging.info(" Outcome Activated -> Success: Book quantity changed FROM 0 to another amount successfuly") 
            log_action(f"""  User updated Book: 
                        <br> <b>[</b>{book.name}<b>]</b> 
                    <br><br> ID:<b>(</b>{book_id}<b>)</b>
                    <br><br> To be back in stock after update in quantity.
                    <br><br> <mark> book wont be active to loan untill user activate it manualy</mark>
                    <br><br> quantity updated from amount of: {previous_quantity} To {new_quantity}. """)
# Just change to quantity in case it was just changed from number above 0 to another number above 0 which doesnt need special attention:
        elif previous_quantity > 0 and new_quantity > 0:
# Log the actions:
            logging.info(" Outcome Activated -> Success: Book quantity changed sucessfuly ") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser updated Book: <b>[</b>{book.name}<b>]</b>
                    <br><br> ID:({book_id}) 
                    <br><br> <mark>Quantity updated</mark> from amount of: {previous_quantity} To {new_quantity}. """)
# push the changes to the DataBase and close session:
        db.session.commit()
# return data to the front:
        return jsonify({ "success": {
                "book_id": book.id,
                "book_name": book.name,
                "previous_quantity": previous_quantity,
                "new_quantity": book.book_quantity,
                "is_out_of_stock": book.is_out_of_stock } }), 200
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error updating quantity: {str(e)}") 
        log_action(f" Error updating quantity: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/deactivate_book/<int:id>', methods=['PUT'])
def remove_book(id):
    try:
# Get an id number from the user through URI:
        book = db.session.get(Book,id)  
# Check if its already deactivated:
        if book: 
            if book.is_out_of_stock:
# Log to the action logger file, log it to the database admin log, and return data to front:
                logging.info(" Outcome Activated -> Error: Book is already deactivated, matched by ID") 
                log_action(f"""  <span style="font-size: 18px;">U</span>ser <mark>tried</mark> to mark out of stock the book<b>:</b>
                        <br><br> <b>[</b>{book.name}<b>]</b> 
                            <br> ID Number: <b>(</b>{book.id}<b>)</b> 
                        <br><br> <span style="font-size: 18px;">B</span>ut its already out """)
                return jsonify({"errorDeactivated": {"name": book.name, "id": book.id } }), 400
# If it isnt already deactivated then make it deactivated and close session:
            book.is_out_of_stock = True
            db.session.commit()
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Success: Book deactivated succesfuly ") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser Marked book:
                        <br> [ {book.name} ] 
                        <br> ID Number: {book.id} --> <mark>out of stock</mark> """)
            return jsonify({"success": {"name": book.name, "id": book.id} }), 200

# User alert message incase no book was found:
# Log to the action logger file, log it to the database admin log, and return data to front:    
        logging.info(" Outcome Activated -> Error: Book wasnt found, matched by ID") 
        log_action(f""" <span style="font-size: 18px;">U</span>ser <mark>tried</mark> to Mark out of stock book with ID:( {id} ) --> But no book with that ID was found """)
        return jsonify({"errorNotfound": {"id": id } }), 404
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error removing book: {str(e)} ") 
        log_action(f" Error removing book: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/activate_book/<int:id>', methods=['PUT'])
def activate_book(id):
    try:
# Get user id query through URI:
        book = db.session.get(Book,id) 
# If book id doesnt exist in the Database:
        if not book:
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: Book wasnt found in Database, matched by ID ") 
            log_action(f"""<span style="font-size: 18px;">U</span>ser tried to <mark>Activate</mark> a Book with ID: ( {id} ) , no Book with this ID was found.""")    
            return jsonify({"errorFoundid": id}), 404

# check if there are any of the specifc book in stock: 
        if book.book_quantity == 0:
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Error: Book cant be activated without books in stock ") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser tried to <mark>activate</mark> Book:
                        <br> <b>[</b>{book.name}, ID: {book.id}<b>]</b>
                    <br><br> <span style="font-size: 18px;">I</span>t cant be activated Because no books of it are in stock.""")
            return jsonify ({"errorquantity": {"name": book.name, "id":book.id} }), 400
# If deactivated then change "out of stock" to false and make it active:
        if book.is_out_of_stock: 
            book.is_out_of_stock = False
# Push the change into the DataBase and close session:
            db.session.commit() 
# Log to the action logger file, log it to the database admin log, and return data to front:
            logging.info(" Outcome Activated -> Success: Book activated ") 
            log_action(f"""  <span style="font-size: 18px;">U</span>ser <mark>Activated</mark> Book:
                        <br> <b>[</b> {book.name} <b>]</b>
                        <br> ID: {book.id} """)
            return jsonify({"success": {"name":book.name,"id":book.id} }), 200
# Log to the action logger file, log it to the database admin log, and return data to front:
        logging.info(" Outcome Activated -> Error: Book is alerady activated, matched by ID ") 
        log_action(f"""  <span style="font-size: 18px;">U</span>ser tried to <mark>Activate</mark> book:
                    <br> [ {book.name} ]
                    <br> ID: ( {book.id} ),
                <br><br> <span style="font-size: 20px;">T</span>hat Book is already Active in stock""")
        return jsonify({"errorActivated": {"name":book.name, "id":id} }), 400
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error activating book: {str(e)} ") 
        log_action(f" Error activating book: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500
    
@app.route('/search_books', methods=['GET'])
def search_books():
    try:
# Get the request paremeters from the user using URI:
        name = request.args.get('name')
        author = request.args.get('author')
        category = request.args.get('category')
        out_of_stock = request.args.get('out_of_stock') 
# Open query session:
        query = Book.query 
# Start query chains (its when you use if conditions in SQLalchemy):
        if name: 
            query = query.filter(Book.name.ilike(f'%{name}%'))
        if author:
            query = query.filter(Book.author.ilike(f'%{author}%'))
        if category:
# Ensure category is parsed correctly:
            try:
                query = query.filter(Book.category == BookCategory[category])
            except KeyError:
# if error found log the action to the logger file and return the data to the front:
                logging.info(" Outcome Activated -> Error: invalid category ") 
                return jsonify({"error": f"Invalid category: {category}"}), 400
# Checking if the book is out of stock and that the value is proper 'true' or 'false':
        if out_of_stock: 
            if out_of_stock.lower() in ['true', 'false']:
                is_out_of_stock_bool = out_of_stock.lower() == 'true' # [the lower method is to make sure the parameter from the user would be all lower case letters]
                query = query.filter(Book.is_out_of_stock == is_out_of_stock_bool)
            else:
                logging.info(" Outcome Activated -> Error: invalid value for out of stock (true\false)") 
                return jsonify({"error": "Invalid value in out_of_stock. Use 'true' or 'false'."}), 400
# Request all the results of the query chain:
        books = query.all() 
# log it for the store logger:
        log_action(f"""  <span style="font-size: 18px;">E</span>mployee searched for books with filters: 
                <br><br> Name: {name if name else "?"} 
                    <br> Author: {author if author else "?"}
                    <br> Category: {category if category else "?"}
                    <br> Out of stock: {out_of_stock if out_of_stock else "?"}
                <br><br> <span style="font-size: 18px;">I</span>f all fields are '?', <span style="font-size: 18px;">U</span>ser will get all the books in DataBase.""")
# If no books found in the search:   
        if not books:
            logging.info(" Outcome Activated -> Error: No book found")
            return jsonify({"errorNotFound": {  "Name": name if name else "?", 
                                                "Author": author if author else "?",
                                                "Category": category if category else "?",      
                                                "Out_of_stock": out_of_stock if out_of_stock else "?" }}), 404
        
        logging.info(" Outcome Activated -> Success: Book list shown")
# If books were found in the search: 
        return jsonify([ {
            'id': book.id, 
            'name': book.name,
            'author': book.author,
            'year_published': book.year_published, 
            'loan type': book.type.value,
            'category': book.category.value, 
            'quantity': book.book_quantity,
            'is_out_of_stock': book.is_out_of_stock } for book in books]), 200
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error searching book: {str(e)}") 
        log_action(f"Error searching book: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/Returned_Books_list', methods=['GET'])
def search_Returned_list():
# Get user query through URI:
    try: 
        name = request.args.get('name') 
        id = request.args.get('id')
# Start query session:
        query = ReturnedBooks.query
# Query chain:
        if name:
            query = query.filter(ReturnedBooks.cust_name.ilike(f'%{name}%'))  
        if id:
            query = query.filter(ReturnedBooks.cust_id == id) 
# Ask for results, and close session:
        returned_books = query.all()

# Log and return to front failed search result:
        if not returned_books:
            logging.info(" Outcome Activated -> Error: returned books werent found, matched by customer ID and/or customer name  ") 
            log_action(f"""  <span style="font-size: 18px;">N</span>o ReturnedBooks with 
                        <br> Customer ID: ( {id} )
                        <br> OR/And
                        <br> Customer Name: ( {name} ) """) 
            return jsonify({"errorSearchfound": {"id": id if id else '?', "name": name if name else '?' } }), 404
            
# Log and return to front the search successs result:
        logging.info(" Outcome Activated -> Success: Returned Book list showed") 
        log_action(f"""  <span style="font-size: 18px;">U</span>ser made search in Returned Books DataBase looking for:
                <br><br> <span style="font-size: 18px;">C</span>ustomer name: {name if name else '?'} 
                    <br> ID: {id if id else '?'} 
                <br><br> <span style="font-size: 18px;">I</span>f query returned with full list it means  
                        User didnt put paramters to search <b>(</b>would show as "?"<b>)</b>. """)
        return jsonify([{
            'id': ret.id,
            'book_name': ret.book_name,
            'cust_name': ret.cust_name,
            'cust_id': ret.cust_id,
            'loan_id': ret.loan_id,
            'cust_phonenumber': ret.cust_phonenumber,
            'loan_date': safe_format_datetime(ret.loan_date.isoformat()),
            'returned_date': safe_format_datetime(ret.returned_date.isoformat() if ret.returned_date else None) } for ret in returned_books]), 200
# catching unexpected error for gracious error handle:
    except Exception as e:
            logging.info(f" Outcome Activated -> Error Search returned books: {str(e)} ") 
            log_action(f" Error Search returned books: {str(e)}")
            return jsonify({"error": str(e)}), 500

#  --------------------------- LOAN RELATED METHODS =================================
# ===================================================================================

@app.route('/loan_book', methods=['POST'])
def loan_book():
# Ask from the User to put parameters, get them with JSON body:
    try:
        data = request.json
# Command pull of the areguments from the body:
        customer = db.session.get(Customer, data['cust_id']) 
        book = db.session.get(Book, data['book_id'])
        
# Ensure customer and book exist:
        if not customer:
            logging.info(" Outcome Activated -> Error: customer wasnt found, matched by ID")
            return jsonify({"errorCustnotfound": data['cust_id']}), 404
        if not book:
            logging.info(" Outcome Activated -> Error: Book wasnt found, matched by ID ")
            return jsonify({"errorBooknotfound": data['book_id']}), 404
#check if they are active:
        if customer.is_deactivated:
            logging.info(" Outcome Activated -> Error: customer is deactivated, matched by ID ")
            return jsonify({"errorCustdeactivated": {"name": customer.name, "id":customer.id} }), 400
        if book.is_out_of_stock:
            logging.info(" Outcome Activated -> Error: book is out of stock, matched by ID ")
            return jsonify({"erroroutofstock": {"name":book.name, "id":book.id} }), 400
# Check if this book is already loaned to this customer:
        existing_loan = Loan.query.filter_by(cust_id=customer.id, book_id=book.id).first()
# if exist then return an error to not allow double book loans:
        if existing_loan:
            logging.info(" Outcome Activated -> Error: customer already loaned this book, matched by ID ") 
            log_action(f"""User tried to make a loan. <br><br> [ {book.name} ] is Already loaned to [{customer.name}, ID:{customer.id}] according to records""")
            return jsonify({"errorloaned": { "bookname":book.name, 
                                             "bookid":book.id,
                                             "custname": customer.name,
                                             "custid":customer.id }}), 400

# Prepear the Loan specifics variables:
        loan_days = {BookType.TYPE_1: 10, BookType.TYPE_2: 5, BookType.TYPE_3: 2}
        return_due_date = datetime.now() + timedelta(days=loan_days[book.type])
# Update the Book stock, make book out of stock if quantity == 0:       
        if book.book_quantity > 0:
            book.book_quantity -= 1
            if book.book_quantity == 0:
                book.is_out_of_stock = True

# Prepear the Loan object: 
        new_loan = Loan(cust_id=customer.id,
                        cust_name=customer.name,
                        cust_phonenumber=customer.phone_number, 
                        book_name = book.name, 
                        book_id=book.id, 
                        loan_date=datetime.now(), 
                        return_due_date=return_due_date)

        db.session.add(new_loan) #request the add to DataBase
        db.session.commit() #push the data and close session

# Log and return Loan data to the front:   
        logging.info(" Outcome Activated -> Success: customer loaned a book ")      
        log_action(f"""  <mark><span style="font-size: 18px;"><b>L</b></span>oaned</mark> book:
                    <br> [ {book.name} ],
                    <br> ID: ({book.id})
                <br><br> <span style="font-size: 18px;">T</span>o Customer:
                    <br> [ {customer.name} ],
                    <br> ID: ( {customer.id} )
                <br><br> <span style="font-size: 18px;">N</span>ew Loan ID: <b>(</b> {new_loan.id} <b>)</b> 
            { "<br><br> Book quantity is 0, <mark><b>book out of stock</b></mark>" if book.book_quantity == 0 else f"New book quantity: {book.book_quantity}" } """)

        return jsonify({"success": {"bookname": book.name,
                                    "customername":customer.name,
                                    "customerid":customer.id,
                                    "bookid":book.id,
                                    "bookquantity":book.book_quantity,
                                    "newloandid":new_loan.id }}), 201
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error loaning book: {str(e)}") 
        log_action(f"Error loaning book: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/return_book', methods=['POST'])
def return_book():
# Request JSON body data from user filled with the parameters:
    try:
        data = request.json
# Check if the JSON body data returned empty or insufficient:
        if not data or 'cust_id' not in data or 'book_id' not in data : 
            logging.info(" Outcome Activated -> Error: User tried to Activate Book Return and didnt enter all necessary fields ") 
            log_action("User tried to Activate Book Return and didnt enter all necessary fields")
            return jsonify({"error": "Invalid data. All fields are required."}), 400
# if sufficient put them into variables:   
        cust_id = data['cust_id']
        book_id = data['book_id']
# Check the existence of a customer or book with the specific Id's:
        customer = db.session.get(Customer, cust_id)
        book = db.session.get(Book, book_id)
# If customer or book with these id's doesnt exist:
        if not customer or not book:
            logging.info(" Outcome Activated -> Error: book or customer doesnt exist, matched by ID") 
            log_action(f"User tried to Return Book and book or Customer were not found <br> ( CustomerID: {cust_id} <br> BookID: {book_id} )")
            return jsonify({"error_not_found": {"custid":cust_id, "bookid":book_id} }), 404
# If exists, start query:
        loan = Loan.query.filter_by(cust_id=cust_id, book_id=book_id ).order_by(Loan.loan_date.desc()).first()         
# check if loan requested exist:
        if not loan:
            logging.info(" Outcome Activated -> Error: no active loan found, matched by customer and book ID") 
            log_action(f"No Active loan found for <br> customer id:( {cust_id} ),<br> book id: ( {book_id} ) ")
            return jsonify({ "error_loan": { "bookid": book_id, "custid":cust_id } }), 404
# If it exists, put into variables to work with:            
        customer_name = customer.name
        book_name = book.name
        customer_phone = customer.phone_number
        loan.actual_return_date = datetime.now()
        previous_book_quantity = book.book_quantity
# I made this function just to make the code smaller and simpler and to save lines:
        def return_function (): 
    # Prepare the returned book details to store in the returned book list:
            returned_book = ReturnedBooks(  loan_id = loan.id,
                                            cust_id = loan.cust_id,
                                            cust_name=customer_name,
                                            cust_phonenumber=customer_phone,
                                            book_name=book_name,
                                            loan_date = loan.loan_date, 
                                            returned_date = datetime.now() )
# Add 1 book to total book quantity:
            book.book_quantity += 1
# Prepaer the add, prepear the deletion of the loan, and push:
            db.session.add(returned_book)
            db.session.delete(loan)
            db.session.commit()

# Checking if Book was returned late:
        if loan.actual_return_date <= loan.return_due_date:
    
# Do the return incase it was returned on time:       
            return_function()
            logging.info(" Outcome Activated -> Success: Book was returned on time") 
            log_action(f""" <span style="font-size: 18px;">R</span>eturned book 
                            <br>[ {book_name}, ID: {loan.book_id} ] 
                        <br><br> From Customer (ID: {loan.cust_id}, {customer_name}) 
                        <br><br> On loan (ID: {loan.id} ) at {safe_format_datetime(loan.actual_return_date)}
                        <br><br> Previous book quantity: {previous_book_quantity}
                        <br><br> Updated book quantity: {book.book_quantity}
                    {"""<br><br> <mark>Book quantity back in stock</mark>, unless activated in the system it wont be active for loan""" if previous_book_quantity == 0 else ""} """)

            return jsonify({"success_on_time": { "bookname":book_name,
                                                "customername":customer_name,
                                                "custid": loan.cust_id,
                                                "bookid": loan.book_id,
                                                "loanid":loan.id, 
                                                "actual_return_date": safe_format_datetime(loan.actual_return_date),
                                                "previous_book_quantity":previous_book_quantity,
                                                "Updated_book_quantity": book.book_quantity }}), 201

# Do the return incase it was late and notify the Employee so he could make the judgment needed:
        return_function()
        logging.info(" Outcome Activated -> Success: Book was returned Late") 
        log_action(f""" <span style="font-size: 18px;">U</span>ser Returned book 
                        <br> [ {book_name}, ID: {loan.book_id} ] 
                    <br><br> From Customer 
                        <br> (ID: {loan.cust_id}, {customer_name}) 
                    <br><br> On loan (ID: {loan.id} )
                    <br><br> <mark>Was recived after(!!)</mark> due return date which was {safe_format_datetime(loan.return_due_date)} 
                    <br><br> and was returned on 
                        <br> {safe_format_datetime(loan.actual_return_date)}
                    <br><br> Previous book quantity: {previous_book_quantity}
                    <br><br> Updated book quantity: {book.book_quantity}
                {"""<br><br> <mark>Book quantity back in stock</mark>, unless activated in the system it wont be active for loan""" if previous_book_quantity == 0 else ""} """)
        
        return jsonify({ "success_late": {"return_due_date": safe_format_datetime(loan.return_due_date) , 
                                        "actual_return_date": safe_format_datetime(loan.actual_return_date),
                                        "bookname":book_name,
                                        "customername":customer_name,
                                        "custid": loan.cust_id,
                                        "bookid": loan.book_id,
                                        "loanid":loan.id, 
                                        "book_quantity": book.book_quantity, 
                                        "previous_book_quantity":previous_book_quantity   }}), 201
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error in return_book: {str(e)}") 
        log_action(f"Error in return_book: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/search_loans', methods=['GET'])
def search_loans():
    try:
# Get the parameters from the user using URI: 
        book_id = request.args.get('book_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        cust_id = request.args.get('cust_id')
# Start query session:
        query = Loan.query
# Query chain:
        if cust_id:
            query = query.filter(Loan.cust_id == cust_id)
        if book_id:
            query = query.filter(Loan.book_id == book_id)
        try:
            if start_date and end_date:
# Parse the provided dates (assuming the format is YYYY-MM-DD):
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
# Filter loans between the start and end dates:
                query = query.filter(Loan.loan_date >= start_date_parsed, Loan.loan_date < end_date_parsed)
# If only start date given then Only filter from start_date:
            elif start_date:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(Loan.loan_date >= start_date_parsed)
# If only end date given then Only filter from end_date:
            elif end_date:
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(Loan.loan_date < end_date_parsed)
        except ValueError:
            logging.info(" Outcome Activated -> Error: Invalid date format. Please use 'YYYY-MM-DD' ") 
            return jsonify({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}), 400
# Submit query chain request and end session:        
        loans = query.all()
        
        log_action(f""" Employee searched loans using these search paramters -->> 
                    <br> ---------------------<br>
                    <br> Customer ID: {cust_id if cust_id else "?"}
                    <br> Book ID: {book_id if book_id else "?"}
                    <br><br> Loan start date range: <br>{safe_format_datetime_for_log(start_date if start_date else "?")}
                    <br><br> Loan end date range: {safe_format_datetime_for_log(end_date if end_date else "?")}
                    <br><br><br> If all paramters are '?' or not accurate the User would get full active Loan list """)
# If a Loan was found:
        if loans:
            logging.info(" Outcome Activated -> Success: Loans search occured ") 
            return jsonify([{
                        'loan_ID': loan.id,
                        'Customer_Name': loan.cust_name,
                        'Customer_ID': loan.cust_id,
                        'Customer_phone number': loan.cust_phonenumber,
                        'Book_Name': loan.book_name,
                        'Book_ID': loan.book_id, 
                        'Loan_Date': safe_format_datetime(loan.loan_date.isoformat()),
                        'Return_Due_Date': safe_format_datetime(loan.return_due_date.isoformat()) } for loan in loans]), 200
# If a Loan wasnt found:
        logging.info(" Outcome Activated -> Error: no loans found ")
        return jsonify({"error_loans": {"cust_id": cust_id if cust_id else '?',
                                        "book_id": book_id if book_id else '?', 
                                        "loan_start_date_range": safe_format_datetime_for_log(start_date if start_date else '?'),
                                        "loan_end_date_range": safe_format_datetime_for_log(end_date if end_date else '?') }}), 404
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error searching loan: {str(e)}") 
        log_action(f"Error searching loan: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/search_late_loans', methods=['GET'])
def get_late_loans():
# Query for all loans where return due date is past --> 
# This can be united with "Search Loans", But because of the importence of this in the library (tracking unreturned loans) I keep it seperate. 
# So its for making emphasies on how much its importent to track it.
    try:
# Set a variable to instore the current time and start a query session:
        current_date = datetime.now() 
        late_loans = Loan.query.filter(Loan.return_due_date < current_date, Loan.return_due_date.isnot(None)).all()
# If a late loan wasnt found:
        if not late_loans: 
            logging.info(" Outcome Activated -> Error: no late loans found") 
            log_action(f"""<span style="font-size: 18px;">U</span>ser searched for Late loans. <br> No late loans were found""")
            return jsonify({"error_late_loans": "No late loans found."}), 404

        logging.info(" Outcome Activated -> Success: Late loans found, list shown and documented into databse logger")
#----PUTTING THE RESULT INTO THE STORE LOGGER because late loans are extremly importent to track by the Manager\Boss: 
        for loan in late_loans:
            log_entry = LogEntry(action = f""" Employee searched for Late Loans and <mark>late loans were found</mark>:
                                            <br>--------------------
                                            <br><br> Loan ID: {loan.id}
                                            <br><br> Customer ID: {loan.cust_id}
                                            <br><br> Book ID: {loan.book_id} 
                                            <br><br> Loan Date: {safe_format_datetime(loan.loan_date.isoformat())} 
                                            <br><br> Return due Date: {safe_format_datetime(loan.return_due_date.isoformat())} """)
# Prepear the add + commit it and close session:
            db.session.add(log_entry)
            db.session.commit()
# Return the Late loans to the Front: 
        return jsonify([{
            'Loan_ID': loan.id, 
            'Customer_ID': loan.cust_id,
            'Customer_name': loan.cust_name,
            'Customer_phone number': loan.cust_phonenumber,
            'Book_Name': loan.book_name,
            'Book_ID': loan.book_id,
            'loan_date': safe_format_datetime(loan.loan_date.isoformat()),
            'return_due_date': safe_format_datetime(loan.return_due_date.isoformat())} for loan in late_loans]), 200
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error searching late loans: {str(e)}") 
        log_action(f"Error searching late loans: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

# ------------------- ADDITIONAL METHODS TO HELP THE LIBRARY PROGRAM ==============================
# =================================================================================================

@app.route('/reset_database', methods=['POST'])
def reset_database():
    try:
# Erasing all DataBase:
        db.drop_all() 
# Creating new Database:
        db.create_all()  
# Add 5 random customers:
        customers = [
            Customer(name="Alice Johnson", city="New York", age=28, phone_number="054-6300598"),
            Customer(name="Bob Smith", city="Los Angeles", age=35, phone_number="054-6200598"),
            Customer(name="Charlie Brown", city="Chicago", age=42, phone_number="054-1006598"),
            Customer(name="Diana Ross", city="Houston", age=31, phone_number="054-0006598"),
            Customer(name="Edward Norton", city="Phoenix", age=39, phone_number="054-6406598")
        ]
        db.session.bulk_save_objects(customers) #Prepear save

# Add some sample books:
        books = [
            Book(name="Dune", author="Frank Herbert", year_published=1965, type=BookType.TYPE_1, category=BookCategory.SCIFI, book_quantity = 1),
            Book(name="The Shining", author="Stephen King", year_published=1977, type=BookType.TYPE_2, category=BookCategory.HORROR, book_quantity = 1),
            Book(name="Pride and Prejudice", author="Jane Austen", year_published=1813, type=BookType.TYPE_3, category=BookCategory.ROMANCE, book_quantity = 1),
            Book(name="The Da Vinci Code", author="Dan Brown", year_published=2003, type=BookType.TYPE_1, category=BookCategory.MYSTERY, book_quantity = 1),
            Book(name="The Hobbit", author="J.R.R. Tolkien", year_published=1937, type=BookType.TYPE_2, category=BookCategory.FANTASY, book_quantity = 1)
        ]
        db.session.bulk_save_objects(books) #Prepear save
# Commit changes and end session:
        db.session.commit()
        logging.info(" Outcome Activated -> !!!!!!!! USER ERASED AND RESTARTED ALL DATABASE !!!!!!! ") 
        log_action("<mark>USER has reseted Database</mark> with 5 new Customers and 5 sample books")
        return jsonify({"success": "<mark>Database was reseted successfully!!!</mark>"}), 201
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error reseting database: {str(e)}") 
        log_action(f"Error reseting database: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/log_entries', methods=['GET'])
def get_log_entries():
    try:
# Get the 'start_date' and 'end_date' query parameters:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
# Initialize the query:
        query = LogEntry.query
# Handle start_date and end_date combination:
        try:
# Parse the provided dates (assuming the format is YYYY-MM-DD):
            if start_date and end_date:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
# Filter the logs where the timestamp is between start_date and end_date:
                query = query.filter(LogEntry.timestamp >= start_date_parsed, LogEntry.timestamp < end_date_parsed)
# If Only start date exists - filter from start_date:
            elif start_date:
                start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(LogEntry.timestamp >= start_date_parsed)
# If Only end_date exists - filter from end_date:
            elif end_date:
                end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(LogEntry.timestamp < end_date_parsed)
# Catch possible errors 
        except ValueError:
            logging.info(" Outcome Activated -> Invalid date format. Please use 'YYYY-MM-DD'") 
            return jsonify({"error": "Invalid date format. Please use 'YYYY-MM-DD'."}), 400

# Execute the query and get the logs, sorted by the timestamp (desc by default):
        logs = query.order_by(LogEntry.timestamp.desc()).all()
# this function are to present the log etneries in proper order of day-month-year:
        start_date=safe_format_datetime_for_log(start_date)
        end_date=safe_format_datetime_for_log(end_date)
        
        logging.info(" Outcome Activated -> User has queried the log entries") 
        log_action(f""" User has queried the log entries with 
                        <br><br> Start_date:[{start_date}],
                        <br><br> End_date:[{end_date}]. 
                        <br><br> if no dates mentioned all logs would be retrived.""")
# Return the logs to the front in JSON format:
        return jsonify([{
            'id': log.id,
            'action': log.action,
            'timestamp': safe_format_datetime(log.timestamp.isoformat()) } for log in logs])
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error searching logs: {str(e)}") 
        log_action(f"Error searching logs: {str(e)}")
        return jsonify({"error": f"unknown error occurred: {str(e)} "}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    try:
# Start querying the information to handle the statistics cards and put into Variables to get current time and late loans data:
        current_date = datetime.now() 
        total_books = Book.query.count()
        total_activated_customers = Customer.query.filter_by(is_deactivated=False).count()
        total_deactivated_customers = Customer.query.filter_by(is_deactivated=True).count()
        total_loans = Loan.query.count()
        books_out_of_stock = Book.query.filter_by(is_out_of_stock =True).count()
        books_on_stock = Book.query.filter_by(is_out_of_stock =False).count()
        total_loans_late = Loan.query.filter(Loan.return_due_date < current_date).count()
        total_book_quantity = db.session.query(func.sum(Book.book_quantity)).scalar()

# Log the action and Return the data to the front:
        logging.info(" Outcome Activated -> Success: Store statistics shown") 
        log_action("User has asked for the Stores statistics")
        return jsonify({"success":
            {
            "total_different_books": total_books,
            "total_loans_and_total_books_loaned": total_loans,
            "total_activated_customers" : total_activated_customers,
            "total_deactivated_customers" : total_deactivated_customers,
            "books_out_of_stock": books_out_of_stock,
            "books_on_stock": books_on_stock,
            "total_loans_late_on_returns": total_loans_late,
            "total_book_pieces_in_the_store":  total_book_quantity }}), 200
# catching unexpected error for gracious error handle:
    except Exception as e:
        logging.info(f" Outcome Activated -> Error getting stats: {str(e)}") 
        log_action(f"Error getting stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

def safe_format_datetime(date_value): # A METHOD TO HANDLE TIME ISSUES

# Attempt to convert from string to datetime:
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value)  # If it's an ISO format string
        except ValueError:
            return date_value  # If conversion fails, return original string
    
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y, %H:%M.%S')
    return date_value  # Return original if it's not a string or datetime

def safe_format_datetime_for_log(date_value): # A METHOD TO HANDLE TIME ISSUES FOR THE LOG
# Attempt to convert from string to datetime:
    if isinstance(date_value, str):
        try:
            date_value = datetime.fromisoformat(date_value)  # If it's an ISO format string
        except ValueError:
            return date_value  # If conversion fails, return original string

    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y')
    return date_value  # Return original if it's not a string or datetime


# -------- UNIVERSAL ERROR HANDLERS (FOR UNEXPECTED CASES) =========================================
# ==================================================================================================

@app.errorhandler(404)
def not_found(error):
    logger.error(" Outcome Activated -> unexpected Not found", request.method ,request.path) 
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    logger.error(" Outcome Activated -> Method not allowed: %s in app %s ", request.method ,request.path)
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(" Outcome Activated -> Internal server error ", request.method ,request.path) 
    return jsonify({"error": "Internal server error"}), 500


# ---------------------- START MAIN ==============================
# ================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)










# =========================================== NOTES ================================================


# --- [[debbuging: TERMINAL ROUTE MAP METHODS  to show which routes are being accepted ==========
# print(app.url_map)
# -------------------------------------------------------------------------------------------------