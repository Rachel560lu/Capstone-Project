import React, { useRef } from 'react';

const UploadSection = ({ onFileSelect, isVisible, selectedModule }) => {
  const fileInputRef = useRef(null);
  const uploadAreaRef = useRef(null);

  const getUploadTitle = () => {
    if (selectedModule === 'denoise') {
      return 'Upload image for Clutter Removal processing';
    } else if (selectedModule === 'virtual') {
      return 'Upload image for virtual staging processing';
    }
    return 'Upload your property photo';
  };

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      onFileSelect(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (uploadAreaRef.current) {
      uploadAreaRef.current.style.borderColor = '#ff8a00';
      uploadAreaRef.current.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
    }
  };

  const handleDragLeave = () => {
    if (uploadAreaRef.current) {
      uploadAreaRef.current.style.borderColor = 'rgba(255, 255, 255, 0.3)';
      uploadAreaRef.current.style.backgroundColor = 'transparent';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (uploadAreaRef.current) {
      uploadAreaRef.current.style.borderColor = 'rgba(255, 255, 255, 0.3)';
      uploadAreaRef.current.style.backgroundColor = 'transparent';
    }
    
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  if (!isVisible) return null;

  return (
    <section className="upload-section">
      <h2 className="upload-title">{getUploadTitle()}</h2>
      <div
        className="upload-area"
        ref={uploadAreaRef}
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="upload-icon">📁</div>
        <p className="upload-text">Drag and drop image or click to upload</p>
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <button className="upload-btn">Select Image</button>
      </div>
    </section>
  );
};

export default UploadSection;


