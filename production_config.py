# PRODUCTION AUTO-APPLY CONFIGURATION
# Complete setup for maximum success rates

# 1. EMAIL INFRASTRUCTURE
SMTP_SETTINGS = {
    'providers': [
        {
            'name': 'gmail',
            'host': 'smtp.gmail.com',
            'port': 587,
            'username': 'your_email@gmail.com',
            'password': 'your_app_specific_password',  # Not regular password!
            'tls': True,
            'daily_limit': 500  # Gmail's sending limit
        },
        {
            'name': 'sendgrid', 
            'api_key': 'SG.xxx',
            'daily_limit': 40000  # SendGrid limit
        }
    ],
    'rotation_strategy': 'round_robin',  # Distribute across providers
    'templates': {
        'subject': 'Application for {position} at {company}',
        'signature': '''
Best regards,
{name}
{phone}
{email}

LinkedIn: {linkedin_url}
Portfolio: {portfolio_url}
        '''
    }
}

# 2. BROWSER AUTOMATION SETUP
BROWSER_CONFIG = {
    'playwright': {
        'headless': False,  # Show browser for CAPTCHA solving
        'slow_mo': 1000,    # 1 second delays between actions
        'user_data_dir': './browser_profiles',  # Persistent login sessions
        'extensions': ['captcha_solver_extension'],
        'proxy_rotation': True
    },
    'session_management': {
        'linkedin_sessions': 5,      # Multiple LinkedIn accounts
        'indeed_sessions': 3,        # Multiple Indeed accounts  
        'rotation_interval': '24h'   # Switch accounts daily
    }
}

# 3. CAPTCHA SOLVING SERVICE
CAPTCHA_CONFIG = {
    'provider': '2captcha',  # or 'anticaptcha', 'deathbycaptcha'
    'api_key': 'your_2captcha_key',
    'timeout': 120,  # 2 minutes max per CAPTCHA
    'retry_limit': 3,
    'cost_per_solve': 0.003  # $0.003 per CAPTCHA
}

# 4. PROXY INFRASTRUCTURE  
PROXY_CONFIG = {
    'residential_proxies': [
        '192.168.1.100:8080:username:password',
        '192.168.1.101:8080:username:password', 
        '192.168.1.102:8080:username:password'
    ],
    'rotation_strategy': 'per_application',  # New proxy per job
    'geolocation': 'match_job_location',     # Use local proxies
    'provider': 'luminati'  # or 'smartproxy', 'oxylabs'
}

# 5. RATE LIMITING & SAFETY
RATE_LIMITS = {
    'applications_per_hour': 5,      # Conservative rate
    'applications_per_day': 50,      # Daily maximum
    'delay_between_apps': (300, 600), # 5-10 minutes between applications
    'cooldown_periods': {
        'linkedin': 3600,    # 1 hour between LinkedIn apps
        'indeed': 1800,      # 30 minutes between Indeed apps
        'email': 900         # 15 minutes between emails
    }
}

# 6. SUCCESS DETECTION
SUCCESS_INDICATORS = {
    'positive_phrases': [
        'thank you for applying',
        'application received', 
        'application submitted',
        'we have received your application',
        'your application has been sent',
        'application successful'
    ],
    'url_patterns': [
        '/thank-you',
        '/application-complete', 
        '/success',
        '/confirmation'
    ],
    'element_selectors': [
        '.success-message',
        '.application-complete',
        '.thank-you-message'
    ]
}

# 7. MONITORING & ANALYTICS
MONITORING = {
    'webhook_url': 'https://your-app.com/webhooks/auto-apply',
    'slack_notifications': True,
    'email_reports': 'daily',
    'metrics_tracking': [
        'applications_sent',
        'success_rates_by_method',
        'response_rates',
        'interview_conversion_rates'
    ],
    'error_logging': {
        'level': 'DEBUG',
        'retention_days': 30,
        'alert_on_failure_rate': 0.8  # Alert if >80% failures
    }
}