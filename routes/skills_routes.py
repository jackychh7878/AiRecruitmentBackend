from flask import request
from flask_restx import Namespace, Resource
from database import db
from models import CandidateSkills, CandidateMasterProfile, CandidateCareerHistory
from datetime import datetime

skills_ns = Namespace('skills', description='Skills operations')

@skills_ns.route('/')
class SkillsList(Resource):
    def get(self):
        """Get all skills"""
        return {'message': 'Skills endpoint - under construction with Swagger'}, 200
    
    def post(self):
        """Create a new skill"""
        return {'message': 'Create skill endpoint - under construction'}, 201 