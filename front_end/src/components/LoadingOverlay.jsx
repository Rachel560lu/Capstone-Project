import React from 'react';

const LoadingOverlay = ({ isLoading }) => {
  return (
    <div className={`loading-overlay ${isLoading ? 'show' : ''}`}>
      <div className="loading-spinner"></div>
      <div className="loading-text">AI is processing your image, please wait...</div>
    </div>
  );
};

export default LoadingOverlay;



