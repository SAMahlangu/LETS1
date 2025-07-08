from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from decorators import role_required
from models import db, Employee, User, Car, CarServiceHistory, Fuel, JobCard, JobCardCompany, Company, Trailer, TrailerServiceHistory, FuelDelivery
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from datetime import datetime

superadmin_routes = Blueprint("superadmin_routes", __name__, url_prefix="/super_admin")

@superadmin_routes.route("/dashboard")
@role_required("super_admin")
def super_admin_dashboard():
    # Get counts for dashboard statistics
    employee_count = Employee.query.count()
    car_count = Car.query.count()
    trailer_count = Trailer.query.count()
    job_card_count = JobCard.query.count()
    
    # Get active counts
    active_employees = Employee.query.filter_by(is_active=True).count()
    active_cars = Car.query.filter_by(is_active=True).count()
    active_trailers = Trailer.query.filter_by(is_active=True).count()
    
    # Get job card status counts
    assigned_jobs = JobCard.query.filter_by(status='assigned').count()
    in_progress_jobs = JobCard.query.filter_by(status='in_progress').count()
    in_transit_jobs = JobCard.query.filter_by(status='in_transit').count()
    delivered_jobs = JobCard.query.filter_by(status='delivered').count()
    
    # Get fuel delivery count
    fuel_delivery_count = FuelDelivery.query.count()
    
    # Get company job card counts
    company_job_counts = db.session.query(
        Company.name,
        func.count(JobCardCompany.id).label('job_count')
    ).join(
        JobCardCompany, Company.id == JobCardCompany.company_id
    ).group_by(
        Company.name
    ).all()
    
    # Get fuel cost analysis by fuel type from JobCardCompany
    fuel_cost_analysis = db.session.query(
        JobCardCompany.fuel_type,
        func.count(JobCardCompany.id).label('count'),
        func.sum(Fuel.price_per_litre).label('total_cost')
    ).join(
        Fuel, JobCardCompany.fuel_type == Fuel.name
    ).filter(
        JobCardCompany.fuel_type.isnot(None)
    ).group_by(
        JobCardCompany.fuel_type
    ).all()
    
    # Get daily job card data for the current month
    from datetime import timedelta
    import calendar
    
    # Get current month start and end dates
    current_date = datetime.now()
    month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get the last day of current month
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1, day=1)
    month_end = next_month - timedelta(days=1)
    
    daily_data = []
    current_day = month_start
    
    while current_day <= month_end:
        start_date = current_day
        end_date = current_day + timedelta(days=1)
        
        # Count job cards created on this day
        daily_count = JobCard.query.filter(
            JobCard.created_at >= start_date,
            JobCard.created_at < end_date
        ).count()
        
        day_name = current_day.strftime('%d')
        daily_data.append({
            'day': day_name,
            'count': daily_count
        })
        
        current_day += timedelta(days=1)
    
    # Get monthly job card data for the last 6 months
    monthly_data = []
    for i in range(6):
        # Calculate the date for this month
        current_date = datetime.now()
        target_date = current_date - timedelta(days=30*i)
        year = target_date.year
        month = target_date.month
        
        # Count job cards created in this month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        monthly_count = JobCard.query.filter(
            JobCard.created_at >= start_date,
            JobCard.created_at < end_date
        ).count()
        
        month_name = calendar.month_abbr[month]
        monthly_data.append({
            'month': month_name,
            'count': monthly_count
        })
    
    # Reverse to show oldest to newest
    monthly_data.reverse()
    
    # Prepare dashboard data
    dashboard_data = {
        'employee_count': employee_count,
        'car_count': car_count,
        'trailer_count': trailer_count,
        'job_card_count': job_card_count,
        'active_employees': active_employees,
        'active_cars': active_cars,
        'active_trailers': active_trailers,
        'assigned_jobs': assigned_jobs,
        'in_progress_jobs': in_progress_jobs,
        'in_transit_jobs': in_transit_jobs,
        'delivered_jobs': delivered_jobs,
        'fuel_delivery_count': fuel_delivery_count,
        'daily_data': daily_data,
        'monthly_data': monthly_data,
        'fuel_cost_analysis': fuel_cost_analysis,
        'company_job_counts': company_job_counts
    }
    
    # Debug: Print daily data
    print("Daily data for dashboard:", daily_data)
    print("Dashboard data keys:", list(dashboard_data.keys()))
    
    return render_template("superadmin/dashboard.html", dashboard_data=dashboard_data)

@superadmin_routes.route("/users")
@role_required("super_admin")
def manage_users():
    # Fetch all users with their related employee information
    users = User.query.options(db.joinedload(User.employee)).all()
    return render_template("superadmin/manage_users.html", users=users)

@superadmin_routes.route("/disable-user/<int:user_id>", methods=["POST"])
@role_required("super_admin")
def disable_user(user_id):
    user = User.query.get_or_404(user_id)
    if not user.is_active:
        flash('User is already disabled.', 'info')
        return redirect(url_for('superadmin_routes.manage_users'))
    user.is_active = False
    # Also set employee status to fired if linked
    if user.employee:
        user.employee.status = 'fired'
    db.session.commit()
    flash('User account disabled and employee status set to fired.', 'success')
    return redirect(url_for('superadmin_routes.manage_users'))

@superadmin_routes.route("/employees")
@role_required("super_admin")
def manage_employees():
    # Fetch only employees with status 'hired'
    employees = Employee.query.filter_by(status='hired').all()
    return render_template("superadmin/manage_employees.html", employees=employees)

@superadmin_routes.route("/add-employee", methods=['GET', 'POST'])
@role_required("super_admin")
def add_employee():
    status = request.args.get('status', 'hired')
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            date_of_birth = request.form.get('date_of_birth')
            hire_date = request.form.get('hire_date')
            is_active = request.form.get('is_active') == '1'
            
            # Next of kin data
            next_of_kin_name = request.form.get('next_of_kin_name')
            next_of_kin_relationship = request.form.get('next_of_kin_relationship')
            next_of_kin_phone = request.form.get('next_of_kin_phone')
            
            # Generate employee_id
            import uuid
            employee_id = f"EMP{uuid.uuid4().hex[:8].upper()}"
            
            # User account data
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Validate required fields
            if not all([first_name, last_name, username, password]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_employee.html", status=status)
            
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return render_template("superadmin/add_employee.html", status=status)
            
            # Create new employee
            new_employee = Employee(
                employee_id=employee_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email=email,
                address=address,
                date_of_birth=date_of_birth if date_of_birth else None,
                hire_date=hire_date if hire_date else None,
                next_of_kin_name=next_of_kin_name,
                next_of_kin_relationship=next_of_kin_relationship,
                next_of_kin_phone=next_of_kin_phone,
                is_active=is_active,
                status=request.form.get('status', status)
            )
            
            # Add employee to database
            db.session.add(new_employee)
            db.session.flush()  # Get the employee ID
            
            # Create user account
            from werkzeug.security import generate_password_hash
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role='driver',  # Default role for employees
                employee_id=new_employee.id
            )
            
            # Add user to database
            db.session.add(new_user)
            
            # Commit all changes
            db.session.commit()
            
            flash('Employee added successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_employees'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding employee: {str(e)}', 'error')
            return render_template("superadmin/add_employee.html", status=status)
    
    return render_template("superadmin/add_employee.html", status=status)

@superadmin_routes.route("/cars")
@role_required("super_admin")
def manage_cars():
    # Fetch all cars
    cars = Car.query.all()
    return render_template("superadmin/manage_cars.html", cars=cars)

@superadmin_routes.route("/add-car", methods=['GET', 'POST'])
@role_required("super_admin")
def add_car():
    if request.method == 'POST':
        try:
            # Get form data
            model = request.form.get('model')
            registration_number = request.form.get('registration_number')
            year = request.form.get('year')
            capacity = request.form.get('capacity')
            fuel_type = request.form.get('fuel_type')
            is_active = request.form.get('is_active') == '1'
            
            # Validate required fields
            if not all([model, registration_number, year]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_car.html")
            
            # Check if registration number already exists
            existing_car = Car.query.filter_by(registration_number=registration_number).first()
            if existing_car:
                flash('Registration number already exists', 'error')
                return render_template("superadmin/add_car.html")
            
            # Create new car
            new_car = Car(
                model=model,
                registration_number=registration_number,
                year=int(year) if year else None,
                capacity=float(capacity) if capacity else None,
                fuel_type=fuel_type,
                is_active=is_active
            )
            
            # Add car to database
            db.session.add(new_car)
            db.session.commit()
            
            flash('Car added successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_cars'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding car: {str(e)}', 'error')
            return render_template("superadmin/add_car.html")
    
    return render_template("superadmin/add_car.html")

@superadmin_routes.route("/car-service/<int:car_id>")
@role_required("super_admin")
def car_service_history(car_id):
    # Fetch car and its service history
    car = Car.query.get_or_404(car_id)
    service_history = CarServiceHistory.query.filter_by(car_id=car_id).order_by(CarServiceHistory.service_date.desc()).all()
    return render_template("superadmin/car_service_history.html", car=car, service_history=service_history)

@superadmin_routes.route("/add-service/<int:car_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def add_service_record(car_id):
    car = Car.query.get_or_404(car_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            service_date = request.form.get('service_date')
            description = request.form.get('description')
            cost = request.form.get('cost')
            service_provider = request.form.get('service_provider')
            
            # Validate required fields
            if not all([service_date, description]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_service_record.html", car=car)
            
            # Create new service record
            new_service = CarServiceHistory(
                car_id=car_id,
                service_date=service_date,
                description=description,
                cost=float(cost) if cost else None,
                service_provider=service_provider
            )
            
            # Add service record to database
            db.session.add(new_service)
            db.session.commit()
            
            flash('Service record added successfully!', 'success')
            return redirect(url_for('superadmin_routes.car_service_history', car_id=car_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding service record: {str(e)}', 'error')
            return render_template("superadmin/add_service_record.html", car=car)
    
    return render_template("superadmin/add_service_record.html", car=car)

@superadmin_routes.route("/edit-car/<int:car_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_car(car_id):
    car = Car.query.get_or_404(car_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            model = request.form.get('model')
            registration_number = request.form.get('registration_number')
            year = request.form.get('year')
            capacity = request.form.get('capacity')
            fuel_type = request.form.get('fuel_type')
            is_active = request.form.get('is_active') == '1'
            
            # Validate required fields
            if not all([model, registration_number, year]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/edit_car.html", car=car)
            
            # Check if registration number already exists (excluding current car)
            existing_car = Car.query.filter_by(registration_number=registration_number).first()
            if existing_car and existing_car.id != car_id:
                flash('Registration number already exists', 'error')
                return render_template("superadmin/edit_car.html", car=car)
            
            # Update car
            car.model = model
            car.registration_number = registration_number
            car.year = int(year) if year else None
            car.capacity = float(capacity) if capacity else None
            car.fuel_type = fuel_type
            car.is_active = is_active
            
            # Commit changes
            db.session.commit()
            
            flash('Car updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_cars'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating car: {str(e)}', 'error')
            return render_template("superadmin/edit_car.html", car=car)
    
    return render_template("superadmin/edit_car.html", car=car)

@superadmin_routes.route("/delete-car/<int:car_id>", methods=['DELETE'])
@role_required("super_admin")
def delete_car(car_id):
    try:
        car = Car.query.get_or_404(car_id)
        db.session.delete(car)
        db.session.commit()
        return {'success': True, 'message': 'Car deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}

@superadmin_routes.route("/edit-employee/<int:employee_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_employee(employee_id):
    # Fetch employee with user relationship loaded for editing
    employee = Employee.query.options(joinedload(Employee.user)).get_or_404(employee_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            email = request.form.get('email')
            address = request.form.get('address')
            date_of_birth = request.form.get('date_of_birth')
            hire_date = request.form.get('hire_date')
            is_active = request.form.get('is_active') == '1'
            
            # Next of kin data
            next_of_kin_name = request.form.get('next_of_kin_name')
            next_of_kin_relationship = request.form.get('next_of_kin_relationship')
            next_of_kin_phone = request.form.get('next_of_kin_phone')
            
            # Validate required fields
            if not all([first_name, last_name]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/edit_employee.html", employee=employee)
            
            # Update employee
            employee.first_name = first_name
            employee.last_name = last_name
            employee.phone = phone
            employee.email = email
            employee.address = address
            employee.date_of_birth = date_of_birth if date_of_birth else None
            employee.hire_date = hire_date if hire_date else None
            employee.next_of_kin_name = next_of_kin_name
            employee.next_of_kin_relationship = next_of_kin_relationship
            employee.next_of_kin_phone = next_of_kin_phone
            employee.is_active = is_active
            employee.status = request.form.get('status', employee.status)
            
            # Commit changes
            db.session.commit()
            
            flash('Employee updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_employees'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating employee: {str(e)}', 'error')
            return render_template("superadmin/edit_employee.html", employee=employee)
    
    return render_template("superadmin/edit_employee.html", employee=employee)

@superadmin_routes.route("/delete-employee/<int:employee_id>", methods=['DELETE'])
@role_required("super_admin")
def delete_employee(employee_id):
    try:
        employee = Employee.query.get_or_404(employee_id)
        db.session.delete(employee)
        db.session.commit()
        return {'success': True, 'message': 'Employee deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}

@superadmin_routes.route("/add-user-for-employee/<int:employee_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def add_user_for_employee(employee_id):
    # Fetch employee with user relationship loaded
    employee = Employee.query.options(joinedload(Employee.user)).get_or_404(employee_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            
            # Validate required fields
            if not all([username, password, role]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_user_for_employee.html", employee=employee)
            
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return render_template("superadmin/add_user_for_employee.html", employee=employee)
            
            # Create new user
            from werkzeug.security import generate_password_hash
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                employee_id=employee_id
            )
            
            # Add user to database
            db.session.add(new_user)
            db.session.commit()
            
            flash('User account created successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_employees'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user account: {str(e)}', 'error')
            return render_template("superadmin/add_user_for_employee.html", employee=employee)
    
    return render_template("superadmin/add_user_for_employee.html", employee=employee)

@superadmin_routes.route("/add-user", methods=['GET', 'POST'])
@role_required("super_admin")
def add_user():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            password = request.form.get('password')
            role = request.form.get('role')
            employee_id = request.form.get('employee_id')
            
            # Validate required fields
            if not all([username, password, role]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_user.html")
            
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return render_template("superadmin/add_user.html")
            
            # Validate employee_id if provided
            if employee_id:
                employee = Employee.query.get(employee_id)
                if not employee:
                    flash('Selected employee does not exist', 'error')
                    return render_template("superadmin/add_user.html")
            
            # Create new user
            from werkzeug.security import generate_password_hash
            new_user = User(
                username=username,
                password_hash=generate_password_hash(password),
                role=role,
                employee_id=int(employee_id) if employee_id else None
            )
            
            # Add user to database
            db.session.add(new_user)
            db.session.commit()
            
            flash('User added successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {str(e)}', 'error')
            return render_template("superadmin/add_user.html")
    
    # Get all employees for the dropdown
    employees = Employee.query.all()
    return render_template("superadmin/add_user.html", employees=employees)

@superadmin_routes.route("/edit-user/<int:user_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_user(user_id):
    # Fetch user with employee relationship loaded for editing
    user = User.query.options(joinedload(User.employee)).get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            role = request.form.get('role')
            employee_id = request.form.get('employee_id')
            new_password = request.form.get('new_password')
            
            # Validate required fields
            if not all([username, role]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/edit_user.html", user=user, employees=Employee.query.all())
            
            # Check if username already exists (excluding current user)
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user_id:
                flash('Username already exists', 'error')
                return render_template("superadmin/edit_user.html", user=user, employees=Employee.query.all())
            
            # Validate employee_id if provided
            if employee_id:
                employee = Employee.query.get(employee_id)
                if not employee:
                    flash('Selected employee does not exist', 'error')
                    return render_template("superadmin/edit_user.html", user=user, employees=Employee.query.all())
            
            # Update user
            user.username = username
            user.role = role
            user.employee_id = int(employee_id) if employee_id else None
            
            # Update password if provided
            if new_password:
                from werkzeug.security import generate_password_hash
                user.password_hash = generate_password_hash(new_password)
            
            # Commit changes
            db.session.commit()
            
            flash('User updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
            return render_template("superadmin/edit_user.html", user=user, employees=Employee.query.all())
    
    # Get all employees for the dropdown
    employees = Employee.query.all()
    return render_template("superadmin/edit_user.html", user=user, employees=employees)

@superadmin_routes.route("/settings")
@role_required("super_admin")
def settings():
    return render_template("superadmin/settings.html")

# --- Fuel Management ---
@superadmin_routes.route("/fuel")
@role_required("super_admin")
def manage_fuel():
    fuels = Fuel.query.order_by(Fuel.name).all()
    return render_template("superadmin/manage_fuel.html", fuels=fuels)

@superadmin_routes.route("/add-fuel", methods=['GET', 'POST'])
@role_required("super_admin")
def add_fuel():
    if request.method == 'POST':
        name = request.form.get('name')
        price_per_litre = request.form.get('price_per_litre')
        description = request.form.get('description')
        if not name or not price_per_litre:
            flash('Name and price are required.', 'error')
            return render_template("superadmin/add_fuel.html")
        if Fuel.query.filter_by(name=name).first():
            flash('Fuel type already exists.', 'error')
            return render_template("superadmin/add_fuel.html")
        try:
            fuel = Fuel(name=name, price_per_litre=price_per_litre, description=description)
            db.session.add(fuel)
            db.session.commit()
            flash('Fuel type added successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_fuel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template("superadmin/add_fuel.html")
    return render_template("superadmin/add_fuel.html")

@superadmin_routes.route("/edit-fuel/<int:fuel_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_fuel(fuel_id):
    fuel = Fuel.query.get_or_404(fuel_id)
    if request.method == 'POST':
        name = request.form.get('name')
        price_per_litre = request.form.get('price_per_litre')
        description = request.form.get('description')
        if not name or not price_per_litre:
            flash('Name and price are required.', 'error')
            return render_template("superadmin/edit_fuel.html", fuel=fuel)
        if Fuel.query.filter(Fuel.name==name, Fuel.id!=fuel_id).first():
            flash('Another fuel type with this name already exists.', 'error')
            return render_template("superadmin/edit_fuel.html", fuel=fuel)
        try:
            fuel.name = name
            fuel.price_per_litre = price_per_litre
            fuel.description = description
            db.session.commit()
            flash('Fuel type updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_fuel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template("superadmin/edit_fuel.html", fuel=fuel)
    return render_template("superadmin/edit_fuel.html", fuel=fuel)

@superadmin_routes.route("/delete-fuel/<int:fuel_id>", methods=['DELETE'])
@role_required("super_admin")
def delete_fuel(fuel_id):
    try:
        fuel = Fuel.query.get_or_404(fuel_id)
        db.session.delete(fuel)
        db.session.commit()
        return {'success': True, 'message': 'Fuel deleted successfully'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}

# --- Company Management ---
@superadmin_routes.route("/add-company-ajax", methods=['POST'])
@role_required("super_admin")
def add_company_ajax():
    try:
        name = request.form.get('name')
        address = request.form.get('address')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        email = request.form.get('email')
        
        if not name:
            return {'success': False, 'message': 'Company name is required'}
        
        # Check if company already exists
        existing_company = Company.query.filter_by(name=name).first()
        if existing_company:
            return {'success': False, 'message': 'Company already exists'}
        
        new_company = Company(
            name=name,
            address=address,
            contact_person=contact_person,
            phone=phone,
            email=email,
            is_active=True
        )
        
        db.session.add(new_company)
        db.session.commit()
        
        return {
            'success': True, 
            'message': 'Company added successfully',
            'company': {
                'id': new_company.id,
                'name': new_company.name,
                'address': new_company.address,
                'contact_person': new_company.contact_person,
                'phone': new_company.phone,
                'email': new_company.email
            }
        }
        
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}

# --- Job Card Management ---
@superadmin_routes.route("/job-cards")
@role_required("super_admin")
def manage_job_cards():
    job_cards = JobCard.query.order_by(JobCard.created_at.desc()).all()
    
    # For each job card, get the associated companies with fuel types
    for job_card in job_cards:
        job_card_companies = JobCardCompany.query.filter_by(job_card_id=job_card.id).all()
        job_card.companies_with_fuel = []
        for jcc in job_card_companies:
            company = Company.query.get(jcc.company_id)
            if company:
                job_card.companies_with_fuel.append({
                    'company': company,
                    'fuel_type': jcc.fuel_type,
                    'delivery_order': jcc.delivery_order
                })
                print(f"Job {job_card.job_number}: Company {company.name}, Fuel: {jcc.fuel_type}, Order: {jcc.delivery_order}")
    
    return render_template("superadmin/manage_job_cards.html", job_cards=job_cards)

@superadmin_routes.route("/add-job-card", methods=['GET', 'POST'])
@role_required("super_admin")
def add_job_card():
    from sqlalchemy import func
    employees = Employee.query.all()
    cars = Car.query.all()
    trailers = Trailer.query.all()
    fuels = Fuel.query.all()
    companies = Company.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        # Basic job card fields
        job_number = request.form.get('job_number')
        driver_id = request.form.get('driver_id')
        car_id = request.form.get('car_id')
        trailer_id = request.form.get('trailer_id')
        
        # New location and cargo fields
        pickup_location = request.form.get('pickup_location')
        delivery_location = request.form.get('delivery_location')
        cargo_description = request.form.get('cargo_description')
        cargo_weight = request.form.get('cargo_weight')
        special_instructions = request.form.get('special_instructions')
        priority = request.form.get('priority', 'medium')
        
        # Timing fields
        pickup_time = datetime.fromisoformat(request.form.get('pickup_time')) if request.form.get('pickup_time') else None
        estimated_arrival_time = datetime.fromisoformat(request.form.get('estimated_arrival_time')) if request.form.get('estimated_arrival_time') else None
        
        # Status and notes
        status = request.form.get('status', 'assigned')
        notes = request.form.get('notes')
        
        # Financial fields
        total_distance = request.form.get('total_distance')
        fuel_consumed = request.form.get('fuel_consumed')
        total_cost = request.form.get('total_cost')
        
        created_by = current_user.id
        company_ids = request.form.getlist('company_ids')
        delivery_orders = request.form.getlist('delivery_orders')
        fuel_types = request.form.getlist('fuel_types')
        
        try:
            print(f"Creating job card with data: job_number={job_number}, driver_id={driver_id}, car_id={car_id}")
            job_card = JobCard(
                job_number=job_number,
                driver_id=driver_id,
                car_id=car_id,
                trailer_id=trailer_id or None,
                pickup_location=pickup_location,
                delivery_location=delivery_location,
                cargo_description=cargo_description,
                cargo_weight=float(cargo_weight) if cargo_weight else None,
                special_instructions=special_instructions,
                priority=priority,
                pickup_time=pickup_time,
                estimated_arrival_time=estimated_arrival_time,
                status=status,
                notes=notes,
                total_distance=float(total_distance) if total_distance else None,
                fuel_consumed=float(fuel_consumed) if fuel_consumed else None,
                total_cost=float(total_cost) if total_cost else None,
                created_by=created_by
            )
            db.session.add(job_card)
            db.session.flush()  # get job_card.id
            print(f"Job card created with ID: {job_card.id}")
            
            # Add companies with fuel types
            print(f"Adding companies: company_ids={company_ids}, delivery_orders={delivery_orders}, fuel_types={fuel_types}")
            for idx, company_id in enumerate(company_ids):
                if company_id:  # Only add if company_id is not empty
                    delivery_order = delivery_orders[idx] if idx < len(delivery_orders) and delivery_orders[idx] else None
                    fuel_type = fuel_types[idx] if idx < len(fuel_types) and fuel_types[idx] else None
                    print(f"Adding company {company_id} with delivery_order={delivery_order}, fuel_type={fuel_type}")
                    db.session.add(JobCardCompany(
                        job_card_id=job_card.id,
                        company_id=company_id,
                        delivery_order=int(delivery_order) if delivery_order else None,
                        fuel_type=fuel_type
                    ))
            
            print("Committing to database...")
            db.session.commit()
            print("Database commit successful!")
            flash('Job card created successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_job_cards'))
        except Exception as e:
            print(f"Error creating job card: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template("superadmin/add_job_card.html", employees=employees, cars=cars, trailers=trailers, fuels=fuels, companies=companies)
    return render_template("superadmin/add_job_card.html", employees=employees, cars=cars, trailers=trailers, fuels=fuels, companies=companies)

@superadmin_routes.route("/edit-job-card/<int:job_card_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_job_card(job_card_id):
    job_card = JobCard.query.get_or_404(job_card_id)
    employees = Employee.query.all()
    cars = Car.query.all()
    trailers = Trailer.query.all()
    fuels = Fuel.query.all()
    companies = Company.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        # Basic job card fields
        job_card.job_number = request.form.get('job_number')
        job_card.driver_id = request.form.get('driver_id')
        job_card.car_id = request.form.get('car_id')
        job_card.trailer_id = request.form.get('trailer_id') or None
        
        # New location and cargo fields
        job_card.pickup_location = request.form.get('pickup_location')
        job_card.delivery_location = request.form.get('delivery_location')
        job_card.cargo_description = request.form.get('cargo_description')
        job_card.cargo_weight = float(request.form.get('cargo_weight')) if request.form.get('cargo_weight') else None
        job_card.special_instructions = request.form.get('special_instructions')
        job_card.priority = request.form.get('priority', 'medium')
        
        # Timing fields
        job_card.pickup_time = datetime.fromisoformat(request.form.get('pickup_time')) if request.form.get('pickup_time') else None
        job_card.estimated_arrival_time = datetime.fromisoformat(request.form.get('estimated_arrival_time')) if request.form.get('estimated_arrival_time') else None
        job_card.actual_pickup_time = datetime.fromisoformat(request.form.get('actual_pickup_time')) if request.form.get('actual_pickup_time') else None
        job_card.actual_delivery_time = datetime.fromisoformat(request.form.get('actual_delivery_time')) if request.form.get('actual_delivery_time') else None
        
        # Status and notes
        job_card.status = request.form.get('status', 'assigned')
        job_card.notes = request.form.get('notes')
        
        # Financial fields
        job_card.total_distance = float(request.form.get('total_distance')) if request.form.get('total_distance') else None
        job_card.fuel_consumed = float(request.form.get('fuel_consumed')) if request.form.get('fuel_consumed') else None
        job_card.total_cost = float(request.form.get('total_cost')) if request.form.get('total_cost') else None
        
        # Update companies with fuel types
        company_ids = request.form.getlist('company_ids')
        delivery_orders = request.form.getlist('delivery_orders')
        fuel_types = request.form.getlist('fuel_types')
        
        # Remove old company associations
        JobCardCompany.query.filter_by(job_card_id=job_card.id).delete()
        
        # Add new company associations
        for idx, company_id in enumerate(company_ids):
            if company_id:  # Only add if company_id is not empty
                delivery_order = delivery_orders[idx] if idx < len(delivery_orders) and delivery_orders[idx] else None
                fuel_type = fuel_types[idx] if idx < len(fuel_types) and fuel_types[idx] else None
                db.session.add(JobCardCompany(
                    job_card_id=job_card.id,
                    company_id=company_id,
                    delivery_order=int(delivery_order) if delivery_order else None,
                    fuel_type=fuel_type
                ))
        
        try:
            db.session.commit()
            flash('Job card updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_job_cards'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template("superadmin/edit_job_card.html", job_card=job_card, employees=employees, cars=cars, trailers=trailers, fuels=fuels, companies=companies)
    return render_template("superadmin/edit_job_card.html", job_card=job_card, employees=employees, cars=cars, trailers=trailers, fuels=fuels, companies=companies)

# --- Trailer Management ---
@superadmin_routes.route("/trailers")
@role_required("super_admin")
def manage_trailers():
    trailers = Trailer.query.order_by(Trailer.created_at.desc()).all()
    return render_template("superadmin/manage_trailers.html", trailers=trailers)

@superadmin_routes.route("/add-trailer", methods=['GET', 'POST'])
@role_required("super_admin")
def add_trailer():
    if request.method == 'POST':
        try:
            model = request.form.get('model')
            registration_number = request.form.get('registration_number')
            capacity = request.form.get('capacity')
            trailer_type = request.form.get('trailer_type')
            is_active = request.form.get('is_active') == '1'
            # Validate required fields
            if not all([model, registration_number]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_trailer.html")
            # Check if registration number already exists
            existing_trailer = Trailer.query.filter_by(registration_number=registration_number).first()
            if existing_trailer:
                flash('Registration number already exists', 'error')
                return render_template("superadmin/add_trailer.html")
            new_trailer = Trailer(
                model=model,
                registration_number=registration_number,
                capacity=float(capacity) if capacity else None,
                trailer_type=trailer_type,
                is_active=is_active
            )
            db.session.add(new_trailer)
            db.session.commit()
            flash('Trailer added successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_trailers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding trailer: {str(e)}', 'error')
            return render_template("superadmin/add_trailer.html")
    return render_template("superadmin/add_trailer.html")

@superadmin_routes.route("/edit-trailer/<int:trailer_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_trailer(trailer_id):
    trailer = Trailer.query.get_or_404(trailer_id)
    if request.method == 'POST':
        trailer.model = request.form.get('model')
        trailer.registration_number = request.form.get('registration_number')
        trailer.capacity = request.form.get('capacity')
        trailer.trailer_type = request.form.get('trailer_type')
        trailer.is_active = request.form.get('is_active') == '1'
        try:
            db.session.commit()
            flash('Trailer updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.manage_trailers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating trailer: {str(e)}', 'error')
            return render_template("superadmin/edit_trailer.html", trailer=trailer)
    return render_template("superadmin/edit_trailer.html", trailer=trailer)

# --- Trailer Service Management ---
@superadmin_routes.route("/trailer-service-history")
@role_required("super_admin")
def trailer_service_history():
    services = TrailerServiceHistory.query.order_by(TrailerServiceHistory.service_date.desc()).all()
    return render_template("superadmin/trailer_service_history.html", services=services)

@superadmin_routes.route("/add-trailer-service", methods=['GET', 'POST'])
@role_required("super_admin")
def add_trailer_service():
    trailers = Trailer.query.filter_by(is_active=True).all()
    if request.method == 'POST':
        try:
            trailer_id = request.form.get('trailer_id')
            service_date = request.form.get('service_date')
            description = request.form.get('description')
            cost = request.form.get('cost')
            service_provider = request.form.get('service_provider')
            
            # Validate required fields
            if not all([trailer_id, service_date, description]):
                flash('Please fill in all required fields', 'error')
                return render_template("superadmin/add_trailer_service.html", trailers=trailers)
            
            new_service = TrailerServiceHistory(
                trailer_id=trailer_id,
                service_date=service_date,
                description=description,
                cost=float(cost) if cost else None,
                service_provider=service_provider
            )
            
            db.session.add(new_service)
            db.session.commit()
            
            flash('Trailer service added successfully!', 'success')
            return redirect(url_for('superadmin_routes.trailer_service_history'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding trailer service: {str(e)}', 'error')
            return render_template("superadmin/add_trailer_service.html", trailers=trailers)
    
    return render_template("superadmin/add_trailer_service.html", trailers=trailers)

@superadmin_routes.route("/edit-trailer-service/<int:service_id>", methods=['GET', 'POST'])
@role_required("super_admin")
def edit_trailer_service(service_id):
    service = TrailerServiceHistory.query.get_or_404(service_id)
    trailers = Trailer.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        try:
            service.trailer_id = request.form.get('trailer_id')
            service.service_date = request.form.get('service_date')
            service.description = request.form.get('description')
            service.cost = float(request.form.get('cost')) if request.form.get('cost') else None
            service.service_provider = request.form.get('service_provider')
            
            db.session.commit()
            flash('Trailer service updated successfully!', 'success')
            return redirect(url_for('superadmin_routes.trailer_service_history'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating trailer service: {str(e)}', 'error')
            return render_template("superadmin/edit_trailer_service.html", service=service, trailers=trailers)
    
    return render_template("superadmin/edit_trailer_service.html", service=service, trailers=trailers)

# --- Fuel Delivery Management ---
@superadmin_routes.route("/fuel-deliveries")
@role_required("super_admin")
def manage_fuel_deliveries():
    # Query all fuel deliveries with related data
    fuel_deliveries = FuelDelivery.query.join(JobCard).join(Company).order_by(FuelDelivery.created_at.desc()).all()
    
    return render_template("superadmin/manage_fuel_deliveries.html", fuel_deliveries=fuel_deliveries)

@superadmin_routes.route("/fuel-delivery/<int:delivery_id>")
@role_required("super_admin")
def view_fuel_delivery(delivery_id):
    # Get the actual fuel delivery record from database
    fuel_delivery = FuelDelivery.query.get_or_404(delivery_id)
    
    # Get related data
    job_card = JobCard.query.get(fuel_delivery.job_card_id)
    company = Company.query.get(fuel_delivery.company_id)
    driver = Employee.query.get(job_card.driver_id) if job_card else None
    
    fuel_delivery_data = {
        'delivery': fuel_delivery,
        'job_card': job_card,
        'company': company,
        'driver': driver,
        'photo_filename': fuel_delivery.photo_filename,
        'signature_filename': fuel_delivery.signature_filename,
        'employee_name': fuel_delivery.employee_name,
        'delivery_date': fuel_delivery.created_at,
        'notes': fuel_delivery.notes
    }
    
    return render_template("superadmin/view_fuel_delivery.html", fuel_delivery=fuel_delivery_data)

@superadmin_routes.route("/profile")
@role_required("super_admin")
def profile():
    # Get current user with employee details
    user = User.query.options(db.joinedload(User.employee)).filter_by(id=current_user.id).first()
    return render_template("superadmin/profile.html", current_user=user)

@superadmin_routes.route("/change-password", methods=['POST'])
@role_required("super_admin")
def change_password():
    try:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate required fields
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Check if new password matches confirmation
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New password and confirmation do not match'})
        
        # Check if new password is different from current
        if current_password == new_password:
            return jsonify({'success': False, 'message': 'New password must be different from current password'})
        
        # Verify current password
        from werkzeug.security import check_password_hash, generate_password_hash
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'})
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'})

@superadmin_routes.route("/history-employees")
@role_required("super_admin")
def history_employees():
    # Fetch all employees with status 'fired'
    employees = Employee.query.filter_by(status='fired').all()
    return render_template("superadmin/history_employees.html", employees=employees)
