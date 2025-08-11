from flask import request
from flask_restx import Namespace, Resource
from database import db
from models import CandidateLanguages, CandidateMasterProfile
from datetime import datetime

languages_ns = Namespace('languages', description='Languages operations')

@languages_ns.route('/')
class LanguagesList(Resource):
    def get(self):
        """Get all language records"""
        return {'message': 'Languages endpoint - under construction with Swagger'}, 200
    
    def post(self):
        """Create a new language record"""
        return {'message': 'Create language endpoint - under construction'}, 201 