#!/usr/bin/env python3
"""
Job Scoring Agent - AI-driven candidate-job fit evaluation system
Uses weighted semantic similarity with transformer embeddings for intelligent job matching

Features:
- Semantic text embeddings using Sentence-BERT
- Section-wise similarity computation (skills, experience, education)
- Weighted scoring formula with configurable weights
- Score normalization and classification (0-100 scale)
- Explainable results with section breakdown
"""

import os
import re
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Sentence-BERT for semantic embeddings
try:
    from sentence_transformers import SentenceTransformer
    HAS_SBERT = True
    print("✅ Sentence-BERT available for semantic embeddings")
except ImportError:
    HAS_SBERT = False
    print("⚠️  Sentence-BERT not available, using TF-IDF fallback")

@dataclass
class ScoringResult:
    """Result of job-candidate scoring evaluation"""
    total_score: float
    classification: str
    section_scores: Dict[str, float]
    explanation: str
    metadata: Dict[str, Any]

@dataclass
class ScoringWeights:
    """Configurable weights for different sections"""
    skills: float = 0.7      # Further increased - skills are most critical
    experience: float = 0.2  # Reduced to balance
    education: float = 0.1   # Minimized - less predictive of job performance
    
    def __post_init__(self):
        # Ensure weights sum to 1.0
        total = self.skills + self.experience + self.education
        if abs(total - 1.0) > 0.01:
            self.skills /= total
            self.experience /= total
            self.education /= total

class JobScoringAgent:
    """
    AI-powered job scoring agent using weighted semantic similarity
    
    Architecture:
    1. Input: Parsed resume + job description
    2. Preprocessing: Extract and clean sections
    3. Feature Extraction: Generate embeddings using SBERT/TF-IDF
    4. Similarity Computation: Cosine similarity per section
    5. Scoring Formula: Weighted aggregation
    6. Classification: Score-based fit categories
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", weights: Optional[ScoringWeights] = None):
        """
        Initialize the scoring agent
        
        Args:
            model_name: Sentence-BERT model name
            weights: Custom section weights (defaults to balanced)
        """
        self.logger = logging.getLogger(__name__)
        self.weights = weights or ScoringWeights()
        
        # Initialize embedding model
        self.embedding_model = None
        self.tfidf_vectorizer = None
        
        if HAS_SBERT:
            try:
                self.embedding_model = SentenceTransformer(model_name)
                self.embedding_method = "sbert"
                self.logger.info(f"Loaded Sentence-BERT model: {model_name}")
            except Exception as e:
                self.logger.warning(f"Failed to load SBERT model: {e}")
                self._init_tfidf_fallback()
        else:
            self._init_tfidf_fallback()
    
    def _init_tfidf_fallback(self):
        """Initialize TF-IDF vectorizer as fallback"""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.embedding_method = "tfidf"
        self.logger.info("Using TF-IDF vectorizer as fallback")
    
    def score_candidate(self, resume_data: Dict[str, Any], job_description: Dict[str, Any]) -> ScoringResult:
        """
        Score candidate fit for a job using weighted semantic similarity
        
        Args:
            resume_data: Parsed resume data from resume parser
            job_description: Job posting data with description, requirements
            
        Returns:
            ScoringResult with total score, classification, and breakdown
        """
        try:
            # Extract and preprocess sections
            resume_sections = self._extract_resume_sections(resume_data)
            job_sections = self._extract_job_sections(job_description)
            
            # Compute section-wise similarities
            section_scores = {}
            
            # Skills similarity
            skills_sim = self._compute_section_similarity(
                resume_sections['skills'], 
                job_sections['skills']
            )
            section_scores['skills'] = skills_sim * 100  # Convert to 0-100
            
            # Experience similarity
            experience_sim = self._compute_section_similarity(
                resume_sections['experience'], 
                job_sections['experience']
            )
            section_scores['experience'] = experience_sim * 100
            
            # Education similarity
            education_sim = self._compute_section_similarity(
                resume_sections['education'], 
                job_sections['education']
            )
            section_scores['education'] = education_sim * 100
            
            # Calculate weighted total score
            weighted_score = (
                self.weights.skills * section_scores['skills'] +
                self.weights.experience * section_scores['experience'] +
                self.weights.education * section_scores['education']
            )
            
            # Apply score normalization boost (calibration adjustment)
            # Use progressive boost that helps high scores more
            if weighted_score >= 70:
                # Very strong boost for excellent matches
                normalized_score = weighted_score + (100 - weighted_score) * 0.35
            elif weighted_score >= 55:
                # Strong boost for good matches
                normalized_score = weighted_score + (100 - weighted_score) * 0.25
            else:
                # Light boost for lower matches
                normalized_score = weighted_score + (100 - weighted_score) * 0.08
            total_score = min(100.0, normalized_score)  # Cap at 100%
            
            # Classify fit level
            classification = self._classify_score(total_score)
            
            # Generate explanation
            explanation = self._generate_explanation(section_scores, classification)
            
            # Metadata
            metadata = {
                'scoring_method': self.embedding_method,
                'weights_used': {
                    'skills': self.weights.skills,
                    'experience': self.weights.experience,
                    'education': self.weights.education
                },
                'scored_at': datetime.utcnow().isoformat(),
                'model_name': getattr(self.embedding_model, 'model_name', 'tfidf') if self.embedding_model else 'tfidf'
            }
            
            return ScoringResult(
                total_score=round(total_score, 2),
                classification=classification,
                section_scores=section_scores,
                explanation=explanation,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error scoring candidate: {str(e)}")
            # Return default low score on error
            return ScoringResult(
                total_score=0.0,
                classification="Error",
                section_scores={'skills': 0, 'experience': 0, 'education': 0},
                explanation=f"Error during scoring: {str(e)}",
                metadata={'error': str(e)}
            )
    
    def _extract_resume_sections(self, resume_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract and clean resume sections for scoring"""
        sections = {
            'skills': '',
            'experience': '',
            'education': ''
        }
        
        # Skills - enhanced processing with synonyms (handle both list and string formats)
        if 'skills' in resume_data:
            if isinstance(resume_data['skills'], list):
                skills_text = ' '.join(resume_data['skills'])
            elif isinstance(resume_data['skills'], str):
                skills_text = resume_data['skills']
            else:
                skills_text = str(resume_data['skills'])
            
            # Add common variations and synonyms
            enhanced_skills = skills_text
            if 'JavaScript' in skills_text or 'Javascript' in skills_text:
                enhanced_skills += ' JS frontend web development'
            if 'React' in skills_text:
                enhanced_skills += ' ReactJS frontend UI component library'
            if 'Python' in skills_text:
                enhanced_skills += ' backend programming scripting'
            if 'Node.js' in skills_text or 'NodeJS' in skills_text:
                enhanced_skills += ' backend JavaScript server runtime'
            sections['skills'] = enhanced_skills
        
        # Experience (handle both list and string formats)
        if 'experience' in resume_data:
            if isinstance(resume_data['experience'], list):
                exp_texts = []
                for exp in resume_data['experience']:
                    if isinstance(exp, dict):
                        exp_text = f"{exp.get('title', '')} {exp.get('company', '')} {exp.get('description', '')}"
                        exp_texts.append(exp_text)
                sections['experience'] = ' '.join(exp_texts)
            elif isinstance(resume_data['experience'], str):
                sections['experience'] = resume_data['experience']
        
        # Education (handle both list and string formats)
        if 'education' in resume_data:
            if isinstance(resume_data['education'], list):
                edu_texts = []
                for edu in resume_data['education']:
                    if isinstance(edu, dict):
                        edu_text = f"{edu.get('degree', '')} {edu.get('field', '')} {edu.get('institution', '')}"
                        edu_texts.append(edu_text)
                sections['education'] = ' '.join(edu_texts)
            elif isinstance(resume_data['education'], str):
                sections['education'] = resume_data['education']
        
        return sections
    
    def _extract_job_sections(self, job_description: Dict[str, Any]) -> Dict[str, str]:
        """Extract and clean job description sections for scoring"""
        sections = {
            'skills': '',
            'experience': '',
            'education': ''
        }
        
        # Get full job description text
        job_text = ""
        if 'description' in job_description:
            job_text = job_description['description']
        elif 'summary' in job_description:
            job_text = job_description['summary']
        elif isinstance(job_description, str):
            job_text = job_description
        
        # Use keywords extraction for better section identification
        sections['skills'] = self._extract_skills_from_job(job_text)
        sections['experience'] = self._extract_experience_from_job(job_text)
        sections['education'] = self._extract_education_from_job(job_text)
        
        return sections
    
    def _extract_skills_from_job(self, job_text: str) -> str:
        """Extract skills-related content from job description with improved matching"""
        # Comprehensive skills keywords with synonyms
        skills_keywords = [
            # Programming Languages & Variants
            'python', 'javascript', 'js', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
            'typescript', 'ts', 'html', 'css', 'sql', 'r', 'scala', 'kotlin', 'dart',
            
            # Frameworks & Libraries (with variations)
            'react', 'reactjs', 'react.js', 'angular', 'angularjs', 'vue', 'vuejs', 'vue.js',
            'node', 'nodejs', 'node.js', 'django', 'flask', 'spring', 'laravel', 'express',
            'fastapi', 'rails', 'asp.net', 'jquery', 'bootstrap', 'tailwind',
            
            # Databases
            'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'sqlite', 'oracle',
            'dynamodb', 'elasticsearch', 'cassandra', 'neo4j', 'database',
            
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'k8s',
            'jenkins', 'git', 'github', 'gitlab', 'ci/cd', 'terraform', 'ansible',
            'linux', 'ubuntu', 'containerization', 'microservices',
            
            # Data Science & AI
            'machine learning', 'ml', 'deep learning', 'ai', 'tensorflow', 'pytorch',
            'pandas', 'numpy', 'scikit-learn', 'jupyter', 'data analysis', 'statistics',
            'data science', 'analytics', 'big data',
            
            # Web & API Development
            'rest api', 'restful', 'graphql', 'api development', 'web development',
            'frontend', 'backend', 'full stack', 'fullstack', 'responsive design',
            
            # Development Practices
            'agile', 'scrum', 'testing', 'unit testing', 'integration testing',
            'tdd', 'selenium', 'jest', 'cypress', 'debugging'
        ]
        
        found_skills = []
        job_lower = job_text.lower()
        
        # Enhanced keyword matching with partial matches
        for skill in skills_keywords:
            if skill in job_lower:
                found_skills.append(skill)
        
        # Extract from dedicated skills sections with better patterns
        skills_patterns = [
            r'(?:skills?|technologies?|requirements?|qualifications?)[:\-]\s*(.+?)(?:\n\n|\n[A-Z]|$)',
            r'(?:must have|required)[:\-]?\s*(.+?)(?:\n\n|\n[A-Z]|$)',
            r'(?:experience (?:with|in))[:\-]?\s*(.+?)(?:\n\n|\n[A-Z]|$)'
        ]
        
        for pattern in skills_patterns:
            matches = re.findall(pattern, job_text, re.IGNORECASE | re.DOTALL)
            for match in matches:
                found_skills.append(match.strip())
        
        return ' '.join(found_skills)
    
    def _extract_experience_from_job(self, job_text: str) -> str:
        """Extract experience-related content from job description"""
        # Look for experience requirements
        exp_patterns = [
            r'(\d+\+?\s*years?\s*(?:of\s*)?experience)',
            r'(experience\s+(?:in|with)[^.]+)',
            r'(responsibilities?[:\-]\s*[^.]+)',
            r'(you\s+will[^.]+)',
        ]
        
        experience_text = []
        for pattern in exp_patterns:
            matches = re.findall(pattern, job_text, re.IGNORECASE)
            experience_text.extend(matches)
        
        return ' '.join(experience_text)
    
    def _extract_education_from_job(self, job_text: str) -> str:
        """Extract education-related content from job description"""
        # Look for education requirements
        edu_patterns = [
            r'(bachelor\'?s?\s+(?:degree)?[^.]*)',
            r'(master\'?s?\s+(?:degree)?[^.]*)',
            r'(phd|doctorate[^.]*)',
            r'(degree\s+in[^.]+)',
            r'(education[:\-][^.]+)'
        ]
        
        education_text = []
        for pattern in edu_patterns:
            matches = re.findall(pattern, job_text, re.IGNORECASE)
            education_text.extend(matches)
        
        return ' '.join(education_text)
    
    def _compute_section_similarity(self, section1: str, section2: str) -> float:
        """Compute cosine similarity between two text sections with keyword boosting"""
        if not section1.strip() or not section2.strip():
            return 0.0
        
        try:
            base_similarity = 0.0
            
            if self.embedding_method == "sbert" and self.embedding_model:
                # Use Sentence-BERT embeddings
                embeddings = self.embedding_model.encode([section1, section2])
                base_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
                base_similarity = max(0.0, base_similarity)  # Ensure non-negative
                
                # Add keyword matching boost for skills sections
                keyword_boost = self._compute_keyword_match_boost(section1, section2)
                enhanced_similarity = min(1.0, base_similarity + keyword_boost)
                
                return enhanced_similarity
            
            elif self.embedding_method == "tfidf" and self.tfidf_vectorizer:
                # Use TF-IDF vectors
                vectors = self.tfidf_vectorizer.fit_transform([section1, section2])
                similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
                return max(0.0, similarity)
            
            else:
                # Fallback to simple word overlap
                words1 = set(section1.lower().split())
                words2 = set(section2.lower().split())
                if not words1 or not words2:
                    return 0.0
                
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                return intersection / union if union > 0 else 0.0
                
        except Exception as e:
            self.logger.warning(f"Error computing similarity: {e}")
            return 0.0
    
    def _compute_keyword_match_boost(self, section1: str, section2: str) -> float:
        """Compute boost for exact keyword matches - especially important for skills"""
        # Common technical skills and technologies
        important_keywords = {
            # Programming languages
            'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
            'typescript', 'html', 'css', 'sql', 'r', 'scala', 'kotlin', 'dart',
            # Frameworks
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel', 'rails',
            'express', 'fastapi', 'nodejs', 'node.js', 'next.js', 'nuxt',
            # Databases
            'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'cassandra',
            # Cloud & DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'github', 'gitlab',
            # Tools & Technologies
            'git', 'linux', 'unix', 'bash', 'powershell', 'terraform', 'ansible',
        }
        
        # Normalize text
        text1 = section1.lower().replace('.', '').replace(',', '').replace('-', '')
        text2 = section2.lower().replace('.', '').replace(',', '').replace('-', '')
        
        # Extract words
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Find matches in important keywords
        matched_keywords = words1.intersection(words2).intersection(important_keywords)
        
        # Calculate boost (0.05 per matched important keyword, max 0.2)
        boost = min(0.2, len(matched_keywords) * 0.05)
        
        return boost
    
    def _classify_score(self, score: float) -> str:
        """Classify score into fit categories with calibrated thresholds"""
        if score >= 80:      # High bar for excellent - only truly perfect matches
            return "Excellent Fit"
        elif score >= 65:    # Good matches should be clearly above average
            return "Good Fit"
        elif score >= 40:    # Fair matches have some relevance but gaps
            return "Fair Fit"
        else:
            return "Poor Fit"
    
    def _generate_explanation(self, section_scores: Dict[str, float], classification: str) -> str:
        """Generate human-readable explanation of the scoring"""
        explanations = []
        
        # Section analysis
        for section, score in section_scores.items():
            if score >= 80:
                explanations.append(f"Strong {section} alignment ({score:.1f}%)")
            elif score >= 60:
                explanations.append(f"Good {section} match ({score:.1f}%)")
            elif score >= 30:
                explanations.append(f"Moderate {section} alignment ({score:.1f}%)")
            else:
                explanations.append(f"Limited {section} match ({score:.1f}%)")
        
        # Overall classification
        base_explanation = f"Overall classification: {classification}. "
        section_explanation = ". ".join(explanations)
        
        return base_explanation + section_explanation + "."
    
    def should_filter_job(self, score: float, min_threshold: float = 30.0) -> bool:
        """Determine if job should be filtered out based on score"""
        return score < min_threshold
    
    def batch_score_jobs(self, resume_data: Dict[str, Any], jobs: List[Dict[str, Any]], 
                        filter_threshold: float = 30.0) -> List[Tuple[Dict[str, Any], ScoringResult]]:
        """
        Score multiple jobs for a candidate and filter out poor matches
        
        Args:
            resume_data: Parsed resume data
            jobs: List of job postings
            filter_threshold: Minimum score to include job
            
        Returns:
            List of (job, scoring_result) tuples, sorted by score descending
        """
        scored_jobs = []
        
        for job in jobs:
            try:
                scoring_result = self.score_candidate(resume_data, job)
                
                # Only include jobs above threshold
                if not self.should_filter_job(scoring_result.total_score, filter_threshold):
                    scored_jobs.append((job, scoring_result))
                    
            except Exception as e:
                self.logger.error(f"Error scoring job {job.get('id', 'unknown')}: {e}")
                continue
        
        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[1].total_score, reverse=True)
        
        return scored_jobs

# Demo function for testing
def demo_scoring():
    """Demo function to test the scoring agent"""
    
    # Sample resume data
    resume_data = {
        'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Machine Learning'],
        'experience': [
            {
                'title': 'Software Developer',
                'company': 'Tech Corp',
                'description': 'Developed web applications using React and Node.js'
            }
        ],
        'education': [
            {
                'degree': 'Bachelor of Technology',
                'field': 'Computer Science',
                'institution': 'Tech University'
            }
        ]
    }
    
    # Sample job description
    job_description = {
        'description': '''
        We are looking for a Python Developer with experience in web development.
        Requirements: 2+ years experience with Python, JavaScript, React.
        Bachelor's degree in Computer Science or related field.
        Skills: Python, React, SQL, API development.
        '''
    }
    
    # Initialize scoring agent
    scoring_agent = JobScoringAgent()
    
    # Score the candidate
    result = scoring_agent.score_candidate(resume_data, job_description)
    
    print("=== Job Scoring Demo ===")
    print(f"Total Score: {result.total_score}")
    print(f"Classification: {result.classification}")
    print(f"Section Scores: {result.section_scores}")
    print(f"Explanation: {result.explanation}")
    print(f"Method: {result.metadata.get('scoring_method', 'unknown')}")

if __name__ == "__main__":
    demo_scoring()