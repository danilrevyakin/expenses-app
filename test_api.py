import pytest
import os
from app import app, db, Expense


@pytest.fixture
def client():
    # Set TESTING environment variable to use SQLite in-memory
    os.environ['TESTING'] = "1"
    
    # Create a test client
    app.config['TESTING'] = True
    client = app.test_client()

    # Create all tables in the in-memory SQLite database
    with app.app_context():
        db.create_all()

    yield client  # Provide the test client to the tests

    # Drop all tables after the test
    with app.app_context():
        db.drop_all()

    # Reset TESTING environment variable
    os.environ.pop('TESTING', None)


def test_create_expense(client):
    response = client.post('/expenses', json={
        "amount": 100.0,
        "category": "Food",
        "date": "2024-12-10",
        "description": "Lunch"
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data["amount"] == 100.0
    assert data["category"] == "Food"
    assert data["date"] == "2024-12-10"
    assert data["description"] == "Lunch"


def test_get_expenses(client):
    # Add a sample expense
    with app.app_context():
        expense = Expense(amount=50.0, category="Transport", date="2024-12-09", description="Bus ticket")
        db.session.add(expense)
        db.session.commit()

    # Test retrieving the expenses
    response = client.get('/expenses')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["amount"] == 50.0
    assert data[0]["category"] == "Transport"


def test_update_expense(client):
    # Add a sample expense
    with app.app_context():
        expense = Expense(amount=75.0, category="Utilities", date="2024-12-08", description="Electricity bill")
        db.session.add(expense)
        db.session.commit()
        expense_id = expense.id

    # Update the expense
    response = client.put(f'/expenses/{expense_id}', json={
        "amount": 80.0,
        "description": "Updated electricity bill"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["amount"] == 80.0
    assert data["description"] == "Updated electricity bill"


def test_delete_expense(client):
    # Add a sample expense
    with app.app_context():
        expense = Expense(amount=120.0, category="Travel", date="2024-12-07", description="Train ticket")
        db.session.add(expense)
        db.session.commit()
        expense_id = expense.id

    # Delete the expense
    response = client.delete(f'/expenses/{expense_id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Expense deleted"

    # Verify it's deleted
    response = client.get(f'/expenses/{expense_id}')
    assert response.status_code == 404
