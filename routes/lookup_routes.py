from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import AiRecruitmentComCode
from datetime import datetime

# Create namespace
lookup_ns = Namespace('lookups', description='Lookup code operations')

# Define data models for Swagger documentation
lookup_model = lookup_ns.model('LookupCode', {
    'id': fields.Integer(readonly=True, description='Lookup ID'),
    'category': fields.String(required=True, description='Category'),
    'com_code': fields.String(required=True, description='Code'),
    'description': fields.String(description='Description'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

lookup_input_model = lookup_ns.model('LookupCodeInput', {
    'category': fields.String(required=True, description='Category'),
    'com_code': fields.String(required=True, description='Code'),
    'description': fields.String(description='Description')
})

lookup_list_model = lookup_ns.model('LookupCodeList', {
    'lookup_codes': fields.List(fields.Nested(lookup_model)),
    'total': fields.Integer(description='Total number of records'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

@lookup_ns.route('/')
class LookupCodeList(Resource):
    @lookup_ns.doc('get_all_lookup_codes')
    @lookup_ns.marshal_with(lookup_list_model)
    @lookup_ns.param('page', 'Page number', type=int, default=1)
    @lookup_ns.param('per_page', 'Items per page', type=int, default=50)
    @lookup_ns.param('is_active', 'Filter by active status', type=bool)
    @lookup_ns.param('category', 'Filter by category')
    def get(self):
        """Get all lookup codes with optional filtering"""
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
            
            return {
                'lookup_codes': [record.to_dict() for record in records.items],
                'total': records.total,
                'pages': records.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
        except Exception as e:
            lookup_ns.abort(500, str(e))

    @lookup_ns.doc('create_lookup_code')
    @lookup_ns.expect(lookup_input_model)
    @lookup_ns.marshal_with(lookup_model, code=201)
    def post(self):
        """Create a new lookup code"""
        try:
            data = request.get_json()
            
            required_fields = ['category', 'com_code']
            for field in required_fields:
                if field not in data or not data[field]:
                    lookup_ns.abort(400, f'{field} is required')
            
            # Check if combination already exists
            existing = AiRecruitmentComCode.query.filter_by(
                category=data['category'],
                com_code=data['com_code']
            ).first()
            
            if existing:
                lookup_ns.abort(400, 'This category and code combination already exists')
            
            record = AiRecruitmentComCode(
                category=data['category'],
                com_code=data['com_code'],
                description=data.get('description')
            )
            
            db.session.add(record)
            db.session.commit()
            
            return record.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            lookup_ns.abort(500, str(e))

@lookup_ns.route('/<string:category>')
@lookup_ns.param('category', 'Category name')
class LookupByCategory(Resource):
    @lookup_ns.doc('get_lookup_by_category')
    def get(self, category):
        """Get lookup codes by category"""
        try:
            records = AiRecruitmentComCode.query.filter_by(
                category=category, is_active=True
            ).order_by(AiRecruitmentComCode.com_code).all()
            
            return {
                'category': category,
                'codes': [record.to_dict() for record in records]
            }, 200
        except Exception as e:
            lookup_ns.abort(500, str(e))

@lookup_ns.route('/categories')
class Categories(Resource):
    @lookup_ns.doc('get_categories')
    def get(self):
        """Get all distinct categories"""
        try:
            categories = db.session.query(AiRecruitmentComCode.category).filter_by(
                is_active=True
            ).distinct().order_by(AiRecruitmentComCode.category).all()
            
            return {
                'categories': [cat[0] for cat in categories]
            }, 200
        except Exception as e:
            lookup_ns.abort(500, str(e))

@lookup_ns.route('/<int:lookup_id>')
@lookup_ns.param('lookup_id', 'Lookup ID')
class LookupCode(Resource):
    @lookup_ns.doc('update_lookup_code')
    @lookup_ns.expect(lookup_input_model)
    @lookup_ns.marshal_with(lookup_model)
    def put(self, lookup_id):
        """Update an existing lookup code"""
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
                    lookup_ns.abort(400, 'This category and code combination already exists')
            
            updatable_fields = ['category', 'com_code', 'description', 'is_active']
            for field in updatable_fields:
                if field in data:
                    setattr(record, field, data[field])
            
            record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return record.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            lookup_ns.abort(500, str(e))

    @lookup_ns.doc('delete_lookup_code')
    def delete(self, lookup_id):
        """Delete a lookup code (soft delete)"""
        try:
            record = AiRecruitmentComCode.query.get_or_404(lookup_id)
            record.is_active = False
            record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Lookup code deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            lookup_ns.abort(500, str(e)) 