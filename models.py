from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('super_admin', 'admin', 'driver','user', name='user_role'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    employee = db.relationship('Employee', backref='user', uselist=False)


class Employee(db.Model):
    __tablename__ = 'employee'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.String(50), unique=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    hire_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    status = db.Column(db.Enum('hired', 'fired', name='employee_status'), default='hired', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    next_of_kin_name = db.Column(db.String(100))
    next_of_kin_phone = db.Column(db.String(20))
    next_of_kin_relationship = db.Column(db.String(50))
    
    # Relationships
    documents = db.relationship('Document', backref='employee', cascade='all, delete-orphan')
    job_cards = db.relationship('JobCard', backref='driver')


class Document(db.Model):
    __tablename__ = 'employee_document'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id', ondelete='CASCADE'), nullable=False)
    document_type = db.Column(db.String(100))
    filename = db.Column(db.String(255))
    original_filename = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class Car(db.Model):
    __tablename__ = 'car'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model = db.Column(db.String(100))
    registration_number = db.Column(db.String(50), unique=True)
    year = db.Column(db.Integer)
    capacity = db.Column(db.Numeric(10, 2))
    fuel_type = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    service_history = db.relationship('CarServiceHistory', backref='car', cascade='all, delete-orphan')
    job_cards = db.relationship('JobCard', backref='car')


class CarServiceHistory(db.Model):
    __tablename__ = 'car_service_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id', ondelete='CASCADE'), nullable=False)
    service_date = db.Column(db.Date)
    description = db.Column(db.Text)
    cost = db.Column(db.Numeric(10, 2))
    service_provider = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Trailer(db.Model):
    __tablename__ = 'trailer'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    model = db.Column(db.String(100))
    registration_number = db.Column(db.String(50), unique=True)
    capacity = db.Column(db.Numeric(10, 2))
    trailer_type = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    service_history = db.relationship('TrailerServiceHistory', backref='trailer', cascade='all, delete-orphan')
    job_cards = db.relationship('JobCard', backref='trailer')


class TrailerServiceHistory(db.Model):
    __tablename__ = 'trailer_service_history'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    trailer_id = db.Column(db.Integer, db.ForeignKey('trailer.id', ondelete='CASCADE'), nullable=False)
    service_date = db.Column(db.Date)
    description = db.Column(db.Text)
    cost = db.Column(db.Numeric(10, 2))
    service_provider = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Company(db.Model):
    __tablename__ = 'company'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Relationships
    job_card_companies = db.relationship('JobCardCompany', backref='company', cascade='all, delete-orphan')


class JobCard(db.Model):
    __tablename__ = 'job_card'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_number = db.Column(db.String(50), unique=True, nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey('car.id'), nullable=False)
    trailer_id = db.Column(db.Integer, db.ForeignKey('trailer.id'))
    
    pickup_location = db.Column(db.String(255))
    delivery_location = db.Column(db.String(255))
    cargo_description = db.Column(db.Text)
    cargo_weight = db.Column(db.Numeric(10, 2))  # in kg
    special_instructions = db.Column(db.Text)
    priority = db.Column(db.Enum('low', 'medium', 'high', 'urgent', name='priority_level'), default='medium')
    
    # Timing fields
    pickup_time = db.Column(db.DateTime)
    estimated_arrival_time = db.Column(db.DateTime)
    actual_pickup_time = db.Column(db.DateTime)
    actual_delivery_time = db.Column(db.DateTime)
    
    # Status and tracking
    status = db.Column(db.Enum('assigned', 'in_progress', 'picked_up', 'in_transit', 'delivered', 'cancelled', name='job_status'), default='assigned')
    notes = db.Column(db.Text)
    
    # Financial fields
    total_distance = db.Column(db.Numeric(10, 2))  # in km
    fuel_consumed = db.Column(db.Numeric(10, 2))  # in liters
    total_cost = db.Column(db.Numeric(10, 2))
    
    # Metadata
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # job_card_companies = db.relationship('JobCardCompany', backref='job_card', cascade='all, delete-orphan')


class JobCardCompany(db.Model):
    __tablename__ = 'job_card_company'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_card_id = db.Column(db.Integer, db.ForeignKey('job_card.id', ondelete='CASCADE'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    delivery_order = db.Column(db.Integer)
    fuel_type = db.Column(db.String(50))  # Fuel type for this specific company
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Fuel(db.Model):
    __tablename__ = 'fuel'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    price_per_litre = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class FuelDelivery(db.Model):
    __tablename__ = 'fuel_delivery'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    job_card_id = db.Column(db.Integer, db.ForeignKey('job_card.id', ondelete='CASCADE'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id', ondelete='CASCADE'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    employee_name = db.Column(db.String(100), nullable=False)
    
    # File paths for stored images
    photo_filename = db.Column(db.String(255))  # Path to stored photo
    signature_filename = db.Column(db.String(255))  # Path to stored signature
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    job_card = db.relationship('JobCard', backref='fuel_deliveries')
    company = db.relationship('Company', backref='fuel_deliveries')

