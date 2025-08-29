from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import StringField, TextAreaField, SelectField, SubmitField, BooleanField, DateField, DecimalField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Optional, Length, ValidationError
from wtforms.widgets import ListWidget, CheckboxInput
from app.models import Company, ClientContact, MediaGroup

class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class CompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    vat_code = StringField('VAT Code', validators=[Optional(), Length(max=50)])
    registration_number = StringField('Registration Number', validators=[Optional(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional()])
    bank_account = StringField('Bank Account', validators=[Optional(), Length(max=100)])
    agency_fees = TextAreaField('Agency Fees', validators=[Optional()])
    parent_company_id = SelectField('Parent Company', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')], 
                        validators=[DataRequired()])
    submit = SubmitField('Save Company')
    
    def __init__(self, company=None, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
        self.company = company
    
    def validate_vat_code(self, vat_code):
        if vat_code.data:
            query = Company.query.filter_by(vat_code=vat_code.data)
            if self.company:
                query = query.filter(Company.id != self.company.id)
            if query.first():
                raise ValidationError('This VAT code is already registered.')

class AgreementForm(FlaskForm):
    type = SelectField('Agreement Type', choices=[
        ('service', 'Service Agreement'),
        ('data', 'Data Agreement'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    valid_until = DateField('Valid Until', format='%Y-%m-%d', validators=[Optional()])
    file = FileField('Agreement File (PDF)', validators=[
        FileAllowed(['pdf'], 'Only PDF files are allowed!')
    ])
    submit = SubmitField('Upload Agreement')

class BrandForm(FlaskForm):
    name = StringField('Brand Name', validators=[DataRequired(), Length(max=200)])
    company_id = SelectField('Company', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'Inactive')], 
                        validators=[DataRequired()])
    submit = SubmitField('Save Brand')
    
    def __init__(self, *args, **kwargs):
        super(BrandForm, self).__init__(*args, **kwargs)
        self.company_id.choices = [(c.id, c.name) for c in Company.query.filter_by(status='active').order_by(Company.name).all()]

class SubbrandForm(FlaskForm):
    name = StringField('Subbrand Name', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('Add Subbrand')

class ClientContactForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=100)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    linkedin_url = StringField('LinkedIn URL', validators=[Optional(), Length(max=200)])
    birthday_month = SelectField('Birthday Month', coerce=int, validators=[Optional()], choices=[
        (0, '-- Select Month --'),
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ])
    birthday_day = IntegerField('Birthday Day', validators=[Optional()])
    responsibility_description = TextAreaField('Responsibility Description', validators=[Optional()])
    should_get_gift = BooleanField('Should Get Gift')
    receive_newsletter = BooleanField('Receive Newsletter')
    status = SelectField('Status', choices=[('active', 'Active'), ('passive', 'Passive')], 
                        validators=[DataRequired()])
    brands = MultiCheckboxField('Associated Brands', coerce=int)
    submit = SubmitField('Save Contact')
    
    def __init__(self, contact=None, *args, **kwargs):
        super(ClientContactForm, self).__init__(*args, **kwargs)
        self.contact = contact
        from app.models import Brand
        brands = Brand.query.outerjoin(Company).order_by(Company.name, Brand.name).all()
        self.brands.choices = [(b.id, f"{b.name} ({b.company.name if b.company else 'No Company'})") for b in brands]
    
    def validate_email(self, email):
        query = ClientContact.query.filter_by(email=email.data)
        if self.contact:
            query = query.filter(ClientContact.id != self.contact.id)
        if query.first():
            raise ValidationError('This email is already registered.')

class BrandTeamForm(FlaskForm):
    team_members = MultiCheckboxField('Team Members', coerce=int)
    key_responsible_id = SelectField('Key Responsible Person', validators=[Optional()])
    submit = SubmitField('Save Team Assignment')
    
    def __init__(self, *args, **kwargs):
        super(BrandTeamForm, self).__init__(*args, **kwargs)
        from app.models import User
        active_users = User.query.filter_by(is_active=True).order_by(User.last_name, User.first_name).all()
        self.team_members.choices = [(u.id, f"{u.first_name} {u.last_name} ({u.role.replace('_', ' ').title()})") for u in active_users]
        self.key_responsible_id.choices = [(0, '-- Select Key Responsible --')] + [(u.id, f"{u.first_name} {u.last_name}") for u in active_users]

class CommitmentForm(FlaskForm):
    media_group_id = SelectField('Media Group', coerce=int, validators=[DataRequired()])
    year = IntegerField('Year', validators=[DataRequired()])
    amount = DecimalField('Commitment Amount', places=2, validators=[DataRequired()])
    currency = SelectField('Currency', choices=[('EUR', 'EUR'), ('USD', 'USD'), ('GBP', 'GBP')], 
                          default='EUR', validators=[DataRequired()])
    submit = SubmitField('Save Commitment')
    
    def __init__(self, *args, **kwargs):
        super(CommitmentForm, self).__init__(*args, **kwargs)
        self.media_group_id.choices = [(mg.id, mg.name) for mg in MediaGroup.query.order_by(MediaGroup.name).all()]

class StatusUpdateForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[DataRequired()])
    evaluation = SelectField('Evaluation', choices=[
        ('perfect', 'Perfect'),
        ('medium', 'Medium'),
        ('risk', 'Risk')
    ], validators=[DataRequired()])
    submit = SubmitField('Add Status Update')

class MediaGroupForm(FlaskForm):
    name = StringField('Media Group Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Save Media Group')

class PlanningInfoForm(FlaskForm):
    comments = TextAreaField('Planning Comments', validators=[DataRequired()])
    attachments = MultipleFileField('Attachments', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'], 
                    'Allowed file types: PDF, Word, PowerPoint, Excel, Images')
    ])
    submit = SubmitField('Add Planning Info')

class KeyMeetingForm(FlaskForm):
    date = DateField('Meeting Date', format='%Y-%m-%d', validators=[DataRequired()])
    comment = TextAreaField('Meeting Details', validators=[DataRequired()])
    attachments = MultipleFileField('Attachments (Presentations, etc.)', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif'], 
                    'Allowed file types: PDF, Word, PowerPoint, Excel, Images')
    ])
    submit = SubmitField('Add Meeting')

class KeyLinkForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), Length(max=500)])
    comment = StringField('Description', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Add Link')

class GiftForm(FlaskForm):
    year = IntegerField('Year', validators=[DataRequired()])
    gift_description = StringField('Gift Description', validators=[DataRequired(), Length(max=255)])
    gift_value = DecimalField('Gift Value (EUR)', places=2, validators=[Optional()])
    sent_date = DateField('Date Sent', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Gift')

class TaskTemplateForm(FlaskForm):
    name = StringField('Task Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Task Template')

class BrandTaskForm(FlaskForm):
    task_template_id = SelectField('Task', coerce=int, validators=[DataRequired()])
    frequency = SelectField('Frequency', choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly (every 3 months)'),
        ('twice_yearly', 'Twice a Year (every 6 months)'),
        ('yearly', 'Once a Year')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Save Task')

class TaskCompletionForm(FlaskForm):
    completion_date = DateField('Completion Date', format='%Y-%m-%d', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Mark as Complete')

class SubcompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    vat_code = StringField('VAT Code', validators=[Optional(), Length(max=50)])
    registration_number = StringField('Registration Number', validators=[Optional(), Length(max=100)])
    address = TextAreaField('Address', validators=[Optional()])
    bank_account = StringField('Bank Account', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Save Subcompany')

class InvoiceForm(FlaskForm):
    company_id = SelectField('Invoice To', coerce=int, validators=[DataRequired()])
    invoice_date = DateField('Invoice Date', format='%Y-%m-%d', validators=[DataRequired()])
    short_info = TextAreaField('Description', validators=[Optional()])
    total_amount = DecimalField('Total Amount (EUR)', places=2, validators=[DataRequired()])
    files = MultipleFileField('Invoice Files (PDF/Excel)', validators=[
        FileAllowed(['pdf', 'xlsx', 'xls'], 'Only PDF and Excel files are allowed!')
    ])
    submit = SubmitField('Save Invoice')