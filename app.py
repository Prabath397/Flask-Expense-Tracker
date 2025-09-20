from flask import Flask, render_template, request, redirect, url_for, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Expense Model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Home Page with optional month filter
@app.route('/')
def index():
    month = request.args.get('month')  # e.g. "2025-09"
    if month:
        year, mon = map(int, month.split('-'))
        expenses = Expense.query.filter(
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == mon
        ).order_by(Expense.date.desc()).all()
    else:
        expenses = Expense.query.order_by(Expense.date.desc()).all()

    total = sum(exp.amount for exp in expenses)

    # Chart data
    categories = {}
    for exp in expenses:
        categories[exp.category] = categories.get(exp.category, 0) + exp.amount

    return render_template(
        'index.html',
        expenses=expenses,
        total=total,
        categories=categories,
        selected_month=month
    )

# Add Expense
@app.route('/add', methods=['POST'])
def add():
    title = request.form['title']
    amount = float(request.form['amount'])
    category = request.form['category']
    new_expense = Expense(title=title, amount=amount, category=category)
    db.session.add(new_expense)
    db.session.commit()
    return redirect(url_for('index'))

# Delete Expense
@app.route('/delete/<int:id>')
def delete(id):
    expense = Expense.query.get_or_404(id)
    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for('index'))

# ✅ Export to CSV
@app.route('/export')
def export():
    month = request.args.get('month')
    if month:
        year, mon = map(int, month.split('-'))
        expenses = Expense.query.filter(
            db.extract('year', Expense.date) == year,
            db.extract('month', Expense.date) == mon
        ).order_by(Expense.date.desc()).all()
    else:
        expenses = Expense.query.order_by(Expense.date.desc()).all()

    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Amount', 'Category', 'Date'])  # header
    for exp in expenses:
        writer.writerow([exp.title, exp.amount, exp.category, exp.date.strftime('%Y-%m-%d')])

    # Send file as response
    response = Response(output.getvalue(), mimetype='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=expenses.csv'
    return response

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
