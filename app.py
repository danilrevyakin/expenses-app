import logging
from logging.handlers import RotatingFileHandler
import os
import pymysql

pymysql.install_as_MySQLdb()

from flask import Flask, jsonify, request, abort
from flask_sqlalchemy import SQLAlchemy
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Prometheus metrics setup
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:reallystrongpassword@database-1.cvs4wk28mn9l.eu-central-1.rds.amazonaws.com:3306/expenses_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Log directory and file setup
log_dir = "/var/log/webapp"
os.makedirs(log_dir, exist_ok=True)  # Ensure the log directory exists
log_file = os.path.join(log_dir, "logs.log")

# Root logger configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S UTC'  # Use UTC for consistency in logs
)

# Rotating file handler for logs
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setLevel(logging.INFO)  # Only log INFO and higher level
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Add handler to root logger
logging.getLogger().addHandler(file_handler)

# Logger for application
logger = logging.getLogger(__name__)

# Disable Werkzeug logging (set to WARNING to capture only client errors)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

# Request logging
@app.before_request
def log_request_info():
    if not request.path.startswith('/metrics'):
        logger.info(f"Request: {request.method} {request.url} Body: {request.data.decode('utf-8')[:200]}")  # Limit body size for logging


# Response logging
@app.after_request
def log_response_info(response):
    if not request.path.startswith('/metrics'):
        logger.info(f"Response: {response.status_code} Response: {response.data.decode('utf-8')[:200]}")  # Limit response size for logging
    return response


# Error handling with metrics and detailed logging
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return jsonify({"message": "An internal error occurred.", "error": str(e)}), 500


# Expense model
class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(120), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Expense {self.id} - {self.category} - {self.amount}>"


# Create database tables
with app.app_context():
    db.create_all()


# Routes
@app.route('/expenses', methods=['GET'])
def get_expenses():
    expenses = Expense.query.all()
    return jsonify([{
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "date": expense.date,
        "description": expense.description
    } for expense in expenses]), 200


@app.route('/expenses', methods=['POST'])
def create_expense():
    data = request.get_json()
    if not data or 'amount' not in data or 'category' not in data:
        abort(400, "Invalid expense data")

    expense = Expense(
        amount=data["amount"],
        category=data["category"],
        date=data.get("date", ""),
        description=data.get("description", "")
    )
    db.session.add(expense)
    db.session.commit()
    return jsonify({
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "date": expense.date,
        "description": expense.description
    }), 201


@app.route('/expenses/<int:expense_id>', methods=['GET'])
def get_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        abort(404, "Expense not found")
    return jsonify({
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "date": expense.date,
        "description": expense.description
    }), 200


@app.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.get_json()
    expense = Expense.query.get(expense_id)
    if not expense:
        abort(404, "Expense not found")

    if "amount" in data:
        expense.amount = data["amount"]
    if "category" in data:
        expense.category = data["category"]
    if "date" in data:
        expense.date = data["date"]
    if "description" in data:
        expense.description = data["description"]

    db.session.commit()
    return jsonify({
        "id": expense.id,
        "amount": expense.amount,
        "category": expense.category,
        "date": expense.date,
        "description": expense.description
    }), 200


@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        abort(404, "Expense not found")

    db.session.delete(expense)
    db.session.commit()
    return jsonify({"message": "Expense deleted"}), 200


# Application entry point
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
