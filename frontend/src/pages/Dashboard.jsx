import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  TrendingUp, 
  Briefcase, 
  Clock,
  CheckCircle,
  AlertTriangle,
  PieChart,
  Calendar,
  Download,
  Play,
  RefreshCw
} from 'lucide-react';
import TrackerTable from '../components/TrackerTable';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('30'); // days

  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  // Helper function for authenticated API calls
  const authenticatedFetch = (url, options = {}) => {
    const token = localStorage.getItem('authToken');
    const headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
    
    return fetch(`http://localhost:8000${url}`, {
      ...options,
      headers
    });
  };

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch real applications data from tracker API
      const applicationsResponse = await authenticatedFetch(`/api/tracker/applications?days=${timeRange}`);
      let applicationsData = [];
      
      if (applicationsResponse.ok) {
        applicationsData = await applicationsResponse.json();
        setApplications(applicationsData);
      } else {
        console.error('Failed to fetch applications');
        setApplications([]);
      }
      
      // Fetch real statistics from tracker API
      const statsResponse = await authenticatedFetch(`/api/tracker/applications/stats?days=${timeRange}`);
      let statsData = {
        total_applications: 0,
        applications_this_week: 0,
        response_rate: 0,
        interview_rate: 0,
        success_rate: 0,
        status_breakdown: {}
      };
      
      if (statsResponse.ok) {
        statsData = await statsResponse.json();
      } else {
        console.error('Failed to fetch statistics');
      }
      
      // Fetch job count
      let totalJobs = 0;
      try {
        const jobsResponse = await fetch('http://localhost:8000/api/jobs/count');
        if (jobsResponse.ok) {
          const jobsData = await jobsResponse.json();
          totalJobs = jobsData.count || 0;
        }
      } catch (error) {
        console.log('Could not fetch job count:', error);
      }
      
      // Process stats data for dashboard
      const statusBreakdown = statsData.status_breakdown || {};
      const totalApplications = statsData.total_applications || 0;
      const pendingApplications = statusBreakdown.applied || 0;
      const interviewsScheduled = (statusBreakdown.interview || 0) + 
                                  (statusBreakdown.second_interview || 0) + 
                                  (statusBreakdown.final_interview || 0);
      const acceptedOffers = (statusBreakdown.accepted || 0) + 
                            (statusBreakdown.offer_accepted || 0);
      const rejectedApplications = statusBreakdown.rejected || 0;
      
      setStats({
        totalApplications: totalApplications,
        pendingApplications: pendingApplications,
        interviewsScheduled: interviewsScheduled,
        avgResponseTime: statsData.avg_response_time || 0,
        successRate: (statsData.success_rate * 100) || 0,
        responseRate: (statsData.response_rate * 100) || 0,
        totalJobs: totalJobs,
        acceptedOffers: acceptedOffers,
        rejectedApplications: rejectedApplications,
        applicationsThisWeek: statsData.applications_this_week || 0
      });
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Set empty data on error - no fallback mock data for production
      setApplications([]);
      setStats({
        totalApplications: 0,
        pendingApplications: 0,
        interviewsScheduled: 0,
        avgResponseTime: 0,
        successRate: 0,
        responseRate: 0,
        totalJobs: 0,
        acceptedOffers: 0,
        rejectedApplications: 0,
        applicationsThisWeek: 0
      });
    } finally {
      setLoading(false);
    }
  };

  // Manual trigger functions for supervisor
  const [triggerLoading, setTriggerLoading] = useState(false);
  const [triggerMessage, setTriggerMessage] = useState('');

  const triggerManualJobSearch = async () => {
    try {
      setTriggerLoading(true);
      setTriggerMessage('');
      
      const response = await authenticatedFetch('/api/supervisor/workflow/trigger', {
        method: 'POST',
        body: JSON.stringify({
          search_query: 'python developer',
          location: 'Remote',
          job_type: 'full-time',
          max_jobs: 50
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setTriggerMessage('✅ Job search workflow triggered successfully!');
        // Refresh dashboard data after successful trigger
        setTimeout(() => {
          fetchDashboardData();
        }, 3000);
      } else {
        setTriggerMessage('❌ Failed to trigger workflow. Please try again.');
      }
    } catch (error) {
      console.error('Error triggering manual job search:', error);
      setTriggerMessage('❌ Error occurred. Please check your connection.');
    } finally {
      setTriggerLoading(false);
      // Clear message after 5 seconds
      setTimeout(() => setTriggerMessage(''), 5000);
    }
  };

  const checkSupervisorStatus = async () => {
    try {
      const response = await authenticatedFetch('/api/supervisor/status');
      if (response.ok) {
        const status = await response.json();
        const isAutoMode = status.auto_mode_enabled;
        setTriggerMessage(
          isAutoMode 
            ? '✅ Auto-mode is running. Jobs are being processed automatically every hour.' 
            : '⚠️ Auto-mode is OFF. Use manual trigger below or enable auto-mode.'
        );
      }
    } catch (error) {
      setTriggerMessage('❌ Could not check supervisor status.');
    }
    setTimeout(() => setTriggerMessage(''), 5000);
  };

  const StatCard = ({ icon: Icon, title, value, subtitle, color = 'blue', trend }) => (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-semibold text-gray-900 mt-2">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg bg-${color}-100`}>
          <Icon className={`w-6 h-6 text-${color}-600`} />
        </div>
      </div>
      {trend && (
        <div className="mt-4 flex items-center">
          <TrendingUp className={`w-4 h-4 ${trend > 0 ? 'text-green-500' : 'text-red-500'} mr-1`} />
          <span className={`text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '+' : ''}{trend}% from last period
          </span>
        </div>
      )}
    </div>
  );

  const QuickAction = ({ icon: Icon, title, description, onClick, color = 'blue' }) => (
    <button
      onClick={onClick}
      className="card p-6 text-left hover:shadow-md transition-shadow duration-200 w-full"
    >
      <div className="flex items-start">
        <div className={`p-2 rounded-lg bg-${color}-100 mr-4`}>
          <Icon className={`w-5 h-5 text-${color}-600`} />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
          <p className="text-sm text-gray-600">{description}</p>
        </div>
      </div>
    </button>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner text="Loading your dashboard..." />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-600 mt-1">Track your job search progress and performance</p>
          </div>
          
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="input px-3 py-2 text-sm"
            >
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 3 months</option>
              <option value="365">Last year</option>
            </select>
            
            <button className="btn-secondary px-4 py-2 text-sm inline-flex items-center">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={Briefcase}
            title="Total Applications"
            value={stats.totalApplications}
            subtitle="This period"
            color="blue"
          />
          <StatCard
            icon={Clock}
            title="Pending Reviews"
            value={stats.pendingApplications}
            subtitle="Awaiting response"
            color="orange"
          />
          <StatCard
            icon={CheckCircle}
            title="Interviews Scheduled"
            value={stats.interviewsScheduled}
            subtitle="This period"
            color="green"
          />
          <StatCard
            icon={TrendingUp}
            title="Success Rate"
            value={`${stats.successRate.toFixed(1)}%`}
            subtitle="Response rate"
            color="purple"
          />
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
          
          {/* Supervisor Status and Manual Trigger */}
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <RefreshCw className="w-5 h-5 mr-2 text-blue-600" />
                  AI Job Search Engine
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Manually trigger job search and application process if auto-mode malfunctions
                </p>
                {triggerMessage && (
                  <div className="mt-2 text-sm font-medium">
                    {triggerMessage}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={checkSupervisorStatus}
                  className="btn-secondary px-4 py-2 text-sm inline-flex items-center"
                  disabled={triggerLoading}
                >
                  <AlertTriangle className="w-4 h-4 mr-2" />
                  Check Status
                </button>
                <button
                  onClick={triggerManualJobSearch}
                  disabled={triggerLoading}
                  className="btn-primary px-4 py-2 text-sm inline-flex items-center"
                >
                  {triggerLoading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Triggering...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Manual Trigger
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <QuickAction
              icon={Briefcase}
              title="Find New Jobs"
              description="Discover job opportunities that match your skills"
              onClick={() => window.location.href = '/'}
              color="blue"
            />
            <QuickAction
              icon={BarChart3}
              title="Analyze Performance"
              description="Review your application success metrics"
              color="green"
            />
            <QuickAction
              icon={Calendar}
              title="Schedule Follow-ups"
              description="Manage your interview and follow-up schedule"
              color="purple"
            />
          </div>
        </div>

        {/* Application Status Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <div className="card p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Application Timeline</h3>
                <PieChart className="w-5 h-5 text-gray-400" />
              </div>
              
              <div className="space-y-4">
                {[
                  { key: 'applied', label: 'Applied', color: 'bg-blue-500' },
                  { key: 'interview', label: 'Interview', color: 'bg-yellow-500' },
                  { key: 'accepted', label: 'Accepted', color: 'bg-green-500' },
                  { key: 'rejected', label: 'Rejected', color: 'bg-red-500' }
                ].map((statusInfo) => {
                  // Handle multiple interview statuses
                  let count = 0;
                  if (statusInfo.key === 'interview') {
                    count = applications.filter(app => 
                      app.status === 'interview' || 
                      app.status === 'second_interview' || 
                      app.status === 'final_interview'
                    ).length;
                  } else if (statusInfo.key === 'accepted') {
                    count = applications.filter(app => 
                      app.status === 'accepted' || 
                      app.status === 'offer_accepted'
                    ).length;
                  } else {
                    count = applications.filter(app => app.status === statusInfo.key).length;
                  }
                  
                  const percentage = applications.length > 0 ? (count / applications.length) * 100 : 0;
                  
                  return (
                    <div key={statusInfo.key} className="flex items-center">
                      <div className="flex items-center w-32">
                        <div className={`w-3 h-3 rounded-full ${statusInfo.color} mr-2`}></div>
                        <span className="text-sm font-medium text-gray-700">
                          {statusInfo.label}
                        </span>
                      </div>
                      <div className="flex-1 mx-4">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${statusInfo.color}`}
                            style={{ width: `${percentage}%` }}
                          ></div>
                        </div>
                      </div>
                      <span className="text-sm text-gray-600 w-8 text-right">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-3">
              {applications
                .sort((a, b) => new Date(b.applied_at || b.created_at) - new Date(a.applied_at || a.created_at))
                .slice(0, 5)
                .map((app, index) => (
                <div key={app.id || index} className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Applied to {app.job_title}
                    </p>
                    <p className="text-xs text-gray-500">
                      {app.company} • {new Date(app.applied_at || app.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
              
              {applications.length === 0 && (
                <div className="text-center py-4">
                  <AlertTriangle className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">No recent activity</p>
                  <p className="text-xs text-gray-400">Start tracking applications to see your progress here</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Application Tracker */}
        <TrackerTable applications={applications} />
      </div>
    </div>
  );
};

export default Dashboard;
