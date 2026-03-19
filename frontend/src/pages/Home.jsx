import React, { useState, useEffect } from 'react';
import { Search, Filter, Briefcase, TrendingUp, Users, Target } from 'lucide-react';
import JobCard from '../components/JobCard';
import LoadingSpinner from '../components/LoadingSpinner';
import axios from 'axios';
import { apiBase } from '../utils/api';

const Home = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [fallbackNotice, setFallbackNotice] = useState('');
  const [scrapeInProgress, setScrapeInProgress] = useState(false);
  const [scrapeStatusMessage, setScrapeStatusMessage] = useState('');
  const [hasPreferences, setHasPreferences] = useState(false);
  const [stats, setStats] = useState({
    totalJobs: 0,
    appliedJobs: 0,
    avgMatchScore: 0,
    pendingApplications: 0
  });

  const getJobUrl = (job) => job?.application_url || job?.apply_url || '';
  const getEmailAddress = (url) => url.replace(/^mailto:/i, '').split('?')[0];

  useEffect(() => {
    console.log('[home] api base', apiBase);
    const scrapeStartedAt = localStorage.getItem('scrapeStartedAt');
    if (scrapeStartedAt) {
      setScrapeInProgress(true);
      setScrapeStatusMessage('Fetching fresh job opportunities based on your preferences...');
      console.log('[home] scrape started at', scrapeStartedAt);
    }
    fetchJobs();
    fetchStats();
    fetchUserProfile();
    checkScrapeStatus();
  }, []);

  useEffect(() => {
    if (!scrapeInProgress) return;

    const intervalId = setInterval(() => {
      checkScrapeStatus();
      fetchJobs();
    }, 7000);

    return () => clearInterval(intervalId);
  }, [scrapeInProgress]);

  const fetchUserProfile = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      if (!user.id) {
        console.log('[home] no user id found for profile');
        setHasPreferences(false);
        return;
      }

      const token = localStorage.getItem('authToken');
      const response = await fetch(`${apiBase}/api/user/profile/${user.id}`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
      });

      if (!response.ok) {
        console.warn('[home] profile fetch failed:', response.status);
        setHasPreferences(false);
        return;
      }

      const profile = await response.json();
      const skills = profile.skills || [];
      const preferences = profile.preferences || {};
      const hasSkills = Array.isArray(skills) && skills.length > 0;
      const hasPrefs = preferences && Object.keys(preferences).length > 0;
      console.log('[home] preferences loaded', { hasSkills, hasPrefs });
      setHasPreferences(hasSkills || hasPrefs);
    } catch (error) {
      console.warn('Unable to load user profile:', error);
      setHasPreferences(false);
    }
  };

  const checkScrapeStatus = async () => {
    const scrapeStartedAt = localStorage.getItem('scrapeStartedAt');
    if (!scrapeStartedAt) {
      setScrapeInProgress(false);
      return;
    }

    try {
      console.log('[home] checking supervisor status');
      const response = await axios.get(`${apiBase}/api/supervisor/status`);
      const lastSearchTime = response.data?.last_search_time;
      console.log('[home] supervisor status', response.data);
      if (lastSearchTime && new Date(lastSearchTime) >= new Date(scrapeStartedAt)) {
        localStorage.removeItem('scrapeStartedAt');
        setScrapeInProgress(false);
        setScrapeStatusMessage('');
      }
    } catch (error) {
      console.warn('Unable to check supervisor status:', error);
    }
  };

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setFallbackNotice('');
      console.log('[home] fetching jobs');

      const response = await axios.get(`${apiBase}/api/jobs/?limit=100&offset=0`, { timeout: 5000 });
      if (response.data && response.data.length > 0) {
        console.log('[home] jobs fetched', response.data.length);
        setJobs(response.data);
      } else {
        console.log('[home] no jobs returned');
        setJobs([]);
      }

      const scrapeStartedAt = localStorage.getItem('scrapeStartedAt');
      if (scrapeStartedAt) {
        localStorage.removeItem('scrapeStartedAt');
        setScrapeInProgress(false);
        setScrapeStatusMessage('');
      }
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
      setFallbackNotice('We could not load live job data. Please try again shortly.');
      setScrapeInProgress(false);
      setScrapeStatusMessage('');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${apiBase}/api/jobs/stats/summary`);
      setStats({
        totalJobs: response.data.total_jobs || 0,
        appliedJobs: 0,
        avgMatchScore: response.data.avg_match_score || 0,
        pendingApplications: 0
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      fetchJobs();
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(`${apiBase}/api/jobs/?limit=100&offset=0`);
      // Filter jobs on frontend since backend doesn't have full-text search yet
      const filteredResults = response.data.filter(job =>
        job.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        job.location?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setJobs(filteredResults);
    } catch (error) {
      console.error('Error searching jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleViewDetails = (job) => {
    setSelectedJob(job);
  };

  const filteredJobs = jobs.filter(job =>
    job.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    job.location?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const StatCard = ({ icon: Icon, title, value, color = 'blue' }) => (
    <div className="card p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg bg-${color}-100`}>
          <Icon className={`w-6 h-6 text-${color}-600`} />
        </div>
        <div className="ml-4">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900">{value}</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">
              Navigate Your Career with AI
            </h1>
            <p className="text-xl text-primary-100 mb-8">
              Find the perfect job matches, get AI-powered application assistance, and track your progress
            </p>
            
            {/* Search Bar */}
            <div className="max-w-2xl mx-auto">
              <div className="flex space-x-4">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    placeholder="Search for jobs, companies, or skills..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    className="w-full px-4 py-3 pl-12 rounded-lg border border-transparent focus:outline-none focus:ring-2 focus:ring-white focus:border-transparent text-gray-900"
                  />
                  <Search className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" />
                </div>
                <button
                  onClick={handleSearch}
                  className="btn-secondary bg-white text-primary-600 hover:bg-gray-50 px-6 py-3"
                >
                  Search
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {scrapeInProgress && scrapeStatusMessage && (
          <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {scrapeStatusMessage}
          </div>
        )}
        {fallbackNotice && (
          <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
            {fallbackNotice}
          </div>
        )}
        {/* Stats Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Briefcase}
            title="Available Jobs"
            value={stats.totalJobs || jobs.length}
            color="blue"
          />
          <StatCard
            icon={TrendingUp}
            title="Applications Sent"
            value={stats.appliedJobs || 0}
            color="green"
          />
          <StatCard
            icon={Target}
            title="Avg Match Score"
            value={hasPreferences ? `${stats.avgMatchScore || 0}%` : '—'}
            color="purple"
          />
          <StatCard
            icon={Users}
            title="Pending Reviews"
            value={stats.pendingApplications || 0}
            color="orange"
          />
        </div>

        {/* Filters and Controls */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-4">
            <h2 className="text-2xl font-bold text-gray-900">
              Job Opportunities
            </h2>
            <span className="bg-primary-100 text-primary-800 px-3 py-1 rounded-full text-sm font-medium">
              {filteredJobs.length} jobs
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button className="btn-secondary px-4 py-2 text-sm inline-flex items-center">
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
          </div>
        </div>

        {/* Jobs Grid */}
        {loading ? (
          <LoadingSpinner text="Finding the best job matches for you..." />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {filteredJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                showScore={hasPreferences}
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        )}

        {!loading && filteredJobs.length === 0 && (
          <div className="text-center py-12">
            <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No jobs found
            </h3>
            <p className="text-gray-500">
              Try adjusting your search terms or check back later for new opportunities.
            </p>
          </div>
        )}
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-xl font-bold text-gray-900">{selectedJob.title}</h3>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Company</h4>
                  <p className="text-gray-700">{selectedJob.company}</p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Location</h4>
                  <p className="text-gray-700">{selectedJob.location}</p>
                </div>
                
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Description</h4>
                  <p className="text-gray-700 whitespace-pre-wrap">{selectedJob.description}</p>
                </div>
                
                {selectedJob.requirements && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-2">Requirements</h4>
                    <p className="text-gray-700 whitespace-pre-wrap">{selectedJob.requirements}</p>
                  </div>
                )}
                
                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    onClick={() => setSelectedJob(null)}
                    className="btn-secondary px-4 py-2"
                  >
                    Close
                  </button>
                  {(() => {
                    const jobUrl = getJobUrl(selectedJob);
                    const isMailto = jobUrl?.toLowerCase().startsWith('mailto:');

                    if (!jobUrl) return null;

                    if (!isMailto) {
                      return (
                        <a
                          href={jobUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-primary px-4 py-2"
                        >
                          Apply Now
                        </a>
                      );
                    }

                    const emailAddress = getEmailAddress(jobUrl);

                    return (
                      <button
                        type="button"
                        onClick={async () => {
                          try {
                            await navigator.clipboard.writeText(emailAddress);
                            alert('Email address copied to clipboard.');
                          } catch (error) {
                            window.prompt('Copy email address:', emailAddress);
                          }
                        }}
                        className="btn-primary px-4 py-2"
                      >
                        Copy Email
                      </button>
                    );
                  })()}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
