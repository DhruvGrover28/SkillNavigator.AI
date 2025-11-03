import React, { useState, useEffect } from 'react'
import { Search, Filter, MapPin, Clock, DollarSign, Bookmark, ExternalLink } from 'lucide-react'
import JobCard from '../components/JobCard'
import { jobsAPI } from '../utils/api'

const Jobs = () => {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [filters, setFilters] = useState({
    location: '',
    jobType: '',
    experience: '',
    salary: ''
  })

  useEffect(() => {
    fetchJobs()
  }, [])

  const fetchJobs = async () => {
    try {
      setLoading(true)
      const response = await jobsAPI.getAll()
      setJobs(response.data)
    } catch (error) {
      console.error('Error fetching jobs:', error)
      // Set empty array if API fails
      setJobs([])
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    // Implement search logic
    console.log('Searching for:', searchTerm)
  }

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value
    }))
  }

  const toggleSaveJob = (jobId) => {
    setJobs(prev => prev.map(job => 
      job.id === jobId ? { ...job, saved: !job.saved } : job
    ))
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Find Your Next Job
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            Discover opportunities that match your skills and interests
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8">
          <form onSubmit={handleSearch} className="mb-4">
            <div className="flex gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
                <input
                  type="text"
                  placeholder="Search jobs, companies, or keywords..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                />
              </div>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
              >
                Search
              </button>
            </div>
          </form>

          {/* Filters */}
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters:</span>
            </div>
            
            <select
              value={filters.location}
              onChange={(e) => handleFilterChange('location', e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Locations</option>
              <option value="remote">Remote</option>
              <option value="san-francisco">San Francisco</option>
              <option value="new-york">New York</option>
              <option value="los-angeles">Los Angeles</option>
            </select>

            <select
              value={filters.jobType}
              onChange={(e) => handleFilterChange('jobType', e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Types</option>
              <option value="full-time">Full-time</option>
              <option value="part-time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
            </select>

            <select
              value={filters.experience}
              onChange={(e) => handleFilterChange('experience', e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Experience</option>
              <option value="entry">Entry Level</option>
              <option value="mid">Mid Level</option>
              <option value="senior">Senior Level</option>
              <option value="lead">Lead/Principal</option>
            </select>

            <select
              value={filters.minScore}
              onChange={(e) => handleFilterChange('minScore', e.target.value)}
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white"
            >
              <option value="">All Matches</option>
              <option value="80">Excellent Match (80%+)</option>
              <option value="65">Good Match (65%+)</option>
              <option value="40">Fair Match (40%+)</option>
            </select>
          </div>
        </div>

        {/* Results Header */}
        {!loading && jobs.length > 0 && (
          <div className="flex justify-between items-center mb-4 px-1">
            <div className="text-sm text-gray-600 dark:text-gray-300">
              Showing {jobs.length} jobs sorted by match score
            </div>
            <div className="text-xs text-gray-500">
              AI-filtered and personalized results
            </div>
          </div>
        )}

        {/* Job Results */}
        <div className="grid gap-6">
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {jobs.length} Jobs Found
                </h2>
                <select className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-sm dark:bg-gray-700 dark:text-white">
                  <option>Sort by: Relevance</option>
                  <option>Sort by: Date Posted</option>
                  <option>Sort by: Salary</option>
                  <option>Sort by: Company</option>
                </select>
              </div>

              {jobs.map(job => (
                <JobCard
                  key={job.id}
                  job={job}
                  onSave={() => toggleSaveJob(job.id)}
                />
              ))}
            </>
          )}
        </div>

        {/* Load More Button */}
        {!loading && jobs.length > 0 && (
          <div className="text-center mt-8">
            <button className="px-6 py-3 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              Load More Jobs
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default Jobs
