from flask import Blueprint, request, jsonify
from app import db
from models import AiRecruitmentComCode
from datetime import datetime

lookup_bp = Blueprint('lookup', __name__)

@lookup_bp.route('/', methods=['GET'])
def get_all_lookup_codes():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        is_active = request.args.get('is_active', type=bool)
        category = request.args.get('category')
        
        query = AiRecruitmentComCode.query
        if is_active is not None:
            query = query.filter(AiRecruitmentComCode.is_active == is_active)
        if category:
            query = query.filter(AiRecruitmentComCode.category.ilike(f'%{category}%'))
        
        records = query.order_by(AiRecruitmentComCode.category, AiRecruitmentComCode.com_code).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'lookup_codes': [record.to_dict() for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookup_bp.route('/<string:category>', methods=['GET'])
def get_lookup_by_category(category):
    try:
        records = AiRecruitmentComCode.query.filter_by(
            category=category, is_active=True
        ).order_by(AiRecruitmentComCode.com_code).all()
        
        return jsonify({
            'category': category,
            'codes': [record.to_dict() for record in records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookup_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        categories = db.session.query(AiRecruitmentComCode.category).filter_by(
            is_active=True
        ).distinct().order_by(AiRecruitmentComCode.category).all()
        
        return jsonify({
            'categories': [cat[0] for cat in categories]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lookup_bp.route('/', methods=['POST'])
def create_lookup_code():
    try:
        data = request.get_json()
        
        required_fields = ['category', 'com_code']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if combination already exists
        existing = AiRecruitmentComCode.query.filter_by(
            category=data['category'],
            com_code=data['com_code']
        ).first()
        
        if existing:
            return jsonify({'error': 'This category and code combination already exists'}), 400
        
        record = AiRecruitmentComCode(
            category=data['category'],
            com_code=data['com_code'],
            description=data.get('description')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'message': 'Lookup code created successfully',
            'lookup_code': record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lookup_bp.route('/<int:lookup_id>', methods=['PUT'])
def update_lookup_code(lookup_id):
    try:
        record = AiRecruitmentComCode.query.get_or_404(lookup_id)
        data = request.get_json()
        
        # Check if category/com_code combination would be duplicate
        if 'category' in data or 'com_code' in data:
            new_category = data.get('category', record.category)
            new_com_code = data.get('com_code', record.com_code)
            
            existing = AiRecruitmentComCode.query.filter_by(
                category=new_category,
                com_code=new_com_code
            ).filter(AiRecruitmentComCode.id != lookup_id).first()
            
            if existing:
                return jsonify({'error': 'This category and code combination already exists'}), 400
        
        updatable_fields = ['category', 'com_code', 'description', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(record, field, data[field])
        
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Lookup code updated successfully',
            'lookup_code': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@lookup_bp.route('/<int:lookup_id>', methods=['DELETE'])
def delete_lookup_code(lookup_id):
    try:
        record = AiRecruitmentComCode.query.get_or_404(lookup_id)
        record.is_active = False
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Lookup code deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 