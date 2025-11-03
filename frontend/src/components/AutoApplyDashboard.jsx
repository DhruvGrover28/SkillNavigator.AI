import React, { useState, useEffect } from 'react';
import './AutoApplyDashboard.css';

const AutoApplyDashboard = () => {
  
  // Helper function for authenticated API calls
  const authenticatedFetch = (url, options = {}) => {
    const token = localStorage.getItem('authToken');
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };
    
    return fetch(`http://localhost:8000${url}`, {
      ...options,
      headers
    });
  };
  const [emailJobs, setEmailJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [applying, setApplying] = useState(false);
  const [selectedJobs, setSelectedJobs] = useState(new Set());
  const [applicationResults, setApplicationResults] = useState([]);
  const [stats, setStats] = useState({});
  const [systemHealth, setSystemHealth] = useState({});

  // Fetch email jobs on component mount
  useEffect(() => {
    fetchEmailJobs();
    fetchStats();
    checkSystemHealth();
  }, []);

  const fetchEmailJobs = async () => {
    setLoading(true);
    try {
      const response = await authenticatedFetch('/api/auto-apply/email-jobs');
      const data = await response.json();
      
      if (data.success) {
        setEmailJobs(data.jobs);
      } else {
        console.error('Failed to fetch email jobs:', data);
      }
    } catch (error) {
      console.error('Error fetching email jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await authenticatedFetch('/api/auto-apply/stats');
      const data = await response.json();
      
      if (data.success) {
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const checkSystemHealth = async () => {
    try {
      const response = await authenticatedFetch('/api/auto-apply/health');
      const data = await response.json();
      setSystemHealth(data);
    } catch (error) {
      console.error('Error checking system health:', error);
      setSystemHealth({ success: false, status: 'unhealthy', error: error.message });
    }
  };

  const handleJobSelect = (jobId) => {
    const newSelected = new Set(selectedJobs);
    if (newSelected.has(jobId)) {
      newSelected.delete(jobId);
    } else {
      newSelected.add(jobId);
    }
    setSelectedJobs(newSelected);
  };

  const selectAllJobs = () => {
    if (selectedJobs.size === emailJobs.length) {
      setSelectedJobs(new Set());
    } else {
      setSelectedJobs(new Set(emailJobs.map(job => job.id)));
    }
  };

  const applyToSelectedJobs = async () => {
    if (selectedJobs.size === 0) {
      alert('Please select at least one job to apply to.');
      return;
    }

    if (!window.confirm(`Are you sure you want to send REAL EMAIL APPLICATIONS to ${selectedJobs.size} jobs?`)) {
      return;
    }

    setApplying(true);
    setApplicationResults([]);

    try {
      const response = await authenticatedFetch('/api/auto-apply/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_ids: Array.from(selectedJobs)
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setApplicationResults(data.results);
        alert(`Applications sent! ${data.applications_sent}/${data.total_jobs} successful.`);
        
        // Refresh stats
        fetchStats();
      } else {
        alert(`Application failed: ${data.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error applying to jobs:', error);
      alert('Failed to send applications. Please check your connection and try again.');
    } finally {
      setApplying(false);
    }
  };

  const sendTestEmail = async () => {
    const testEmail = prompt('Enter email address to send test email to:');
    if (!testEmail) return;

    try {
      const response = await authenticatedFetch('/api/auto-apply/test-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          recipient_email: testEmail
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert('Test email sent successfully!');
      } else {
        alert(`Test email failed: ${data.message}`);
      }
    } catch (error) {
      console.error('Error sending test email:', error);
      alert('Failed to send test email.');
    }
  };

  if (loading) {
    return (
      <div className="auto-apply-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading email jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="auto-apply-dashboard">
      <div className="dashboard-header">
        <h1>🚀 Auto Apply Dashboard</h1>
        <p className="subtitle">Send real job applications via email automatically</p>
      </div>

      {/* System Health Status */}
      <div className={`health-status ${systemHealth.success ? 'healthy' : 'unhealthy'}`}>
        <div className="health-indicator">
          <span className="status-icon">{systemHealth.success ? '✅' : '❌'}</span>
          <span className="status-text">
            System Status: {systemHealth.status || 'Unknown'}
          </span>
        </div>
        {systemHealth.email_configured && (
          <div className="email-config">
            <span className="config-icon">📧</span>
            <span>Email: {systemHealth.user_email}</span>
          </div>
        )}
        <button className="test-email-btn" onClick={sendTestEmail}>
          Test Email Configuration
        </button>
      </div>

      {/* Stats Overview */}
      <div className="stats-overview">
        <div className="stat-card">
          <h3>{stats.total_email_jobs || 0}</h3>
          <p>Email Jobs Available</p>
        </div>
        <div className="stat-card">
          <h3>{stats.total_email_applications || 0}</h3>
          <p>Total Applications Sent</p>
        </div>
        <div className="stat-card">
          <h3>{stats.recent_applications_7_days || 0}</h3>
          <p>Applications (7 days)</p>
        </div>
      </div>

      {/* Job Selection Controls */}
      <div className="controls-section">
        <div className="selection-controls">
          <button 
            className="select-all-btn"
            onClick={selectAllJobs}
          >
            {selectedJobs.size === emailJobs.length ? 'Deselect All' : 'Select All'}
          </button>
          <span className="selection-count">
            {selectedJobs.size} of {emailJobs.length} jobs selected
          </span>
        </div>
        
        <button 
          className="apply-btn"
          onClick={applyToSelectedJobs}
          disabled={applying || selectedJobs.size === 0}
        >
          {applying ? 'Sending Applications...' : `Apply to ${selectedJobs.size} Jobs`}
        </button>
      </div>

      {/* Application Results */}
      {applicationResults.length > 0 && (
        <div className="results-section">
          <h3>Application Results</h3>
          <div className="results-grid">
            {applicationResults.map((result, index) => (
              <div key={index} className={`result-card ${result.success ? 'success' : 'error'}`}>
                <div className="result-status">
                  {result.success ? '✅' : '❌'}
                </div>
                <div className="result-details">
                  <p><strong>Job ID:</strong> {result.job_id}</p>
                  <p><strong>Method:</strong> {result.method}</p>
                  {result.success ? (
                    <div>
                      <p><strong>Sent to:</strong> {result.recipient}</p>
                      <p className="success-message">{result.message}</p>
                    </div>
                  ) : (
                    <p className="error-message">{result.error}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Email Jobs List */}
      <div className="jobs-section">
        <h3>Available Email Jobs ({emailJobs.length})</h3>
        
        {emailJobs.length === 0 ? (
          <div className="no-jobs">
            <p>No email jobs available at the moment.</p>
            <button onClick={fetchEmailJobs}>Refresh</button>
          </div>
        ) : (
          <div className="jobs-grid">
            {emailJobs.map((job) => (
              <div 
                key={job.id} 
                className={`job-card ${selectedJobs.has(job.id) ? 'selected' : ''}`}
                onClick={() => handleJobSelect(job.id)}
              >
                <div className="job-card-header">
                  <div className="job-checkbox">
                    <input 
                      type="checkbox" 
                      checked={selectedJobs.has(job.id)}
                      onChange={() => handleJobSelect(job.id)}
                    />
                  </div>
                  <h4 className="job-title">{job.title}</h4>
                </div>
                
                <div className="job-details">
                  <p className="company"><strong>{job.company}</strong></p>
                  <p className="salary">
                    {job.salary_min && job.salary_max 
                      ? `$${job.salary_min.toLocaleString()} - $${job.salary_max.toLocaleString()}`
                      : 'Salary not specified'
                    }
                  </p>
                  <p className="email-target">
                    📧 {job.apply_url.replace('mailto:', '').split('?')[0]}
                  </p>
                </div>
                
                <div className="job-description">
                  <p>{job.description}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AutoApplyDashboard;