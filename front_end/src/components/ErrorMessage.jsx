import React from 'react';

const ErrorMessage = ({ message }) => {
  if (!message) return null;

  return (
    <div className="error-message show">
      {message}
    </div>
  );
};

export default ErrorMessage;




