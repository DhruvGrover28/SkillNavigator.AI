import React from 'react';

const ScoreTag = ({ score, classification, showLabel = true, size = 'normal' }) => {
  // If score is null/undefined, show processing state
  if (score === null || score === undefined) {
    return (
      <div className="flex items-center space-x-2">
        <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600">
          Processing...
        </span>
      </div>
    );
  }

  // Color and styling based on our calibrated thresholds
  const getScoreStyles = (score) => {
    if (score >= 80) {
      return {
        bgColor: 'bg-emerald-100',
        textColor: 'text-emerald-800',
        borderColor: 'border-emerald-200'
      };
    } else if (score >= 65) {
      return {
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        borderColor: 'border-blue-200'
      };
    } else if (score >= 40) {
      return {
        bgColor: 'bg-amber-100',
        textColor: 'text-amber-800',
        borderColor: 'border-amber-200'
      };
    } else {
      return {
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        borderColor: 'border-red-200'
      };
    }
  };

  const getDisplayLabel = (score, classification) => {
    // Use classification if available, otherwise derive from score
    if (classification) {
      return classification;
    }
    
    if (score >= 80) return 'Excellent Fit';
    if (score >= 65) return 'Good Fit';
    if (score >= 40) return 'Fair Fit';
    return 'Poor Fit';
  };

  const styles = getScoreStyles(score);
  const sizeClass = size === 'small' ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1';
  const label = getDisplayLabel(score, classification);

  return (
    <div className="flex items-center space-x-2">
      <div className={`flex items-center space-x-1 rounded-full border ${styles.bgColor} ${styles.borderColor} ${sizeClass}`}>
        <span className={`font-medium ${styles.textColor}`}>
          {Math.round(score)}%
        </span>
      </div>
      {showLabel && (
        <span className={`text-xs font-medium ${styles.textColor}`}>
          {label}
        </span>
      )}
    </div>
  );
};

export default ScoreTag;
