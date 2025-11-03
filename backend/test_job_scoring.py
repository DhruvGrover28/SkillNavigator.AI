#!/usr/bin/env python3
"""
Comprehensive Job Scoring Test Suite
Tests multiple candidate-job combinations to evaluate scoring accuracy
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.job_scoring_agent import JobScoringAgent

def test_multiple_scenarios():
    """Test multiple candidate-job scenarios to evaluate scoring accuracy"""
    
    print("🧪 Starting Comprehensive Job Scoring Test Suite\n")
    print("=" * 80)
    
    # Initialize scoring agent
    scoring_agent = JobScoringAgent()
    
    # Test scenarios
    scenarios = [
        {
            "name": "Perfect Match - Senior Python Developer",
            "candidate": {
                'skills': ['Python', 'Django', 'Flask', 'PostgreSQL', 'AWS', 'Docker', 'Git', 'REST API', 'Machine Learning', 'Redis'],
                'experience': [
                    {
                        'title': 'Senior Python Developer',
                        'company': 'TechCorp Solutions',
                        'description': 'Led development of scalable web applications using Django and Flask. Managed AWS infrastructure and implemented ML models for data analysis. 5 years of experience.'
                    },
                    {
                        'title': 'Python Developer',
                        'company': 'StartUp Inc',
                        'description': 'Built REST APIs and microservices. Used PostgreSQL and Redis for data management.'
                    }
                ],
                'education': [
                    {
                        'degree': 'Master of Science',
                        'field': 'Computer Science',
                        'institution': 'Stanford University'
                    }
                ]
            },
            "job": {
                'description': '''
                Senior Python Developer Position
                We are seeking an experienced Python developer to join our backend team.
                
                Requirements:
                - 4+ years of Python development experience
                - Strong experience with Django or Flask frameworks
                - Database experience with PostgreSQL or MySQL
                - Cloud experience (AWS preferred)  
                - Experience with Docker and containerization
                - REST API development experience
                - Master's degree in Computer Science or related field preferred
                
                Skills: Python, Django, Flask, PostgreSQL, AWS, Docker, REST API, Git
                '''
            },
            "expected_range": (85, 95)  # Should be Excellent Fit
        },
        
        {
            "name": "Good Match - Frontend Developer for React Role",
            "candidate": {
                'skills': ['JavaScript', 'React', 'HTML', 'CSS', 'Node.js', 'Git', 'Bootstrap', 'jQuery', 'MongoDB'],
                'experience': [
                    {
                        'title': 'Frontend Developer',
                        'company': 'Web Agency',
                        'description': 'Developed responsive web applications using React and JavaScript. Created user interfaces with HTML/CSS and Bootstrap. 3 years experience.'
                    }
                ],
                'education': [
                    {
                        'degree': 'Bachelor of Technology',
                        'field': 'Information Technology',
                        'institution': 'Tech Institute'
                    }
                ]
            },
            "job": {
                'description': '''
                React Frontend Developer
                Looking for a skilled React developer to build modern web applications.
                
                Requirements:
                - 2+ years of React development experience
                - Strong JavaScript, HTML, CSS skills
                - Experience with responsive design
                - Bachelor's degree preferred
                - Git version control experience
                
                Skills: React, JavaScript, HTML, CSS, responsive design, Git
                Nice to have: Node.js, TypeScript, Redux
                '''
            },
            "expected_range": (70, 85)  # Should be Good Fit
        },
        
        {
            "name": "Partial Match - Junior vs Senior Role Mismatch",
            "candidate": {
                'skills': ['Python', 'Django', 'HTML', 'CSS', 'Git', 'MySQL'],
                'experience': [
                    {
                        'title': 'Junior Python Developer',
                        'company': 'Small Company',
                        'description': 'Entry-level Python developer with 1 year experience. Built basic web applications using Django. Learning full-stack development.'
                    }
                ],
                'education': [
                    {
                        'degree': 'Bachelor of Science',
                        'field': 'Computer Science',
                        'institution': 'Local University'
                    }
                ]
            },
            "job": {
                'description': '''
                Senior Full-Stack Engineer
                We need an experienced full-stack engineer to lead our development team.
                
                Requirements:
                - 5+ years of full-stack development experience
                - Expert-level Python and JavaScript skills
                - Experience with React, Node.js, and modern frameworks
                - Leadership and mentoring experience
                - Master's degree preferred
                - Experience with cloud platforms (AWS, Azure)
                - DevOps and CI/CD pipeline experience
                
                Skills: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, leadership
                '''
            },
            "expected_range": (40, 60)  # Should be Fair Fit (skills match but experience gap)
        },
        
        {
            "name": "Poor Match - Complete Skills Mismatch",
            "candidate": {
                'skills': ['Photoshop', 'Illustrator', 'InDesign', 'Figma', 'Adobe Creative Suite', 'UI Design', 'UX Research'],
                'experience': [
                    {
                        'title': 'Graphic Designer',
                        'company': 'Design Studio',
                        'description': 'Created visual designs for marketing materials, logos, and branding. Specialized in print and digital media design. 4 years experience.'
                    }
                ],
                'education': [
                    {
                        'degree': 'Bachelor of Fine Arts',
                        'field': 'Graphic Design',
                        'institution': 'Art College'
                    }
                ]
            },
            "job": {
                'description': '''
                Backend Java Developer
                Seeking a skilled backend developer for enterprise application development.
                
                Requirements:
                - 3+ years of Java development experience
                - Spring Boot framework experience
                - Database design with Oracle or PostgreSQL
                - Microservices architecture experience
                - Computer Science degree required
                - Experience with Maven, Jenkins, Docker
                
                Skills: Java, Spring Boot, Oracle, PostgreSQL, Maven, Jenkins, Docker, microservices
                '''
            },
            "expected_range": (10, 30)  # Should be Poor Fit (complete mismatch)
        }
    ]
    
    # Run tests
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n🔍 TEST {i}: {scenario['name']}")
        print("-" * 60)
        
        # Score the candidate
        result = scoring_agent.score_candidate(scenario['candidate'], scenario['job'])
        
        # Analyze result
        score = result.total_score
        classification = result.classification
        expected_min, expected_max = scenario['expected_range']
        
        # Determine if result is acceptable
        is_acceptable = expected_min <= score <= expected_max
        
        print(f"📊 SCORE: {score:.2f}% - {classification}")
        print(f"📈 SECTION BREAKDOWN:")
        print(f"   • Skills: {result.section_scores['skills']:.1f}%")
        print(f"   • Experience: {result.section_scores['experience']:.1f}%")
        print(f"   • Education: {result.section_scores['education']:.1f}%")
        print(f"🎯 EXPECTED RANGE: {expected_min}-{expected_max}%")
        print(f"✅ ACCEPTABLE: {'YES' if is_acceptable else 'NO'}")
        print(f"💬 EXPLANATION: {result.explanation}")
        
        # Store result
        results.append({
            'scenario': scenario['name'],
            'score': score,
            'classification': classification,
            'expected_range': scenario['expected_range'],
            'acceptable': is_acceptable,
            'section_scores': result.section_scores
        })
    
    # Summary
    print("\n" + "=" * 80)
    print("📋 TEST SUMMARY")
    print("=" * 80)
    
    acceptable_count = sum(1 for r in results if r['acceptable'])
    total_count = len(results)
    
    print(f"Total Tests: {total_count}")
    print(f"Acceptable Results: {acceptable_count}")
    print(f"Success Rate: {(acceptable_count/total_count)*100:.1f}%")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✅ PASS" if result['acceptable'] else "❌ FAIL"
        print(f"{status} | {result['scenario']}: {result['score']:.1f}% ({result['classification']})")
    
    # Recommendation
    print("\n🎯 RECOMMENDATION:")
    if acceptable_count >= total_count * 0.75:  # 75% pass rate
        print("✅ SCORING SYSTEM IS PERFORMING WELL - READY TO MOVE FORWARD")
        print("The AI model demonstrates good accuracy in matching candidates to jobs.")
    else:
        print("⚠️  SCORING SYSTEM NEEDS ADJUSTMENT")
        print("Consider tuning weights or improving section extraction logic.")
    
    return results

if __name__ == "__main__":
    test_multiple_scenarios()