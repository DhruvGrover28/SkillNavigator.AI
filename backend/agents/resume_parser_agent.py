#!/usr/bin/env python3
"""
Resume Parser Agent - Extracts structured information from uploaded resume files
Simplified version for reliable text and skill extraction
"""

import os
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import logging

# PDF parsing
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

# DOC/DOCX parsing  
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

class ResumeParserAgent:
    """
    Simplified resume parser that extracts skills and basic information from resumes
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Common technical skills for extraction
        self.skill_keywords = [
            # Programming Languages
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Ruby', 'PHP', 'Go', 'Rust', 'Swift',
            'TypeScript', 'HTML', 'CSS', 'SQL', 'R', 'Scala', 'Kotlin', 'Dart', 'C',
            
            # Frameworks/Libraries
            'React', 'Angular', 'Vue', 'Node.js', 'Django', 'Flask', 'Spring', 'Laravel',
            'Express', 'FastAPI', 'Rails', 'ASP.NET', 'jQuery', 'Bootstrap', 'Tailwind',
            
            # Databases
            'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite', 'Oracle', 'DynamoDB',
            'Elasticsearch', 'Cassandra', 'Neo4j',
            
            # Cloud/DevOps
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Jenkins', 'Git', 'GitHub',
            'GitLab', 'CI/CD', 'Terraform', 'Ansible', 'Linux', 'Ubuntu',
            
            # Data Science/AI
            'Machine Learning', 'Deep Learning', 'TensorFlow', 'PyTorch', 'Pandas',
            'NumPy', 'Scikit-learn', 'Jupyter', 'Data Analysis', 'Statistics',
            
            # Other
            'Agile', 'Scrum', 'REST API', 'GraphQL', 'Microservices', 'Testing',
            'Unit Testing', 'Integration Testing', 'Selenium', 'Jest'
        ]
    
    def parse_resume(self, file_path: str, filename: str) -> Dict[str, Any]:
        """
        Parse resume from file and return structured data with skills
        
        Args:
            file_path: Path to the resume file
            filename: Original filename for format detection
            
        Returns:
            Dictionary with parsed resume data
        """
        try:
            # Extract text from file
            text = self._extract_text(file_path, filename)
            
            if not text or len(text.strip()) == 0:
                return {
                    'success': False,
                    'error': 'Could not extract text from resume file or file is empty'
                }
            
            # Extract skills from text
            skills = self._extract_skills(text)
            
            # Extract basic personal information
            personal_info = self._extract_basic_info(text)
            
            # Create contact_info from extracted personal_info for backward compatibility
            contact_info = {
                'email': personal_info.get('email', ''),
                'phone': personal_info.get('phone', ''),
                'linkedin': personal_info.get('linkedin', ''),
                'address': '',  # Not implemented yet
                'github': '',   # Not implemented yet
                'website': ''   # Not implemented yet
            }
            
            # Return structured data
            return {
                'success': True,
                'filename': filename,
                'parsed_at': datetime.utcnow().isoformat(),
                'skills': skills,
                'personal_info': personal_info,
                'experience': [],  # Placeholder
                'education': [],   # Placeholder
                'contact_info': contact_info,  # Now populated with extracted data
                'raw_text': text[:500] + '...' if len(text) > 500 else text
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing resume: {str(e)}")
            return {
                'success': False,
                'error': f'Error parsing resume: {str(e)}'
            }
    
    def _extract_text(self, file_path: str, filename: str) -> str:
        """Extract text content from various file formats"""
        
        file_ext = os.path.splitext(filename.lower())[1]
        
        try:
            if file_ext == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_ext in ['.doc', '.docx']:
                return self._extract_docx_text(file_path)
            elif file_ext == '.txt':
                return self._extract_txt_text(file_path)
            else:
                # For unsupported formats, try to read as text
                try:
                    return self._extract_txt_text(file_path)
                except:
                    raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            self.logger.error(f"Error extracting text: {str(e)}")
            raise
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file using PyPDF2"""
        if not HAS_PDF:
            raise ValueError("PDF parsing not available. Please install PyPDF2 library.")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise ValueError(f"Error extracting PDF text: {str(e)}")
        
        return text.strip()
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        if not HAS_DOCX:
            raise ValueError("DOCX parsing not available. Please install python-docx library.")
        
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error extracting DOCX text: {str(e)}")
    
    def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read().strip()
        except Exception as e:
            raise ValueError(f"Error reading text file: {str(e)}")
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical skills from resume text"""
        found_skills = []
        text_lower = text.lower()
        
        # Look for skills in the text (case-insensitive)
        for skill in self.skill_keywords:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        # Remove duplicates and return
        return list(set(found_skills))
    
    def _extract_basic_info(self, text: str) -> Dict[str, str]:
        """Extract basic personal information from resume text"""
        
        info = {
            'first_name': '',
            'last_name': '',
            'full_name': '',
            'email': '',
            'phone': '',
            'linkedin': ''
        }
        
        lines = text.split('\n')
        
        # Extract name - look for capitalized words in first few lines
        for line in lines[:5]:
            line = line.strip()
            if len(line) > 0 and len(line) < 50:  # Reasonable name length
                words = line.split()
                # Look for lines with 2-4 capitalized words (likely names)
                if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word.isalpha()):
                    # Check if it looks like a name (no numbers, reasonable length)
                    if not any(char.isdigit() for char in line) and not '@' in line and 'linkedin' not in line.lower():
                        info['full_name'] = line
                        info['first_name'] = words[0]
                        if len(words) > 1:
                            info['last_name'] = ' '.join(words[1:])
                        break
        
        # Extract email using regex
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        if email_matches:
            info['email'] = email_matches[0]
        
        # Extract phone number patterns
        phone_patterns = [
            r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (555) 123-4567, 555-123-4567, 555.123.4567, 555 123 4567
            r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1 555 123 4567
            r'\d{10}',  # 5551234567
        ]
        
        for pattern in phone_patterns:
            phone_matches = re.findall(pattern, text)
            if phone_matches:
                # Clean up the phone number
                phone = re.sub(r'[^\d+]', '', phone_matches[0])
                if len(phone) >= 10:
                    info['phone'] = phone_matches[0]
                    break
        
        # Extract LinkedIn profile
        linkedin_patterns = [
            r'linkedin\.com/in/[\w-]+',
            r'www\.linkedin\.com/in/[\w-]+',
            r'https?://(?:www\.)?linkedin\.com/in/[\w-]+',
            r'LinkedIn:\s*([^\s\n]+)',
            r'linkedin\.com/[\w-]+',
        ]
        
        for pattern in linkedin_patterns:
            linkedin_matches = re.findall(pattern, text, re.IGNORECASE)
            if linkedin_matches:
                linkedin_url = linkedin_matches[0]
                # Clean up LinkedIn URL
                if not linkedin_url.startswith('http'):
                    if not linkedin_url.startswith('www.'):
                        linkedin_url = 'https://www.' + linkedin_url
                    else:
                        linkedin_url = 'https://' + linkedin_url
                info['linkedin'] = linkedin_url
                break
        
        return info


# Demo/Testing functions
def demo_parse_resume():
    """Demo function to test resume parsing"""
    
    sample_resume_text = """
    John Smith
    Software Engineer
    Email: john.smith@email.com
    Phone: (555) 123-4567
    LinkedIn: linkedin.com/in/johnsmith
    
    EXPERIENCE
    Senior Software Engineer - Tech Corp
    Full Stack Developer - StartupXYZ
    
    EDUCATION  
    Bachelor of Science Computer Science - MIT
    
    SKILLS
    Python, JavaScript, React, Node.js, AWS, Docker, MySQL
    """
    
    parser = ResumeParserAgent()
    
    # Create a temporary file for testing
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_resume_text)
        temp_file = f.name
    
    try:
        result = parser.parse_resume(temp_file, 'sample_resume.txt')
        print("Demo Resume Parse Result:")
        print(json.dumps(result, indent=2))
        return result
    finally:
        import os
        os.unlink(temp_file)

if __name__ == "__main__":
    demo_parse_resume()