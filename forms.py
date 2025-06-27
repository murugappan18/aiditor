from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, SubmitField, TextAreaField, DateField, FloatField, IntegerField, BooleanField, HiddenField
from wtforms.validators import DataRequired, InputRequired, Email, Length, Optional, NumberRange, Regexp
from wtforms.widgets import TextArea


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])

class ClientForm(FlaskForm):
    name = StringField('Client Name', validators=[
        DataRequired(message="Client name is required"),
        Length(max=200, message="Name must be under 200 characters")
    ])

    pan = StringField('PAN', validators=[
        Optional(),
        Length(min=10, max=10, message="PAN must be 10 characters"),
        Regexp(r'^[A-Z]{5}[0-9]{4}[A-Z]$', message="PAN format is invalid (e.g. ABCDE1234F)")
    ])

    gstin = StringField('GSTIN', validators=[
        Optional(),
        Length(min=15, max=15, message="GSTIN must be 15 characters"),
        Regexp(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$', message="GSTIN format is invalid")
    ])

    email = StringField('Email', validators=[
        Optional(),
        Email(message="Invalid email address")
    ])

    phone = StringField('Phone', validators=[
        Optional(),
        Regexp(r'^[6-9]\d{9}$', message="Enter a valid 10-digit phone number")
    ])

    address = TextAreaField('Address', validators=[
        Optional(),
        Length(max=500, message="Address too long")
    ])

    date_of_birth = DateField('Date of Birth', validators=[Optional()])

    incorporation_date = DateField('Incorporation Date', validators=[Optional()])

    client_type = SelectField('Client Type', choices=[
        ('Individual', 'Individual'),
        ('Company', 'Company'),
        ('Partnership', 'Partnership'),
        ('LLP', 'LLP'),
        ('Trust', 'Trust'),
        ('Society', 'Society')
    ], validators=[DataRequired(message="Client type is required")])

    status = SelectField('Status', choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], default='Active', validators=[DataRequired(message="Status is required")])

class IncomeTaxReturnForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    assessment_year = StringField('Assessment Year', validators=[DataRequired(), Length(max=10)])
    return_type = SelectField('Return Type', choices=[
        ('ITR-1', 'ITR-1'),
        ('ITR-2', 'ITR-2'),
        ('ITR-3', 'ITR-3'),
        ('ITR-4', 'ITR-4'),
        ('ITR-5', 'ITR-5'),
        ('ITR-6', 'ITR-6'),
        ('ITR-7', 'ITR-7')
    ], validators=[DataRequired()])
    filing_date = DateField('Filing Date', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    total_income = FloatField('Total Income', validators=[Optional(), NumberRange(min=0)])
    tax_payable = FloatField('Tax Payable', validators=[Optional(), NumberRange(min=0)])
    refund_amount = FloatField('Refund Amount', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Filed', 'Filed'),
        ('Processed', 'Processed')
    ], default='Pending')
    acknowledgment_number = StringField('Acknowledgment Number', validators=[Optional(), Length(max=50)])

class TDSReturnForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    tan = StringField('TAN', validators=[DataRequired(), Length(min=10, max=10)])
    quarter = SelectField('Quarter', choices=[
        ('Q1', 'Q1 (Apr-Jun)'),
        ('Q2', 'Q2 (Jul-Sep)'),
        ('Q3', 'Q3 (Oct-Dec)'),
        ('Q4', 'Q4 (Jan-Mar)')
    ], validators=[DataRequired()])
    financial_year = StringField('Financial Year', validators=[DataRequired(), Length(max=10)])
    return_type = SelectField('Return Type', choices=[
        ('24Q', '24Q'),
        ('26Q', '26Q'),
        ('27Q', '27Q'),
        ('27EQ', '27EQ')
    ], validators=[DataRequired()])
    filing_date = DateField('Filing Date', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    total_tds = FloatField('Total TDS', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Filed', 'Filed'),
        ('Processed', 'Processed')
    ], default='Pending')
    token_number = StringField('Token Number', validators=[Optional(), Length(max=50)])

class GSTReturnForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    gstin = StringField('GSTIN', validators=[DataRequired(), Length(min=15, max=15)])
    return_type = SelectField('Return Type', choices=[
        ('GSTR-1', 'GSTR-1'),
        ('GSTR-3B', 'GSTR-3B'),
        ('GSTR-9', 'GSTR-9'),
        ('GSTR-9C', 'GSTR-9C')
    ], validators=[DataRequired()])
    month_year = StringField('Month/Year', validators=[DataRequired(), Length(max=10)])
    filing_date = DateField('Filing Date', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    total_sales = FloatField('Total Sales', validators=[Optional(), NumberRange(min=0)])
    total_tax = FloatField('Total Tax', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Filed', 'Filed'),
        ('Processed', 'Processed')
    ], default='Pending')
    arn_number = StringField('ARN Number', validators=[Optional(), Length(max=50)])

class EmployeeForm(FlaskForm):
    name = StringField('Employee Name', validators=[DataRequired(), Length(max=200)])
    employee_id = StringField('Employee ID', validators=[Optional(), Length(max=20)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=15)])
    pan = StringField('PAN', validators=[Optional(), Length(min=10, max=10)])
    designation = StringField('Designation', validators=[Optional(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    date_of_joining = DateField('Date of Joining', validators=[Optional()])
    salary = FloatField('Salary', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], default='Active')

class TaskForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    priority = SelectField('Priority', choices=[
        ('Low', 'Low'),
        ('Normal', 'Normal'),
        ('High', 'High')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    task_id = HiddenField()  # for editing existing tasks


class PayrollEntryForm(FlaskForm):
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    month_year = StringField('Month/Year', validators=[DataRequired(), Length(max=10)])
    basic_salary = FloatField('Basic Salary', validators=[DataRequired(), NumberRange(min=0)])
    allowances = FloatField('Allowances', validators=[Optional(), NumberRange(min=0)])
    deductions = FloatField('Deductions', validators=[Optional(), NumberRange(min=0)])
    pf_deduction = FloatField('PF Deduction', validators=[Optional(), NumberRange(min=0)])
    tds_deduction = FloatField('TDS Deduction', validators=[Optional(), NumberRange(min=0)])

class DocumentForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    title = StringField('Document Title', validators=[DataRequired(), Length(max=200)])
    document_type = SelectField('Document Type', choices=[
        ('PAN Card', 'PAN Card'),
        ('Aadhar Card', 'Aadhar Card'),
        ('GST Certificate', 'GST Certificate'),
        ('Income Tax Return', 'Income Tax Return'),
        ('Audit Report', 'Audit Report'),
        ('Bank Statement', 'Bank Statement'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    file = FileField('Upload File', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'], 'Invalid file format!')
    ])
    notes = TextAreaField('Notes', validators=[Optional()])

class OutstandingFeeForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    service_type = StringField('Service Type', validators=[DataRequired(), Length(max=100)])
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0)])
    due_date = DateField('Due Date', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Overdue', 'Overdue')
    ], default='Pending')
    invoice_number = StringField('Invoice Number', validators=[Optional(), Length(max=50)])

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    is_active = BooleanField('Active')

class ReminderForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[Optional()])
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    reminder_date = DateField('Reminder Date', validators=[DataRequired()])
    reminder_type = SelectField('Reminder Type', choices=[
        ('Birthday', 'Birthday'),
        ('Due Date', 'Due Date'),
        ('Follow-up', 'Follow-up'),
        ('Meeting', 'Meeting'),
        ('Other', 'Other')
    ], validators=[DataRequired()])

class ROCFormForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    form_type = SelectField('Form Type', choices=[
        ('AOC-4', 'AOC-4 (Financial Statements)'),
        ('MGT-7', 'MGT-7 (Annual Return)'),
        ('DIR-3 KYC', 'DIR-3 KYC (Director KYC)'),
        ('ADT-1', 'ADT-1 (Auditor Appointment)'),
        ('INC-20A', 'INC-20A (Commencement of Business)'),
        ('INC-22', 'INC-22 (Notice of Situation)'),
        ('MGT-14', 'MGT-14 (Board Resolution)')
    ], validators=[DataRequired()])
    financial_year = StringField('Financial Year', validators=[DataRequired(), Length(max=10)])
    filing_date = DateField('Filing Date', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    acknowledgment_number = StringField('Acknowledgment Number', validators=[Optional(), Length(max=50)])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Filed', 'Filed'),
        ('Approved', 'Approved')
    ], default='Pending')
    filing_fee = FloatField('Filing Fee', validators=[Optional(), NumberRange(min=0)])
    late_fee = FloatField('Late Fee', validators=[Optional(), NumberRange(min=0)])

class SFTReturnForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    financial_year = StringField('Financial Year', validators=[DataRequired(), Length(max=10)])
    form_type = SelectField('Form Type', choices=[
        ('SFT-001', 'SFT-001 (Statement of Financial Transaction)'),
        ('SFT-002', 'SFT-002 (Correction Statement)')
    ], default='SFT-001')
    filing_date = DateField('Filing Date', validators=[Optional()])
    due_date = DateField('Due Date', validators=[Optional()])
    acknowledgment_number = StringField('Acknowledgment Number', validators=[Optional(), Length(max=50)])
    total_transactions = IntegerField('Total Transactions', validators=[Optional(), NumberRange(min=0)])
    total_amount = FloatField('Total Amount', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Filed', 'Filed'),
        ('Processed', 'Processed')
    ], default='Pending')

class BalanceSheetAuditForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    financial_year = StringField('Financial Year', validators=[DataRequired(), Length(max=10)])
    audit_type = SelectField('Audit Type', choices=[
        ('Statutory', 'Statutory Audit'),
        ('Tax', 'Tax Audit'),
        ('Internal', 'Internal Audit'),
        ('Bank', 'Bank Audit'),
        ('Government', 'Government Audit')
    ], validators=[DataRequired()])
    balance_sheet_date = DateField('Balance Sheet Date', validators=[Optional()])
    auditor_name = StringField('Auditor Name', validators=[Optional(), Length(max=200)])
    auditor_membership_no = StringField('Auditor Membership No.', validators=[Optional(), Length(max=20)])
    opinion_type = SelectField('Opinion Type', choices=[
        ('Unqualified', 'Unqualified'),
        ('Qualified', 'Qualified'),
        ('Adverse', 'Adverse'),
        ('Disclaimer', 'Disclaimer of Opinion')
    ], validators=[Optional()])
    key_audit_matters = TextAreaField('Key Findings', validators=[Optional()])
    recommendations = TextAreaField('Recommendations', validators=[Optional()])
    audit_period_from = DateField('Audit Period From', validators=[Optional()])
    audit_period_to = DateField('Audit Period To', validators=[Optional()])
    management_response = TextAreaField('Management Response', validators=[Optional()])
    management_letter_issued = BooleanField('Management Letter Issued')
    status = SelectField('Status', choices=[
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Submitted', 'Submitted')
    ], default='In Progress')

class CMAReportForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    reporting_period = SelectField('Reporting Period', choices=[
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Annual', 'Annual')
    ], validators=[DataRequired()])
    report_date = DateField('Report Date', validators=[Optional()])
    working_capital_limit = FloatField('Working Capital Limit', validators=[Optional(), NumberRange(min=0)])
    utilized_amount = FloatField('Utilized Amount', validators=[Optional(), NumberRange(min=0)])
    cash_credit_limit = FloatField('Cash Credit Limit', validators=[Optional(), NumberRange(min=0)])
    overdraft_limit = FloatField('Overdraft Limit', validators=[Optional(), NumberRange(min=0)])
    bill_discounting_limit = FloatField('Bill Discounting Limit', validators=[Optional(), NumberRange(min=0)])
    letter_of_credit = FloatField('Letter of Credit', validators=[Optional(), NumberRange(min=0)])
    bank_guarantee = FloatField('Bank Guarantee', validators=[Optional(), NumberRange(min=0)])
    inventory_value = FloatField('Inventory Value', validators=[Optional(), NumberRange(min=0)])
    receivables_value = FloatField('Receivables Value', validators=[Optional(), NumberRange(min=0)])
    status = SelectField('Status', choices=[
        ('Draft', 'Draft'),
        ('Final', 'Final'),
        ('Submitted', 'Submitted')
    ], default='Draft')

class AssessmentOrderForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    assessment_year = StringField('Assessment Year', validators=[DataRequired(), Length(max=10)])
    order_type = SelectField('Order Type', choices=[
        ('Scrutiny', 'Scrutiny Assessment'),
        ('Best Judgment', 'Best Judgment Assessment'),
        ('Ex-parte', 'Ex-parte Assessment'),
        ('Penalty', 'Penalty Order'),
        ('Rectification', 'Rectification Order')
    ], validators=[DataRequired()])
    order_date = DateField('Order Date', validators=[Optional()])
    order_number = StringField('Order Number', validators=[Optional(), Length(max=50)])
    total_income_assessed = FloatField('Total Income Assessed', validators=[Optional(), NumberRange(min=0)])
    tax_demanded = FloatField('Tax Demanded', validators=[Optional(), NumberRange(min=0)])
    interest_charged = FloatField('Interest Charged', validators=[Optional(), NumberRange(min=0)])
    penalty_imposed = FloatField('Penalty Imposed', validators=[Optional(), NumberRange(min=0)])
    appeal_filed = BooleanField('Appeal Filed')
    appeal_date = DateField('Appeal Date', validators=[Optional()])
    appeal_number = StringField('Appeal Number', validators=[Optional(), Length(max=50)])
    status = SelectField('Status', choices=[
        ('Received', 'Received'),
        ('Under Review', 'Under Review'),
        ('Appealed', 'Appealed'),
        ('Settled', 'Settled')
    ], default='Received')
    remarks = TextAreaField('Remarks', validators=[Optional()])

class XBRLReportForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    financial_year = StringField('Financial Year', validators=[DataRequired(), Length(max=10)])
    report_type = SelectField('Report Type', choices=[
        ('Balance Sheet', 'Balance Sheet'),
        ('P&L', 'Profit & Loss'),
        ('Cash Flow', 'Cash Flow Statement'),
        ('Notes', 'Notes to Accounts')
    ], validators=[DataRequired()])
    filing_category = SelectField('Filing Category', choices=[
        ('Individual', 'Individual'),
        ('Company', 'Company'),
        ('LLP', 'Limited Liability Partnership'),
        ('Partnership', 'Partnership'),
        ('Trust', 'Trust')
    ], validators=[DataRequired()])
    xbrl_file = FileField('XBRL File', validators=[
        FileAllowed(['xbrl', 'xml'], 'Only XBRL/XML files allowed!')
    ])
    validation_status = SelectField('Validation Status', choices=[
        ('Pending', 'Pending'),
        ('Valid', 'Valid'),
        ('Invalid', 'Invalid')
    ], default='Pending')
    validation_errors = TextAreaField('Validation Errors', validators=[Optional()])
    filing_date = DateField('Filing Date', validators=[Optional()])
    acknowledgment_number = StringField('Acknowledgment Number', validators=[Optional(), Length(max=50)])
    status = SelectField('Status', choices=[
        ('Draft', 'Draft'),
        ('Validated', 'Validated'),
        ('Filed', 'Filed')
    ], default='Draft')

class ChallanManagementForm(FlaskForm):
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    challan_number = StringField('Challan Number', validators=[DataRequired()])
    challan_type = SelectField('Challan Type', choices=[
        ('ITNS 281', 'ITNS 281'),
        ('GST PMT-06', 'GST PMT-06'),
        ('TDS Payment', 'TDS Payment')
    ], validators=[DataRequired()])
    tax_type = SelectField('Tax Type', choices=[
        ('Income Tax', 'Income Tax'),
        ('TDS', 'TDS'),
        ('GST', 'GST')
    ], validators=[DataRequired()])
    assessment_year = StringField('Assessment Year', validators=[Optional()])
    amount = FloatField('Amount', validators=[DataRequired()])
    payment_date = DateField('Payment Date', format='%Y-%m-%d', validators=[Optional()])
    bank_name = StringField('Bank Name', validators=[Optional()])
    bank_branch = StringField('Bank Branch', validators=[Optional()])
    bsr_code = StringField('BSR Code', validators=[Optional()])
    serial_number = StringField('Serial Number', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('Cleared', 'Cleared'),
        ('Failed', 'Failed'),
        ('Bounced', 'Bounced')
    ], default='Pending', validators=[DataRequired()])
    remarks = TextAreaField('Remarks', validators=[Optional()])
    submit = SubmitField('Save')


class SMSTemplateForm(FlaskForm):
    template_id = HiddenField()  # Used for editing
    template_name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    template_type = SelectField('Template Type', choices=[
        ('sms', 'sms')
    ])
    content = TextAreaField('Template Content', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)


class EmailTemplateForm(FlaskForm):
    template_id = HiddenField()
    template_name = StringField('Template Name', validators=[DataRequired(), Length(max=100)])
    template_type = SelectField('Template Type', choices=[
        ('email', 'email')
    ])
    subject = StringField('Email Subject', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Template Content', validators=[DataRequired()])
    is_active = BooleanField('Active', default=True)


class EmailSetupForm(FlaskForm):
    email_service = SelectField('Email Service', choices=[('gmail', 'Gmail'), ('outlook', 'Outlook')], validators=[DataRequired()])
    email_address = StringField('Email Address', validators=[DataRequired(), Email()])
    email_password = PasswordField('Password', validators=[DataRequired()])
    smtp_server = StringField('SMTP Server', render_kw={"readonly": True})
    smtp_port = IntegerField('Port', render_kw={"readonly": True})


class InventoryForm(FlaskForm):
    item_id = HiddenField()  # Used for editing
    item_name = StringField('Item Name', validators=[DataRequired(), Length(max=200)])
    item_code = StringField('Item Code', validators=[Optional(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])
    unit = SelectField('Unit', choices=[
        ('pcs', 'Pieces'),
        ('kg', 'Kilograms'),
        ('ltr', 'Liters'),
        ('mtr', 'Meters'),
        ('box', 'Box'),
        ('set', 'Set'),
        ('other', 'Other')
    ], validators=[DataRequired()], default='pcs')
    unit_price = FloatField('Unit Price', validators=[InputRequired(), NumberRange(min=0)])
    current_stock = IntegerField('Current Stock', validators=[InputRequired(), NumberRange(min=0)])
    minimum_stock = IntegerField('Minimum Stock', validators=[InputRequired(), NumberRange(min=0)])
    location = StringField('Location', validators=[Optional(), Length(max=100)])
    category = SelectField('Category', choices=[
        ('Office Supplies', 'Office Supplies'),
        ('Furniture', 'Furniture'),
        ('Computers & IT', 'Computers & IT'),
        ('Software', 'Software'),
        ('Hardware', 'Hardware'),
        ('Stationery', 'Stationery'),
        ('Others', 'Others')
    ], validators=[DataRequired()], default='Others')
