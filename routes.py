import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, make_response
from flask_login import login_required, current_user
from app import db
from models import *
from forms import *
from utils import allowed_file, save_uploaded_file
from datetime import datetime, date, timedelta
from sqlalchemy import func, extract, distinct, or_
from sqlalchemy.exc import IntegrityError
from collections import OrderedDict
from calendar import month_abbr

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
    try:
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

    except IntegrityError as e:
        if 'clients.pan' in str(e):
            flash('Given PAN Number already exist', 'danger')
        else:
            flash('Error Occured due to creating Client', 'danger')
        return redirect(url_for('main.clients'))

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

@main_bp.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)

    # Refresh the client to get the latest state from DB
    db.session.refresh(client)

    if OutstandingFee.query.filter_by(client_id=client.id).count() > 0:
        flash("Cannot delete client with existing outstanding fees. Please remove them first.", "danger")
        return redirect(url_for('main.clients'))
    
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully.', 'success')
    return redirect(url_for('main.clients'))

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

@main_bp.route('/tax/income-tax/edit/<int:itr_id>', methods=['POST'])
@login_required
def edit_income_tax_return(itr_id):
    itr = IncomeTaxReturn.query.get_or_404(itr_id)
    form = IncomeTaxReturnForm(obj=itr)

    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]

    if form.validate_on_submit():
        form.populate_obj(itr)
        db.session.commit()
        flash('Income Tax Return updated successfully!', 'success')
    else:
        flash('Failed to update ITR. Please check form input.', 'danger')

    return redirect(url_for('main.income_tax_returns'))

@main_bp.route('/tax/income-tax/delete/<int:itr_id>', methods=['POST'])
@login_required
def delete_income_tax_return(itr_id):
    itr = IncomeTaxReturn.query.get_or_404(itr_id)
    db.session.delete(itr)
    db.session.commit()
    flash('Income Tax Return deleted successfully.', 'success')
    return redirect(url_for('main.income_tax_returns'))

#TDS Returns Routes
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

@main_bp.route('/tax/tds/update/<int:tds_id>', methods=['POST'])
@login_required
def update_tds_return(tds_id):
    tds = TDSReturn.query.get_or_404(tds_id)
    form = TDSReturnForm(obj=tds)

    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]
    
    if form.validate_on_submit():
        form.populate_obj(tds)        
        db.session.commit()
        flash('TDS Return updated successfully!', 'success')
    
    return redirect(url_for('main.tds_returns'))

@main_bp.route('/tax/tds/delete/<int:tds_id>', methods=['POST'])
@login_required
def delete_tds_return(tds_id):
    tds = TDSReturn.query.get_or_404(tds_id)
    db.session.delete(tds)
    db.session.commit()
    flash('TDS Return deleted successfully!', 'success')
    return redirect(url_for('main.tds_returns'))

# GST Returns Routes
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

@main_bp.route('/tax/gst/edit/<int:gst_id>', methods=['POST'])
@login_required
def edit_gst_return(gst_id):
    gst = GSTReturn.query.get_or_404(gst_id)
    form = GSTReturnForm(obj=gst)

    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]

    if form.validate_on_submit():
        form.populate_obj(gst)
        db.session.commit()
        flash('GST Return updated successfully!', 'success')
    else:
        flash('Failed to update GST Return.', 'danger')

    return redirect(url_for('main.gst_returns'))

@main_bp.route('/tax/gst/delete/<int:gst_id>', methods=['POST'])
@login_required
def delete_gst_return(gst_id):
    gst = GSTReturn.query.get_or_404(gst_id)
    db.session.delete(gst)
    db.session.commit()
    flash('GST Return deleted successfully!', 'success')
    return redirect(url_for('main.gst_returns'))

# Employee Management Routes
@main_bp.route('/admin/employees')
@login_required
def employees():
    page = request.args.get('page', 1, type=int)
    employees_pagination = Employee.query.order_by(Employee.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    form = EmployeeForm()
    # Total employee count
    total_employees = Employee.query.count()
    # Active employees count
    active_employees = Employee.query.filter_by(status='Active').count()
    # ✅ Distinct department count
    departments_count = db.session.query(func.count(func.distinct(Employee.department))).scalar()
    # ✅ Average salary
    avg_salary = db.session.query(func.avg(Employee.salary)).scalar()
    avg_salary = round(avg_salary or 0, 2)  # Handle None case if no employees yet

    return render_template(
        'admin/employees.html', 
        form=form, 
        employees=employees_pagination,
        total_employees=total_employees,
        active_employees=active_employees,
        departments_count=departments_count,
        avg_salary=avg_salary
    )

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

@main_bp.route('/admin/employees/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    form = EmployeeForm(obj=employee)

    if form.validate_on_submit():
        form.populate_obj(employee)
        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('main.employees'))

    return render_template('admin/employees.html', form=form, employee=employee, edit=True)

@main_bp.route('/admin/employees/<int:id>/delete', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    db.session.delete(employee)
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('main.employees'))

# Payroll Management Routes
@main_bp.route('/admin/payroll', methods=['GET'])
@login_required
def payroll():
    page = request.args.get('page', 1, type=int)
    payroll_pagination = PayrollEntry.query.join(Employee).order_by(PayrollEntry.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    form = PayrollEntryForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(status='Active').all()]
    emp_id = request.args.get('emp_id')
    search_emp_id = emp_id if emp_id else None

    # 🔸 Calculating required metrics
    total_payroll = db.session.query(db.func.sum(Employee.salary)).scalar() or 0
    active_employees = Employee.query.filter_by(status='Active').count()
    total_deductions = db.session.query(
        db.func.sum(PayrollEntry.deductions + PayrollEntry.pf_deduction + PayrollEntry.tds_deduction)
    ).scalar() or 0
    net_payroll = db.session.query(db.func.sum(PayrollEntry.net_salary)).scalar() or 0

    return render_template(
        'admin/payroll.html', 
        form=form, 
        payroll=payroll_pagination, 
        search_emp_id=search_emp_id,
        total_payroll=total_payroll,
        active_employees=active_employees,
        total_deductions=total_deductions,
        net_payroll=net_payroll
    )

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

@main_bp.route('/admin/payroll/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_payroll_entry(id):
    entry = PayrollEntry.query.get_or_404(id)
    form = PayrollEntryForm(obj=entry)
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.filter_by(status='Active').all()]
    form.employee_id.data = entry.employee_id

    if form.validate_on_submit():
        basic = form.basic_salary.data or 0
        allowances = form.allowances.data or 0
        deductions = form.deductions.data or 0
        pf = form.pf_deduction.data or 0
        tds = form.tds_deduction.data or 0
        net_salary = basic + allowances - deductions - pf - tds

        entry.employee_id = form.employee_id.data
        entry.month_year = form.month_year.data
        entry.basic_salary = basic
        entry.allowances = allowances
        entry.deductions = deductions
        entry.pf_deduction = pf
        entry.tds_deduction = tds
        entry.net_salary = net_salary

        db.session.commit()
        flash('Payroll entry updated successfully!', 'success')
        return redirect(url_for('main.payroll'))

    return render_template('admin/payroll_form.html', form=form, payroll=None)

@main_bp.route('/admin/payroll/<int:id>/delete', methods=['POST'])
@login_required
def delete_payroll_entry(id):
    entry = PayrollEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Payroll entry deleted successfully!', 'success')
    return redirect(url_for('main.payroll'))

# Document Management Routes
@main_bp.route('/admin/documents')
@login_required
def documents():
    page = request.args.get('page', 1, type=int)
    documents_pagination = Document.query.join(Client, isouter=True).order_by(Document.upload_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Stats
    total_documents = db.session.query(func.count(Document.id)).scalar()
    total_file_size = db.session.query(func.sum(Document.file_size)).scalar() or 0

    now = datetime.utcnow()
    documents_this_month = db.session.query(func.count(Document.id)).filter(
        extract('month', Document.upload_date) == now.month,
        extract('year', Document.upload_date) == now.year
    ).scalar()

    # Form
    form = DocumentForm()
    form.client_id.choices = [(0, 'Select Client')] + [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]

    document_types_count = len(form.document_type.choices) or 0
    
    return render_template(
        'admin/documents.html',
        form=form,
        documents=documents_pagination,
        total_documents=total_documents,
        total_file_size=total_file_size,
        documents_this_month=documents_this_month,
        document_types_count=document_types_count
    )

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

# Edit Document
@main_bp.route('/admin/documents/<int:id>/edit', methods=['POST'])
@login_required
def edit_document(id):
    document = Document.query.get_or_404(id)
    title = request.form.get('title')
    document_type = request.form.get('document_type')
    client_id = int(request.form.get('client_id')) or None
    notes = request.form.get('notes')
    file = request.files.get('file')

    if title:
        document.title = title
    if document_type:
        document.document_type = document_type
    document.client_id = client_id
    document.notes = notes

    if file:
        file_path, file_size = save_uploaded_file(file)
        document.file_path = file_path
        document.file_size = file_size

    db.session.commit()
    flash('Document updated successfully!', 'success')
    return redirect(url_for('main.documents'))

# Delete Document
@main_bp.route('/admin/documents/<int:id>/delete', methods=['POST'])
@login_required
def delete_document(id):
    document = Document.query.get_or_404(id)
    db.session.delete(document)
    db.session.commit()
    flash('Document deleted successfully!', 'success')
    return redirect(url_for('main.documents'))

# Preview Document
@main_bp.route('/admin/documents/<int:id>/preview')
@login_required
def preview_document(id):
    document = Document.query.get_or_404(id)
    if document.file_path:
        from flask import send_file

        return send_file(document.file_path)
    flash('File not found.', 'warning')
    return redirect(url_for('main.documents'))

# Download Document
@main_bp.route('/admin/documents/<int:id>/download')
@login_required
def download_document(id):
    document = Document.query.get_or_404(id)
    
    if document.file_path and os.path.exists(document.file_path):
        from flask import send_file
        from werkzeug.utils import secure_filename

        # Get the file extension from the file path
        file_ext = os.path.splitext(document.file_path)[1]  # Example: '.pdf'

        # Sanitize and construct the full filename with extension
        filename = secure_filename(document.title or 'document') + file_ext

        return send_file(document.file_path, as_attachment=True, download_name=filename)

    flash('File not found.', 'warning')
    return redirect(url_for('main.documents'))

# Reports Routes
@main_bp.route('/reports/outstanding')
@login_required
def outstanding_reports():
    page = request.args.get('page', 1, type=int)
    outstanding_pagination = OutstandingFee.query.join(Client, Client.id == OutstandingFee.client_id).order_by(OutstandingFee.due_date).paginate(
        page=page, per_page=20, error_out=False
    )

    today = date.today()
    month = today.month
    year = today.year

    # Add below these lines:
    pending_count = OutstandingFee.query.filter_by(status='Pending').count()

    this_month_collection = db.session.query(func.sum(OutstandingFee.amount)) \
        .filter_by(status='Paid') \
        .filter(extract('month', OutstandingFee.created_at) == month) \
        .filter(extract('year', OutstandingFee.created_at) == year) \
        .scalar() or 0
    
    # Calculate totals
    total_outstanding = db.session.query(func.sum(OutstandingFee.amount)).scalar() or 0
    overdue_count = OutstandingFee.query.filter(
        OutstandingFee.status == 'Overdue',
        OutstandingFee.due_date < date.today()
    ).count()

    form = OutstandingFeeForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]

    trend_data = OrderedDict()
    for i in range(5, -1, -1):  # last 6 months
        month_date = today - timedelta(days=i*30)
        key = month_abbr[month_date.month]
        total = db.session.query(func.sum(OutstandingFee.amount)).filter(
            extract('month', OutstandingFee.created_at) == month_date.month,
            extract('year', OutstandingFee.created_at) == month_date.year
        ).scalar() or 0
        trend_data[key] = total

    # Status Breakdown
    status_data = {
        'Pending': OutstandingFee.query.filter_by(status='Pending').count(),
        'Overdue': OutstandingFee.query.filter_by(status='Overdue').count(),
        'Paid': OutstandingFee.query.filter_by(status='Paid').count()
    }
    
    return render_template('reports/outstanding.html', 
                        form=form, 
                        outstanding=outstanding_pagination,
                        total_outstanding=total_outstanding,
                        overdue_count=overdue_count,
                        pending_count=pending_count,
                        today=today,
                        this_month_collection=this_month_collection,
                        trend_data=list(trend_data.values()),
                        trend_labels=list(trend_data.keys()),
                        status_data=status_data)

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

@main_bp.route('/reports/outstanding/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_outstanding_fee(id):
    fee = OutstandingFee.query.get_or_404(id)
    form = OutstandingFeeForm(obj=fee)
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(status='Active').all()]

    if form.validate_on_submit():
        form.populate_obj(fee)
        db.session.commit()
        flash('Outstanding fee updated successfully!', 'success')
        return redirect(url_for('main.outstanding_reports'))

    flash('Error updating outstanding fee!', 'danger')
    return redirect(url_for('main.outstanding_reports'))

@main_bp.route('/reports/outstanding/<int:id>/paid', methods=['POST'])
@login_required
def mark_as_paid(id):
    fee = OutstandingFee.query.get_or_404(id)
    fee.status = "Paid"
    db.session.commit()
    flash(f"{fee.invoice_number} is marked as Paid", 'success')
    return redirect(url_for('main.outstanding_reports'))

@main_bp.route('/reports/outstanding/<int:id>/delete', methods=['POST'])
@login_required
def delete_outstanding_fee(id):
    fee = OutstandingFee.query.get_or_404(id)
    db.session.delete(fee)
    db.session.commit()
    flash('Outstanding fee deleted successfully!', 'success')
    return redirect(url_for('main.outstanding_reports'))

@main_bp.route('/api/outstanding/<int:id>/send-reminder', methods=['POST'])
@login_required
def send_payment_reminder(id):
    fee = OutstandingFee.query.get_or_404(id)
    client = Client.query.get(fee.client_id)
    
    if not client:
        flash('Client Not Found.', 'danger')
        return redirect(url_for('main.outstanding_reports'))

    # Check if a similar reminder already exists for today (optional)
    today = datetime.now().date()
    existing = Reminder.query.filter(
        Reminder.client_id == client.id,
        Reminder.fee_id == fee.id,
        func.date(Reminder.reminder_date) == today
    ).first()
    if existing:
        flash(f"Reminder already sent today for {client.name}!", 'warning')
        return redirect(url_for('main.outstanding_reports'))

    # Create reminder
    reminder = Reminder(
        client_id=client.id,
        fee_id=fee.id,
        title='Payment Due',
        description=f'Payment of ₹{fee.amount} is due for Invoice {fee.invoice_number}.',
        reminder_date=today,
        reminder_type='Due Date',
        auto_created=True,
        created_by=current_user.id
    )
    db.session.add(reminder)
    db.session.commit()

    flash(f"Payment Reminder Created successfully for {client.name}!", 'success')
    return redirect(url_for('main.outstanding_reports'))

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
    
    form = UserForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]

    # 🟢 Stats computation
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_role = Role.query.filter_by(name='admin').first()
    admin_users = User.query.filter_by(role_id=admin_role.id).count() if admin_role else 0
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    recent_logins = User.query.filter(User.last_login != None, User.last_login >= twenty_four_hours_ago).count()
    
    return render_template(
        'settings/users.html',
        form=form,
        users=users_pagination,
        datetime=datetime,
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users,
        recent_logins=recent_logins
    )

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

# Edit User (Form Update via Modal or Page)
@main_bp.route('/settings/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if current_user.role.name != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))

    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.all()]

    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash

        user.username = form.username.data
        user.email = form.email.data
        user.role_id = form.role_id.data
        user.is_active = form.is_active.data
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('main.users'))

    return redirect(url_for('main.users'))

@main_bp.route('/settings/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.users'))

# Toggle Active/Inactive User
@main_bp.route('/api/users/<int:id>/toggle-status', methods=['POST'])
@login_required
def toggle_user_status(id):
    if current_user.role.name != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        return jsonify({'error': 'You cannot change your own status.'}), 400

    user.is_active = data.get('is_active', user.is_active)
    db.session.commit()
    return jsonify({'success': True})


# Reset User Password
@main_bp.route('/api/users/<int:id>/reset-password', methods=['POST'])
@login_required
def reset_password(id):
    if current_user.role.name != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    user = User.query.get_or_404(id)

    if user.id == current_user.id:
        return jsonify({'error': 'You cannot reset your own password.'}), 400
    
    from werkzeug.security import generate_password_hash
    import secrets

    new_password = secrets.token_urlsafe(8)
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({'success': True, 'new_password': new_password})

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

@main_bp.route('/reminders/<int:id>/delete', methods=['POST'])
@login_required
def delete_reminder(id):
    reminder = Reminder.query.get_or_404(id)
    db.session.delete(reminder)
    db.session.commit()
    flash('Reminder deleted successfully.', 'success')
    return redirect(url_for('main.reminders'))

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

@main_bp.route('/erp/task-manager', methods=['GET', 'POST'])
@login_required
def task_manager():
    form = TaskForm()
    form.employee_id.choices = [(e.id, e.name) for e in Employee.query.all()]

    tasks = Task.query.order_by(Task.start_date.desc()).all()

    # Task counts
    active_tasks_count = Task.query.filter_by(status='In Progress').count()
    pending_tasks_count = Task.query.filter_by(status='Pending').count()
    completed_tasks_count = Task.query.filter_by(status='Completed').count()

    # Overdue tasks: end_date < today AND not completed
    today = date.today()
    overdue_tasks_count = Task.query.filter(Task.end_date < today, Task.status != 'Completed').count()

    # Average completion rate
    total_tasks = Task.query.count()
    if total_tasks == 0:
        avg_completion = 0
    else:
        avg_completion = round((completed_tasks_count / total_tasks) * 100)

    if form.validate_on_submit():
        task_id = form.task_id.data
        if task_id:
            task = Task.query.get(int(task_id))
            if task:
                task.employee_id = form.employee_id.data
                task.start_date = form.start_date.data
                task.end_date = form.end_date.data
                task.priority = form.priority.data
                task.status = form.status.data
                task.description = form.description.data
                flash('Task updated successfully!', 'success')
            else:
                flash('Task not found.', 'danger')
        else:
            task = Task(
                employee_id=form.employee_id.data,
                start_date=form.start_date.data,
                end_date=form.end_date.data,
                priority=form.priority.data,
                status=form.status.data,
                description=form.description.data,
                created_at=datetime.utcnow()
            )
            db.session.add(task)
            flash('Task created successfully!', 'success')

        db.session.commit()
        return redirect(url_for('main.task_manager'))

    tasks = Task.query.order_by(Task.start_date.desc()).all()
    return render_template(
        'erp/task_manager.html',
        tasks=tasks,
        form=form,
        active_tasks_count=active_tasks_count,
        pending_tasks_count=pending_tasks_count,
        completed_tasks_count=completed_tasks_count,
        overdue_tasks_count=overdue_tasks_count,
        avg_completion=avg_completion
    )


@main_bp.route('/erp/delete-task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully.', 'success')
    return redirect(url_for('main.task_manager'))

# ERP Routes
@main_bp.route('/inventory')
@login_required
def inventory():
    form = InventoryForm()
    items = InventoryItems.query.all()

    # Calculate dynamic stats
    total_items = len(items)
    low_stock = InventoryItems.query.filter(InventoryItems.current_stock < InventoryItems.minimum_stock).count()
    total_value = db.session.query(func.sum(InventoryItems.total_value)).scalar() or 0.0
    categories_count = len(form.category.choices) or 0

    return render_template('erp/inventory.html',
                           items=items,
                           total_items=total_items,
                           low_stock=low_stock,
                           total_value=total_value,
                           categories_count=categories_count,
                           form=form)

@main_bp.route('/inventory/new', methods=['POST'])
@login_required
def new_inventory_item():
    form = InventoryForm()
    
    if form.validate_on_submit():
        status='Not Available'
        total_value=0.0
        if form.current_stock.data <= 0:
            status='Out of Stock'
        elif form.current_stock.data < form.minimum_stock.data:
            status='Low Stock'
        elif form.current_stock.data >= form.minimum_stock.data:
            status='In Stock'
        if(form.unit_price.data and form.current_stock.data):
            total_value = round(form.unit_price.data * form.current_stock.data, 2)
        item = InventoryItems(
            item_name=form.item_name.data,
            item_code=form.item_code.data,
            description=form.description.data,
            unit=form.unit.data,
            unit_price=form.unit_price.data or 0.0,
            total_value=total_value or 0.0,
            current_stock=form.current_stock.data or 0,
            minimum_stock=form.minimum_stock.data or 0,
            location=form.location.data,
            category=form.category.data,
            status=status,
            created_at=datetime.now(),
            created_by=current_user.id
        )
        
        db.session.add(item)
        db.session.commit()
        flash('Inventory item created successfully!', 'success')
        return redirect(url_for('main.inventory'))
    
    flash('Error when Creating New Inventory Item!', 'danger')
    return render_template('erp/inventory.html', form=form, title='New Inventory Item')

@main_bp.route('/inventory/<int:id>/edit', methods=['POST'])
@login_required
def edit_inventory_item(id):
    item = InventoryItems.query.get_or_404(id)

    # Get raw POST data
    item.item_name = request.form.get('item_name')
    item.item_code = request.form.get('item_code')
    item.description = request.form.get('description')
    item.unit = request.form.get('unit')
    item.unit_price = float(request.form.get('unit_price') or 0.0)
    item.current_stock = int(request.form.get('current_stock') or 0)
    item.minimum_stock = int(request.form.get('minimum_stock') or 0)
    item.location = request.form.get('location')
    item.category = request.form.get('category')

    # Recalculate status and total value
    if item.current_stock <= 0:
        item.status = 'Out of Stock'
    elif item.current_stock < item.minimum_stock:
        item.status = 'Low Stock'
    else:
        item.status = 'In Stock'

    item.total_value = round(item.unit_price * item.current_stock, 2)

    db.session.commit()
    flash('Inventory item updated successfully!', 'success')
    return redirect(url_for('main.inventory'))

@main_bp.route('/inventory/<int:id>/increment', methods=['POST'])
@login_required
def increment_inventory_item(id):
    item = InventoryItems.query.get_or_404(id)
    item.current_stock += 1
    item.total_value = round(item.unit_price * item.current_stock, 2)

    # Update status
    if item.current_stock <= 0:
        item.status = 'Out of Stock'
    elif item.current_stock < item.minimum_stock:
        item.status = 'Low Stock'
    else:
        item.status = 'In Stock'

    db.session.commit()
    flash(f'Stock incremented for "{item.item_name}".', 'success')
    return redirect(url_for('main.inventory'))

@main_bp.route('/inventory/<int:id>/decrement', methods=['POST'])
@login_required
def decrement_inventory_item(id):
    item = InventoryItems.query.get_or_404(id)
    if item.current_stock > 0:
        item.current_stock -= 1
        item.total_value = round(item.unit_price * item.current_stock, 2)

        # Update status
        if item.current_stock <= 0:
            item.status = 'Out of Stock'
        elif item.current_stock < item.minimum_stock:
            item.status = 'Low Stock'
        else:
            item.status = 'In Stock'

        db.session.commit()
        flash(f'Stock decremented for "{item.item_name}".', 'warning')
    else:
        flash(f'Cannot decrement. "{item.item_name}" stock is already zero.', 'danger')

    return redirect(url_for('main.inventory'))

@main_bp.route('/inventory/<int:id>/delete', methods=['POST'])
@login_required
def delete_inventory_item(id):
    item = InventoryItems.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Inventory item deleted successfully.', 'success')
    return redirect(url_for('main.inventory'))

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

    form = ROCFormForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    return render_template('compliance/roc_forms.html', roc_forms=roc_forms, Rform=form, search=search, today=date.today())

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

@main_bp.route('/roc_forms/edit/<int:roc_id>', methods=['POST'])
@login_required
def edit_roc_form(roc_id):
    roc_form = ROCForm.query.get_or_404(roc_id)
    form = ROCFormForm(obj=roc_form)

    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

    if form.validate_on_submit():
        form.populate_obj(roc_form)        
        db.session.commit()
        flash('ROC Form updated successfully!', 'success')
    
    return redirect(url_for('main.roc_forms'))

@main_bp.route('/roc_forms/delete/<int:roc_id>', methods=['POST'])
@login_required
def delete_roc_form(roc_id):
    roc_form = ROCForm.query.get_or_404(roc_id)
    db.session.delete(roc_form)
    db.session.commit()
    flash('ROC Form entry deleted successfully.', 'success')
    return redirect(url_for('main.roc_forms'))

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

    form = SFTReturnForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]
    
    return render_template('compliance/sft_returns.html', sft_returns=sft_returns, Sform=form, search=search, today=date.today())

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

@main_bp.route('/sft_returns/<int:sft_id>/edit', methods=['POST'])
@login_required
def edit_sft_return(sft_id):
    sft = SFTReturn.query.get_or_404(sft_id)
    form = SFTReturnForm(obj=sft)
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

    if form.validate_on_submit():
        form.populate_obj(sft)
        db.session.commit()
        flash('SFT Return updated successfully!', 'success')
    return redirect(url_for('main.sft_returns'))

@main_bp.route('/sft_returns/<int:sft_id>/delete', methods=['POST'])
@login_required
def delete_sft_form(sft_id):
    sft = SFTReturn.query.get_or_404(sft_id)
    db.session.delete(sft)
    db.session.commit()
    flash('SFT Return deleted.', 'success')
    return redirect(url_for('main.sft_returns'))

# Balance Sheet & Audit Routes
@main_bp.route('/balance_sheet_audits')
@login_required
def balance_sheet_audits():
    form = BalanceSheetAuditForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

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

    return render_template('compliance/balance_sheet_audits.html', form=form, audits=audits, search=search)


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
            auditor_name=form.auditor_name.data,
            auditor_membership_no=form.auditor_membership_no.data,
            opinion_type=form.opinion_type.data,
            key_audit_matters=form.key_audit_matters.data,
            recommendations=form.recommendations.data,
            audit_period_from=form.audit_period_from.data,
            audit_period_to=form.audit_period_to.data,
            management_response=form.management_response.data,
            management_letter_issued=form.management_letter_issued.data,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(audit)
        db.session.commit()
        flash('Balance Sheet & Audit entry created successfully!', 'success')
        return redirect(url_for('main.balance_sheet_audits'))
    
    return render_template('compliance/balance_sheet_audits.html', form=form, title='New Balance Sheet & Audit')

@main_bp.route('/balance_sheet_audits/edit/<int:bsa_id>', methods=['GET', 'POST'])
@login_required
def edit_balance_sheet_audit(bsa_id):
    audit = BalanceSheetAudit.query.get_or_404(bsa_id)
    form = BalanceSheetAuditForm(obj=audit)
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

    if form.validate_on_submit():
        form.populate_obj(audit)
        db.session.commit()
        flash('Audit Report updated successfully.', 'success')

    return redirect(url_for('main.balance_sheet_audits'))

@main_bp.route('/balance_sheet_audits/delete/<int:bsa_id>', methods=['POST'])
@login_required
def delete_balance_sheet_audit(bsa_id):
    audit = BalanceSheetAudit.query.get_or_404(bsa_id)
    db.session.delete(audit)
    db.session.commit()
    flash('Audit Report deleted successfully.', 'success')
    return redirect(url_for('main.balance_sheet_audits'))

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

@main_bp.route('/cma_report/edit/<int:report_id>', methods=['GET', 'POST'])
def edit_cma_report(report_id):
    report = CMAReport.query.get_or_404(report_id)
    form = CMAReportForm(obj=report)

    # Populate dynamic client choices
    form.client_id.choices = [(client.id, client.name) for client in Client.query.all()]

    if form.validate_on_submit():
        form.populate_obj(report)
        db.session.commit()
        flash('CMA Report updated successfully!', 'success')
        return redirect(url_for('main.cma_reports'))

    return render_template('compliance/cma_form.html', form=form)

@main_bp.route('/cma_report/delete/<int:report_id>', methods=['POST'])
def delete_cma_report(report_id):
    report = CMAReport.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash('CMA Report deleted successfully!', 'success')
    return redirect(url_for('main.cma_reports'))

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

# Edit Route
@main_bp.route('/assessment_order/edit/<int:order_id>', methods=['GET', 'POST'])
def edit_assessment_order(order_id):
    order = AssessmentOrder.query.get_or_404(order_id)
    form = AssessmentOrderForm(obj=order)
    form.client_id.choices = [(client.id, client.name) for client in Client.query.all()]

    if form.validate_on_submit():
        form.populate_obj(order)
        db.session.commit()
        flash('Assessment Order updated successfully!', 'success')
        return redirect(url_for('main.assessment_orders'))

    return render_template('compliance/assessment_form.html', form=form)

# Delete Route
@main_bp.route('/assessment_order/delete/<int:order_id>', methods=['POST'])
def delete_assessment_order(order_id):
    order = AssessmentOrder.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Assessment Order deleted successfully!', 'success')
    return redirect(url_for('main.assessment_orders'))

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

    xbrl_file_path = None  # Always initialize your path

    if form.validate_on_submit():
        if form.xbrl_file.data:
            xbrl_file_path, file_size = save_uploaded_file(form.xbrl_file.data, 'xbrl')  # ✅ Use correct folder & unpack tuple
            print(f"File saved to: {xbrl_file_path}")  # Optional debug

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

@main_bp.route('/xbrl_reports/edit/<int:report_id>', methods=['GET', 'POST'])
@login_required
def xbrl_edit(report_id):
    report = XBRLReport.query.get_or_404(report_id)
    form = XBRLReportForm(obj=report)
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

    if form.validate_on_submit():
        report.client_id = form.client_id.data
        report.financial_year = form.financial_year.data
        report.report_type = form.report_type.data
        report.filing_category = form.filing_category.data
        report.validation_status = form.validation_status.data
        report.validation_errors = form.validation_errors.data
        report.filing_date = form.filing_date.data
        report.acknowledgment_number = form.acknowledgment_number.data
        report.status = form.status.data
        db.session.commit()
        flash('XBRL Report updated successfully!', 'success')
        return redirect(url_for('main.xbrl_reports'))

    return render_template('compliance/xbrl_form.html', form=form, title='Edit XBRL Report')

# Route: Delete XBRL Report
@main_bp.route('/xbrl_reports/delete/<int:report_id>', methods=['POST'])
@login_required
def xbrl_delete(report_id):
    report = XBRLReport.query.get_or_404(report_id)
    if report.xbrl_file_path:
        try:
            abs_path = os.path.join(current_app.root_path, report.xbrl_file_path)
            if os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    db.session.delete(report)
    db.session.commit()
    flash('XBRL Report deleted successfully!', 'success')
    return redirect(url_for('main.xbrl_reports'))

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


@main_bp.route('/smart/challan-management', methods=['GET', 'POST'])
@login_required
def challan_management():
    form = ChallanManagementForm()
    query = ChallanManagement.query

    if form.validate_on_submit():
        if form.status.data:
            query = query.filter_by(status=form.status.data)

    challans = query.order_by(ChallanManagement.created_at.desc()).all()

        # 📊 Metric calculations
    total_challans = len(challans)
    pending_amount = sum(c.amount for c in challans if c.status.lower() != 'cleared')
    cleared_amount = sum(c.amount for c in challans if c.status.lower() == 'cleared')

    return render_template(
        'smart/challan_management.html',
        challans=challans,
        form=form,
        total_challans=total_challans,
        pending_amount=pending_amount,
        cleared_amount=cleared_amount
    )

@main_bp.route('/smart/challan-management/new', methods=['GET', 'POST'])
@login_required
def new_challan():
    form = ChallanManagementForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

    if form.validate_on_submit():
        challan = ChallanManagement(
            client_id=form.client_id.data,
            challan_number=form.challan_number.data,
            challan_type=form.challan_type.data,
            tax_type=form.tax_type.data,
            assessment_year=form.assessment_year.data,
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            bank_name=form.bank_name.data,
            bank_branch=form.bank_branch.data,
            bsr_code=form.bsr_code.data,
            serial_number=form.serial_number.data,
            status=form.status.data,
            remarks=form.remarks.data,
            created_by=current_user.id
        )
        
        db.session.add(challan)
        db.session.commit()
        flash("Challan created successfully!", "success")
        return redirect(url_for('main.challan_management'))

    return render_template('smart/challan_form.html', form=form, title='New Challan')


@main_bp.route('/smart/challan-management/edit/<int:challan_id>', methods=['GET', 'POST'])
@login_required
def edit_challan(challan_id):
    challan = ChallanManagement.query.get_or_404(challan_id)
    form = ChallanManagementForm(obj=challan)
    form.client_id.choices = [(c.id, c.name) for c in Client.query.all()]

    if form.validate_on_submit():
        form.populate_obj(challan)
        db.session.commit()
        flash('Challan updated successfully!', 'success')
        return redirect(url_for('main.challan_management'))

    return render_template('smart/challan_form.html', form=form, title='Edit Challan')

@main_bp.route('/smart/challan-management/delete/<int:challan_id>', methods=['POST'])
@login_required
def delete_challan(challan_id):
    challan = ChallanManagement.query.get_or_404(challan_id)
    db.session.delete(challan)
    db.session.commit()
    flash('Challan deleted successfully!', 'success')
    return redirect(url_for('main.challan_management'))

@main_bp.route('/smart/challan-management/print/<int:challan_id>', methods=['GET'])
@login_required
def print_challan(challan_id):
    challan = ChallanManagement.query.get_or_404(challan_id)
    return render_template('smart/challan_print.html', challan=challan)

""" @main_bp.route('/print-pdf/<int:id>')
def print_pdf(id):
    challan = ChallanManagement.query.get_or_404(id)
    rendered = render_template('challan_print.html', challan=challan, now=datetime.now)
    pdf = HTML(string=rendered).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=challan.pdf'
    return response """


@main_bp.route('/smart/return-tracker')
@login_required
def return_tracker():
    filter_type = request.args.get('filter', '')
    clients = Client.query.order_by(Client.name).all()

    if filter_type:
        # Match entries like 'ITR-1', 'ITR-2', etc., using LIKE
        returns = ReturnTracker.query.filter(ReturnTracker.return_type.like(f"{filter_type}%"))\
                                     .order_by(ReturnTracker.due_date).all()
    else:
        returns = ReturnTracker.query.order_by(ReturnTracker.due_date).all()

    # Status counters
    pending_count = ReturnTracker.query.filter_by(status='Pending').count()
    filed_count = ReturnTracker.query.filter_by(status='Filed').count()
    overdue_count = ReturnTracker.query.filter_by(status='Overdue').count()
    processed_count = ReturnTracker.query.filter_by(status='Processed').count()

    return render_template(
        'smart/return_tracker.html',
        returns=returns,
        clients=clients,
        pending_count=pending_count,
        filed_count=filed_count,
        overdue_count=overdue_count,
        processed_count=processed_count,
        filter_type=filter_type  # Pass the filter value to keep dropdown selection
    )

@main_bp.route('/smart/add-return', methods=['POST'])
@login_required
def add_return():
    try:
        return_id = request.form.get('return_id')
        client_id = request.form.get('client_id')
        return_type = request.form.get('return_type')
        period = request.form.get('period')
        due_date = request.form.get('due_date')
        filing_date = request.form.get('filing_date')
        status = request.form.get('status')
        ack_number = request.form.get('acknowledgment_number')
        remarks = request.form.get('remarks')

        due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None
        filing_date = datetime.strptime(filing_date, '%Y-%m-%d').date() if filing_date else None

        if return_id:
            # Edit existing
            rtn = ReturnTracker.query.get(int(return_id))
            if not rtn:
                flash("Return not found.", "danger")
                return redirect(url_for('main.return_tracker'))
        else:
            # New
            rtn = ReturnTracker()
            db.session.add(rtn)

        # Common fields
        rtn.client_id = int(client_id)
        rtn.return_type = return_type
        rtn.period = period
        rtn.due_date = due_date
        rtn.filing_date = filing_date
        rtn.status = status
        rtn.acknowledgment_number = ack_number
        rtn.remarks = remarks

        db.session.commit()
        flash("Return saved successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving return: {str(e)}", "danger")

    return redirect(url_for('main.return_tracker'))

@main_bp.route('/smart/auto-reminders')
@login_required
def auto_reminders():
    settings = AutoReminderSetting.query.filter_by(user_id=current_user.id).first()

    reminders = Reminder.query.filter_by(created_by=current_user.id, auto_created=True).all()

    formatted_rules = []
    active_count = 0

    for r in reminders:
        if r.status == 'Active':
            active_count += 1
        formatted_rules.append({
            'title': r.title,
            'reminder_type': r.reminder_type,
            'days_before': (datetime.utcnow() - r.reminder_date).days,
            'method': r.description,
            'method_class': 'bg-info' if 'email' in r.description.lower() else 'bg-warning',
            'field': r.reminder_type.lower()
        })

    return render_template(
        'smart/auto_reminders.html',
        settings=settings,
        rules=formatted_rules,
        active_count=active_count
    )

@main_bp.route('/smart/auto-reminders/add', methods=['POST'])
@login_required
def save_auto_reminder():
    name = request.form.get('rule_name')
    trigger = request.form.get('trigger_type')
    days = int(request.form.get('days', 0))
    day_type = request.form.get('dayType')
    method = request.form.get('method')
    status = request.form.get('status', 'Active')

    message = request.form.get('messageTemplate', '')

    base_date = datetime.utcnow()
    if day_type == 'before':
        reminder_date = base_date - timedelta(days=days)
    elif day_type == 'after':
        reminder_date = base_date + timedelta(days=days)
    else:
        reminder_date = base_date

    reminder = Reminder(
        created_by=current_user.id,
        title=name,
        description=message or method,
        reminder_type=trigger,
        reminder_date=reminder_date,
        status = status.capitalize(),
        auto_created=True
    )

    db.session.add(reminder)
    db.session.commit()

    return redirect(url_for('main.auto_reminders'))


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

@main_bp.route('/crm/client-notes', methods=['GET', 'POST'])
@login_required
def client_notes():
    if request.method == 'POST':
        try:
            client_id = request.form['client_id']
            note_type = request.form['note_type']
            priority = request.form['priority']
            title = request.form['title']
            content = request.form['content']

            # ✅ Safely convert follow-up date string to Python date object
            follow_up_date_str = request.form.get('follow_up_date')
            follow_up_date = datetime.strptime(follow_up_date_str, '%Y-%m-%d').date() if follow_up_date_str else None

            new_note = ClientNote(
                client_id=client_id,
                note_type=note_type,
                priority=priority,
                follow_up_date=follow_up_date,
                title=title,
                content=content,
                created_by=current_user.id
            )

            db.session.add(new_note)
            db.session.commit()
            flash("Client note added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving note: {e}", "danger")

        return redirect(url_for('main.client_notes'))

    # GET: Handle filters
    note_type = request.args.get('note_type', '')
    client_id = request.args.get('client_id', '')

    notes_query = ClientNote.query.order_by(ClientNote.created_at.desc())

    if note_type:
        notes_query = notes_query.filter(ClientNote.note_type == note_type)
    if client_id:
        notes_query = notes_query.filter(ClientNote.client_id == int(client_id))

    notes = notes_query.all()
    clients = Client.query.all()

    return render_template('crm/client_notes.html', notes=notes, clients=clients, note_type=note_type)

@main_bp.route('/crm/client-notes/delete/<int:note_id>', methods=['POST'])
@login_required
def delete_client_note(note_id):
    note = ClientNote.query.get_or_404(note_id)
    
    try:
        db.session.delete(note)
        db.session.commit()
        flash("Client note deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting note: {e}", "danger")
    
    return redirect(url_for('main.client_notes'))


import json

# Utility functions
def get_service_color(service):
    return {
        'ITR Filing': 'primary',
        'Audit': 'info',
        'GST Returns': 'warning',
        'ROC Compliance': 'success'
    }.get(service, 'secondary')

def get_progress_color(progress):
    if progress >= 90:
        return 'success'
    elif progress >= 60:
        return 'warning'
    elif progress > 0:
        return 'danger'
    return 'secondary'

def get_status_color(status):
    return {
        'Complete': 'success',
        'In Progress': 'warning',
        'Overdue': 'danger'
    }.get(status, 'secondary')

def get_actions(status):
    if status == 'Complete':
        return [
            {'icon': 'eye', 'color': 'primary', 'tooltip': 'View Details'},
            {'icon': 'download', 'color': 'secondary', 'tooltip': 'Download Report'}
        ]
    elif status == 'In Progress':
        return [
            {'icon': 'eye', 'color': 'primary', 'tooltip': 'View Details'},
            {'icon': 'check', 'color': 'success', 'tooltip': 'Mark Complete'},
            {'icon': 'bell', 'color': 'info', 'tooltip': 'Send Reminder'}
        ]
    elif status == 'Overdue':
        return [
            {'icon': 'eye', 'color': 'primary', 'tooltip': 'View Details'},
            {'icon': 'phone', 'color': 'danger', 'tooltip': 'Urgent Follow Up'}
        ]
    return []


# View Route
@main_bp.route('/crm/document-checklists')
@login_required
def document_checklists():
    raw_checklists = DocumentChecklist.query.order_by(DocumentChecklist.due_date).all()
    clients = Client.query.order_by(Client.name).all()

    checklists = []
    for c in raw_checklists:
        # Safely parse JSON fields
        required_docs = json.loads(c.documents_required or "[]")
        received_docs = json.loads(c.documents_received or "[]")
        total = len(required_docs)
        received = len(received_docs)
        progress = int((received / total) * 100) if total else 0

        checklist = {
            'id': c.id,
            'client': c.client.name if c.client else 'N/A',
            'description': c.checklist_name,
            'service': c.service_type,
            'service_color': get_service_color(c.service_type),
            'due_date': c.due_date.strftime('%d-%m-%Y') if c.due_date else 'N/A',
            'overdue': c.due_date < date.today() and progress < 100 if c.due_date else False,
            'progress': progress,
            'progress_color': get_progress_color(progress),
            'received': received,
            'total': total,
            'status': c.status,
            'status_color': get_status_color(c.status),
            'actions': get_actions(c.status)
        }

        checklists.append(checklist)

    return render_template('crm/document_checklists.html', checklists=checklists, clients=clients)


# Form Submission Route
@main_bp.route('/create_checklist', methods=['POST'])
@login_required
def create_checklist():
    try:
        form = request.form

        client_id = int(form.get("client"))
        checklist_name = form.get("description")
        service_type = form.get("service")
        due_date = datetime.strptime(form.get("due_date"), "%Y-%m-%d").date()

        # Get documents
        documents = request.form.getlist("documents")         # Checked default documents
        custom_docs = request.form.getlist("custom_docs")     # All custom added documents

        all_documents = documents + custom_docs
        total_docs = len(all_documents)
        checked_docs = len(documents)  # Assume only default docs are initially checked
        percentage = int((checked_docs / total_docs) * 100) if total_docs else 0

        new_checklist = DocumentChecklist(
            client_id=client_id,
            checklist_name=checklist_name,
            service_type=service_type,
            documents_required=json.dumps(all_documents),
            documents_received=json.dumps(documents),
            completion_percentage=percentage,
            due_date=due_date,
            status="Pending",
            created_by=current_user.id
        )

        db.session.add(new_checklist)
        db.session.commit()

        flash("Checklist created successfully!", "success")
        return redirect(url_for("main.document_checklists"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error creating checklist: {e}", "danger")
        return redirect(url_for("main.document_checklists"))


@main_bp.route('/delete_checklist/<int:checklist_id>', methods=['POST'])
@login_required
def delete_checklist(checklist_id):
    try:
        checklist = DocumentChecklist.query.get_or_404(checklist_id)
        db.session.delete(checklist)
        db.session.commit()
        flash("Checklist deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting checklist: {e}", "danger")
    return redirect(url_for("main.document_checklists"))


@main_bp.route('/crm/communications')
@login_required
def communications():
    # Communication Logs
    logs = CommunicationLog.query.order_by(CommunicationLog.sent_at.desc()).limit(100).all()
    clients = Client.query.filter_by(status='Active').all()  # assuming a Client model exists

    # Stats
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    sms_count = CommunicationLog.query.filter(
        CommunicationLog.communication_type == 'SMS',
        func.extract('month', CommunicationLog.sent_at) == current_month,
        func.extract('year', CommunicationLog.sent_at) == current_year
    ).count()

    email_count = CommunicationLog.query.filter(
        CommunicationLog.communication_type == 'email',
        func.extract('month', CommunicationLog.sent_at) == current_month,
        func.extract('year', CommunicationLog.sent_at) == current_year
    ).count()

    auto_reminders = AutoReminderSetting.query.filter_by(user_id=current_user.id).first()

    templates_count = SMSTemplate.query.filter_by(is_active=True).count() + \
                      EmailTemplate.query.filter_by(is_active=True).count()

    # Load templates
    sms_templates = SMSTemplate.query.all()
    email_templates = EmailTemplate.query.all()

    email_config = Configuration.query.filter_by(user_id=current_user.id, type='email').first()

    # Simulated configuration statuses (you would fetch these from settings/config DB table)
    config = {
        "twilio_status": "NotConfigured",  # handle this later
        "smtp_status": email_config.status if email_config else "NotConfigured"
    }

    smsForm = SMSTemplateForm()

    return render_template('crm/communications.html',
                           smsForm=smsForm,
                           email_form = EmailSetupForm(),
                           logs=logs,
                           clients=clients,
                           sms_templates=sms_templates,
                           email_templates=email_templates,
                           sms_count=sms_count,
                           email_count=email_count,
                           auto_reminders=auto_reminders,
                           templates_count=templates_count,
                           config=config,
                           timedelta=timedelta)

@main_bp.route('/crm/setup-email', methods=['POST'])
@login_required
def setup_email():
    form = EmailSetupForm()
    if form.validate_on_submit():
        existing = Configuration.query.filter_by(user_id=current_user.id, type='email').first()
        if not existing:
            existing = Configuration(user_id=current_user.id, type='email')
        
        existing.email_service = form.email_service.data
        existing.email_address = form.email_address.data
        existing.email_password = form.email_password.data  # encrypt this if storing
        existing.smtp_server = form.smtp_server.data
        existing.smtp_port = form.smtp_port.data
        existing.status = 'Configured'

        db.session.add(existing)
        db.session.commit()
        flash('Email configuration saved.', 'success')
    else:
        flash('Error in configuration form.', 'danger')

    return redirect(url_for('main.communications'))

@main_bp.route('/crm/reset-email-config', methods=['POST'])
@login_required
def reset_email_config():
    config = Configuration.query.filter_by(user_id=current_user.id, type='email').first()
    if config:
        config.status = 'NotConfigured'
        db.session.commit()
        flash('Email configuration has been reset.', 'info')
    else:
        flash('No configuration found to reset.', 'warning')
    return redirect(url_for('main.communications'))

@main_bp.route('/crm/send-email', methods=['POST'])
@login_required
def send_email():
    import smtplib
    from email.message import EmailMessage
    # Check SMTP config for current user
    smtp_config = Configuration.query.filter_by(user_id=current_user.id, type='email', status='Configured').first()
    if not smtp_config:
        flash('Email configuration not found. Please configure SMTP settings before sending emails.', 'warning')
        return redirect(url_for('main.communications'))

    # Extract form data
    message_type = request.form.get('message_type')  # should be 'email'
    subject = request.form.get('subject')
    body = request.form.get('message')
    template_id = request.form.get('template_id')
    recipient_ids = request.form.getlist('recipients')

    # Prepare recipients
    if 'all' in recipient_ids:
        clients = Client.query.filter_by(status='Active').all()
    else:
        clients = Client.query.filter(Client.id.in_(recipient_ids)).all()

    template_name = EmailTemplate.query.get_or_404(template_id).template_name

    # Send emails
    try:
        with smtplib.SMTP(smtp_config.smtp_server, smtp_config.smtp_port) as server:
            server.starttls()
            server.login(smtp_config.email_address, smtp_config.email_password)

            for client in clients:
                # Replace placeholders in subject and body
                personalized_subject = substitute_vars(subject, client)
                personalized_body = substitute_vars(body, client)

                msg = EmailMessage()
                msg['From'] = smtp_config.email_address
                msg['To'] = client.email  # assumes Client model has .email
                msg['Subject'] = personalized_subject
                msg.set_content(personalized_body)

                server.send_message(msg)

                # Log communication
                log = CommunicationLog(
                    client_id=client.id,
                    communication_type=message_type,
                    subject=personalized_subject,
                    message=personalized_body,
                    recipient=client.name,
                    status='Sent',
                    template_used=template_name or 'Custom',
                    created_by=current_user.id
                )
                db.session.add(log)

            db.session.commit()
        flash(f"Email sent to {len(clients)} client(s) successfully!", 'success')
    
    except smtplib.SMTPAuthenticationError:
        flash('Authentication failed. Please check your email address and password.', 'danger')
    except smtplib.SMTPException as e:
        flash(f"SMTP error occurred: {str(e)}", 'danger')
    except Exception as e:
        flash(f"Unexpected error occurred: {str(e)}", 'danger')

    return redirect(url_for('main.communications'))

def substitute_vars(template, client):
    # Fetch the most recent OutstandingFee entry for the client (if exists)
    fee = OutstandingFee.query.filter_by(client_id=client.id).order_by(OutstandingFee.due_date.desc()).first()

    # Replace variables with client-specific values
    vars = {
        '{client_name}': client.name,
        '{due_date}': fee.due_date.strftime('%d-%m-%Y') if fee and fee.due_date else '',
        '{amount}': str(fee.amount) if fee and fee.amount else '',
        '{status}': fee.status if fee and fee.status else '',
        '{invoice_number}': fee.invoice_number if fee and fee.invoice_number else ''
    }
    for var, value in vars.items():
        template = template.replace(var, value)
    return template

@main_bp.route('/crm/delete_log/<int:id>', methods=['POST'])
@login_required
def delete_log(id):
    log = CommunicationLog.query.get_or_404(id)

    try:
        db.session.delete(log)
        db.session.commit()
        flash('Log deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting log: {str(e)}', 'danger')

    return redirect(url_for('main.communications'))

@main_bp.route('/crm/auto-reminders/update', methods=['POST'])
@login_required
def update_auto_reminders():
    # Fetch existing settings or create new one
    setting = AutoReminderSetting.query.filter_by(user_id=current_user.id).first()
    
    if not setting:
        setting = AutoReminderSetting(user_id=current_user.id)
        db.session.add(setting)

    # Update values from checkboxes
    setting.itr = bool(request.form.get('autoITR'))
    setting.gst = bool(request.form.get('autoGST'))
    setting.birthday = bool(request.form.get('autoBirthday'))
    setting.fees = bool(request.form.get('autoFees'))

    db.session.commit()
    flash('Auto reminder settings updated successfully.', 'success')
    return redirect(url_for('main.communications'))

@main_bp.route('/crm/templates/add', methods=['POST'])
@login_required
def add_template():
    sms_form = SMSTemplateForm()
    email_form = EmailTemplateForm()

    if request.form.get('template_type') == 'email':
        form = email_form
    else:
        form = sms_form

    if form.validate_on_submit():
        is_active = form.is_active.data
        created_by = current_user.id

        if request.form.get('template_type') == 'email':
            template = EmailTemplate(
                template_name=form.template_name.data,
                template_type=form.template_type.data,
                subject=form.subject.data,
                content=form.content.data,
                is_active=is_active,
                created_by=created_by
            )
        else:
            template = SMSTemplate(
                template_name=form.template_name.data,
                template_type=form.template_type.data,
                content=form.content.data,
                is_active=is_active,
                created_by=created_by
            )

        db.session.add(template)
        db.session.commit()
        flash('Template added successfully!', 'success')
    else:
        flash('Form validation failed. Please check your input.', 'danger')

    return redirect(url_for('main.communications'))

@main_bp.route('/crm/template/edit', methods=['POST'])
@login_required
def edit_template():
    template_type = request.form.get('template_type')
    
    if template_type == 'email':
        form = EmailTemplateForm()
        template = EmailTemplate.query.get(request.form.get('template_id'))
    else:
        form = SMSTemplateForm()
        template = SMSTemplate.query.get(request.form.get('template_id'))

    print(request.form.get('template_id'), request.form.get('template_type'))

    if template and form.validate_on_submit():
        template.template_name = form.template_name.data
        template.template_type = form.template_type.data
        template.content = form.content.data
        template.is_active = form.is_active.data

        if template_type == 'email':
            template.subject = form.subject.data

        db.session.commit()
        flash('Template updated successfully!', 'success')
    else:
        flash('Template not found or validation failed.', 'danger')

    return redirect(url_for('main.communications'))

@main_bp.route('/crm/template/delete', methods=['POST'])
@login_required
def delete_template():
    template_type = request.form.get('template_type')
    template_id = request.form.get('template_id')

    if template_type == 'sms':
        template = SMSTemplate.query.get(template_id)
    else:
        template = EmailTemplate.query.get(template_id)

    if template:
        db.session.delete(template)
        db.session.commit()
        flash('Template deleted successfully.', 'success')
    else:
        flash('Template not found.', 'danger')

    return redirect(url_for('main.communications'))