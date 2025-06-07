from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, TextAreaField, DateField, FloatField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange
from wtforms.widgets import TextArea

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField('Password', validators=[DataRequired()])

class ClientForm(FlaskForm):
    name = StringField('Client Name', validators=[DataRequired(), Length(max=200)])
    pan = StringField('PAN', validators=[Optional(), Length(min=10, max=10)])
    gstin = StringField('GSTIN', validators=[Optional(), Length(min=15, max=15)])
    email = StringField('Email', validators=[Optional(), Email()])
    phone = StringField('Phone', validators=[Optional(), Length(max=15)])
    address = TextAreaField('Address', validators=[Optional()])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    incorporation_date = DateField('Incorporation Date', validators=[Optional()])
    client_type = SelectField('Client Type', choices=[
        ('Individual', 'Individual'),
        ('Company', 'Company'),
        ('Partnership', 'Partnership'),
        ('LLP', 'LLP'),
        ('Trust', 'Trust'),
        ('Society', 'Society')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], default='Active')

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
