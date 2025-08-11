from flask import request
from flask_restx import Namespace, Resource
from database import db
from models import CandidateEducation, CandidateMasterProfile
from datetime import datetime

education_ns = Namespace('education', description='Education operations')

@education_ns.route('/')
class EducationList(Resource):
    def get(self):
        """Get all education records"""
        return {'message': 'Education endpoint - under construction with Swagger'}, 200
    
    def post(self):
        """Create a new education record"""
        return {'message': 'Create education endpoint - under construction'}, 201 