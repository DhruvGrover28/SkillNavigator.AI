"""
Scoring Agent - AI-Powered Job Matching
Uses semantic matching and ML algorithms to score jobs based on user profiles
"""

import logging
import os
from typing import List, Dict, Tuple, Optional
import json
import asyncio

import openai
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database.db_connection import database
from utils.matching import (
    extract_features_from_job,
    extract_features_from_profile,
    calculate_skill_match,
    normalize_score
)

logger = logging.getLogger(__name__)


class ScoringAgent:
    """Autonomous agent for scoring and ranking jobs based on user preferences"""
    
    def __init__(self):
        self.openai_client = None
        self.sentence_model = None
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.user_profile_cache = {}
        
        # Scoring weights
        self.weights = {
            'semantic_similarity': 0.30,
            'skill_match': 0.25,
            'experience_match': 0.15,
            'location_match': 0.10,
            'salary_match': 0.10,
            'job_type_match': 0.05,
            'company_preference': 0.05
        }
    
    async def initialize(self):
        """Initialize the scoring agent"""
        try:
            # Initialize OpenAI client
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OpenAI API key not found, semantic scoring will be limited")
            
            # Initialize sentence transformer model
            try:
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Sentence transformer model loaded")
            except Exception as e:
                logger.warning(f"Failed to load sentence transformer: {e}")
            
            logger.info("Scoring agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize scoring agent: {e}")
            raise
    
    async def score_jobs(self, user_id: int, max_jobs: int = 100) -> List[Dict]:
        """
        Score all unscored jobs for a user
        
        Returns:
            List of jobs with relevance scores
        """
        try:
            # Get user profile
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User profile not found for user_id: {user_id}")
            
            # Get jobs that need scoring
            jobs = await database.get_jobs_for_scoring(limit=max_jobs)
            if not jobs:
                logger.info("No jobs found for scoring")
                return []
            
            logger.info(f"Scoring {len(jobs)} jobs for user {user_id}")
            
            # Score jobs in batches
            batch_size = 20
            scored_jobs = []
            
            for i in range(0, len(jobs), batch_size):
                batch = jobs[i:i + batch_size]
                batch_scores = await self._score_job_batch(user_profile, batch)
                scored_jobs.extend(batch_scores)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            # Sort by score (highest first)
            scored_jobs.sort(key=lambda x: x['score'], reverse=True)
            
            # Update database with scores
            await self._update_job_scores(scored_jobs)
            
            await database.log_system_activity(
                agent_name="scoring_agent",
                action="score_jobs_complete",
                message=f"Scored {len(scored_jobs)} jobs for user {user_id}",
                metadata={"user_id": user_id, "jobs_scored": len(scored_jobs)}
            )
            
            return scored_jobs
            
        except Exception as e:
            logger.error(f"Error scoring jobs: {e}")
            await database.log_system_activity(
                agent_name="scoring_agent",
                action="score_jobs_error",
                message=f"Error scoring jobs: {str(e)}",
                level="error"
            )
            raise
    
    async def _score_job_batch(self, user_profile: Dict, jobs: List) -> List[Dict]:
        """Score a batch of jobs"""
        scored_jobs = []
        
        for job in jobs:
            try:
                score_data = await self._calculate_job_score(user_profile, job)
                scored_jobs.append(score_data)
            except Exception as e:
                logger.warning(f"Error scoring job {job.id}: {e}")
                # Add job with default score
                scored_jobs.append({
                    'job_id': job.id,
                    'score': 0.0,
                    'skills_match': {},
                    'job': job
                })
        
        return scored_jobs
    
    async def _calculate_job_score(self, user_profile: Dict, job) -> Dict:
        """Calculate comprehensive score for a single job"""
        
        # Extract features
        job_features = extract_features_from_job(job)
        profile_features = extract_features_from_profile(user_profile)
        
        # Calculate individual scores
        scores = {}
        
        # 1. Semantic similarity score
        scores['semantic_similarity'] = await self._calculate_semantic_similarity(
            profile_features, job_features
        )
        
        # 2. Skill match score
        scores['skill_match'], skills_match = self._calculate_skill_match_score(
            profile_features, job_features
        )
        
        # 3. Experience match score
        scores['experience_match'] = self._calculate_experience_match(
            profile_features, job_features
        )
        
        # 4. Location match score
        scores['location_match'] = self._calculate_location_match(
            profile_features, job_features
        )
        
        # 5. Salary match score
        scores['salary_match'] = self._calculate_salary_match(
            profile_features, job_features
        )
        
        # 6. Job type match score
        scores['job_type_match'] = self._calculate_job_type_match(
            profile_features, job_features
        )
        
        # 7. Company preference score
        scores['company_preference'] = self._calculate_company_preference(
            profile_features, job_features
        )
        
        # Calculate weighted final score
        final_score = sum(
            scores[component] * self.weights[component]
            for component in scores
        )
        
        # Normalize score to 0-1 range
        final_score = normalize_score(final_score)
        
        return {
            'job_id': job.id,
            'score': final_score,
            'component_scores': scores,
            'skills_match': skills_match,
            'job': job
        }
    
    async def _calculate_semantic_similarity(self, profile_features: Dict, job_features: Dict) -> float:
        """Calculate semantic similarity using embeddings"""
        try:
            if not self.sentence_model:
                return 0.0
            
            # Combine profile text
            profile_text = " ".join([
                " ".join(profile_features.get('skills', [])),
                profile_features.get('experience_summary', ''),
                " ".join(profile_features.get('interests', []))
            ])
            
            # Combine job text
            job_text = " ".join([
                job_features.get('title', ''),
                job_features.get('description', ''),
                job_features.get('requirements', ''),
                " ".join(job_features.get('required_skills', []))
            ])
            
            if not profile_text.strip() or not job_text.strip():
                return 0.0
            
            # Generate embeddings
            profile_embedding = self.sentence_model.encode([profile_text])
            job_embedding = self.sentence_model.encode([job_text])
            
            # Calculate cosine similarity
            similarity = cosine_similarity(profile_embedding, job_embedding)[0][0]
            
            return max(0.0, similarity)
            
        except Exception as e:
            logger.warning(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _calculate_skill_match_score(self, profile_features: Dict, job_features: Dict) -> Tuple[float, Dict]:
        """Calculate skill match score and detailed match info"""
        user_skills = set(skill.lower() for skill in profile_features.get('skills', []))
        required_skills = set(skill.lower() for skill in job_features.get('required_skills', []))
        
        if not required_skills:
            return 0.5, {}  # Default score if no skills specified
        
        # Exact matches
        exact_matches = user_skills.intersection(required_skills)
        
        # Partial matches (using semantic similarity)
        partial_matches = self._find_partial_skill_matches(user_skills, required_skills)
        
        # Calculate score
        total_required = len(required_skills)
        exact_match_count = len(exact_matches)
        partial_match_count = len(partial_matches)
        
        # Weight exact matches more than partial matches
        score = (exact_match_count * 1.0 + partial_match_count * 0.5) / total_required
        score = min(1.0, score)  # Cap at 1.0
        
        # Detailed match info
        skills_match = {
            'exact_matches': list(exact_matches),
            'partial_matches': partial_matches,
            'missing_skills': list(required_skills - user_skills),
            'match_percentage': score * 100
        }
        
        return score, skills_match
    
    def _find_partial_skill_matches(self, user_skills: set, required_skills: set) -> List[Dict]:
        """Find partial skill matches using similarity"""
        partial_matches = []
        
        skill_mappings = {
            'javascript': ['js', 'node.js', 'nodejs'],
            'python': ['django', 'flask', 'fastapi'],
            'react': ['reactjs', 'react.js'],
            'machine learning': ['ml', 'ai', 'deep learning'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb']
        }
        
        for req_skill in required_skills:
            if req_skill in user_skills:
                continue
            
            for user_skill in user_skills:
                # Check direct mappings
                for key, values in skill_mappings.items():
                    if req_skill in values and user_skill == key:
                        partial_matches.append({
                            'user_skill': user_skill,
                            'required_skill': req_skill,
                            'confidence': 0.8
                        })
                    elif user_skill in values and req_skill == key:
                        partial_matches.append({
                            'user_skill': user_skill,
                            'required_skill': req_skill,
                            'confidence': 0.8
                        })
        
        return partial_matches
    
    def _calculate_experience_match(self, profile_features: Dict, job_features: Dict) -> float:
        """Calculate experience level match score"""
        user_experience = profile_features.get('experience_years', 0)
        required_level = job_features.get('experience_level', 'entry')
        
        # Map experience levels to years
        level_mapping = {
            'entry': (0, 2),
            'mid': (2, 5),
            'senior': (5, 10),
            'lead': (8, 15)
        }
        
        if required_level not in level_mapping:
            return 0.5  # Default score
        
        min_years, max_years = level_mapping[required_level]
        
        if min_years <= user_experience <= max_years:
            return 1.0
        elif user_experience < min_years:
            # Penalize if under-qualified
            return max(0.0, 1.0 - (min_years - user_experience) * 0.2)
        else:
            # Slight penalty for being over-qualified
            return max(0.5, 1.0 - (user_experience - max_years) * 0.1)
    
    def _calculate_location_match(self, profile_features: Dict, job_features: Dict) -> float:
        """Calculate location preference match score"""
        preferred_locations = profile_features.get('preferred_locations', [])
        job_location = job_features.get('location', '').lower()
        job_remote = job_features.get('remote_allowed', False)
        
        if not preferred_locations:
            return 0.5  # Default score if no preference
        
        # Remote jobs get high score if user prefers remote
        if job_remote and any('remote' in loc.lower() for loc in preferred_locations):
            return 1.0
        
        # Check for location matches
        for pref_location in preferred_locations:
            if pref_location.lower() in job_location or job_location in pref_location.lower():
                return 1.0
        
        # Check for city/state matches
        for pref_location in preferred_locations:
            pref_parts = pref_location.lower().split(',')
            job_parts = job_location.split(',')
            
            for pref_part in pref_parts:
                for job_part in job_parts:
                    if pref_part.strip() in job_part.strip():
                        return 0.7
        
        return 0.2  # Low score for location mismatch
    
    def _calculate_salary_match(self, profile_features: Dict, job_features: Dict) -> float:
        """Calculate salary expectation match score"""
        min_salary_expectation = profile_features.get('salary_min', 0)
        max_salary_expectation = profile_features.get('salary_max', float('inf'))
        
        job_salary_min = job_features.get('salary_min', 0)
        job_salary_max = job_features.get('salary_max', 0)
        
        if not job_salary_min and not job_salary_max:
            return 0.5  # Default score if no salary info
        
        job_salary_avg = (job_salary_min + job_salary_max) / 2 if job_salary_max else job_salary_min
        
        if job_salary_avg >= min_salary_expectation:
            # Job pays enough
            if job_salary_avg <= max_salary_expectation:
                return 1.0  # Perfect match
            else:
                return 0.9  # Pays more than expected (still good)
        else:
            # Job pays less than expectation
            if min_salary_expectation > 0:
                ratio = job_salary_avg / min_salary_expectation
                return max(0.0, ratio)
            else:
                return 0.5
    
    def _calculate_job_type_match(self, profile_features: Dict, job_features: Dict) -> float:
        """Calculate job type preference match score"""
        preferred_types = profile_features.get('job_types', ['full-time'])
        job_type = job_features.get('job_type', 'full-time')
        
        if job_type in preferred_types:
            return 1.0
        else:
            return 0.3  # Lower score for non-preferred job type
    
    def _calculate_company_preference(self, profile_features: Dict, job_features: Dict) -> float:
        """Calculate company preference score"""
        preferred_companies = profile_features.get('preferred_companies', [])
        avoided_companies = profile_features.get('avoided_companies', [])
        company = job_features.get('company', '').lower()
        
        # Check if company is in preferred list
        for pref_company in preferred_companies:
            if pref_company.lower() in company:
                return 1.0
        
        # Check if company is in avoided list
        for avoided_company in avoided_companies:
            if avoided_company.lower() in company:
                return 0.0
        
        return 0.5  # Neutral score
    
    async def _get_user_profile(self, user_id: int) -> Dict:
        """Get user profile with caching"""
        if user_id in self.user_profile_cache:
            return self.user_profile_cache[user_id]
        
        # Get user from database
        user = await database.get_user_by_id(user_id)
        if not user:
            return None
        
        profile = {
            'user_id': user_id,
            'skills': user.get_skills(),
            'experience_years': user.experience_years,
            'location': user.location,
            **user.get_preferences()
        }
        
        # Cache the profile
        self.user_profile_cache[user_id] = profile
        return profile
    
    async def _update_job_scores(self, scored_jobs: List[Dict]):
        """Update job scores in database"""
        score_updates = []
        for job_data in scored_jobs:
            score_updates.append({
                'job_id': job_data['job_id'],
                'score': job_data['score'],
                'skills_match': job_data['skills_match']
            })
        
        await database.update_job_scores(score_updates)
    
    async def get_top_jobs_for_user(self, user_id: int, limit: int = 20) -> List[Dict]:
        """Get top scored jobs for a user"""
        # This would query the database for top scored jobs
        # For now, return empty list
        return []
    
    async def rescore_jobs_for_user(self, user_id: int) -> List[Dict]:
        """Rescore all jobs for a user (when profile changes)"""
        # Clear cache for this user
        if user_id in self.user_profile_cache:
            del self.user_profile_cache[user_id]
        
        # Rescore all jobs
        return await self.score_jobs(user_id)
    
    def is_healthy(self) -> bool:
        """Check if the scoring agent is healthy"""
        return self.sentence_model is not None or self.openai_client is not None
