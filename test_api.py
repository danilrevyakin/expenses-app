import pytest
from app import app, db, Expense

# Загальна фікстура для налаштування тестового середовища
@pytest.fixture(scope="module")
def test_client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://admin:reallystrongpassword@database-1.cvs4wk28mn9l.eu-central-1.rds.amazonaws.com:3306/expenses_database'
    with app.test_client() as client:
        with app.app_context():
            connection = db.engine.connect()
            transaction = connection.begin()
            options = dict(bind=connection, binds={})
            db.session = db.create_scoped_session(options=options)
            yield client
            transaction.rollback()
            connection.close()

# Фікстура для наповнення бази даних тестовими даними
@pytest.fixture
def setup_test_data():
    with app.app_context():
        db.session.add(Expense(amount=50, category="Food", description="Lunch"))
        db.session.add(Expense(amount=20, category="Transport", description="Bus"))
        db.session.commit()


def test_get_expenses(test_client, setup_test_data):
    response = test_client.get('/expenses')
    assert response.status_code == 200
    expenses = response.json
    assert len(expenses) == 2
    assert expenses[0]['category'] == "Food"


def test_create_expense(test_client):
    response = test_client.post('/expenses', json={
        "amount": 100.5,
        "category": "Entertainment",
        "description": "Movie"
    })
    assert response.status_code == 201
    assert response.json['category'] == "Entertainment"


def test_update_expense(test_client, setup_test_data):
    response = test_client.put('/expenses/1', json={
        "amount": 200.0,
        "description": "Updated Lunch"
    })
    assert response.status_code == 200
    assert response.json['amount'] == 200.0


def test_get_expense(test_client, setup_test_data):
    response = test_client.get('/expenses/1')
    assert response.status_code == 200
    assert response.json['category'] == "Food"


def test_delete_expense(test_client, setup_test_data):
    response = test_client.delete('/expenses/1')
    assert response.status_code == 200
    assert response.json['message'] == "Expense deleted"
    check_response = test_client.get('/expenses/1')
    assert check_response.status_code == 404

