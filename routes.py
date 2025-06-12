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
    form = IncomeTaxReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    return render_template('tax/income_tax.html', returns=returns, form=form, today=date.today())

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
    form = TDSReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    return render_template('tax/tds.html', returns=returns, form=form, today=date.today())

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
    form = GSTReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    return render_template('tax/gst.html', returns=returns, form=form, today=date.today())

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
    form = EmployeeForm()
    return render_template('admin/employees.html', form=form, employees=employees_pagination)

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
    form = PayrollEntryForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(status='Active').all()]
    return render_template('admin/payroll.html', form=form, payroll=payroll_pagination)

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
    form = DocumentForm()
    form.client_id.choices = [(0, 'Select Client')] + [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    return render_template('admin/documents.html', form=form, documents=documents_pagination)

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

    form = OutstandingFeeForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    return render_template('reports/outstanding.html', form=form, 
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

    if current_user.role.name != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = UserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]
    
    return render_template('settings/users.html', form=form, users=users_pagination, datetime=datetime)

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
    # Use SQLite's strftime to extract the 'YYYY-MM' format for the month
    monthly_revenue = db.session.query(
        func.strftime('%Y-%m', OutstandingFee.created_at).label('month'),
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

# ROC Forms Routes
@main_bp.route('/roc_forms')
@login_required
def roc_forms():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = ROCForm.query
    if search:
        query = query.join(Client).filter(or_(
            Client.name.contains(search),
            ROCForm.form_type.contains(search),
            ROCForm.acknowledgment_number.contains(search)
        ))
    
    roc_forms = query.order_by(ROCForm.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compliance/roc_forms.html', roc_forms=roc_forms, search=search, today=date.today())

@main_bp.route('/roc_forms/new', methods=['GET', 'POST'])
@login_required
def new_roc_form():
    form = ROCFormForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        roc_form = ROCForm(
            client_id=form.client_id.data,
            form_type=form.form_type.data,
            financial_year=form.financial_year.data,
            filing_date=form.filing_date.data,
            due_date=form.due_date.data,
            acknowledgment_number=form.acknowledgment_number.data,
            status=form.status.data,
            filing_fee=form.filing_fee.data or 0,
            late_fee=form.late_fee.data or 0,
            created_by=current_user.id
        )
        
        db.session.add(roc_form)
        db.session.commit()
        flash('ROC Form entry created successfully!', 'success')
        return redirect(url_for('main.roc_forms'))
    
    return render_template('compliance/roc_form.html', form=form, title='New ROC Form')

# SFT Returns Routes
@main_bp.route('/sft_returns')
@login_required
def sft_returns():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = SFTReturn.query
    if search:
        query = query.join(Client).filter(or_(
            Client.name.contains(search),
            SFTReturn.acknowledgment_number.contains(search)
        ))
    
    sft_returns = query.order_by(SFTReturn.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compliance/sft_returns.html', sft_returns=sft_returns, search=search, today=date.today())

@main_bp.route('/sft_returns/new', methods=['GET', 'POST'])
@login_required
def new_sft_return():
    form = SFTReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        sft_return = SFTReturn(
            client_id=form.client_id.data,
            financial_year=form.financial_year.data,
            form_type=form.form_type.data,
            filing_date=form.filing_date.data,
            due_date=form.due_date.data,
            acknowledgment_number=form.acknowledgment_number.data,
            total_transactions=form.total_transactions.data or 0,
            total_amount=form.total_amount.data or 0,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(sft_return)
        db.session.commit()
        flash('SFT Return created successfully!', 'success')
        return redirect(url_for('main.sft_returns'))
    
    return render_template('compliance/sft_return.html', form=form, title='New SFT Return')

# Balance Sheet & Audit Routes
@main_bp.route('/balance_sheet_audits')
@login_required
def balance_sheet_audits():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = BalanceSheetAudit.query
    if search:
        query = query.join(Client).filter(or_(
            Client.name.contains(search),
            BalanceSheetAudit.auditor_name.contains(search)
        ))
    
    audits = query.order_by(BalanceSheetAudit.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compliance/balance_sheet_audits.html', audits=audits, search=search)

@main_bp.route('/balance_sheet_audits/new', methods=['GET', 'POST'])
@login_required
def new_balance_sheet_audit():
    form = BalanceSheetAuditForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        audit = BalanceSheetAudit(
            client_id=form.client_id.data,
            financial_year=form.financial_year.data,
            audit_type=form.audit_type.data,
            balance_sheet_date=form.balance_sheet_date.data,
            audit_completion_date=form.audit_completion_date.data,
            auditor_name=form.auditor_name.data,
            auditor_membership_no=form.auditor_membership_no.data,
            opinion_type=form.opinion_type.data,
            key_audit_matters=form.key_audit_matters.data,
            management_letter_issued=form.management_letter_issued.data,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(audit)
        db.session.commit()
        flash('Balance Sheet & Audit entry created successfully!', 'success')
        return redirect(url_for('main.balance_sheet_audits'))
    
    return render_template('compliance/audit.html', form=form, title='New Balance Sheet & Audit')

# CMA Reports Routes
@main_bp.route('/cma_reports')
@login_required
def cma_reports():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = CMAReport.query
    if search:
        query = query.join(Client).filter(or_(
            Client.name.contains(search),
            CMAReport.reporting_period.contains(search)
        ))
    
    cma_reports = query.order_by(CMAReport.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compliance/cma_reports.html', cma_reports=cma_reports, search=search)

@main_bp.route('/cma_reports/new', methods=['GET', 'POST'])
@login_required
def new_cma_report():
    form = CMAReportForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        cma_report = CMAReport(
            client_id=form.client_id.data,
            reporting_period=form.reporting_period.data,
            report_date=form.report_date.data,
            working_capital_limit=form.working_capital_limit.data or 0,
            utilized_amount=form.utilized_amount.data or 0,
            cash_credit_limit=form.cash_credit_limit.data or 0,
            overdraft_limit=form.overdraft_limit.data or 0,
            bill_discounting_limit=form.bill_discounting_limit.data or 0,
            letter_of_credit=form.letter_of_credit.data or 0,
            bank_guarantee=form.bank_guarantee.data or 0,
            inventory_value=form.inventory_value.data or 0,
            receivables_value=form.receivables_value.data or 0,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(cma_report)
        db.session.commit()
        flash('CMA Report created successfully!', 'success')
        return redirect(url_for('main.cma_reports'))
    
    return render_template('compliance/cma_form.html', form=form, title='New CMA Report')

# Assessment Orders Routes
@main_bp.route('/assessment_orders')
@login_required
def assessment_orders():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = AssessmentOrder.query
    if search:
        query = query.join(Client).filter(or_(
            Client.name.contains(search),
            AssessmentOrder.order_number.contains(search)
        ))
    
    orders = query.order_by(AssessmentOrder.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compliance/assessment_orders.html', orders=orders, search=search)

@main_bp.route('/assessment_orders/new', methods=['GET', 'POST'])
@login_required
def new_assessment_order():
    form = AssessmentOrderForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        order = AssessmentOrder(
            client_id=form.client_id.data,
            assessment_year=form.assessment_year.data,
            order_type=form.order_type.data,
            order_date=form.order_date.data,
            order_number=form.order_number.data,
            total_income_assessed=form.total_income_assessed.data or 0,
            tax_demanded=form.tax_demanded.data or 0,
            interest_charged=form.interest_charged.data or 0,
            penalty_imposed=form.penalty_imposed.data or 0,
            appeal_filed=form.appeal_filed.data,
            appeal_date=form.appeal_date.data,
            appeal_number=form.appeal_number.data,
            status=form.status.data,
            remarks=form.remarks.data,
            created_by=current_user.id
        )
        
        db.session.add(order)
        db.session.commit()
        flash('Assessment Order created successfully!', 'success')
        return redirect(url_for('main.assessment_orders'))
    
    return render_template('compliance/assessment_form.html', form=form, title='New Assessment Order')

# XBRL Reports Routes
@main_bp.route('/xbrl_reports')
@login_required
def xbrl_reports():
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = XBRLReport.query
    if search:
        query = query.join(Client).filter(or_(
            Client.name.contains(search),
            XBRLReport.acknowledgment_number.contains(search)
        ))
    
    xbrl_reports = query.order_by(XBRLReport.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('compliance/xbrl_reports.html', xbrl_reports=xbrl_reports, search=search)

@main_bp.route('/xbrl_reports/new', methods=['GET', 'POST'])
@login_required
def new_xbrl_report():
    form = XBRLReportForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    if form.validate_on_submit():
        xbrl_file_path = None
        if form.xbrl_file.data:
            xbrl_file_path = save_uploaded_file(form.xbrl_file.data, 'xbrl')
        
        xbrl_report = XBRLReport(
            client_id=form.client_id.data,
            financial_year=form.financial_year.data,
            report_type=form.report_type.data,
            filing_category=form.filing_category.data,
            xbrl_file_path=xbrl_file_path,
            validation_status=form.validation_status.data,
            validation_errors=form.validation_errors.data,
            filing_date=form.filing_date.data,
            acknowledgment_number=form.acknowledgment_number.data,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(xbrl_report)
        db.session.commit()
        flash('XBRL Report created successfully!', 'success')
        return redirect(url_for('main.xbrl_reports'))
    
    return render_template('compliance/xbrl_form.html', form=form, title='New XBRL Report')

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

# Smart Features Routes
@main_bp.route('/smart/gst-validator')
@login_required
def gst_validator():
    recent_validations = GSTValidation.query.order_by(GSTValidation.last_validated.desc()).limit(10).all()
    return render_template('smart/gst_validator.html', recent_validations=recent_validations)

@main_bp.route('/smart/validate-gst', methods=['POST'])
@login_required
def validate_gst():
    gstin = request.form.get('gstin', '').strip()
    
    if not gstin or len(gstin) != 15:
        flash('Please enter a valid 15-digit GSTIN', 'error')
        return redirect(url_for('main.gst_validator'))
    
    # Check if already validated recently
    existing = GSTValidation.query.filter_by(gstin=gstin).first()
    
    # Simple validation logic - in production, integrate with GST API
    is_valid = len(gstin) == 15 and gstin.isalnum()
    
    if existing:
        existing.last_validated = datetime.utcnow()
        existing.is_valid = is_valid
    else:
        validation = GSTValidation(
            gstin=gstin,
            is_valid=is_valid,
            business_name=f"Business for {gstin[:2]}" if is_valid else None,
            status="Active" if is_valid else "Invalid",
            state_code=gstin[:2] if is_valid else None,
            state_name=f"State {gstin[:2]}" if is_valid else None,
            taxpayer_type="Regular" if is_valid else None,
            constitution="Private Limited" if is_valid else None
        )
        db.session.add(validation)
        existing = validation
    
    db.session.commit()
    
    recent_validations = GSTValidation.query.order_by(GSTValidation.last_validated.desc()).limit(10).all()
    return render_template('smart/gst_validator.html', 
                         validation_result=existing, 
                         recent_validations=recent_validations)

@main_bp.route('/smart/challan-management')
@login_required
def challan_management():
    challans = ChallanManagement.query.order_by(ChallanManagement.created_at.desc()).all()
    return render_template('smart/challan_management.html', challans=challans)

@main_bp.route('/smart/return-tracker')
@login_required
def return_tracker():
    returns = ReturnTracker.query.order_by(ReturnTracker.due_date).all()
    return render_template('smart/return_tracker.html', returns=returns)

@main_bp.route('/smart/auto-reminders')
@login_required
def auto_reminders():
    auto_reminders = Reminder.query.filter_by(auto_created=True).order_by(Reminder.reminder_date).all()
    return render_template('smart/auto_reminders.html', auto_reminders=auto_reminders)

# Enhanced CRM Routes
@main_bp.route('/crm/client-search')
@login_required
def client_search():
    search = request.args.get('search', '')
    clients = Client.query
    
    if search:
        clients = clients.filter(
            db.or_(
                Client.name.contains(search),
                Client.pan.contains(search),
                Client.gstin.contains(search),
                Client.email.contains(search)
            )
        )
    
    clients = clients.order_by(Client.name).all()
    return render_template('crm/client_search.html', clients=clients, search=search)

@main_bp.route('/crm/client-notes')
@login_required
def client_notes():
    notes = ClientNote.query.order_by(ClientNote.created_at.desc()).all()
    return render_template('crm/client_notes.html', notes=notes)

@main_bp.route('/crm/document-checklists')
@login_required
def document_checklists():
    checklists = DocumentChecklist.query.order_by(DocumentChecklist.due_date).all()
    return render_template('crm/document_checklists.html', checklists=checklists)

@main_bp.route('/crm/communications')
@login_required
def communications():
    logs = CommunicationLog.query.order_by(CommunicationLog.sent_at.desc()).all()
    templates = SMSTemplate.query.filter_by(is_active=True).all()
    email_templates = EmailTemplate.query.filter_by(is_active=True).all()
    return render_template('crm/communications.html', 
                         logs=logs, 
                         templates=templates, 
                         email_templates=email_templates)
