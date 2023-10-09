from flask import Flask, request, render_template, redirect, url_for, session, send_file
from flask_mail import Mail, Message
import matplotlib.pyplot as plt
import csv

app = Flask(__name__)
app.secret_key = 'some_secret_key'

account = {}
transactions = {}
needs = {}
wants = {}
monthincome = 0
budget = 0
spendingamount = 0
app.config['MAIL_SERVER'] = 'stmp.gmail.com'  # e.g., 'smtp.gmail.com' for Gmail
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'your-email@example.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)


@app.route('/')
def index():
    return 'Welcome to the Financial Tracker'


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if email in account and account[email] == password:
            session['email'] = email
            return 'Login successful!'
        elif email not in account:
            return 'This email is not registered. Please sign up.'
        else:
            return 'Incorrect password. Please try again.'

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    global monthincome, budget
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if "@" not in email or "." not in email:
            return "Invalid email. Please try again."

        if len(password) < 8 or not any(char.isdigit() for char in password) or not any(char.isupper() for char in password):
            return "Invalid password. Please enter a better password."

        if email in account:
            return 'Email already registered. Please log in.'

        account[email] = password
        monthincome = float(request.form["monthincome"])
        budget = float(request.form["budget"])
        return 'Sign-up successful! Please log in.'

    return render_template('signup.html')


def send_email(recipient, subject, body):
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipient])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


@app.route('/track', methods=['GET', 'POST'])
def track_expenses():
    global monthincome, budget, spendingamount, transactions
    message = None
    amountleft = budget - spendingamount
    if request.method == 'POST':
        reason = request.form['reason']
        expense = int(request.form['expense'])
        percentage = int(request.form["percentage"])

        # Calculate spending amount
        percentages = percentage / 100
        spendingamount = percentages * percentage


        transactions[reason] = expense

        if reason in ["food", "water", "electricity", "plumbing", "internet"]:
            needs[reason] = expense
        else:
            wants[reason] = expense

        if expense > 1000:
            message = "FRAUD ALERT - someone is using your card"
            send_email(session['email'], "FRAUD ALERT", "Someone might be using your card for a large transaction.")

        if spendingamount > budget:
            send_email(session['email'], "Budget Exceeded", "You have exceeded your monthly budget.")
            message = "You have exceeded your monthly budget."

    return render_template('track.html', needs=needs, wants=wants, message=message, monthincome=monthincome,
                           budget=budget, spendingamount=spendingamount, amountleft=amountleft)


@app.route('/download')
def download_file():
    with open('transactions.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Transaction", "Expense", "Type"])
        for category, expense in transactions.items():
            expense_type = "Need" if category in needs else "Want"
            writer.writerow([category, expense, expense_type])
    return send_file('transactions.csv', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
