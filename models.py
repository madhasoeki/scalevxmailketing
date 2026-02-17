from datetime import datetime
import pytz
from database import db

# Timezone WIB (UTC+7)
WIB = pytz.timezone('Asia/Jakarta')

def get_wib_now():
    """Get current datetime in WIB timezone"""
    return datetime.now(WIB).replace(tzinfo=None)  # Remove tzinfo for SQLite compatibility

class Settings(db.Model):
    """Store API keys and configuration"""
    id = db.Column(db.Integer, primary_key=True)
    scalev_api_key = db.Column(db.String(255), nullable=True)
    scalev_webhook_secret = db.Column(db.String(255), nullable=True)
    mailketing_api_key = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=get_wib_now)
    updated_at = db.Column(db.DateTime, default=get_wib_now, onupdate=get_wib_now)
    
    def __repr__(self):
        return f'<Settings {self.id}>'

class ProductList(db.Model):
    """Product lists mapped to Mailketing lists"""
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.String(100), nullable=False)
    store_name = db.Column(db.String(255), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.String(100), nullable=False, unique=True)
    sales_person_id = db.Column(db.String(100), nullable=True)  # NULL = all sales persons
    sales_person_name = db.Column(db.String(255), nullable=True)
    sales_person_email = db.Column(db.String(255), nullable=True)
    mailketing_list_followup = db.Column(db.String(100), nullable=True)
    mailketing_list_closing = db.Column(db.String(100), nullable=True)
    mailketing_list_not_closing = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_wib_now)
    updated_at = db.Column(db.DateTime, default=get_wib_now, onupdate=get_wib_now)
    
    leads = db.relationship('Lead', backref='product_list', lazy=True)
    
    def __repr__(self):
        return f'<ProductList {self.product_name}>'

class Lead(db.Model):
    """Lead tracking"""
    id = db.Column(db.Integer, primary_key=True)
    product_list_id = db.Column(db.Integer, db.ForeignKey('product_list.id'), nullable=True)
    order_id = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(50), nullable=True)
    sales_person_name = db.Column(db.String(255), nullable=True)
    sales_person_email = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='follow_up')  # follow_up, closing, not_closing
    order_data = db.Column(db.Text, nullable=True)  # JSON string of order details
    created_at = db.Column(db.DateTime, default=get_wib_now)
    updated_at = db.Column(db.DateTime, default=get_wib_now, onupdate=get_wib_now)
    follow_up_start = db.Column(db.DateTime, default=get_wib_now)
    closed_at = db.Column(db.DateTime, nullable=True)
    sent_to_mailketing = db.Column(db.Boolean, default=False)
    sent_to_mailketing_at = db.Column(db.DateTime, nullable=True)
    mailketing_list_id = db.Column(db.String(100), nullable=True)  # Which list was sent to
    
    history = db.relationship('LeadHistory', backref='lead', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Lead {self.email} - {self.status}>'
    
    def days_in_follow_up(self):
        """Calculate days in follow up"""
        if self.status != 'follow_up':
            return 0
        delta = get_wib_now() - self.follow_up_start
        return delta.days

class LeadHistory(db.Model):
    """Lead status history"""
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('lead.id'), nullable=False)
    from_status = db.Column(db.String(50), nullable=True)
    to_status = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=get_wib_now)
    
    def __repr__(self):
        return f'<LeadHistory {self.lead_id}: {self.from_status} -> {self.to_status}>'
