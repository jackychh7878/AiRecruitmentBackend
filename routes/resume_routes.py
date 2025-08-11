from flask import request
from flask_restx import Namespace, Resource
from database import db
from models import CandidateResume, CandidateMasterProfile
from datetime import datetime

resume_ns = Namespace('resumes', description='Resume operations')

@resume_ns.route('/')
class ResumeList(Resource):
    def get(self):
        """Get all resume records"""
        return {'message': 'Resume endpoint - under construction with Swagger'}, 200
    
    def post(self):
        """Create a new resume record"""
        return {'message': 'Create resume endpoint - under construction'}, 201 