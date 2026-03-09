from datetime import datetime, timedelta
import json

class LeadService:
    """Service for managing leads"""
    
    def __init__(self, db):
        self.db = db
        from models import Lead, LeadHistory, get_wib_now
        self.Lead = Lead
        self.LeadHistory = LeadHistory
        self.get_wib_now = get_wib_now
    
    def create_lead(self, product_list_id, order_id, name, email, phone=None, order_data=None, sales_person_name=None, sales_person_email=None):
        """Create a new lead in follow-up status"""
        # Check if lead already exists
        existing_lead = self.Lead.query.filter_by(order_id=str(order_id)).first()
        if existing_lead:
            return existing_lead
        
        lead = self.Lead(
            product_list_id=product_list_id,
            order_id=str(order_id),
            name=name,
            email=email,
            phone=phone,
            sales_person_name=sales_person_name,
            sales_person_email=sales_person_email,
            status='follow_up',
            order_data=json.dumps(order_data) if order_data else None,
            follow_up_start=self.get_wib_now()
        )
        
        self.db.session.add(lead)
        
        # Add history entry
        history = self.LeadHistory(
            lead=lead,
            from_status=None,
            to_status='follow_up',
            notes='Lead created from order'
        )
        self.db.session.add(history)
        
        self.db.session.commit()
        return lead
    
    def move_to_closing(self, lead):
        """Move lead to closing status"""
        old_status = lead.status
        lead.status = 'closing'
        lead.closed_at = self.get_wib_now()
        lead.updated_at = self.get_wib_now()
        
        # Add history entry
        history = self.LeadHistory(
            lead_id=lead.id,
            from_status=old_status,
            to_status='closing',
            notes='Payment received - order paid'
        )
        self.db.session.add(history)
        
        self.db.session.commit()
        return lead
    
    def move_to_not_closing(self, lead):
        """Move lead to not closing status"""
        old_status = lead.status
        lead.status = 'not_closing'
        lead.updated_at = self.get_wib_now()
        
        # Add history entry
        history = self.LeadHistory(
            lead_id=lead.id,
            from_status=old_status,
            to_status='not_closing',
            notes=f'No payment after {lead.days_in_follow_up()} days in follow-up'
        )
        self.db.session.add(history)
        
        self.db.session.commit()
        return lead
    
    def get_expired_follow_up_leads(self, days=7):
        """Get leads that have been in follow-up for more than specified days"""
        cutoff_date = self.get_wib_now() - timedelta(days=days)
        
        expired_leads = self.Lead.query.filter(
            self.Lead.status == 'follow_up',
            self.Lead.follow_up_start <= cutoff_date
        ).all()
        
        return expired_leads
    
    def mark_sent_to_mailketing(self, lead, list_id=None):
        """Mark lead as sent to Mailketing"""
        lead.sent_to_mailketing = True
        lead.sent_to_mailketing_at = self.get_wib_now()
        if list_id:
            lead.mailketing_list_id = list_id
        self.db.session.commit()
        return lead

