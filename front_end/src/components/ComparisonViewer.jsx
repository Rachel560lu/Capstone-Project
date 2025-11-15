import React, { useEffect, useRef, useState } from 'react';

const ComparisonViewer = ({ originalUrl, processedUrl, isVisible }) => {
  const containerRef = useRef(null);
  const sliderRef = useRef(null);
  const afterImageRef = useRef(null);
  const [isMoving, setIsMoving] = useState(false);

  useEffect(() => {
    if (!isVisible || !originalUrl || !processedUrl) return;

    const originalImg = new Image();
    originalImg.src = originalUrl;
    
    originalImg.onload = () => {
      if (containerRef.current && containerRef.current.parentElement) {
        const aspectRatio = originalImg.naturalHeight / originalImg.naturalWidth;
        const wrapperWidth = containerRef.current.parentElement.offsetWidth || containerRef.current.parentElement.clientWidth;
        const maxHeight = window.innerHeight * 0.7;
        
        // Calculate ideal height based on width
        let idealHeight = wrapperWidth * aspectRatio;
        let finalWidth = wrapperWidth;
        let finalHeight = idealHeight;
        
        // If height exceeds limit, calculate width based on height limit
        if (idealHeight > maxHeight) {
          finalHeight = maxHeight;
          finalWidth = maxHeight / aspectRatio;
        }
        
        containerRef.current.style.width = `${finalWidth}px`;
        containerRef.current.style.height = `${finalHeight}px`;
        containerRef.current.style.margin = '0 auto';
      }
    };

    const handleResize = () => {
      if (containerRef.current && originalImg.complete && containerRef.current.parentElement) {
        const aspectRatio = originalImg.naturalHeight / originalImg.naturalWidth;
        const wrapperWidth = containerRef.current.parentElement.offsetWidth || containerRef.current.parentElement.clientWidth;
        const maxHeight = window.innerHeight * 0.7;
        
        // Calculate ideal height based on width
        let idealHeight = wrapperWidth * aspectRatio;
        let finalWidth = wrapperWidth;
        let finalHeight = idealHeight;
        
        // If height exceeds limit, calculate width based on height limit
        if (idealHeight > maxHeight) {
          finalHeight = maxHeight;
          finalWidth = maxHeight / aspectRatio;
        }
        
        containerRef.current.style.width = `${finalWidth}px`;
        containerRef.current.style.height = `${finalHeight}px`;
        containerRef.current.style.margin = '0 auto';
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [originalUrl, processedUrl, isVisible]);

  useEffect(() => {
    if (!isVisible || !sliderRef.current || !afterImageRef.current) return;

    const slider = sliderRef.current;
    const afterImage = afterImageRef.current;

    const slideMove = (x) => {
      const containerWidth = slider.parentNode.offsetWidth;
      if (x < 0) x = 0;
      if (x > containerWidth) x = containerWidth;

      slider.style.left = x + 'px';
      const percentage = (x / containerWidth) * 100;
      afterImage.style.clipPath = `polygon(0 0, ${percentage}% 0, ${percentage}% 100%, 0 100%)`;
    };

    const handleMouseDown = (e) => {
      e.preventDefault();
      setIsMoving(true);
    };

    const handleMouseUp = () => {
      setIsMoving(false);
    };

    const handleMouseMove = (e) => {
      if (!isMoving) return;
      let x = e.pageX;
      x -= slider.parentNode.getBoundingClientRect().left;
      slideMove(x);
    };

    const handleTouchStart = (e) => {
      e.preventDefault();
      setIsMoving(true);
    };

    const handleTouchEnd = () => {
      setIsMoving(false);
    };

    const handleTouchMove = (e) => {
      if (!isMoving) return;
      let x;
      if (e.touches) x = e.touches[0].pageX;
      x -= slider.parentNode.getBoundingClientRect().left;
      slideMove(x);
    };

    slider.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousemove', handleMouseMove);
    slider.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchend', handleTouchEnd);
    document.addEventListener('touchmove', handleTouchMove);

    return () => {
      slider.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousemove', handleMouseMove);
      slider.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchend', handleTouchEnd);
      document.removeEventListener('touchmove', handleTouchMove);
    };
  }, [isVisible, isMoving]);

  if (!isVisible) return null;

  return (
    <section className="comparison-section show">
      <h2 className="comparison-title">Result Comparison</h2>
      <div className="comparison-container-wrapper">
        <div className="comparison-container" ref={containerRef}>
          <img
            className="comparison-before"
            src={originalUrl}
            alt="Original Image"
          />
          <img
            className="comparison-after"
            ref={afterImageRef}
            src={processedUrl}
            alt="Processed Result"
          />
          <div className="comparison-slider" ref={sliderRef}>
            <div className="comparison-handle"></div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ComparisonViewer;



