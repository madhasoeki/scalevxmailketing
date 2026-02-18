from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import pytz
import os
import json
import hmac
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scalevxmailketing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
login_manager.login_message_category = 'warning'

# Hardcoded user credentials
ADMIN_EMAIL = 'madhasoeki@gmail.com'
ADMIN_PASSWORD = 'xferlog812'

class User(UserMixin):
    def __init__(self, id, email):
        self.id = id
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    if user_id == '1':
        return User(id='1', email=ADMIN_EMAIL)
    return None

# Timezone Configuration (WIB = UTC+7)
WIB = pytz.timezone('Asia/Jakarta')

def get_wib_now():
    """Get current time in WIB timezone"""
    return datetime.now(WIB)

# Initialize database
from database import db
db.init_app(app)

# Import models after db initialization
from models import Settings, ProductList, Lead, LeadHistory, get_wib_now as get_wib_now_naive

# Import services
from services.scalev_service import ScalevService
from services.mailketing_service import MailketingService
from services.lead_service import LeadService

# Jinja2 Template Filters for WIB timezone
@app.template_filter('to_wib')
def to_wib_filter(dt):
    """Format datetime as WIB (database already stores in WIB)"""
    if dt is None:
        return '-'
    # Database stores naive datetime in WIB, just format it
    if dt.tzinfo is None:
        return dt.strftime('%d-%m-%Y %H:%M WIB')
    # If has timezone info, convert to WIB
    return dt.astimezone(WIB).strftime('%d-%m-%Y %H:%M WIB')

@app.template_filter('to_wib_date')
def to_wib_date_filter(dt):
    """Format datetime as WIB date only"""
    if dt is None:
        return '-'
    if dt.tzinfo is None:
        return dt.strftime('%d-%m-%Y')
    return dt.astimezone(WIB).strftime('%d-%m-%Y')

@app.template_filter('to_wib_time')
def to_wib_time_filter(dt):
    """Format datetime as WIB time only"""
    if dt is None:
        return '-'
    if dt.tzinfo is None:
        return dt.strftime('%H:%M WIB')
    return dt.astimezone(WIB).strftime('%H:%M WIB')

# Initialize scheduler
scheduler = BackgroundScheduler()

def check_expired_leads():
    """Check for leads that have been in follow-up for more than 7 days"""
    with app.app_context():
        lead_service = LeadService(db)
        expired_leads = lead_service.get_expired_follow_up_leads()
        
        print(f"\n{'='*60}")
        print(f"Checking expired leads: {len(expired_leads)} found")
        print(f"{'='*60}\n")
        
        for lead in expired_leads:
            try:
                # Move to not closing
                lead_service.move_to_not_closing(lead)
                print(f"✓ Lead {lead.email} moved to not_closing")
                
                # Send to Not Closing list
                product_list = ProductList.query.get(lead.product_list_id)
                if product_list and product_list.mailketing_list_not_closing:
                    settings = Settings.query.first()
                    if settings and settings.mailketing_api_key:
                        mailketing = MailketingService(settings.mailketing_api_key)
                        result = mailketing.add_subscriber(
                            list_id=product_list.mailketing_list_not_closing,
                            email=lead.email,
                            first_name=lead.name,
                            mobile=lead.phone
                        )
                        
                        if result:
                            # Mark as sent with list ID
                            lead_service.mark_sent_to_mailketing(lead, product_list.mailketing_list_not_closing)
                            print(f"  ✓ Sent to Not Closing list: {product_list.mailketing_list_not_closing}")
                        else:
                            print(f"  ⚠️  Failed to send to Mailketing")
                else:
                    print(f"  ⚠️  No Not Closing list configured for this product")
                
            except Exception as e:
                print(f"❌ Error processing expired lead {lead.id}: {str(e)}")
                import traceback
                traceback.print_exc()


# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            user = User(id='1', email=ADMIN_EMAIL)
            login_user(user, remember=True)
            flash('Login berhasil! Selamat datang.', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Email atau password salah!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))


# Main Routes
@app.route('/')
@login_required
def index():
    """Dashboard home"""
    stats = {
        'follow_up': Lead.query.filter_by(status='follow_up').count(),
        'closing': Lead.query.filter_by(status='closing').count(),
        'not_closing': Lead.query.filter_by(status='not_closing').count(),
        'total': Lead.query.count()
    }
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(10).all()
    return render_template('index.html', stats=stats, recent_leads=recent_leads)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """API Settings page"""
    settings_obj = Settings.query.first()
    
    if request.method == 'POST':
        scalev_api_key = request.form.get('scalev_api_key')
        scalev_webhook_secret = request.form.get('scalev_webhook_secret')
        mailketing_api_key = request.form.get('mailketing_api_key')
        
        if not settings_obj:
            settings_obj = Settings()
            db.session.add(settings_obj)
        
        settings_obj.scalev_api_key = scalev_api_key
        settings_obj.scalev_webhook_secret = scalev_webhook_secret
        settings_obj.mailketing_api_key = mailketing_api_key
        settings_obj.updated_at = get_wib_now_naive()
        
        db.session.commit()
        flash('Settings saved successfully!', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=settings_obj)

@app.route('/product-lists')
@login_required
def product_lists():
    """Product lists management"""
    try:
        lists = ProductList.query.all()
    except Exception as e:
        # If database not migrated yet, columns might not exist
        print(f"ERROR loading product lists: {str(e)}")
        import traceback
        traceback.print_exc()
        flash('Database belum di-migrate. Silakan restart aplikasi untuk auto-migration.', 'danger')
        lists = []
    
    settings_obj = Settings.query.first()
    
    # Get Mailketing lists if API key is configured
    mailketing_lists = []
    if settings_obj and settings_obj.mailketing_api_key:
        try:
            print("Fetching Mailketing lists...")
            mailketing = MailketingService(settings_obj.mailketing_api_key)
            mailketing_lists = mailketing.get_all_lists()
            print(f"✓ Fetched {len(mailketing_lists)} Mailketing lists")
            if mailketing_lists:
                print(f"  First list: {mailketing_lists[0].get('list_name')} (ID: {mailketing_lists[0].get('list_id')})")
        except Exception as e:
            print(f"ERROR fetching Mailketing lists: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Error fetching Mailketing lists: {str(e)}', 'warning')
    
    return render_template('product_lists.html', lists=lists, mailketing_lists=mailketing_lists)


@app.route('/product-lists/add', methods=['POST'])
@login_required
def add_product_list():
    """Add new product list"""
    store_id = request.form.get('store_id')
    store_name = request.form.get('store_name')
    product_name = request.form.get('product_name')
    product_id = request.form.get('product_id')
    
    # Get multiple sales persons (getlist returns array)
    sales_person_ids = request.form.getlist('sales_person_id[]')
    sales_person_names = request.form.getlist('sales_person_name[]')
    sales_person_emails = request.form.getlist('sales_person_email[]')
    
    mailketing_list_followup = request.form.get('mailketing_list_followup')
    mailketing_list_closing = request.form.get('mailketing_list_closing')
    mailketing_list_not_closing = request.form.get('mailketing_list_not_closing')
    
    if not all([store_id, store_name, product_name, product_id]):
        flash('Store and Product are required', 'danger')
        return redirect(url_for('product_lists'))
    
    product_list = ProductList(
        store_id=store_id,
        store_name=store_name,
        product_name=product_name,
        product_id=product_id,
        mailketing_list_followup=mailketing_list_followup if mailketing_list_followup else None,
        mailketing_list_closing=mailketing_list_closing if mailketing_list_closing else None,
        mailketing_list_not_closing=mailketing_list_not_closing if mailketing_list_not_closing else None
    )
    
    # Set multiple sales persons
    if sales_person_ids and len(sales_person_ids) > 0:
        product_list.set_sales_persons(sales_person_ids, sales_person_names, sales_person_emails)
    
    db.session.add(product_list)
    db.session.commit()
    
    flash(f'Product list "{product_name}" added successfully!', 'success')
    return redirect(url_for('product_lists'))

@app.route('/product-lists/<int:list_id>/delete', methods=['POST'])
@login_required
def delete_product_list(list_id):
    """Delete product list - leads akan tetap ada dengan product_list_id = NULL"""
    try:
        product_list = ProductList.query.get_or_404(list_id)
        product_name = product_list.product_name
        
        # Set product_list_id menjadi NULL untuk semua leads terkait
        Lead.query.filter_by(product_list_id=list_id).update({'product_list_id': None})
        
        # Hapus product list
        db.session.delete(product_list)
        db.session.commit()
        
        flash(f'Product list "{product_name}" berhasil dihapus!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error menghapus product list: {str(e)}', 'danger')
    
    return redirect(url_for('product_lists'))

@app.route('/product-lists/<int:list_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product_list(list_id):
    """Edit product list"""
    product_list = ProductList.query.get_or_404(list_id)
    
    if request.method == 'POST':
        try:
            # Update mailketing lists
            product_list.mailketing_list_followup = request.form.get('mailketing_list_followup')
            product_list.mailketing_list_closing = request.form.get('mailketing_list_closing')
            product_list.mailketing_list_not_closing = request.form.get('mailketing_list_not_closing')
            
            # Update multiple sales persons
            sales_person_ids = request.form.getlist('sales_person_id[]')
            sales_person_names = request.form.getlist('sales_person_name[]')
            sales_person_emails = request.form.getlist('sales_person_email[]')
            
            if sales_person_ids and len(sales_person_ids) > 0:
                product_list.set_sales_persons(sales_person_ids, sales_person_names, sales_person_emails)
            else:
                # Reset to "All Sales"
                product_list.set_sales_persons([], [], [])
            
            db.session.commit()
            flash(f'Product list "{product_list.product_name}" berhasil diupdate!', 'success')
            return redirect(url_for('product_lists'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error mengupdate product list: {str(e)}', 'danger')
            return redirect(url_for('product_lists'))
    
    # GET: Return JSON for AJAX
    return jsonify({
        'id': product_list.id,
        'store_id': product_list.store_id,
        'store_name': product_list.store_name,
        'product_id': product_list.product_id,
        'product_name': product_list.product_name,
        'sales_person_ids': product_list.get_sales_person_ids_list(),
        'sales_person_names': product_list.get_sales_person_names_list(),
        'sales_person_emails': product_list.get_sales_person_emails_list(),
        'mailketing_list_followup': product_list.mailketing_list_followup,
        'mailketing_list_closing': product_list.mailketing_list_closing,
        'mailketing_list_not_closing': product_list.mailketing_list_not_closing
    })

@app.route('/leads')
@login_required
def leads():
    """Leads management"""
    status_filter = request.args.get('status', 'all')
    
    if status_filter == 'all':
        leads_query = Lead.query
    else:
        leads_query = Lead.query.filter_by(status=status_filter)
    
    leads_list = leads_query.order_by(Lead.created_at.desc()).all()
    
    return render_template('leads.html', leads=leads_list, status_filter=status_filter)

@app.route('/leads/<int:lead_id>')
@login_required
def lead_detail(lead_id):
    """Lead detail page"""
    lead = Lead.query.get_or_404(lead_id)
    history = LeadHistory.query.filter_by(lead_id=lead_id).order_by(LeadHistory.created_at.desc()).all()
    
    return render_template('lead_detail.html', lead=lead, history=history)

@app.route('/leads/<int:lead_id>/test-not-closing', methods=['POST'])
@login_required
def test_move_to_not_closing(lead_id):
    """Test endpoint: Force move lead to not_closing and send to Mailketing"""
    lead = Lead.query.get_or_404(lead_id)
    
    # Only allow for follow_up status
    if lead.status != 'follow_up':
        flash(f'Lead sudah dalam status {lead.status}, tidak bisa ditest', 'warning')
        return redirect(url_for('leads'))
    
    try:
        lead_service = LeadService(db)
        
        print(f"\n{'='*60}")
        print(f"🧪 TEST: Moving lead to Not Closing")
        print(f"Lead: {lead.email} - {lead.name}")
        print(f"Product: {lead.product_list.product_name}")
        print(f"{'='*60}\n")
        
        # Move to not closing
        lead_service.move_to_not_closing(lead)
        print(f"✓ Lead status changed to: not_closing")
        
        # Send to Not Closing list
        product_list = ProductList.query.get(lead.product_list_id)
        if product_list and product_list.mailketing_list_not_closing:
            settings_obj = Settings.query.first()
            if settings_obj and settings_obj.mailketing_api_key:
                print(f"Sending to Not Closing List ID: {product_list.mailketing_list_not_closing}")
                
                mailketing = MailketingService(settings_obj.mailketing_api_key)
                result = mailketing.add_subscriber(
                    list_id=product_list.mailketing_list_not_closing,
                    email=lead.email,
                    first_name=lead.name,
                    mobile=lead.phone
                )
                
                print(f"Mailketing API Response: {result}")
                
                if result:
                    # Mark as sent with list ID
                    lead_service.mark_sent_to_mailketing(lead, product_list.mailketing_list_not_closing)
                    print(f"✓ Lead marked as sent to Mailketing")
                    flash(f'✅ SUCCESS! Lead dipindahkan ke Not Closing dan berhasil dikirim ke Mailketing List {product_list.mailketing_list_not_closing}', 'success')
                else:
                    print(f"⚠ Failed to send to Mailketing")
                    flash(f'⚠ Lead dipindahkan ke Not Closing, tapi gagal dikirim ke Mailketing', 'warning')
            else:
                print(f"⚠ Mailketing API key not configured")
                flash(f'⚠ Lead dipindahkan ke Not Closing, tapi Mailketing API key belum diatur', 'warning')
        else:
            print(f"⚠ No Not Closing List configured for this product")
            flash(f'⚠ Lead dipindahkan ke Not Closing, tapi product tidak punya Not Closing List', 'warning')
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"❌ ERROR in test: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'!'*60}\n")
        flash(f'❌ Error: {str(e)}', 'danger')
    
    return redirect(url_for('leads'))


@app.route('/webhook/scalev', methods=['POST'])
def scalev_webhook():
    """Scalev webhook endpoint"""
    try:
        # Get webhook secret from settings
        settings_obj = Settings.query.first()
        if not settings_obj or not settings_obj.scalev_webhook_secret:
            print("WARNING: Webhook secret not configured!")
            return jsonify({'error': 'Webhook secret not configured'}), 500
        
        # Verify webhook signature (REQUIRED for security)
        signature = request.headers.get('X-Scalev-Signature')
        payload = request.get_data()
        
        if signature:
            # Verify signature according to Scalev docs
            expected_signature = hmac.new(
                settings_obj.scalev_webhook_secret.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                print(f"ERROR: Invalid webhook signature!")
                return jsonify({'error': 'Invalid signature'}), 401
        else:
            print("WARNING: No signature provided in webhook request")
            # In production, you should reject requests without signature
            # For development, we'll allow it
            # return jsonify({'error': 'No signature provided'}), 401
        
        # Process webhook
        payload = request.json
        
        # Get event type and data
        event_type = payload.get('event')
        data = payload.get('data', {})
        
        print(f"\n{'='*60}")
        print(f"Webhook received: {event_type}")
        print(f"Unique ID: {payload.get('unique_id')}")
        print(f"Timestamp: {payload.get('timestamp')}")
        print(f"{'='*60}\n")
        
        # Check if this is a test event
        if event_type == 'business.test_event':
            print("✓ Test event received - webhook is working!")
            return jsonify({'success': True, 'message': 'Test event received'}), 200
        
        # Get order_id
        order_id = data.get('order_id')
        print(f"Order ID: {order_id}")
        
        # Debug: Print all available fields in data (to discover handler/CS fields)
        print(f"\n📋 Available fields in payload data:")
        for key in data.keys():
            print(f"  - {key}")
        
        # Check for potential handler/CS fields
        handler_fields = ['handler', 'assigned_to', 'sales_person', 'created_by', 'user', 'employee', 'staff']
        found_handlers = []
        for field in handler_fields:
            if field in data:
                found_handlers.append(f"{field}: {data.get(field)}")
        
        if found_handlers:
            print(f"\n👤 Handler/CS fields found:")
            for h in found_handlers:
                print(f"  ✓ {h}")
        else:
            print(f"\n⚠️  No handler/CS fields found in standard field names")
            print(f"   Checked: {', '.join(handler_fields)}")
        print("")
        
        lead_service = LeadService(db)
        
        # Handle different event types
        if event_type in ['order.created', 'order.epayment_created', 'order.spam_created', 'order.updated']:
            # New order - add to follow up
            print(f"Event: {event_type}")
            
            # Extract product info from orderlines
            orderlines = data.get('orderlines', [])
            if not orderlines:
                print("WARNING: No orderlines in payload")
                return jsonify({'success': False, 'error': 'No orderlines'}), 400
            
            # Get first product (main product)
            first_line = orderlines[0]
            variant_sku = first_line.get('variant_sku') or None  # Convert empty string to None
            product_name = first_line.get('product_name')
            variant_unique_id = first_line.get('variant_unique_id')
            
            print(f"Product: {product_name}")
            print(f"  - SKU: {variant_sku if variant_sku else 'Not available'}")
            print(f"  - Variant ID: {variant_unique_id}")
            
            # Try to match product list by SKU, product name, or variant_unique_id
            product_list = None
            matched_by = None
            
            # Priority 1: Try matching by SKU (if available)
            if variant_sku:
                product_list = ProductList.query.filter_by(product_id=variant_sku).first()
                if product_list:
                    matched_by = f"SKU: {variant_sku}"
            
            # Priority 2: Try matching by exact product name
            if not product_list and product_name:
                product_list = ProductList.query.filter_by(product_name=product_name).first()
                if product_list:
                    matched_by = f"Exact Product Name: {product_name}"
            
            # Priority 3: Try matching by product name (partial/variant match)
            # This handles cases where webhook sends variant name like "Product - 100 ribu"
            # but database has base product name like "Product"
            if not product_list and product_name:
                # Get all active products and check if database name is contained in webhook name
                all_products = ProductList.query.filter_by(is_active=True).all()
                for p in all_products:
                    # Check if database product name is part of webhook product name
                    # AND database name is long enough to avoid false positives (min 5 chars)
                    if len(p.product_name) >= 5 and p.product_name in product_name:
                        product_list = p
                        matched_by = f"Partial Product Name: '{p.product_name}' found in '{product_name}'"
                        break
            
            # Priority 4: Try matching by variant_unique_id
            if not product_list and variant_unique_id:
                product_list = ProductList.query.filter_by(product_id=variant_unique_id).first()
                if product_list:
                    matched_by = f"Variant ID: {variant_unique_id}"
            
            if product_list:
                print(f"✓ Product matched by {matched_by}")
                
                # Extract handler data from webhook
                handler_data = data.get('handler', {})
                handler_email = None
                handler_name = None
                handler_id = None
                
                if handler_data:
                    handler_email = handler_data.get('email')
                    handler_name = handler_data.get('fullname')
                    handler_id = handler_data.get('unique_id') or handler_data.get('id')
                    print(f"   Webhook handler: {handler_name} ({handler_email}, ID: {handler_id})")
                else:
                    print(f"   ⚠️  No handler data in webhook")
                
                # Check if sales person matching is required
                if not product_list.is_for_all_sales():
                    sales_names = product_list.get_sales_person_names_list()
                    sales_ids = product_list.get_sales_person_ids_list()
                    print(f"\n👤 Sales person matching required for: {', '.join(sales_names)}")
                    
                    # Check if handler matches any of the configured sales persons
                    is_matched = False
                    
                    # Try matching by ID first (more reliable)
                    if handler_id and handler_id in sales_ids:
                        is_matched = True
                        print(f"   ✓ Handler matched by ID: {handler_id}")
                    
                    # Fallback: Try matching by email
                    if not is_matched and handler_email:
                        sales_emails = product_list.get_sales_person_emails_list()
                        for sales_email in sales_emails:
                            if sales_email and handler_email.lower() == sales_email.lower():
                                is_matched = True
                                print(f"   ✓ Handler matched by email: {handler_email}")
                                break
                    
                    if not is_matched:
                        print(f"   ❌ Handler NOT matched!")
                        print(f"      Expected any of: {', '.join(sales_names)}")
                        print(f"      Got: {handler_name} ({handler_email}, ID: {handler_id})")
                        print(f"   → Skipping lead creation (sales person mismatch)")
                        return jsonify({'success': True, 'message': 'Sales person mismatch, skipped'}), 200
                else:
                    print(f"✓ No sales person filter (All Sales mode)")
                
                # Extract customer info from destination_address
                destination = data.get('destination_address', {})
                customer_name = destination.get('name')
                customer_email = destination.get('email')
                customer_phone = destination.get('phone')
                
                print(f"Customer: {customer_name} ({customer_email}, {customer_phone})")
                
                # Validate required fields
                if not customer_email or not customer_name:
                    print(f"ERROR: Missing required customer data (name: {customer_name}, email: {customer_email})")
                    return jsonify({'success': False, 'error': 'Missing customer data'}), 400
                
                # Check if lead already exists
                existing_lead = Lead.query.filter_by(order_id=str(order_id)).first()
                if existing_lead:
                    print(f"INFO: Lead already exists for order {order_id}, skipping creation")
                else:
                    # Create lead
                    try:
                        lead = lead_service.create_lead(
                            product_list_id=product_list.id,
                            order_id=order_id,
                            name=customer_name,
                            email=customer_email,
                            phone=customer_phone,
                            order_data=data,
                            sales_person_name=handler_name,
                            sales_person_email=handler_email
                        )
                        print(f"✓ Lead created: {lead.email} - {lead.name}")
                        
                        # Send to Follow Up list immediately
                        if product_list.mailketing_list_followup:
                            print(f"\n📧 Sending to Follow Up list: {product_list.mailketing_list_followup}")
                            try:
                                settings_obj = Settings.query.first()
                                if settings_obj and settings_obj.mailketing_api_key:
                                    mailketing = MailketingService(settings_obj.mailketing_api_key)
                                    result = mailketing.add_subscriber(
                                        list_id=product_list.mailketing_list_followup,
                                        email=lead.email,
                                        first_name=lead.name,
                                        mobile=lead.phone
                                    )
                                    if result:
                                        lead_service.mark_sent_to_mailketing(lead, product_list.mailketing_list_followup)
                                        print(f"   ✓ Subscriber added to Follow Up list")
                                    else:
                                        print(f"   ⚠️  Failed to add subscriber to Follow Up list")
                                else:
                                    print(f"   ⚠️  Mailketing API key not configured")
                            except Exception as e:
                                print(f"   ❌ Error sending to Mailketing: {str(e)}")
                        else:
                            print(f"⚠️  No Follow Up list configured for this product")
                    except Exception as e:
                        print(f"ERROR: Failed to create lead: {str(e)}")
                        return jsonify({'success': False, 'error': str(e)}), 500
            else:
                print(f"\n❌ PRODUCT NOT FOUND IN DATABASE")
                print(f"   Product from webhook: '{product_name}'")
                print(f"   - SKU: {variant_sku if variant_sku else 'Not available'}")
                print(f"   - Variant ID: {variant_unique_id}")
                print(f"\n💡 SOLUTION: Add this product to Product Lists page")
                print(f"\n   📌 TIP: Untuk produk dengan variant (S/M/L, 100rb/200rb/500rb, dll):")
                print(f"      Gunakan NAMA PRODUK BASE (tanpa variant) untuk match semua variant")
                print(f"      Contoh:")
                print(f"        Webhook: 'Sedekah Jariyah Kawasan Qur'an - 100 ribu'")
                print(f"        Database: 'Sedekah Jariyah Kawasan Qur'an'  ← Akan match!")
                print(f"")
                print(f"   Option 1 - Match by Base Product Name (👍 Recommended untuk variant):")
                # Extract potential base name by splitting on common variant separators
                base_name_candidates = []
                if ' - ' in product_name:
                    base_name_candidates.append(product_name.split(' - ')[0])
                if ' / ' in product_name:
                    base_name_candidates.append(product_name.split(' / ')[0])
                
                if base_name_candidates:
                    print(f"      Product ID: (any, e.g., BASE01)")
                    print(f"      Product Name: {base_name_candidates[0]}")
                    print(f"      → Ini akan match semua variant dari produk ini")
                else:
                    print(f"      Product ID: (any, e.g., SJ100)")
                    print(f"      Product Name: [Base product name without variant]")
                print(f"")
                print(f"   Option 2 - Match by Exact Full Name (untuk produk tanpa variant):")
                print(f"      Product ID: (any, e.g., SJ100)")
                print(f"      Product Name: {product_name}")
                print(f"")
                print(f"   Option 3 - Match by Variant ID (specific variant saja):")
                print(f"      Product ID: {variant_unique_id}")
                print(f"      Product Name: {product_name}")
                if variant_sku:
                    print(f"")
                    print(f"   Option 4 - Match by SKU:")
                    print(f"      Product ID: {variant_sku}")
                    print(f"      Product Name: {product_name}")
                
                # List existing products for reference
                existing_products = ProductList.query.filter_by(is_active=True).all()
                if existing_products:
                    print(f"\n📋 Currently configured products ({len(existing_products)}):")
                    for p in existing_products[:5]:  # Show first 5
                        print(f"   - {p.product_name} (ID: {p.product_id})")
                    if len(existing_products) > 5:
                        print(f"   ... and {len(existing_products) - 5} more")
                else:
                    print(f"\n⚠️  No products configured yet. Please add products in Product Lists page.")
                print("")
        
        elif event_type == 'order.payment_status_changed':
            # Order payment status changed
            print(f"Event: {event_type}")
            payment_status = data.get('payment_status')
            print(f"Payment status: {payment_status} for order: {order_id}")
            
            if payment_status == 'paid':
                lead = Lead.query.filter_by(order_id=str(order_id)).first()
                if lead:
                    if lead.status == 'follow_up':
                        lead_service.move_to_closing(lead)
                        print(f"✓ Lead moved to closing: {lead.email}")
                        
                        # Send to Closing list
                        product_list = lead.product_list
                        if product_list.mailketing_list_closing:
                            print(f"\n📧 Sending to Closing list: {product_list.mailketing_list_closing}")
                            try:
                                settings_obj = Settings.query.first()
                                if settings_obj and settings_obj.mailketing_api_key:
                                    mailketing = MailketingService(settings_obj.mailketing_api_key)
                                    result = mailketing.add_subscriber(
                                        list_id=product_list.mailketing_list_closing,
                                        email=lead.email,
                                        first_name=lead.name,
                                        mobile=lead.phone
                                    )
                                    if result:
                                        lead_service.mark_sent_to_mailketing(lead, product_list.mailketing_list_closing)
                                        print(f"   ✓ Subscriber added to Closing list")
                                    else:
                                        print(f"   ⚠️  Failed to add subscriber to Closing list")
                                else:
                                    print(f"   ⚠️  Mailketing API key not configured")
                            except Exception as e:
                                print(f"   ❌ Error sending to Mailketing: {str(e)}")
                        else:
                            print(f"⚠️  No Closing list configured for this product")
                    else:
                        print(f"Lead already in status: {lead.status}")
                else:
                    print(f"WARNING: No lead found for order_id: {order_id}")
        
        elif event_type == 'order.status_changed':
            # Order status changed (canceled, closed, etc)
            status = data.get('status')
            print(f"Event: {event_type}")
            print(f"Order status changed to '{status}' for order: {order_id}")
            # You can handle canceled/closed orders here if needed
        
        elif event_type == 'order.deleted':
            # Order deleted
            print(f"Event: {event_type}")
            print(f"Order deleted: {order_id}")
            # You can handle deleted orders here if needed
        
        else:
            # Other events or unknown events
            print(f"Event: {event_type} (unhandled)")
            print(f"Available data keys: {list(data.keys())}")
        
        return jsonify({'success': True}), 200
    
    except Exception as e:
        print(f"\n{'!'*60}")
        print(f"WEBHOOK ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'!'*60}\n")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test-mailketing', methods=['POST'])
@login_required
def test_mailketing():
    """Test Mailketing API connection"""
    settings_obj = Settings.query.first()
    
    if not settings_obj or not settings_obj.mailketing_api_key:
        return jsonify({'success': False, 'message': 'Mailketing API key not configured'}), 400
    
    try:
        mailketing = MailketingService(settings_obj.mailketing_api_key)
        lists = mailketing.get_all_lists()
        return jsonify({'success': True, 'lists_count': len(lists), 'lists': lists})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/test-scalev', methods=['POST'])
@login_required
def test_scalev():
    """Test ScaleV API connection"""
    settings_obj = Settings.query.first()
    
    if not settings_obj or not settings_obj.scalev_api_key:
        return jsonify({'success': False, 'message': 'ScaleV API key not configured'}), 400
    
    try:
        scalev = ScalevService(settings_obj.scalev_api_key)
        products = scalev.get_products()
        return jsonify({'success': True, 'products_count': len(products), 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/scalev/stores', methods=['GET'])
@login_required
def get_scalev_stores():
    """Get all ScaleV stores with optional search"""
    settings_obj = Settings.query.first()
    
    if not settings_obj or not settings_obj.scalev_api_key:
        return jsonify({'success': False, 'message': 'ScaleV API key not configured'}), 400
    
    try:
        scalev = ScalevService(settings_obj.scalev_api_key)
        stores = scalev.get_stores()
        
        # Filter based on search query (for Select2 search)
        search_term = request.args.get('q', '').lower()
        if search_term:
            stores = [s for s in stores if search_term in s.get('name', '').lower() or search_term in str(s.get('id', ''))]
        
        return jsonify({'success': True, 'stores': stores})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/scalev/stores/<store_id>/products', methods=['GET'])
@login_required
def get_scalev_store_products(store_id):
    """Get products from a specific store"""
    settings_obj = Settings.query.first()
    
    if not settings_obj or not settings_obj.scalev_api_key:
        return jsonify({'success': False, 'message': 'ScaleV API key not configured'}), 400
    
    try:
        scalev = ScalevService(settings_obj.scalev_api_key)
        products = scalev.get_store_products(store_id)
        return jsonify({'success': True, 'products': products})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/scalev/stores/<store_id>/sales-people', methods=['GET'])
@login_required
def get_scalev_store_sales_people(store_id):
    """Get sales people from a specific store"""
    settings_obj = Settings.query.first()
    
    if not settings_obj or not settings_obj.scalev_api_key:
        return jsonify({'success': False, 'message': 'ScaleV API key not configured'}), 400
    
    try:
        scalev = ScalevService(settings_obj.scalev_api_key)
        sales_people = scalev.get_store_sales_people(store_id)
        return jsonify({'success': True, 'sales_people': sales_people})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Auto-run migration for new columns
        try:
            from migrate_database import migrate
            print("\n🔄 Running database migration (safe - will skip existing columns)...")
            migrate()
        except Exception as e:
            print(f"⚠️  Migration skipped or failed: {str(e)}")
            print("Don't worry - this is normal if database is already migrated.")
    
    # Start scheduler
    scheduler.add_job(
        func=check_expired_leads,
        trigger='interval',
        hours=1,  # Check every hour
        id='check_expired_leads',
        name='Check expired follow-up leads',
        replace_existing=True
    )
    scheduler.start()
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

# Auto-run migration on first import (for WSGI servers like gunicorn/uwsgi)
# This ensures migration runs even when app is imported, not executed directly
@app.before_first_request
def run_migrations():
    """Run database migrations before first request"""
    try:
        # Ensure all tables are created first
        db.create_all()
        
        # Then run migrations for new columns
        from migrate_database import migrate
        print("\n🔄 [First Request] Running database migration...")
        migrate()
        print("✅ [First Request] Migration check completed\n")
    except Exception as e:
        print(f"⚠️  [First Request] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
    )
    scheduler.start()
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
