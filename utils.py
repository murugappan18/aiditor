import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'xbrl', 'xml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

""" def save_uploaded_file(file):
    '''Save uploaded file and return file path and size'''
    if file and allowed_file(file.filename):
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        return file_path, file_size
    
    return None, None """

""" def save_uploaded_file(file, subfolder=''):
    '''Save uploaded file into a subfolder and return file path and size'''
    if file and allowed_file(file.filename):
        # Build upload directory with optional subfolder
        upload_dir = os.path.join(current_app.root_path, 'uploads', subfolder)
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        file_size = os.path.getsize(file_path)
        return file_path, file_size

    return None, None """

def save_uploaded_file(file, subfolder=''):
    """Save uploaded file into a subfolder and return relative file path and size"""
    print("Uploaded filename:", file.filename)

    if file and allowed_file(file.filename):
        print("File is allowed. Proceeding to save.")
        upload_dir = os.path.join(current_app.root_path, 'uploads', subfolder)
        os.makedirs(upload_dir, exist_ok=True)

        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)

        file_size = os.path.getsize(file_path)

        rel_path = os.path.join('uploads', subfolder, unique_filename)
        return rel_path, file_size

    print("File is NOT allowed.")
    return None, None

def format_currency(amount):
    """Format amount as Indian currency"""
    if amount is None:
        return "₹0.00"
    return f"₹{amount:,.2f}"

def format_date(date_obj):
    """Format date for display"""
    if date_obj is None:
        return ""
    return date_obj.strftime("%d/%m/%Y")

def get_financial_year(date_obj=None):
    """Get financial year for given date or current date"""
    from datetime import date
    
    if date_obj is None:
        date_obj = date.today()
    
    if date_obj.month >= 4:  # April onwards
        return f"{date_obj.year}-{date_obj.year + 1}"
    else:  # January to March
        return f"{date_obj.year - 1}-{date_obj.year}"

def generate_invoice_number(service_type="GEN"):
    """Generate unique invoice number"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{service_type}-{timestamp}"
