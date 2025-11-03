import React from 'react'

function TestApp() {
  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f5f5f5',
      minHeight: '100vh'
    }}>
      <h1 style={{ color: '#333', marginBottom: '20px' }}>
        SkillNavigator Frontend Test
      </h1>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '20px', 
        borderRadius: '8px', 
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <p>✅ React is working correctly</p>
        <p>✅ Vite development server is running</p>
        <p>✅ JavaScript is executing properly</p>
        <p>📍 Current URL: {window.location.href}</p>
        <p>🕒 Loaded at: {new Date().toLocaleString()}</p>
      </div>
    </div>
  )
}

export default TestApp