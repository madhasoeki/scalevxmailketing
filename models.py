from datetime import datetime
import pytz
import json
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
    product_id = db.Column(db.String(100), nullable=False)  # Note: No unique constraint - one product can have multiple entries (different CS)
    # Store multiple sales persons as JSON arrays
    sales_person_ids = db.Column(db.Text, nullable=True)  # JSON array: ["id1", "id2"]
    sales_person_names = db.Column(db.Text, nullable=True)  # JSON array: ["Name 1", "Name 2"]
    sales_person_emails = db.Column(db.Text, nullable=True)  # JSON array: ["email1@x.com", "email2@x.com"]
    mailketing_list_followup = db.Column(db.String(100), nullable=True)
    mailketing_list_closing = db.Column(db.String(100), nullable=True)
    mailketing_list_not_closing = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_wib_now)
    updated_at = db.Column(db.DateTime, default=get_wib_now, onupdate=get_wib_now)
    
    leads = db.relationship('Lead', backref='product_list', lazy=True)
    
    def get_sales_person_ids_list(self):
        """Get sales person IDs as list (backward compatible)"""
        # Check if new column exists (post-migration)
        if hasattr(self, 'sales_person_ids') and self.sales_person_ids:
            try:
                return json.loads(self.sales_person_ids)
            except:
                return []
        # Fallback to old single column (pre-migration)
        elif hasattr(self, 'sales_person_id') and self.sales_person_id:
            return [self.sales_person_id]
        return []
    
    def get_sales_person_names_list(self):
        """Get sales person names as list (backward compatible)"""
        # Check if new column exists (post-migration)
        if hasattr(self, 'sales_person_names') and self.sales_person_names:
            try:
                return json.loads(self.sales_person_names)
            except:
                return []
        # Fallback to old single column (pre-migration)
        elif hasattr(self, 'sales_person_name') and self.sales_person_name:
            return [self.sales_person_name]
        return []
    
    def get_sales_person_emails_list(self):
        """Get sales person emails as list (backward compatible)"""
        # Check if new column exists (post-migration)
        if hasattr(self, 'sales_person_emails') and self.sales_person_emails:
            try:
                return json.loads(self.sales_person_emails)
            except:
                return []
        # Fallback to old single column (pre-migration)
        elif hasattr(self, 'sales_person_email') and self.sales_person_email:
            return [self.sales_person_email]
        return []
    
    def set_sales_persons(self, ids, names, emails):
        """Set sales persons from lists (backward compatible)"""
        # Only set if columns exist (post-migration)
        if hasattr(self, 'sales_person_ids'):
            self.sales_person_ids = json.dumps(ids) if ids else None
        if hasattr(self, 'sales_person_names'):
            self.sales_person_names = json.dumps(names) if names else None
        if hasattr(self, 'sales_person_emails'):
            self.sales_person_emails = json.dumps(emails) if emails else None
    
    def is_for_all_sales(self):
        """Check if this list is for all sales persons (backward compatible)"""
        # Check new columns first
        if hasattr(self, 'sales_person_ids'):
            return not self.sales_person_ids or len(self.get_sales_person_ids_list()) == 0
        # Fallback to old column
        elif hasattr(self, 'sales_person_id'):
            return not self.sales_person_id
        return True  # Default: all sales
    
    def is_sales_person_included(self, sales_person_id):
        """Check if a sales person ID is included in this list"""
        if self.is_for_all_sales():
            return True
        return sales_person_id in self.get_sales_person_ids_list()
    
    def get_sales_person_display(self):
        """Get display text for sales persons"""
        if self.is_for_all_sales():
            return "All Sales Persons"
        names = self.get_sales_person_names_list()
        if len(names) == 0:
            return "All Sales Persons"
        elif len(names) == 1:
            return names[0]
        else:
            return f"{names[0]} +{len(names)-1} others"
    
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
