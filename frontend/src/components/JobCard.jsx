import React, { useState } from 'react';
import { MapPin, Building, Calendar, ExternalLink } from 'lucide-react';
import ScoreTag from './ScoreTag';

const JobCard = ({ job, onViewDetails, onStatusUpdate }) => {
  const [isApplying, setIsApplying] = useState(false);
  
  const {
    id,
    title,
    company,
    location,
    description,
    requirements,
    salary_range,
    job_type,
    posted_date,
    application_url,
    apply_url, // Also check for apply_url from backend
    match_score,
    status
  } = job;

  // Use apply_url if application_url is not available
  const jobUrl = application_url || apply_url;

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'applied':
        return 'bg-blue-100 text-blue-800';
      case 'interview':
        return 'bg-yellow-100 text-yellow-800';
      case 'offered':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="card p-6 hover:shadow-md transition-shadow duration-200">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
          <div className="flex items-center text-gray-600 mb-2">
            <Building className="w-4 h-4 mr-1" />
            <span className="font-medium">{company}</span>
          </div>
          <div className="flex items-center text-gray-500 mb-2">
            <MapPin className="w-4 h-4 mr-1" />
            <span>{location}</span>
          </div>
          <div className="flex items-center text-gray-500">
            <Calendar className="w-4 h-4 mr-1" />
            <span>Posted: {formatDate(posted_date)}</span>
          </div>
        </div>
        
        <div className="flex flex-col items-end space-y-2">
          <ScoreTag 
            score={match_score} 
            classification={job.classification}
            showLabel={true}
            size="normal"
          />
          {status && (
            <span className={`badge ${getStatusColor(status)}`}>
              {status}
            </span>
          )}
        </div>
      </div>

      <div className="mb-4">
        <p className="text-gray-700 text-sm line-clamp-3">
          {description}
        </p>
      </div>

      {/* AI Score Breakdown */}
      {job.score_breakdown && (
        <div className="mb-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
          <div className="text-xs font-semibold text-gray-700 mb-2">Match Analysis</div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center">
              <div className="font-medium text-gray-600">Skills</div>
              <div className="text-lg font-bold text-blue-600">
                {Math.round(job.score_breakdown.skills)}%
              </div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-600">Experience</div>
              <div className="text-lg font-bold text-green-600">
                {Math.round(job.score_breakdown.experience)}%
              </div>
            </div>
            <div className="text-center">
              <div className="font-medium text-gray-600">Education</div>
              <div className="text-lg font-bold text-purple-600">
                {Math.round(job.score_breakdown.education)}%
              </div>
            </div>
          </div>
          {job.score_explanation && (
            <div className="mt-2 text-xs text-gray-600 border-t border-gray-200 pt-2">
              {job.score_explanation}
            </div>
          )}
        </div>
      )}

      {salary_range && (
        <div className="mb-4">
          <span className="inline-block bg-green-50 text-green-700 text-sm px-2 py-1 rounded">
            {salary_range}
          </span>
        </div>
      )}

      {job_type && (
        <div className="mb-4">
          <span className="inline-block bg-purple-50 text-purple-700 text-sm px-2 py-1 rounded">
            {job_type}
          </span>
        </div>
      )}

      <div className="flex justify-between items-center gap-2">
        <button
          onClick={() => onViewDetails(job)}
          className="btn-secondary px-4 py-2 text-sm"
        >
          View Details
        </button>
        
        <div className="flex gap-2">
          {jobUrl && (
            <a
              href={jobUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary px-4 py-2 text-sm inline-flex items-center hover:bg-blue-700 transition-colors"
              title="Visit original job posting"
            >
              <ExternalLink className="w-4 h-4 mr-1" />
              Visit Job
            </a>
          )}
          
          {jobUrl && (
            <button
              onClick={async () => {
                try {
                  setIsApplying(true);
                  
                  const response = await fetch(`http://localhost:8000/api/jobs/auto-apply/${id}`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                  });
                  
                  const result = await response.json();
                  
                  if (response.ok && result.success) {
                    // Enhanced success notification
                    const successMessage = `✅ Successfully Applied!\n\n` +
                      `Job: ${title}\n` +
                      `Company: ${company}\n` +
                      `Method: ${result.method || 'Auto'}\n` +
                      `Status: ${result.status}\n\n` +
                      `${result.attempts_made ? `Attempts: ${result.attempts_made}\n` : ''}` +
                      `Your application has been submitted and tracked automatically.`;
                    
                    alert(successMessage);
                    
                    // Update job status in parent component
                    if (onStatusUpdate) {
                      onStatusUpdate(id, 'applied');
                    }
                  } else {
                    // Enhanced error handling with helpful suggestions
                    let errorMessage = `❌ Auto-Apply Failed\n\n`;
                    
                    if (result.reason === "Browser not available" || result.error?.includes("not available")) {
                      errorMessage += `🤖 Auto-Apply Service Temporarily Unavailable\n\n` +
                                    `The automated application system is currently limited due to technical constraints.\n\n` +
                                    `📋 What you can do:\n` +
                                    `• Click "Visit Job" to apply manually\n` +
                                    `• Save this job for later\n` +
                                    `• Check back later for auto-apply availability\n\n` +
                                    `Job: ${title} at ${company}`;
                    } else if (result.methods_tried && result.methods_tried.length > 1) {
                      errorMessage += `Multiple application methods were attempted but none succeeded.\n\n` +
                                    `Methods tried: ${result.methods_tried.join(', ')}\n` +
                                    `Total attempts: ${result.total_attempts || 'Unknown'}\n\n` +
                                    `Error: ${result.error || 'Unknown error'}\n\n` +
                                    `💡 Try applying manually via "Visit Job"`;
                    } else {
                      errorMessage += `Failed to apply to ${title}\n\n` +
                                    `Method: ${result.method || 'Unknown'}\n` +
                                    `Error: ${result.error || result.message || result.reason || 'Unknown error'}\n\n` +
                                    `💡 You can still apply manually by clicking "Visit Job"`;
                    }
                    
                    alert(errorMessage);
                  }
                } catch (error) {
                  console.error('Auto-apply error:', error);
                  const errorMessage = `❌ Auto-Apply System Error\n\n` +
                                      `Job: ${title} at ${company}\n` +
                                      `Error: ${error.message}\n\n` +
                                      `🔧 This appears to be a system issue. Please try:\n` +
                                      `• Refreshing the page\n` +
                                      `• Trying again in a few minutes\n` +
                                      `• Applying manually via "Visit Job"`;
                  alert(errorMessage);
                } finally {
                  setIsApplying(false);
                }
              }}
              disabled={isApplying}
              className={`${
                isApplying 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : match_score && match_score >= 80 
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700' 
                    : 'bg-green-600 hover:bg-green-700'
              } text-white px-4 py-2 text-sm rounded-lg inline-flex items-center transition-all duration-300 shadow-md hover:shadow-lg`}
              title={`Auto-apply using AI agent${match_score ? ` (${match_score}% match)` : ''}`}
            >
              {isApplying ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                  Applying...
                </>
              ) : (
                <>
                  <span className="mr-1">🤖</span>
                  Auto Apply
                  {match_score && match_score >= 80 && <span className="ml-1 text-xs">⭐</span>}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default JobCard;
