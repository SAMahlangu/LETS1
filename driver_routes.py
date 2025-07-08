from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from flask_login import login_required, current_user
from models import JobCard, Employee, Car, Trailer, Fuel, Company, JobCardCompany, FuelDelivery, User, db
import os
import base64
from datetime import datetime

driver_routes = Blueprint('driver_routes', __name__)

@driver_routes.route('/driver')
@login_required
def driver_portal():
    # Get driver's job cards
    driver_jobs = JobCard.query.filter_by(driver_id=current_user.id).order_by(JobCard.created_at.desc()).all()
    
    # Get job card counts by status
    total_jobs = len(driver_jobs)
    assigned_jobs = len([job for job in driver_jobs if job.status == 'assigned'])
    in_progress_jobs = len([job for job in driver_jobs if job.status == 'in_progress'])
    in_transit_jobs = len([job for job in driver_jobs if job.status == 'in_transit'])
    delivered_jobs = len([job for job in driver_jobs if job.status == 'delivered'])
    
    # Get daily job card data for the current month (driver-specific)
    from datetime import datetime, timedelta
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
        
        # Count job cards created on this day for this driver
        daily_count = JobCard.query.filter(
            JobCard.driver_id == current_user.id,
            JobCard.created_at >= start_date,
            JobCard.created_at < end_date
        ).count()
        
        day_name = current_day.strftime('%d')
        daily_data.append({
            'day': day_name,
            'count': daily_count
        })
        
        current_day += timedelta(days=1)
    
    dashboard_data = {
        'total_jobs': total_jobs,
        'assigned_jobs': assigned_jobs,
        'in_progress_jobs': in_progress_jobs,
        'in_transit_jobs': in_transit_jobs,
        'delivered_jobs': delivered_jobs,
        'daily_data': daily_data
    }
    
    return render_template('driver/dashboard.html', jobs=driver_jobs, dashboard_data=dashboard_data)

@driver_routes.route('/driver/job-cards')
@login_required
def driver_job_cards():
    # Get all job cards assigned to this driver with car and trailer details
    jobs = JobCard.query.filter_by(driver_id=current_user.id).order_by(JobCard.created_at.desc()).all()
    
    # For each job, get the associated companies and car/trailer details
    for job in jobs:
        # Get car and trailer details
        job.car = Car.query.get(job.car_id) if job.car_id else None
        job.trailer = Trailer.query.get(job.trailer_id) if job.trailer_id else None
        
        # Get associated companies
        job_card_companies = JobCardCompany.query.filter_by(job_card_id=job.id).all()
        job.companies = []
        for jcc in job_card_companies:
            company = Company.query.get(jcc.company_id)
            if company:
                job.companies.append({
                    'company': company,
                    'delivery_order': jcc.delivery_order,
                    'fuel_type': jcc.fuel_type
                })
    
    return render_template('driver/job_cards.html', jobs=jobs)

@driver_routes.route('/driver/job-card/<int:job_card_id>')
@login_required
def driver_job_card_detail(job_card_id):
    # Get specific job card
    job_card = JobCard.query.get_or_404(job_card_id)
    
    # Verify this job card belongs to the current driver
    if job_card.driver_id != current_user.id:
        flash('You are not authorized to view this job card.', 'error')
        return redirect(url_for('driver_routes.driver_job_cards'))
    
    # Update status to in_progress if it's currently assigned
    if job_card.status == 'assigned':
        job_card.status = 'in_progress'
        db.session.commit()
        print(f"Job card {job_card_id} status updated to in_progress")
    
    # Get associated companies and check which ones have fuel deliveries
    job_card_companies = JobCardCompany.query.filter_by(job_card_id=job_card.id).all()
    companies = []
    submitted_companies = set()
    
    # Get all fuel deliveries for this job card
    fuel_deliveries = FuelDelivery.query.filter_by(job_card_id=job_card.id).all()
    for delivery in fuel_deliveries:
        submitted_companies.add(delivery.company_id)
    
    for jcc in job_card_companies:
        company = Company.query.get(jcc.company_id)
        if company and jcc.fuel_type:  # Only show companies that require fuel delivery
            # Check if this company already has a fuel delivery
            has_delivery = jcc.company_id in submitted_companies
            
            companies.append({
                'company': company,
                'delivery_order': jcc.delivery_order,
                'fuel_type': jcc.fuel_type,
                'has_delivery': has_delivery
            })
    
    # Check if all companies with fuel types have been submitted
    total_companies_with_fuel = len([jcc for jcc in job_card_companies if jcc.fuel_type])
    submitted_count = len(submitted_companies)
    
    # Update status to delivered if all companies have been submitted
    if total_companies_with_fuel > 0 and submitted_count >= total_companies_with_fuel:
        if job_card.status != 'delivered':
            job_card.status = 'delivered'
            db.session.commit()
            print(f"Job card {job_card_id} status updated to delivered - all fuel deliveries submitted")
    
    # Get related entities
    car = Car.query.get(job_card.car_id)
    trailer = Trailer.query.get(job_card.trailer_id) if job_card.trailer_id else None
    
    return render_template('driver/job_card_detail.html', 
                         job_card=job_card, 
                         companies=companies,
                         car=car,
                         trailer=trailer)

@driver_routes.route('/driver/fuel-delivery/<int:job_card_id>/<int:company_id>')
@login_required
def fuel_delivery_form(job_card_id, company_id):
    # Get specific job card
    job_card = JobCard.query.get_or_404(job_card_id)
    
    # Verify this job card belongs to the current driver
    if job_card.driver_id != current_user.id:
        flash('You are not authorized to view this job card.', 'error')
        return redirect(url_for('driver_routes.driver_job_cards'))
    
    # Update status to in_transit when starting fuel delivery
    if job_card.status == 'in_progress':
        job_card.status = 'in_transit'
        db.session.commit()
        print(f"Job card {job_card_id} status updated to in_transit - starting fuel delivery")
    
    # Get company details
    company = Company.query.get_or_404(company_id)
    job_card_company = JobCardCompany.query.filter_by(
        job_card_id=job_card_id, 
        company_id=company_id
    ).first()
    
    if not job_card_company or not job_card_company.fuel_type:
        flash('No fuel delivery required for this company.', 'error')
        return redirect(url_for('driver_routes.driver_job_card_detail', job_card_id=job_card_id))
    
    return render_template('driver/fuel_delivery_form.html', 
                         job_card=job_card,
                         company=company,
                         job_card_company=job_card_company)

@driver_routes.route('/driver/profile')
@login_required
def driver_profile():
    # Get current user with employee details
    user = User.query.options(db.joinedload(User.employee)).filter_by(id=current_user.id).first()
    return render_template('driver/profile.html', current_user=user)

@driver_routes.route('/driver/change-password', methods=['POST'])
@login_required
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

@driver_routes.route('/driver/save-meter-reading', methods=['POST'])
@login_required
def save_meter_reading():
    try:
        job_card_id = request.form.get('job_card_id')
        company_id = request.form.get('company_id')
        company_name = request.form.get('company_name')
        employee_name = request.form.get('employee_name')
        photo_data = request.form.get('photo_data')
        signature_data = request.form.get('signature_data')
        
        # Validate required fields
        if not all([job_card_id, company_id, company_name, employee_name, photo_data, signature_data]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Convert to integers for database
        try:
            job_card_id_int = int(job_card_id)
            company_id_int = int(company_id)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid job card or company ID'})
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.getcwd(), 'static', 'uploads', 'meter_readings')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Generate unique filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        photo_filename = f"meter_reading_{job_card_id}_{company_id}_{timestamp}.jpg"
        signature_filename = f"signature_{job_card_id}_{company_id}_{timestamp}.png"
        
        # Save photo
        photo_path = os.path.join(uploads_dir, photo_filename)
        if photo_data:
            photo_data = photo_data.split(',')[1]  # Remove data:image/jpeg;base64, prefix
            with open(photo_path, 'wb') as f:
                f.write(base64.b64decode(photo_data))
        
        # Save signature
        signature_path = os.path.join(uploads_dir, signature_filename)
        if signature_data:
            signature_data = signature_data.split(',')[1]  # Remove data:image/png;base64, prefix
            with open(signature_path, 'wb') as f:
                f.write(base64.b64decode(signature_data))
        
        # Save to database using FuelDelivery model
        fuel_delivery = FuelDelivery(
            job_card_id=job_card_id_int,
            company_id=company_id_int,
            company_name=company_name,
            employee_name=employee_name,
            photo_filename=photo_filename,
            signature_filename=signature_filename,
            notes=request.form.get('notes', '') or None
        )
        
        db.session.add(fuel_delivery)
        db.session.commit()
        
        # Check if all companies with fuel types have been submitted
        job_card = JobCard.query.get(job_card_id_int)
        if job_card:
            job_card_companies = JobCardCompany.query.filter_by(job_card_id=job_card_id_int).all()
            total_companies_with_fuel = len([jcc for jcc in job_card_companies if jcc.fuel_type])
            
            # Get all fuel deliveries for this job card
            fuel_deliveries = FuelDelivery.query.filter_by(job_card_id=job_card_id_int).all()
            submitted_count = len(fuel_deliveries)
            
            # Update status to delivered if all companies have been submitted
            if total_companies_with_fuel > 0 and submitted_count >= total_companies_with_fuel:
                job_card.status = 'delivered'
                db.session.commit()
                print(f"Job card {job_card_id_int} status updated to delivered - all fuel deliveries submitted")
        
        print(f"Fuel delivery record created: ID {fuel_delivery.id}")
        print(f"Meter reading saved for job {job_card_id}, company {company_name}, employee {employee_name}")
        print(f"Photo saved: {photo_filename}")
        print(f"Signature saved: {signature_filename}")
        
        return jsonify({
            'success': True, 
            'message': 'Meter reading saved successfully',
            'photo_filename': photo_filename,
            'signature_filename': signature_filename
        })
        
    except Exception as e:
        print(f"Error saving meter reading: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@driver_routes.route('/company-map/<int:company_id>')
def company_map(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template('driver/company_map.html', company=company)
