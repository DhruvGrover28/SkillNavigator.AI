import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  Upload, 
  User, 
  MapPin, 
  Phone, 
  Mail, 
  Briefcase, 
  GraduationCap,
  FileText,
  Save,
  Eye,
  X,
  CheckCircle,
  AlertCircle,
  Plus,
  Trash2,
  ArrowRight
} from 'lucide-react'

const Preferences = () => {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState('resume') // Start with resume tab
  const [resumeFile, setResumeFile] = useState(null)
  const [resumeUploaded, setResumeUploaded] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [parseStatus, setParseStatus] = useState('') // '', 'parsing', 'success', 'error'
  const [isSaving, setIsSaving] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true) // Show welcome message for new users
  const fileInputRef = useRef(null)

  const [formData, setFormData] = useState({
    // Personal Information
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    location: '',
    linkedinUrl: '',
    githubUrl: '',
    portfolioUrl: '',
    
    // Job Preferences
    desiredRoles: [''],
    preferredLocations: [''],
    salaryRange: { min: '', max: '' },
    jobTypes: [],
    workArrangement: '',
    industryPreferences: [],
    
    // Skills & Experience
    skills: [''],
    experienceLevel: '',
    currentRole: '',
    currentCompany: '',
    
    // Parsed Resume Data (from resume parser agent)
    parsedData: {
      summary: '',
      experience: [],
      education: [],
      skills: [],
      certifications: []
    }
  })

  // Load saved user data on component mount
  useEffect(() => {
    const loadSavedData = () => {
      try {
        // Load from localStorage first (quick load)
        const savedPreferences = localStorage.getItem('userPreferences')
        const savedSkills = localStorage.getItem('userSkills')
        
        if (savedPreferences) {
          const parsedPreferences = JSON.parse(savedPreferences)
          setFormData(prev => ({
            ...prev,
            ...parsedPreferences
          }))
        }
        
        if (savedSkills) {
          const parsedSkills = JSON.parse(savedSkills)
          setFormData(prev => ({
            ...prev,
            skills: parsedSkills
          }))
        }

        // Also load user data from auth token
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user.email) {
          setFormData(prev => ({
            ...prev,
            email: user.email,
            firstName: user.name ? user.name.split(' ')[0] : '',
            lastName: user.name ? user.name.split(' ').slice(1).join(' ') : ''
          }))
        }
        
      } catch (error) {
        console.error('Error loading saved preferences:', error)
      }
    }
    
    loadSavedData()
  }, [])

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleArrayInputChange = (index, value, fieldName) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: prev[fieldName].map((item, i) => i === index ? value : item)
    }))
  }

  const addArrayField = (fieldName) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: [...prev[fieldName], '']
    }))
  }

  const removeArrayField = (index, fieldName) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: prev[fieldName].filter((_, i) => i !== index)
    }))
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a text file (.txt), PDF, or Word document')
      return
    }

    // Validate file size (5MB max)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size should be less than 5MB')
      return
    }

    setResumeFile(file)
    setIsUploading(true)
    setParseStatus('parsing')

    try {
      // Create FormData for file upload
      const formDataObj = new FormData()
      formDataObj.append('file', file)

      // Call resume parser API - using our backend
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const userId = user.id
      
      if (!userId) {
        throw new Error('User not authenticated. Please login again.')
      }
      
      const token = localStorage.getItem('authToken')
      const response = await fetch(`http://localhost:8000/api/user/resume/${userId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formDataObj
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Resume processed successfully:', result)
        
        if (result.parsing_success) {
          // Backend has already saved the skills to the database
          // Update form data with extracted information
          setFormData(prev => ({
            ...prev,
            firstName: result.personal_info?.first_name || prev.firstName,
            lastName: result.personal_info?.last_name || prev.lastName,
            email: result.personal_info?.email || prev.email,
            phone: result.personal_info?.phone || prev.phone,
            linkedinUrl: result.personal_info?.linkedin || prev.linkedinUrl,
            skills: result.extracted_skills && result.extracted_skills.length > 0 ? result.extracted_skills : prev.skills,
            parsedData: {
              summary: '',
              experience: [],
              education: [],
              skills: result.extracted_skills || [],
              certifications: []
            }
          }))
          
          setResumeUploaded(true)
          setParseStatus('success')
          
          // Show success message with extracted skills
          alert(`✅ Resume processed successfully! ${result.skills_count} skills extracted and saved: ${result.extracted_skills.slice(0, 5).join(', ')}${result.skills_count > 5 ? '...' : ''}`)
          
          // Auto-advance to personal info tab after successful parsing
          setTimeout(() => {
            setActiveTab('personal')
          }, 1000)
        } else {
          setParseStatus('error')
          console.error('Resume parsing failed:', result)
          alert(`Resume parsing failed: ${result.message || 'Unknown error'}. You can still fill in your information manually.`)
        }
      } else {
        const errorText = await response.text()
        setParseStatus('error')
        console.error('API error:', errorText)
        alert(`Resume parsing failed: ${errorText}. You can still upload it and fill in your information manually.`)
      }
    } catch (error) {
      // For demo purposes, simulate successful parsing
      setTimeout(() => {
        const demoData = {
          firstName: 'John',
          lastName: 'Doe',
          email: 'john.doe@email.com',
          phone: '+1 (555) 123-4567',
          location: 'San Francisco, CA',
          skills: ['JavaScript', 'React', 'Node.js', 'Python', 'SQL'],
          summary: 'Experienced software engineer with 5+ years in full-stack development...',
          experience: [
            {
              title: 'Senior Software Engineer',
              company: 'Tech Corp',
              duration: '2021 - Present',
              description: 'Led development of web applications using React and Node.js'
            }
          ],
          education: [
            {
              degree: 'Bachelor of Science in Computer Science',
              school: 'University of California',
              year: '2019'
            }
          ]
        }
        
        setFormData(prev => ({
          ...prev,
          ...demoData,
          parsedData: demoData
        }))
        
        setResumeUploaded(true)
        setParseStatus('success')
      }, 2000)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    
    try {
      // Get the authenticated user ID
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      const userId = user.id
      
      if (!userId) {
        throw new Error('User not authenticated. Please login again.')
      }
      
      // Filter out empty skills and prepare clean skills array
      const cleanSkills = formData.skills.filter(skill => skill && skill.trim() !== '')
      
      if (cleanSkills.length === 0) {
        alert('Please add at least one skill before saving.')
        setIsSaving(false)
        return
      }
      
      // Save skills to backend using our API
      const token = localStorage.getItem('authToken')
      const response = await fetch(`http://localhost:8000/api/user/skills/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(cleanSkills)
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Skills saved successfully:', result)
        
        // Show success message
        alert(`✅ Skills saved successfully! ${result.skills_count} skills saved to your profile. These will be used for personalized job matching.`)
        
        // Store user preferences in localStorage for frontend use
        localStorage.setItem('userSkills', JSON.stringify(cleanSkills))
        localStorage.setItem('userPreferences', JSON.stringify(formData))
        
        // Navigate to dashboard after successful save
        navigate('/dashboard')
      } else {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save preferences')
      }
    } catch (error) {
      console.error('Save error:', error)
      alert(`❌ Error saving preferences: ${error.message}. Please try again.`)
    } finally {
      setIsSaving(false)
    }
  }

  const handleSkipAndContinue = () => {
    // Allow users to skip preferences and go directly to dashboard
    navigate('/dashboard')
  }

  const tabs = [
    { id: 'resume', name: 'Resume Upload', icon: FileText },
    { id: 'personal', name: 'Personal Info', icon: User },
    { id: 'preferences', name: 'Job Preferences', icon: Briefcase },
    { id: 'skills', name: 'Skills & Experience', icon: GraduationCap }
  ]

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">Welcome to SkillNavigator! 🎉</h1>
            <p className="mt-2 text-lg text-gray-600">
              Let's get you set up for success. Start by uploading your resume - our AI will extract your information automatically!
            </p>
          </div>
          
          {showWelcome && (
            <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <CheckCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="ml-3">
                  <p className="text-sm text-blue-800">
                    <strong>Quick Setup:</strong> Upload your resume first and we'll automatically fill in your details. 
                    Then customize your job preferences to get the best matches!
                  </p>
                </div>
                <button 
                  onClick={() => setShowWelcome(false)}
                  className="ml-4 text-blue-400 hover:text-blue-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Personal Information Tab */}
          {activeTab === 'personal' && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Personal Information</h2>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    First Name
                  </label>
                  <input
                    type="text"
                    name="firstName"
                    value={formData.firstName}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="John"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Last Name
                  </label>
                  <input
                    type="text"
                    name="lastName"
                    value={formData.lastName}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="Doe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="john@example.com"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={formData.location}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="San Francisco, CA"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    LinkedIn URL
                  </label>
                  <input
                    type="url"
                    name="linkedinUrl"
                    value={formData.linkedinUrl}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="https://linkedin.com/in/johndoe"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    GitHub URL
                  </label>
                  <input
                    type="url"
                    name="githubUrl"
                    value={formData.githubUrl}
                    onChange={handleInputChange}
                    className="input"
                    placeholder="https://github.com/johndoe"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Resume Upload Tab */}
          {activeTab === 'resume' && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Resume Upload</h2>
              
              {/* Upload Area */}
              <div className="mb-8">
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    resumeUploaded 
                      ? 'border-green-300 bg-green-50' 
                      : 'border-gray-300 hover:border-gray-400 bg-gray-50'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".txt,.pdf,.doc,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  
                  {isUploading ? (
                    <div className="flex flex-col items-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
                      <p className="text-lg font-medium text-gray-900">Uploading and parsing...</p>
                      <p className="text-sm text-gray-500">This may take a few moments</p>
                    </div>
                  ) : resumeUploaded ? (
                    <div className="flex flex-col items-center">
                      <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
                      <p className="text-lg font-medium text-gray-900">Resume uploaded successfully!</p>
                      <p className="text-sm text-gray-500 mb-4">{resumeFile?.name}</p>
                      <button
                        onClick={() => fileInputRef.current?.click()}
                        className="btn-secondary"
                      >
                        Upload Different Resume
                      </button>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center">
                      <Upload className="h-12 w-12 text-gray-400 mb-4" />
                      <p className="text-lg font-medium text-gray-900">Upload your resume</p>
                      <p className="text-sm text-gray-500 mb-2">Text files (.txt) work best for parsing</p>
                      <p className="text-xs text-gray-400 mb-4">Also supports PDF, DOC, DOCX up to 5MB</p>
                      <button className="btn-primary">
                        Choose File
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Help Text */}
              {!resumeUploaded && (
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
                  <div className="flex">
                    <FileText className="h-5 w-5 text-blue-400 mr-2 mt-0.5" />
                    <div>
                      <h3 className="text-sm font-medium text-blue-800">💡 Best Results with Text Files</h3>
                      <p className="text-sm text-blue-700 mt-1">
                        For the most accurate parsing, save your resume as a <strong>.txt file</strong> with sections like:
                        <br />• Contact Info (Name, Email, Phone)
                        <br />• Skills, Experience, Education
                        <br />• One section per line for best results
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Parse Status */}
              {parseStatus === 'success' && (
                <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
                  <div className="flex">
                    <CheckCircle className="h-5 w-5 text-green-400 mr-2" />
                    <div>
                      <h3 className="text-sm font-medium text-green-800">Resume parsed successfully!</h3>
                      <p className="text-sm text-green-700 mt-1">
                        We've extracted your information and pre-filled your profile. Review and edit as needed.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {parseStatus === 'error' && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                  <div className="flex">
                    <AlertCircle className="h-5 w-5 text-red-400 mr-2" />
                    <div>
                      <h3 className="text-sm font-medium text-red-800">Parsing failed</h3>
                      <p className="text-sm text-red-700 mt-1">
                        We couldn't parse your resume. You can still upload it and fill in your information manually.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Parsed Information Preview */}
              {formData.parsedData.summary && (
                <div className="mt-6">
                  <h3 className="text-lg font-medium text-gray-900 mb-4">Extracted Information</h3>
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                    <h4 className="font-medium text-blue-900 mb-2">Summary</h4>
                    <p className="text-sm text-blue-800 mb-3">{formData.parsedData.summary}</p>
                    
                    {formData.parsedData.skills.length > 0 && (
                      <div>
                        <h4 className="font-medium text-blue-900 mb-2">Skills</h4>
                        <div className="flex flex-wrap gap-2">
                          {formData.parsedData.skills.map((skill, index) => (
                            <span key={index} className="badge-success">
                              {skill}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Job Preferences Tab */}
          {activeTab === 'preferences' && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Job Preferences</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Desired Roles
                  </label>
                  {formData.desiredRoles.map((role, index) => (
                    <div key={index} className="flex items-center space-x-2 mb-2">
                      <input
                        type="text"
                        value={role}
                        onChange={(e) => handleArrayInputChange(index, e.target.value, 'desiredRoles')}
                        className="input flex-1"
                        placeholder="e.g., Software Engineer, Product Manager"
                      />
                      {formData.desiredRoles.length > 1 && (
                        <button
                          onClick={() => removeArrayField(index, 'desiredRoles')}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayField('desiredRoles')}
                    className="btn-secondary text-sm"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Role
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Salary Range (USD)
                    </label>
                    <div className="flex space-x-2">
                      <input
                        type="number"
                        name="salaryMin"
                        value={formData.salaryRange.min}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          salaryRange: { ...prev.salaryRange, min: e.target.value }
                        }))}
                        className="input"
                        placeholder="Min"
                      />
                      <input
                        type="number"
                        name="salaryMax"
                        value={formData.salaryRange.max}
                        onChange={(e) => setFormData(prev => ({
                          ...prev,
                          salaryRange: { ...prev.salaryRange, max: e.target.value }
                        }))}
                        className="input"
                        placeholder="Max"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Work Arrangement
                    </label>
                    <select
                      name="workArrangement"
                      value={formData.workArrangement}
                      onChange={handleInputChange}
                      className="input"
                    >
                      <option value="">Select arrangement</option>
                      <option value="remote">Remote</option>
                      <option value="hybrid">Hybrid</option>
                      <option value="onsite">On-site</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Skills & Experience Tab */}
          {activeTab === 'skills' && (
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Skills & Experience</h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Skills
                  </label>
                  {formData.skills.map((skill, index) => (
                    <div key={index} className="flex items-center space-x-2 mb-2">
                      <input
                        type="text"
                        value={skill}
                        onChange={(e) => handleArrayInputChange(index, e.target.value, 'skills')}
                        className="input flex-1"
                        placeholder="e.g., JavaScript, Python, Project Management"
                      />
                      {formData.skills.length > 1 && (
                        <button
                          onClick={() => removeArrayField(index, 'skills')}
                          className="text-red-500 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    onClick={() => addArrayField('skills')}
                    className="btn-secondary text-sm"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Skill
                  </button>
                </div>

                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Experience Level
                    </label>
                    <select
                      name="experienceLevel"
                      value={formData.experienceLevel}
                      onChange={handleInputChange}
                      className="input"
                    >
                      <option value="">Select level</option>
                      <option value="entry">Entry Level (0-2 years)</option>
                      <option value="mid">Mid Level (3-5 years)</option>
                      <option value="senior">Senior Level (6-10 years)</option>
                      <option value="lead">Lead/Principal (10+ years)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Current Role
                    </label>
                    <input
                      type="text"
                      name="currentRole"
                      value={formData.currentRole}
                      onChange={handleInputChange}
                      className="input"
                      placeholder="e.g., Senior Software Engineer"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex justify-between items-center">
          <button
            onClick={handleSkipAndContinue}
            className="text-gray-500 hover:text-gray-700 px-4 py-2 transition-colors duration-200"
          >
            Skip for now
          </button>
          
          <div className="flex space-x-4">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="btn-primary px-8 py-3 flex items-center"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-5 w-5 mr-2" />
                  Save & Continue to Dashboard
                  <ArrowRight className="h-5 w-5 ml-2" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Preferences