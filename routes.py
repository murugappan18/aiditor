from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import *
from forms import *
from utils import allowed_file, save_uploaded_file
import os
from datetime import datetime, date, timedelta
from sqlalchemy import func, or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    # Get dashboard statistics
    total_clients = Client.query.count()
    pending_returns = IncomeTaxReturn.query.filter_by(status='Pending').count()
    pending_gst = GSTReturn.query.filter_by(status='Pending').count()
    outstanding_fees = db.session.query(func.sum(OutstandingFee.amount)).filter_by(status='Pending').scalar() or 0
    
    # Get recent activities
    recent_clients = Client.query.order_by(Client.created_at.desc()).limit(5).all()
    upcoming_reminders = Reminder.query.filter(
        Reminder.reminder_date >= date.today(),
        Reminder.status == 'Active'
    ).order_by(Reminder.reminder_date).limit(5).all()
    
    return render_template('dashboard.html',
                         total_clients=total_clients,
                         pending_returns=pending_returns,
                         pending_gst=pending_gst,
                         outstanding_fees=outstanding_fees,
                         recent_clients=recent_clients,
                         upcoming_reminders=upcoming_reminders)

# Client Management Routes
@main_bp.route('/clients')
@login_required
def clients():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Client.query
    if search:
        query = query.filter(or_(
            Client.name.contains(search),
            Client.pan.contains(search),
            Client.gstin.contains(search)
        ))
    
    clients_pagination = query.order_by(Client.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('clients/index.html', 
                         clients=clients_pagination.items,
                         pagination=clients_pagination,
                         search=search)

@main_bp.route('/clients/new', methods=['GET', 'POST'])
@login_required
def new_client():
    form = ClientForm()
    
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            pan=form.pan.data,
            gstin=form.gstin.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            date_of_birth=form.date_of_birth.data,
            incorporation_date=form.incorporation_date.data,
            client_type=form.client_type.data,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(client)
        db.session.commit()
        flash('Client created successfully!', 'success')
        return redirect(url_for('main.clients'))
    
    return render_template('clients/form.html', form=form, title='New Client')

@main_bp.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        form.populate_obj(client)
        db.session.commit()
        flash('Client updated successfully!', 'success')
        return redirect(url_for('main.clients'))
    
    return render_template('clients/form.html', form=form, title='Edit Client', client=client)

# Tax Returns Routes
@main_bp.route('/tax/income-tax')
@login_required
def income_tax_returns():
    page = request.args.get('page', 1, type=int)
    returns = IncomeTaxReturn.query.join(Client).order_by(IncomeTaxReturn.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('tax/income_tax.html', returns=returns)

@main_bp.route('/tax/income-tax/new', methods=['GET', 'POST'])
@login_required
def new_income_tax_return():
    form = IncomeTaxReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        itr = IncomeTaxReturn(
            client_id=form.client_id.data,
            assessment_year=form.assessment_year.data,
            return_type=form.return_type.data,
            filing_date=form.filing_date.data,
            due_date=form.due_date.data,
            total_income=form.total_income.data or 0,
            tax_payable=form.tax_payable.data or 0,
            refund_amount=form.refund_amount.data or 0,
            status=form.status.data,
            acknowledgment_number=form.acknowledgment_number.data,
            created_by=current_user.id
        )
        
        db.session.add(itr)
        db.session.commit()
        flash('Income Tax Return created successfully!', 'success')
        return redirect(url_for('main.income_tax_returns'))
    
    return render_template('tax/income_tax.html', form=form, returns=None)

@main_bp.route('/tax/tds')
@login_required
def tds_returns():
    page = request.args.get('page', 1, type=int)
    returns = TDSReturn.query.join(Client).order_by(TDSReturn.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('tax/tds.html', returns=returns)

@main_bp.route('/tax/tds/new', methods=['GET', 'POST'])
@login_required
def new_tds_return():
    form = TDSReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        tds = TDSReturn(
            client_id=form.client_id.data,
            tan=form.tan.data,
            quarter=form.quarter.data,
            financial_year=form.financial_year.data,
            return_type=form.return_type.data,
            filing_date=form.filing_date.data,
            due_date=form.due_date.data,
            total_tds=form.total_tds.data or 0,
            status=form.status.data,
            token_number=form.token_number.data,
            created_by=current_user.id
        )
        
        db.session.add(tds)
        db.session.commit()
        flash('TDS Return created successfully!', 'success')
        return redirect(url_for('main.tds_returns'))
    
    return render_template('tax/tds.html', form=form, returns=None)

@main_bp.route('/tax/gst')
@login_required
def gst_returns():
    page = request.args.get('page', 1, type=int)
    returns = GSTReturn.query.join(Client).order_by(GSTReturn.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('tax/gst.html', returns=returns)

@main_bp.route('/tax/gst/new', methods=['GET', 'POST'])
@login_required
def new_gst_return():
    form = GSTReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        gst = GSTReturn(
            client_id=form.client_id.data,
            gstin=form.gstin.data,
            return_type=form.return_type.data,
            month_year=form.month_year.data,
            filing_date=form.filing_date.data,
            due_date=form.due_date.data,
            total_sales=form.total_sales.data or 0,
            total_tax=form.total_tax.data or 0,
            status=form.status.data,
            arn_number=form.arn_number.data,
            created_by=current_user.id
        )
        
        db.session.add(gst)
        db.session.commit()
        flash('GST Return created successfully!', 'success')
        return redirect(url_for('main.gst_returns'))
    
    return render_template('tax/gst.html', form=form, returns=None)

# Employee Management Routes
@main_bp.route('/admin/employees')
@login_required
def employees():
    page = request.args.get('page', 1, type=int)
    employees_pagination = Employee.query.order_by(Employee.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/employees.html', employees=employees_pagination)

@main_bp.route('/admin/employees/new', methods=['GET', 'POST'])
@login_required
def new_employee():
    form = EmployeeForm()
    
    if form.validate_on_submit():
        employee = Employee(
            name=form.name.data,
            employee_id=form.employee_id.data,
            email=form.email.data,
            phone=form.phone.data,
            pan=form.pan.data,
            designation=form.designation.data,
            department=form.department.data,
            date_of_joining=form.date_of_joining.data,
            salary=form.salary.data or 0,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(employee)
        db.session.commit()
        flash('Employee created successfully!', 'success')
        return redirect(url_for('main.employees'))
    
    return render_template('admin/employees.html', form=form, employees=None)

# Payroll Management Routes
@main_bp.route('/admin/payroll')
@login_required
def payroll():
    page = request.args.get('page', 1, type=int)
    payroll_pagination = PayrollEntry.query.join(Employee).order_by(PayrollEntry.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/payroll.html', payroll=payroll_pagination)

@main_bp.route('/admin/payroll/new', methods=['GET', 'POST'])
@login_required
def new_payroll_entry():
    form = PayrollEntryForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        # Calculate net salary
        basic = form.basic_salary.data or 0
        allowances = form.allowances.data or 0
        deductions = form.deductions.data or 0
        pf = form.pf_deduction.data or 0
        tds = form.tds_deduction.data or 0
        net_salary = basic + allowances - deductions - pf - tds
        
        payroll = PayrollEntry(
            employee_id=form.employee_id.data,
            month_year=form.month_year.data,
            basic_salary=basic,
            allowances=allowances,
            deductions=deductions,
            net_salary=net_salary,
            pf_deduction=pf,
            tds_deduction=tds,
            created_by=current_user.id
        )
        
        db.session.add(payroll)
        db.session.commit()
        flash('Payroll entry created successfully!', 'success')
        return redirect(url_for('main.payroll'))
    
    return render_template('admin/payroll.html', form=form, payroll=None)

# Document Management Routes
@main_bp.route('/admin/documents')
@login_required
def documents():
    page = request.args.get('page', 1, type=int)
    documents_pagination = Document.query.join(Client, isouter=True).order_by(Document.upload_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/documents.html', documents=documents_pagination)

@main_bp.route('/admin/documents/new', methods=['GET', 'POST'])
@login_required
def new_document():
    form = DocumentForm()
    form.client_id.choices = [(0, 'Select Client')] + [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        file_path = None
        file_size = None
        
        if form.file.data:
            file_path, file_size = save_uploaded_file(form.file.data)
        
        document = Document(
            client_id=form.client_id.data if form.client_id.data > 0 else None,
            title=form.title.data,
            document_type=form.document_type.data,
            file_path=file_path,
            file_size=file_size,
            notes=form.notes.data,
            uploaded_by=current_user.id
        )
        
        db.session.add(document)
        db.session.commit()
        flash('Document uploaded successfully!', 'success')
        return redirect(url_for('main.documents'))
    
    return render_template('admin/documents.html', form=form, documents=None)

# Reports Routes
@main_bp.route('/reports/outstanding')
@login_required
def outstanding_reports():
    page = request.args.get('page', 1, type=int)
    outstanding_pagination = OutstandingFee.query.join(Client).filter_by(status='Pending').order_by(OutstandingFee.due_date).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Calculate totals
    total_outstanding = db.session.query(func.sum(OutstandingFee.amount)).filter_by(status='Pending').scalar() or 0
    overdue_count = OutstandingFee.query.filter(
        OutstandingFee.status == 'Pending',
        OutstandingFee.due_date < date.today()
    ).count()
    
    return render_template('reports/outstanding.html', 
                         outstanding=outstanding_pagination,
                         total_outstanding=total_outstanding,
                         overdue_count=overdue_count)

@main_bp.route('/reports/outstanding/new', methods=['GET', 'POST'])
@login_required
def new_outstanding_fee():
    form = OutstandingFeeForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        fee = OutstandingFee(
            client_id=form.client_id.data,
            service_type=form.service_type.data,
            amount=form.amount.data,
            due_date=form.due_date.data,
            status=form.status.data,
            invoice_number=form.invoice_number.data,
            created_by=current_user.id
        )
        
        db.session.add(fee)
        db.session.commit()
        flash('Outstanding fee record created successfully!', 'success')
        return redirect(url_for('main.outstanding_reports'))
    
    return render_template('reports/outstanding.html', form=form, outstanding=None)

# User Management Routes
@main_bp.route('/settings/users')
@login_required
def users():
    if current_user.role.name != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    users_pagination = User.query.join(Role).order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('settings/users.html', users=users_pagination)

@main_bp.route('/settings/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    if current_user.role.name != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = UserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    
    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role_id=form.role_id.data,
            is_active=form.is_active.data
        )
        
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('main.users'))
    
    return render_template('settings/users.html', form=form, users=None)

# API Routes for AJAX
@main_bp.route('/api/clients/search')
@login_required
def api_search_clients():
    query = request.args.get('q', '')
    clients = Client.query.filter(
        or_(
            Client.name.contains(query),
            Client.pan.contains(query),
            Client.gstin.contains(query)
        )
    ).limit(10).all()
    
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'pan': c.pan,
        'gstin': c.gstin
    } for c in clients])

# CRM Routes
@main_bp.route('/reminders')
@login_required
def reminders():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Reminder.query
    if search:
        query = query.filter(or_(
            Reminder.title.contains(search),
            Reminder.description.contains(search)
        ))
    
    reminders = query.order_by(Reminder.reminder_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get overdue reminders
    overdue_reminders = Reminder.query.filter(
        Reminder.reminder_date < datetime.now(),
        Reminder.status == 'Active'
    ).count()
    
    return render_template('crm/reminders.html', 
                         reminders=reminders, 
                         overdue_count=overdue_reminders,
                         search=search)

@main_bp.route('/reminders/new', methods=['GET', 'POST'])
@login_required
def new_reminder():
    form = ReminderForm()
    form.client_id.choices = [(0, 'Select Client')] + [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        reminder = Reminder(
            client_id=form.client_id.data if form.client_id.data else None,
            title=form.title.data,
            description=form.description.data,
            reminder_date=datetime.combine(form.reminder_date.data, datetime.min.time()),
            reminder_type=form.reminder_type.data,
            created_by=current_user.id
        )
        
        db.session.add(reminder)
        db.session.commit()
        flash('Reminder created successfully!', 'success')
        return redirect(url_for('main.reminders'))
    
    return render_template('crm/reminder_form.html', form=form, title='New Reminder')

@main_bp.route('/reminders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    form = ReminderForm(obj=reminder)
    form.client_id.choices = [(0, 'Select Client')] + [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        reminder.client_id = form.client_id.data if form.client_id.data else None
        reminder.title = form.title.data
        reminder.description = form.description.data
        reminder.reminder_date = datetime.combine(form.reminder_date.data, datetime.min.time())
        reminder.reminder_type = form.reminder_type.data
        
        db.session.commit()
        flash('Reminder updated successfully!', 'success')
        return redirect(url_for('main.reminders'))
    
    return render_template('crm/reminder_form.html', form=form, reminder=reminder, title='Edit Reminder')

@main_bp.route('/reminders/<int:id>/complete')
@login_required
def complete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    reminder.status = 'Completed'
    db.session.commit()
    flash('Reminder marked as completed!', 'success')
    return redirect(url_for('main.reminders'))

@main_bp.route('/communications')
@login_required
def communications():
    return render_template('crm/communications.html')

@main_bp.route('/follow_ups')
@login_required
def follow_ups():
    # Get pending follow-ups based on reminders
    pending_followups = Reminder.query.filter(
        Reminder.reminder_type == 'Follow-up',
        Reminder.status == 'Active',
        Reminder.reminder_date <= datetime.now() + timedelta(days=7)
    ).order_by(Reminder.reminder_date).all()
    
    return render_template('crm/follow_ups.html', follow_ups=pending_followups)

# ERP Routes
@main_bp.route('/inventory')
@login_required
def inventory():
    return render_template('erp/inventory.html')

@main_bp.route('/analytics')
@login_required
def analytics():
    # Get analytics data
    monthly_revenue = db.session.query(
        func.date_trunc('month', OutstandingFee.created_at).label('month'),
        func.sum(OutstandingFee.amount).label('total')
    ).filter(OutstandingFee.status == 'Paid').group_by('month').all()
    
    client_stats = db.session.query(
        Client.client_type,
        func.count(Client.id).label('count')
    ).group_by(Client.client_type).all()
    
    return render_template('reports/analytics.html', 
                         monthly_revenue=monthly_revenue,
                         client_stats=client_stats)

@main_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    stats = {
        'total_clients': Client.query.count(),
        'pending_itr': IncomeTaxReturn.query.filter_by(status='Pending').count(),
        'pending_tds': TDSReturn.query.filter_by(status='Pending').count(),
        'pending_gst': GSTReturn.query.filter_by(status='Pending').count(),
        'total_outstanding': db.session.query(func.sum(OutstandingFee.amount)).filter_by(status='Pending').scalar() or 0
    }
    return jsonify(stats)

@main_bp.route('/api/reminders/upcoming')
@login_required
def api_upcoming_reminders():
    reminders = Reminder.query.filter(
        Reminder.reminder_date >= datetime.now(),
        Reminder.reminder_date <= datetime.now() + timedelta(days=7),
        Reminder.status == 'Active'
    ).order_by(Reminder.reminder_date).all()
    
    return jsonify([{
        'id': r.id,
        'title': r.title,
        'client_name': r.client.name if r.client else 'General',
        'reminder_date': r.reminder_date.strftime('%Y-%m-%d'),
        'reminder_type': r.reminder_type
    } for r in reminders])
