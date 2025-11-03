#!/usr/bin/env python3
"""
Enhanced Demo Server for SkillNavigator Resume Parser with PDF Support
Integrates with existing resume_parser_agent.py for real text parsing
"""

import uvicorn
import tempfile
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json

# Import our existing resume parser
try:
    from agents.resume_parser_agent import ResumeParserAgent
    HAS_PARSER = True
    print("✅ Resume parser agent loaded successfully")
except ImportError as e:
    HAS_PARSER = False
    print(f"⚠️  Resume parser agent not available: {e}")

app = FastAPI(title='SkillNavigator Enhanced Demo API')

# Enable CORS for frontend ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:5173', 
        'http://localhost:5174', 
        'http://localhost:5175', 
        'http://localhost:5176',
        'http://localhost:5177'
    ],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_demo_data():
    """Return demo data in the correct format for frontend"""
    return {
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
        'summary': 'Experienced software developer with 5+ years in full-stack development. Passionate about creating scalable web applications and leading development teams.',
        'certifications': [
            {
                'name': 'AWS Certified Developer',
                'issuer': 'Amazon Web Services',
                'year': '2022'
            }
        ]
    }

@app.post('/api/resume/parse')
async def parse_resume(file: UploadFile = File(...)):
    """
    Parse resume file and return structured data
    Supports TXT and PDF files with text extraction and parsing
    """
    try:
        print(f"📄 Processing file: {file.filename} (Content-Type: {file.content_type})")
        
        # Check file size (max 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
        
        # Check if we have the parser available
        if not HAS_PARSER:
            print("⚠️  Using demo data - parser not available")
            return {
                'success': True,
                'parsed_data': get_demo_data(),
                'message': f'Demo parsing for {file.filename} (parser not available)',
                'source': 'demo'
            }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Use real resume parser
            parser = ResumeParserAgent()
            result = parser.parse_resume(temp_file_path, file.filename)
            
            print(f"📊 Parser result success: {result.get('success', False)}")
            
            if result.get('success'):
                # Format result for frontend
                parsed_data = {
                    'success': True,
                    'personal_info': result.get('personal_info', {}),
                    'contact_info': result.get('contact_info', {}),
                    'skills': result.get('skills', []),
                    'experience': result.get('experience', []),
                    'education': result.get('education', []),
                    'summary': result.get('summary', ''),
                    'certifications': result.get('certifications', [])
                }
                
                print(f"✅ Successfully parsed {file.filename}")
                print(f"   - Skills found: {len(parsed_data['skills'])}")
                print(f"   - Experience entries: {len(parsed_data['experience'])}")
                print(f"   - Education entries: {len(parsed_data['education'])}")
                
                return {
                    'success': True,
                    'parsed_data': parsed_data,
                    'message': f'Successfully parsed {file.filename}',
                    'source': 'real_parser'
                }
            else:
                print(f"❌ Parser failed: {result.get('error', 'Unknown error')}")
                # Fallback to demo data
                return {
                    'success': True,
                    'parsed_data': get_demo_data(),
                    'message': f'Fallback demo data for {file.filename} (parsing failed)',
                    'source': 'demo_fallback',
                    'parse_error': result.get('error')
                }
                
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        print(f"💥 Error processing {file.filename}: {str(e)}")
        # Return demo data on any error
        return {
            'success': True,
            'parsed_data': get_demo_data(),
            'message': f'Demo data for {file.filename} (error occurred)',
            'source': 'demo_error',
            'error': str(e)
        }

@app.get('/api/health')
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy', 
        'service': 'SkillNavigator Enhanced Demo API',
        'parser_available': HAS_PARSER
    }

@app.get('/')
async def root():
    """Root endpoint"""
    return {
        'message': 'SkillNavigator Enhanced Demo API Server', 
        'version': '2.0.0',
        'features': ['txt_parsing', 'pdf_parsing' if HAS_PARSER else 'demo_only'],
        'parser_status': 'available' if HAS_PARSER else 'unavailable'
    }

if __name__ == '__main__':
    print('🚀 Starting SkillNavigator Enhanced Demo API Server on port 8001...')
    print('📋 Resume parser endpoint: http://localhost:8001/api/resume/parse')
    print('🏥 Health check: http://localhost:8001/api/health')
    print(f'🔧 Parser status: {"✅ Available" if HAS_PARSER else "❌ Not Available (demo mode)"}')
    uvicorn.run(app, host='0.0.0.0', port=8001)