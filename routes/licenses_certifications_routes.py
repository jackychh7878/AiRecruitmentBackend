from flask import request
from flask_restx import Namespace, Resource
from database import db
from models import CandidateLicensesCertifications, CandidateMasterProfile
from datetime import datetime

licenses_certifications_ns = Namespace('licenses_certifications', description='Licenses and certifications operations')

@licenses_certifications_ns.route('/')
class LicensesCertificationsList(Resource):
    def get(self):
        """Get all licenses and certifications"""
        return {'message': 'Licenses and certifications endpoint - under construction with Swagger'}, 200
    
    def post(self):
        """Create a new license or certification"""
        return {'message': 'Create license/certification endpoint - under construction'}, 201 