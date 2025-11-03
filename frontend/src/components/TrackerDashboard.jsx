import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Building, 
  MapPin, 
  ExternalLink,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  TrendingUp,
  Users,
  BarChart3,
  Edit,
  Trash2,
  Plus,
  RefreshCw,
  Filter
} from 'lucide-react';

const TrackerDashboard = () => {
  const [applications, setApplications] = useState([]);
  const [stats, setStats] = useState({
    total_applications: 0,
    applications_this_week: 0,
    response_rate: 0,
    interview_rate: 0,
    success_rate: 0,
    status_breakdown: {}
  });
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    status: '',
    company: '',
    days: 30
  });
  const [editingApplication, setEditingApplication] = useState(null);

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

  // Fetch applications and stats
  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch applications
      const params = new URLSearchParams();
      if (filter.status) params.append('status', filter.status);
      if (filter.company) params.append('company', filter.company);
      if (filter.days) params.append('days', filter.days);
      
      const appsResponse = await authenticatedFetch(`/api/tracker/applications?${params}`);
      if (appsResponse.ok) {
        const appsData = await appsResponse.json();
        setApplications(appsData);
      }

      // Fetch statistics
      const statsResponse = await authenticatedFetch(`/api/tracker/applications/stats?days=${filter.days}`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }
    } catch (error) {
      console.error('Error fetching tracker data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filter]);

  // Status icons and colors
  const getStatusIcon = (status) => {
    switch (status?.toLowerCase()) {
      case 'applied':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'interview':
      case 'second_interview':
      case 'final_interview':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'accepted':
      case 'offer_accepted':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'rejected':
      case 'offer_declined':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'applied':
        return 'bg-blue-100 text-blue-800';
      case 'interview':
      case 'second_interview':
      case 'final_interview':
        return 'bg-yellow-100 text-yellow-800';
      case 'accepted':
      case 'offer_accepted':
        return 'bg-green-100 text-green-800';
      case 'rejected':
      case 'offer_declined':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Update application status
  const updateStatus = async (applicationId, newStatus, notes = '') => {
    try {
      const response = await authenticatedFetch('/api/tracker/status', {
        method: 'PUT',
        body: JSON.stringify({
          application_id: applicationId,
          status: newStatus,
          notes: notes
        })
      });

      if (response.ok) {
        fetchData(); // Refresh data
        setEditingApplication(null);
      } else {
        alert('Failed to update application status');
      }
    } catch (error) {
      console.error('Error updating status:', error);
      alert('Error updating application status');
    }
  };

  // Delete application
  const deleteApplication = async (applicationId) => {
    if (!window.confirm('Are you sure you want to delete this application?')) {
      return;
    }

    try {
      const response = await authenticatedFetch(`/api/tracker/application/${applicationId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        fetchData(); // Refresh data
      } else {
        alert('Failed to delete application');
      }
    } catch (error) {
      console.error('Error deleting application:', error);
      alert('Error deleting application');
    }
  };

  // Stats cards
  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <Icon className={`w-8 h-8 ${color}`} />
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
        <span className="ml-2 text-gray-600">Loading applications...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Job Application Tracker</h1>
        <p className="text-gray-600">Track and manage your job applications</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Applications"
          value={stats.total_applications}
          icon={Building}
          color="text-blue-500"
          subtitle="All time"
        />
        <StatCard
          title="This Week"
          value={stats.applications_this_week}
          icon={Calendar}
          color="text-green-500"
          subtitle="Last 7 days"
        />
        <StatCard
          title="Response Rate"
          value={`${(stats.response_rate * 100).toFixed(1)}%`}
          icon={TrendingUp}
          color="text-yellow-500"
          subtitle="Companies responded"
        />
        <StatCard
          title="Interview Rate"
          value={`${(stats.interview_rate * 100).toFixed(1)}%`}
          icon={Users}
          color="text-purple-500"
          subtitle="Got interviews"
        />
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Applications</h2>
          <button
            onClick={fetchData}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <select
            value={filter.status}
            onChange={(e) => setFilter(prev => ({ ...prev, status: e.target.value }))}
            className="border rounded-lg px-3 py-2"
          >
            <option value="">All Statuses</option>
            <option value="applied">Applied</option>
            <option value="interview">Interview</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
          </select>
          
          <input
            type="text"
            placeholder="Filter by company..."
            value={filter.company}
            onChange={(e) => setFilter(prev => ({ ...prev, company: e.target.value }))}
            className="border rounded-lg px-3 py-2"
          />
          
          <select
            value={filter.days}
            onChange={(e) => setFilter(prev => ({ ...prev, days: parseInt(e.target.value) }))}
            className="border rounded-lg px-3 py-2"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
            <option value={365}>Last year</option>
          </select>
          
          <div className="text-sm text-gray-600 flex items-center">
            <Filter className="w-4 h-4 mr-2" />
            {applications.length} applications
          </div>
        </div>

        {/* Applications Table */}
        <div className="overflow-x-auto">
          <table className="w-full table-auto">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4 font-medium text-gray-900">Job Title</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Company</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Status</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Applied Date</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Last Updated</th>
                <th className="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((app) => (
                <tr key={app.id} className="border-b hover:bg-gray-50">
                  <td className="py-4 px-4">
                    <div className="font-medium text-gray-900">{app.job_title}</div>
                    {app.notes && (
                      <div className="text-sm text-gray-500 mt-1">{app.notes}</div>
                    )}
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center">
                      <Building className="w-4 h-4 text-gray-400 mr-2" />
                      <span className="text-gray-900">{app.company}</span>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(app.status)}
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(app.status)}`}>
                        {app.status}
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-4 text-gray-600">
                    {formatDate(app.applied_at)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">
                    {formatDate(app.last_updated)}
                  </td>
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setEditingApplication(app)}
                        className="p-2 text-blue-600 hover:bg-blue-100 rounded-lg"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => deleteApplication(app.id)}
                        className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {applications.length === 0 && (
            <div className="text-center py-12">
              <Building className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No applications found</h3>
              <p className="text-gray-600">Start applying to jobs to see them here!</p>
            </div>
          )}
        </div>
      </div>

      {/* Edit Status Modal */}
      {editingApplication && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Update Application Status</h3>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {editingApplication.job_title} at {editingApplication.company}
              </label>
              <select
                value={editingApplication.status}
                onChange={(e) => setEditingApplication(prev => ({ ...prev, status: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2"
              >
                <option value="applied">Applied</option>
                <option value="interview">Interview Scheduled</option>
                <option value="second_interview">Second Interview</option>
                <option value="final_interview">Final Interview</option>
                <option value="accepted">Offer Received</option>
                <option value="offer_accepted">Offer Accepted</option>
                <option value="offer_declined">Offer Declined</option>
                <option value="rejected">Rejected</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
            </div>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Notes (Optional)
              </label>
              <textarea
                value={editingApplication.notes || ''}
                onChange={(e) => setEditingApplication(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Add any notes about this application..."
                className="w-full border rounded-lg px-3 py-2 h-20 resize-none"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setEditingApplication(null)}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => updateStatus(editingApplication.id, editingApplication.status, editingApplication.notes)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Update Status
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrackerDashboard;