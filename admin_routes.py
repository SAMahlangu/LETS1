from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from decorators import role_required
from models import db, Employee, User, Car, CarServiceHistory, Fuel, JobCard, JobCardCompany, Company, Trailer, TrailerServiceHistory, FuelDelivery
from sqlalchemy.orm import joinedload
from datetime import datetime
from sqlalchemy import func

admin_routes = Blueprint("admin_routes", __name__, url_prefix="/admin")

@admin_routes.route("/")
@role_required("admin")
def dashboard():
    # Get statistics
    stats = {
        'total_jobs': JobCard.query.count(),
        'active_drivers': Employee.query.filter_by(is_active=True).count(),
        'available_vehicles': Car.query.filter_by(is_active=True).count() + Trailer.query.filter_by(is_active=True).count(),
        'completed_deliveries': JobCard.query.filter_by(status='delivered').count()
    }
    
    # Get status counts
    status_counts = {}
    for status in ['assigned', 'in_progress', 'in_transit', 'delivered']:
        status_counts[status] = JobCard.query.filter_by(status=status).count()
    
    # Get recent job cards
    recent_jobs = JobCard.query.order_by(JobCard.created_at.desc()).limit(5).all()
    
    return render_template("admin/dashboard.html", 
                         stats=stats, 
                         status_counts=status_counts, 
                         recent_jobs=recent_jobs)

@admin_routes.route("/job-cards")
@role_required("admin")
def manage_job_cards():
    # Get all job cards with related data
    job_cards = JobCard.query.options(
        joinedload(JobCard.driver),
        joinedload(JobCard.car),
        joinedload(JobCard.trailer)
    ).order_by(JobCard.created_at.desc()).all()
    
    return render_template("admin/manage_job_cards.html", job_cards=job_cards)

@admin_routes.route("/drivers")
@role_required("admin")
def manage_drivers():
    # Get all active drivers
    drivers = Employee.query.filter_by(is_active=True).all()
    return render_template("admin/manage_drivers.html", drivers=drivers)

@admin_routes.route("/vehicles")
@role_required("admin")
def manage_vehicles():
    # Get all vehicles
    cars = Car.query.all()
    trailers = Trailer.query.all()
    return render_template("admin/manage_vehicles.html", cars=cars, trailers=trailers)

@admin_routes.route("/companies")
@role_required("admin")
def manage_companies():
    # Get all companies
    companies = Company.query.all()
    return render_template("admin/manage_companies.html", companies=companies)

@admin_routes.route("/fuel-deliveries")
@role_required("admin")
def manage_fuel_deliveries():
    # Get all fuel deliveries
    fuel_deliveries = FuelDelivery.query.join(JobCard).join(Company).order_by(FuelDelivery.created_at.desc()).all()
    return render_template("admin/manage_fuel_deliveries.html", fuel_deliveries=fuel_deliveries)

@admin_routes.route("/reports")
@role_required("admin")
def reports():
    return render_template("admin/reports.html")

@admin_routes.route("/profile")
@role_required("admin")
def profile():
    # Get current user with employee details
    user = User.query.options(db.joinedload(User.employee)).filter_by(id=current_user.id).first()
    return render_template("admin/profile.html", current_user=user)

@admin_routes.route("/change-password", methods=["POST"])
@role_required("admin")
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate current password
    if not current_user.check_password(current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('admin_routes.profile'))
    
    # Validate new password
    if new_password != confirm_password:
        flash('New passwords do not match', 'error')
        return redirect(url_for('admin_routes.profile'))
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'error')
        return redirect(url_for('admin_routes.profile'))
    
    # Update password
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully', 'success')
    return redirect(url_for('admin_routes.profile'))
