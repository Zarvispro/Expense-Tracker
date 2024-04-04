from flask import render_template, redirect, url_for, flash, request, abort, session, jsonify
from app import app, db
from app.forms import RegistrationForm, LoginForm, ExpenseForm
from app.models import User, Expense
from flask_login import login_user, current_user, login_required
from datetime import datetime
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError


@app.route('/')
@app.route('/home')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            if 'UNIQUE constraint failed: user.email' in str(e):
                flash('Email address is already in use. Please choose a different one.', 'danger')
            elif 'UNIQUE constraint failed: user.username' in str(e):
                flash('Username is already in use. Please choose a different one.', 'danger')
            else:
                flash('An error occurred. Please try again later.', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                if field == 'confirm_password':
                    flash('Confirm Password must be equal to Password', 'danger')
                elif field == 'username' and 'already exists' in error:
                    flash('Username already exists', 'danger')
                elif field == 'email' and 'Invalid email address' in error:
                    flash('Invalid email address', 'danger')
                elif field == 'email' and 'already exists' in error:
                    flash('Email already exists', 'danger')
                else:
                    flash(f'{field.capitalize()}: {error}', 'danger')
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.method == 'POST':
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('home'))
    else:
        pass


@app.route('/dashboard')
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(desc(Expense.date_posted)).all()
    total_expense = sum(expense.amount for expense in expenses)
    return render_template('dashboard.html', expenses=expenses, total_expense=total_expense)


@app.route('/add_expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(title=form.title.data, amount=form.amount.data, date_posted=datetime.now(), user_id=current_user.id)
        db.session.add(expense)
        db.session.commit()
        flash('Expense added successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_expense.html', title='Add Expense', form=form)


@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        abort(403)  # Forbidden
    form = ExpenseForm()
    if form.validate_on_submit():
        expense.title = form.title.data
        expense.amount = form.amount.data
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        form.title.data = expense.title
        form.amount.data = expense.amount
    return render_template('edit_expense.html', title='Edit Expense', form=form)


@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    if expense.user_id != current_user.id:
        abort(403)  # Forbidden
    db.session.delete(expense)
    db.session.commit()
    flash('Your expense has been deleted!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/expenses-data')
@login_required
def expenses_data():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(desc(Expense.date_posted)).all()
    expense_labels = [expense.title for expense in expenses]
    expense_amounts = [expense.amount for expense in expenses]
    return jsonify(labels=expense_labels, amounts=expense_amounts)
