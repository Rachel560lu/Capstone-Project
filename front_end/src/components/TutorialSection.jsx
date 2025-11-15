import React from 'react';

const TutorialSection = () => {
  const steps = [
    'First, select a function module (Clutter Removal or Virtual Staging)',
    'Click "Select Image" button to upload your property photo',
    'The system will automatically process your image and display the result comparison',
    'Drag the slider in the middle to compare before and after effects',
    'The processed image can be saved or shared'
  ];

  return (
    <section className="tutorial-section">
      <h2 className="tutorial-title">Tutorial</h2>
      <ol className="tutorial-steps">
        {steps.map((step, index) => (
          <li key={index} className="tutorial-step">
            {step}
          </li>
        ))}
      </ol>
    </section>
  );
};

export default TutorialSection;



