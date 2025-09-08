from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200))
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    birthday = db.Column(db.Date)
    role = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    team_assignments = db.relationship('BrandTeam', back_populates='team_member', 
                                     foreign_keys='BrandTeam.team_member_id')
    status_updates = db.relationship('StatusUpdate', back_populates='created_by')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Company(db.Model):
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    vat_code = db.Column(db.String(50), unique=True)
    registration_number = db.Column(db.String(100))
    address = db.Column(db.Text)
    bank_account = db.Column(db.String(100))
    agency_fees = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    parent_company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    brands = db.relationship('Brand', back_populates='company', cascade='all, delete-orphan')
    agreements = db.relationship('Agreement', back_populates='company', cascade='all, delete-orphan')
    commitments = db.relationship('Commitment', back_populates='company', cascade='all, delete-orphan')
    parent_company = db.relationship('Company', remote_side=[id], backref='subcompanies')
    invoices = db.relationship('Invoice', back_populates='company', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Company {self.name}>'

class Brand(db.Model):
    __tablename__ = 'brands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    company = db.relationship('Company', back_populates='brands')
    contacts = db.relationship('ClientContact', secondary='brand_contacts', back_populates='brands')
    team_members = db.relationship('BrandTeam', back_populates='brand', cascade='all, delete-orphan')
    planning_info = db.relationship('PlanningInfo', back_populates='brand', 
                                  cascade='all, delete-orphan', order_by='PlanningInfo.created_at.desc()')
    status_updates = db.relationship('StatusUpdate', back_populates='brand', 
                                   cascade='all, delete-orphan')
    key_meetings = db.relationship('KeyMeeting', back_populates='brand', 
                                 cascade='all, delete-orphan', order_by='KeyMeeting.date.desc()')
    key_links = db.relationship('KeyLink', back_populates='brand', 
                              cascade='all, delete-orphan', order_by='KeyLink.created_at.desc()')
    invoices = db.relationship('Invoice', back_populates='brand', cascade='all, delete-orphan')
    brand_tasks = db.relationship('BrandTask', back_populates='brand', cascade='all, delete-orphan')
    subbrands = db.relationship('Subbrand', back_populates='brand', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Brand {self.name}>'

class Subbrand(db.Model):
    __tablename__ = 'subbrands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', back_populates='subbrands')
    
    def __repr__(self):
        return f'<Subbrand {self.name}>'

class ClientContact(db.Model):
    __tablename__ = 'client_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    linkedin_url = db.Column(db.String(200))
    birthday = db.Column(db.Date)
    birthday_month = db.Column(db.Integer)  # 1-12
    birthday_day = db.Column(db.Integer)    # 1-31
    responsibility_description = db.Column(db.Text)
    should_get_gift = db.Column(db.Boolean, default=False)
    receive_newsletter = db.Column(db.Boolean, default=False)
    contact_type = db.Column(db.String(20), default='client')  # client, partner, media
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brands = db.relationship('Brand', secondary='brand_contacts', back_populates='contacts')
    gifts = db.relationship('Gift', back_populates='contact', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ClientContact {self.first_name} {self.last_name}>'

brand_contacts = db.Table('brand_contacts',
    db.Column('brand_id', db.Integer, db.ForeignKey('brands.id'), primary_key=True),
    db.Column('contact_id', db.Integer, db.ForeignKey('client_contacts.id'), primary_key=True)
)

class BrandTeam(db.Model):
    __tablename__ = 'brand_teams'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    team_member_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_key_responsible = db.Column(db.Boolean, default=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', back_populates='team_members')
    team_member = db.relationship('User', back_populates='team_assignments')
    
    __table_args__ = (db.UniqueConstraint('brand_id', 'team_member_id'),)

class Agreement(db.Model):
    __tablename__ = 'agreements'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    valid_until = db.Column(db.Date)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    company = db.relationship('Company', back_populates='agreements')
    uploaded_by = db.relationship('User')

class MediaGroup(db.Model):
    __tablename__ = 'media_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    commitments = db.relationship('Commitment', back_populates='media_group')

class Commitment(db.Model):
    __tablename__ = 'commitments'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    media_group_id = db.Column(db.Integer, db.ForeignKey('media_groups.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), default='EUR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    company = db.relationship('Company', back_populates='commitments')
    media_group = db.relationship('MediaGroup', back_populates='commitments')
    
    __table_args__ = (db.UniqueConstraint('company_id', 'media_group_id', 'year'),)

class PlanningInfo(db.Model):
    __tablename__ = 'planning_info'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    comments = db.Column(db.Text)
    kpis = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    brand = db.relationship('Brand', back_populates='planning_info')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    attachments = db.relationship('PlanningAttachment', back_populates='planning_info', cascade='all, delete-orphan')

class PlanningAttachment(db.Model):
    __tablename__ = 'planning_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    planning_info_id = db.Column(db.Integer, db.ForeignKey('planning_info.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    planning_info = db.relationship('PlanningInfo', back_populates='attachments')

class KeyMeeting(db.Model):
    __tablename__ = 'key_meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    brand = db.relationship('Brand', back_populates='key_meetings')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    attachments = db.relationship('MeetingAttachment', back_populates='meeting', cascade='all, delete-orphan')

class MeetingAttachment(db.Model):
    __tablename__ = 'meeting_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey('key_meetings.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    meeting = db.relationship('KeyMeeting', back_populates='attachments')

class KeyLink(db.Model):
    __tablename__ = 'key_links'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    comment = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    brand = db.relationship('Brand', back_populates='key_links')
    created_by = db.relationship('User', foreign_keys=[created_by_id])

class StatusUpdate(db.Model):
    __tablename__ = 'status_updates'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    comment = db.Column(db.Text, nullable=False)
    evaluation = db.Column(db.String(20), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand = db.relationship('Brand', back_populates='status_updates')
    created_by = db.relationship('User', back_populates='status_updates')

class Gift(db.Model):
    __tablename__ = 'gifts'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('client_contacts.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    gift_description = db.Column(db.String(255), nullable=False)
    gift_value = db.Column(db.Numeric(10, 2))
    sent_date = db.Column(db.Date)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    contact = db.relationship('ClientContact', back_populates='gifts')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    
    __table_args__ = (db.UniqueConstraint('contact_id', 'year'),)

class TaskTemplate(db.Model):
    __tablename__ = 'task_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand_tasks = db.relationship('BrandTask', back_populates='task_template')
    
    def __repr__(self):
        return f'<TaskTemplate {self.name}>'

class BrandTask(db.Model):
    __tablename__ = 'brand_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    task_template_id = db.Column(db.Integer, db.ForeignKey('task_templates.id'), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)  # monthly, quarterly, twice_yearly, yearly
    start_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    brand = db.relationship('Brand', back_populates='brand_tasks')
    task_template = db.relationship('TaskTemplate', back_populates='brand_tasks')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    completions = db.relationship('TaskCompletion', back_populates='brand_task', cascade='all, delete-orphan')
    
    __table_args__ = (db.UniqueConstraint('brand_id', 'task_template_id'),)
    
    def get_next_due_date(self, from_date=None):
        """Calculate next due date based on frequency"""
        from dateutil.relativedelta import relativedelta
        
        if from_date is None:
            from_date = datetime.now().date()
        
        # Get the last completion date
        last_completion = TaskCompletion.query.filter_by(
            brand_task_id=self.id
        ).order_by(TaskCompletion.completion_date.desc()).first()
        
        if last_completion:
            base_date = last_completion.completion_date
        else:
            base_date = self.start_date
        
        # Calculate next due date based on frequency
        if self.frequency == 'monthly':
            next_date = base_date + relativedelta(months=1)
        elif self.frequency == 'quarterly':
            next_date = base_date + relativedelta(months=3)
        elif self.frequency == 'twice_yearly':
            next_date = base_date + relativedelta(months=6)
        elif self.frequency == 'yearly':
            next_date = base_date + relativedelta(years=1)
        else:
            next_date = base_date
        
        # If next date is in the past, calculate from current date
        while next_date < from_date:
            if self.frequency == 'monthly':
                next_date = next_date + relativedelta(months=1)
            elif self.frequency == 'quarterly':
                next_date = next_date + relativedelta(months=3)
            elif self.frequency == 'twice_yearly':
                next_date = next_date + relativedelta(months=6)
            elif self.frequency == 'yearly':
                next_date = next_date + relativedelta(years=1)
            else:
                break
        
        return next_date

class TaskCompletion(db.Model):
    __tablename__ = 'task_completions'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_task_id = db.Column(db.Integer, db.ForeignKey('brand_tasks.id'), nullable=False)
    completion_date = db.Column(db.Date, nullable=False)
    completed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    brand_task = db.relationship('BrandTask', back_populates='completions')
    completed_by = db.relationship('User', foreign_keys=[completed_by_id])

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('brands.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    short_info = db.Column(db.Text)
    filename = db.Column(db.String(255))  # Keep for backward compatibility
    file_path = db.Column(db.String(500))  # Keep for backward compatibility
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    brand = db.relationship('Brand', back_populates='invoices')
    company = db.relationship('Company', back_populates='invoices')
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    attachments = db.relationship('InvoiceAttachment', back_populates='invoice', cascade='all, delete-orphan')

class InvoiceAttachment(db.Model):
    __tablename__ = 'invoice_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    invoice = db.relationship('Invoice', back_populates='attachments')