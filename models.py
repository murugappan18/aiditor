from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, Date
from sqlalchemy.orm import relationship

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship('User', backref='role', lazy='dynamic')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Client(db.Model):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    pan = Column(String(10), unique=True)
    gstin = Column(String(15))
    email = Column(String(120))
    phone = Column(String(15))
    address = Column(Text)
    date_of_birth = Column(Date)
    incorporation_date = Column(Date)
    client_type = Column(String(50))  # Individual, Company, Partnership, etc.
    status = Column(String(20), default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    # Relationships
    income_tax_returns = relationship('IncomeTaxReturn', backref='client', lazy='dynamic')
    tds_returns = relationship('TDSReturn', backref='client', lazy='dynamic')
    gst_returns = relationship('GSTReturn', backref='client', lazy='dynamic')
    documents = relationship('Document', backref='client', lazy='dynamic')
    outstanding_fees = relationship('OutstandingFee', backref='client', lazy='dynamic')

class IncomeTaxReturn(db.Model):
    __tablename__ = 'income_tax_returns'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    assessment_year = Column(String(10), nullable=False)
    return_type = Column(String(50))  # ITR-1, ITR-2, etc.
    filing_date = Column(Date)
    due_date = Column(Date)
    total_income = Column(Float, default=0)
    tax_payable = Column(Float, default=0)
    refund_amount = Column(Float, default=0)
    status = Column(String(20), default='Pending')  # Pending, Filed, Processed
    acknowledgment_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class TDSReturn(db.Model):
    __tablename__ = 'tds_returns'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    tan = Column(String(10), nullable=False)
    quarter = Column(String(10), nullable=False)
    financial_year = Column(String(10), nullable=False)
    return_type = Column(String(20))  # 24Q, 26Q, 27Q, etc.
    filing_date = Column(Date)
    due_date = Column(Date)
    total_tds = Column(Float, default=0)
    status = Column(String(20), default='Pending')
    token_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class GSTReturn(db.Model):
    __tablename__ = 'gst_returns'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    gstin = Column(String(15), nullable=False)
    return_type = Column(String(10))  # GSTR-1, GSTR-3B, etc.
    month_year = Column(String(10), nullable=False)
    filing_date = Column(Date)
    due_date = Column(Date)
    total_sales = Column(Float, default=0)
    total_tax = Column(Float, default=0)
    status = Column(String(20), default='Pending')
    arn_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class Employee(db.Model):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    employee_id = Column(String(20), unique=True)
    email = Column(String(120))
    phone = Column(String(15))
    pan = Column(String(10))
    designation = Column(String(100))
    department = Column(String(100))
    date_of_joining = Column(Date)
    salary = Column(Float, default=0)
    status = Column(String(20), default='Active')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    payroll_entries = relationship('PayrollEntry', backref='employee', lazy='dynamic')

class PayrollEntry(db.Model):
    __tablename__ = 'payroll_entries'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    month_year = Column(String(10), nullable=False)
    basic_salary = Column(Float, default=0)
    allowances = Column(Float, default=0)
    deductions = Column(Float, default=0)
    net_salary = Column(Float, default=0)
    pf_deduction = Column(Float, default=0)
    tds_deduction = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    title = Column(String(200), nullable=False)
    document_type = Column(String(50))  # PAN, Aadhar, GST Certificate, etc.
    file_path = Column(String(500))
    file_size = Column(Integer)
    upload_date = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(Integer, ForeignKey('users.id'))
    notes = Column(Text)

class OutstandingFee(db.Model):
    __tablename__ = 'outstanding_fees'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    service_type = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date)
    status = Column(String(20), default='Pending')  # Pending, Paid, Overdue
    invoice_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class ChallanPayment(db.Model):
    __tablename__ = 'challan_payments'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    challan_number = Column(String(50), nullable=False)
    tax_type = Column(String(50))  # Income Tax, TDS, GST, etc.
    amount = Column(Float, nullable=False)
    payment_date = Column(Date)
    bank_name = Column(String(100))
    status = Column(String(20), default='Pending')  # Pending, Cleared, Failed
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class AuditReport(db.Model):
    __tablename__ = 'audit_reports'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    report_type = Column(String(50))  # Statutory Audit, Tax Audit, etc.
    financial_year = Column(String(10), nullable=False)
    report_date = Column(Date)
    findings = Column(Text)
    recommendations = Column(Text)
    status = Column(String(20), default='Draft')  # Draft, Final, Submitted
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class ROCForm(db.Model):
    __tablename__ = 'roc_forms'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    form_type = Column(String(20), nullable=False)  # AOC-4, MGT-7, DIR-3 KYC, etc.
    financial_year = Column(String(10), nullable=False)
    filing_date = Column(Date)
    due_date = Column(Date)
    acknowledgment_number = Column(String(50))
    status = Column(String(20), default='Pending')  # Pending, Filed, Approved
    filing_fee = Column(Float, default=0)
    late_fee = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class SFTReturn(db.Model):
    __tablename__ = 'sft_returns'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    financial_year = Column(String(10), nullable=False)
    form_type = Column(String(20), default='SFT')  # SFT-001, SFT-002
    filing_date = Column(Date)
    due_date = Column(Date)
    acknowledgment_number = Column(String(50))
    total_transactions = Column(Integer, default=0)
    total_amount = Column(Float, default=0)
    status = Column(String(20), default='Pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class BalanceSheetAudit(db.Model):
    __tablename__ = 'balance_sheet_audits'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    financial_year = Column(String(10), nullable=False)
    audit_type = Column(String(50))  # Statutory, Tax, Internal, etc.
    balance_sheet_date = Column(Date)
    audit_completion_date = Column(Date)
    auditor_name = Column(String(200))
    auditor_membership_no = Column(String(20))
    opinion_type = Column(String(50))  # Unqualified, Qualified, Adverse, Disclaimer
    key_audit_matters = Column(Text)
    management_letter_issued = Column(Boolean, default=False)
    status = Column(String(20), default='In Progress')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class CMAReport(db.Model):
    __tablename__ = 'cma_reports'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    reporting_period = Column(String(20), nullable=False)  # Monthly, Quarterly, Annual
    report_date = Column(Date)
    working_capital_limit = Column(Float, default=0)
    utilized_amount = Column(Float, default=0)
    cash_credit_limit = Column(Float, default=0)
    overdraft_limit = Column(Float, default=0)
    bill_discounting_limit = Column(Float, default=0)
    letter_of_credit = Column(Float, default=0)
    bank_guarantee = Column(Float, default=0)
    inventory_value = Column(Float, default=0)
    receivables_value = Column(Float, default=0)
    status = Column(String(20), default='Draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class AssessmentOrder(db.Model):
    __tablename__ = 'assessment_orders'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    assessment_year = Column(String(10), nullable=False)
    order_type = Column(String(50))  # Scrutiny, Best Judgment, Ex-parte
    order_date = Column(Date)
    order_number = Column(String(50))
    total_income_assessed = Column(Float, default=0)
    tax_demanded = Column(Float, default=0)
    interest_charged = Column(Float, default=0)
    penalty_imposed = Column(Float, default=0)
    appeal_filed = Column(Boolean, default=False)
    appeal_date = Column(Date)
    appeal_number = Column(String(50))
    status = Column(String(20), default='Received')  # Received, Under Review, Appealed, Settled
    remarks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class XBRLReport(db.Model):
    __tablename__ = 'xbrl_reports'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    financial_year = Column(String(10), nullable=False)
    report_type = Column(String(50))  # Balance Sheet, P&L, Cash Flow
    filing_category = Column(String(50))  # Individual, Company, LLP
    xbrl_file_path = Column(String(500))
    validation_status = Column(String(20), default='Pending')  # Pending, Valid, Invalid
    validation_errors = Column(Text)
    filing_date = Column(Date)
    acknowledgment_number = Column(String(50))
    status = Column(String(20), default='Draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    reminder_date = Column(DateTime, nullable=False)
    reminder_type = Column(String(50))  # Birthday, Due Date, Follow-up
    status = Column(String(20), default='Active')  # Active, Completed, Cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'))
