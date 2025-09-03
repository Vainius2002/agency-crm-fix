from flask import request, jsonify
from app.api import bp
from app.models import User, Brand, Company
from app import db
from functools import wraps
import requests

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != 'dev-api-key':  # In production, use a secure API key
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/auth/login', methods=['POST'])
@require_api_key
def api_login():
    """Authenticate user credentials and return user data if valid"""
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    # Check if user exists, is active, and password is correct
    if user and user.is_active and user.check_password(data['password']):
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'phone': user.phone,
                'birthday': user.birthday.isoformat() if user.birthday else None
            }
        })
    
    return jsonify({'error': 'Invalid credentials or account disabled'}), 401

@bp.route('/users', methods=['GET'])
@require_api_key
def get_users():
    users = User.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role
    } for user in users])

@bp.route('/brands', methods=['GET'])
@require_api_key
def get_brands():
    brands = Brand.query.join(Company).filter(Brand.status == 'active').all()
    return jsonify([{
        'id': brand.id,
        'name': brand.name,
        'company_name': brand.company.name,
        'company_id': brand.company_id
    } for brand in brands])

@bp.route('/brands/<int:brand_id>', methods=['GET'])
@require_api_key
def get_brand(brand_id):
    brand = Brand.query.join(Company).filter(Brand.id == brand_id, Brand.status == 'active').first()
    if not brand:
        return jsonify({'error': 'Brand not found'}), 404
    
    return jsonify({
        'id': brand.id,
        'name': brand.name,
        'company_name': brand.company.name,
        'company_id': brand.company_id
    })

def notify_projects_crm_new_user(user_data):
    """Send webhook to projects-crm when a new user is created"""
    try:
        webhook_url = 'http://localhost:5002/api/webhooks/user_created'
        headers = {'Content-Type': 'application/json', 'X-Webhook-Secret': 'shared-secret-key'}
        response = requests.post(webhook_url, json=user_data, headers=headers, timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to notify projects-crm: {e}")
        return False

@bp.route('/users', methods=['POST'])
@require_api_key
def create_user():
    """Create a new user and notify projects-crm"""
    data = request.get_json()
    
    required_fields = ['email', 'password', 'first_name', 'last_name', 'role']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 409
    
    user = User(
        email=data['email'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        role=data['role']
    )
    user.set_password(data['password'])
    
    if 'birthday' in data:
        from datetime import datetime
        try:
            user.birthday = datetime.strptime(data['birthday'], '%Y-%m-%d').date()
        except ValueError:
            pass
    
    db.session.add(user)
    db.session.commit()
    
    # Notify projects-crm
    user_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role
    }
    notify_projects_crm_new_user(user_data)
    
    return jsonify(user_data), 201

@bp.route('/users/<int:user_id>', methods=['PUT'])
@require_api_key
def update_user(user_id):
    """Update an existing user and notify projects-crm"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    # Update user fields
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    db.session.commit()
    
    # Notify projects-crm
    user_data = {
        'id': user.id,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'role': user.role,
        'is_active': user.is_active
    }
    
    try:
        webhook_url = 'http://localhost:5002/api/webhooks/user_updated'
        headers = {'Content-Type': 'application/json', 'X-Webhook-Secret': 'shared-secret-key'}
        requests.post(webhook_url, json=user_data, headers=headers, timeout=5)
    except Exception as e:
        print(f"Failed to notify projects-crm of user update: {e}")
    
    return jsonify(user_data)

@bp.route('/brands/sync-to-ekranu', methods=['POST'])
@require_api_key
def sync_brands_to_ekranu():
    """Send active brands to ekranu-crm as kampanijos (clients)"""
    try:
        # Get all active brands with their companies
        brands = Brand.query.join(Company).filter(Brand.status == 'active').all()
        
        # Prepare data for ekranu-crm
        brands_data = []
        for brand in brands:
            brands_data.append({
                'name': brand.name,
                'company': brand.company.name,
                'company_vat': brand.company.vat_code,
                'email': '',  # We'll use company contact if available
                'phone': '',  # We'll use company contact if available
                'contact_person': '',  # We'll use brand team contact if available
                'external_id': f'agency_brand_{brand.id}'  # Unique identifier
            })
        
        # Send to ekranu-crm
        ekranu_url = 'http://172.20.89.236:5003/api/import-brands'
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': 'ekranu-crm-api-key'  # This should match the key in ekranu-crm
        }
        
        response = requests.post(ekranu_url, json={'brands': brands_data}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'success': True,
                'message': f'Successfully synced {len(brands_data)} brands to ekranu-crm',
                'synced_count': result.get('imported_count', len(brands_data))
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to sync brands: {response.text}'
            }), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'message': f'Connection error to ekranu-crm: {str(e)}'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error syncing brands: {str(e)}'
        }), 500