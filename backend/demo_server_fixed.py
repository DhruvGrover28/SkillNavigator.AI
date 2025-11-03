#!/usr/bin/env python3
"""
Fixed Demo Server for SkillNavigator Resume Parser
Provides working API endpoints with correct data structure
"""

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title='SkillNavigator Demo API')

# Enable CORS for frontend ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173', 
        'http://localhost:5174', 
        'http://localhost:5175', 
        'http://localhost:5176'
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

@app.post('/api/resume/parse')
async def parse_resume(file: UploadFile = File(...)):
    """
    Parse resume file and return structured data
    Returns data in the format expected by the frontend
    """
    # Demo parsed data with correct structure
    demo_parsed_data = {
        'success': True,
        'personal_info': {
            'first_name': 'John',
            'last_name': 'Smith',
            'full_name': 'John Smith',
            'email': 'john.smith@email.com',
            'phone': '+1-555-123-4567',
            'location': 'San Francisco, CA',
            'linkedin': 'linkedin.com/in/johnsmith',
            'portfolio': 'johnsmith.dev'
        },
        'contact_info': {
            'email': 'john.smith@email.com',
            'phone': '+1-555-123-4567',
            'address': 'San Francisco, CA',
            'linkedin': 'linkedin.com/in/johnsmith',
            'github': 'github.com/johnsmith',
            'website': 'johnsmith.dev'
        },
        'skills': [
            'JavaScript', 'Python', 'React', 'Node.js', 'SQL', 'Git',
            'HTML/CSS', 'MongoDB', 'Express.js', 'RESTful APIs',
            'Machine Learning', 'Data Analysis', 'Project Management',
            'Docker', 'AWS', 'TypeScript', 'PostgreSQL'
        ],
        'experience': [
            {
                'company': 'Tech Solutions Inc.',
                'title': 'Senior Software Developer',
                'position': 'Senior Software Developer',
                'duration': '2021 - Present',
                'description': 'Led development of web applications using React and Node.js. Managed team of 4 developers and delivered 12+ projects successfully.'
            },
            {
                'company': 'StartupXYZ',
                'title': 'Full Stack Developer',
                'position': 'Full Stack Developer', 
                'duration': '2019 - 2021',
                'description': 'Built scalable web applications and APIs. Implemented CI/CD pipelines and reduced deployment time by 60%.'
            },
            {
                'company': 'Digital Agency Co.',
                'title': 'Junior Developer',
                'position': 'Junior Developer',
                'duration': '2018 - 2019', 
                'description': 'Developed responsive websites and maintained legacy systems. Collaborated with design team on 20+ client projects.'
            }
        ],
        'education': [
            {
                'institution': 'University of Technology',
                'degree': 'Bachelor of Science in Computer Science',
                'field': 'Computer Science',
                'year': '2019',
                'gpa': '3.8',
                'graduation_year': '2019'
            }
        ],
        'summary': 'Experienced software developer with 5+ years in full-stack development. Passionate about creating scalable web applications and leading development teams. Proficient in modern JavaScript frameworks and cloud technologies.',
        'certifications': [
            {
                'name': 'AWS Certified Developer',
                'issuer': 'Amazon Web Services',
                'year': '2022'
            },
            {
                'name': 'React Developer Certification',
                'issuer': 'Meta',
                'year': '2021'
            }
        ]
    }
    
    # Return in the format expected by frontend
    return {
        'success': True,
        'parsed_data': demo_parsed_data,
        'message': f'Successfully parsed resume: {file.filename}'
    }

@app.get('/api/health')
async def health_check():
    """Health check endpoint"""
    return {'status': 'healthy', 'service': 'SkillNavigator Demo API'}

@app.get('/')
async def root():
    """Root endpoint"""
    return {'message': 'SkillNavigator Demo API Server', 'version': '1.0.0'}

if __name__ == '__main__':
    print('🚀 Starting SkillNavigator Demo API Server on port 8001...')
    print('📋 Resume parser endpoint: http://localhost:8001/api/resume/parse')
    print('🏥 Health check: http://localhost:8001/api/health')
    uvicorn.run(app, host='0.0.0.0', port=8001)