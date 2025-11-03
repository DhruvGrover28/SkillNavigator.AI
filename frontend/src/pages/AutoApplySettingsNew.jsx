import React, { useState } from 'react';
import AutoApplyDashboard from '../components/AutoApplyDashboard';

const AutoApplySettings = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-lg flex items-center justify-center mr-3 font-bold">
              🚀
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Auto-Apply System</h1>
          </div>
          
          <p className="text-gray-600 mb-6">
            Send real job applications automatically via email and monitor your progress
          </p>
          
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'dashboard'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                🚀 Dashboard
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'settings'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                ⚙️ Settings
              </button>
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'dashboard' && <AutoApplyDashboard />}
        
        {activeTab === 'settings' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Auto-Apply Settings</h2>
            <p className="text-gray-600 mb-6">
              Configure your automatic job application preferences. Settings will be implemented in future updates.
            </p>
            
            <div className="space-y-4">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h3 className="font-medium text-gray-900 mb-2">Current Configuration</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>✅ Email applications enabled</li>
                  <li>✅ SMTP configured and working</li>
                  <li>✅ Resume attachment enabled</li>
                  <li>📧 Sending from: grover.dhruv28@gmail.com</li>
                </ul>
              </div>
              
              <div className="p-4 border border-blue-200 bg-blue-50 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Available Actions</h3>
                <p className="text-sm text-blue-800 mb-3">
                  Use the Dashboard tab above to send real job applications.
                </p>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  Go to Dashboard
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AutoApplySettings;