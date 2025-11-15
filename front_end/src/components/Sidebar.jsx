import React from 'react';

const Sidebar = ({ selectedModule, onModuleSelect }) => {
  const modules = [
    {
      id: 'denoise',
      icon: '🖼️',
      title: 'Clutter Removal',
      desc: 'Intelligently enhance image quality and remove unwanted objects'
    },
    {
      id: 'virtual',
      icon: '🛋️',
      title: 'Virtual Staging',
      desc: 'Add beautiful furniture to empty rooms and showcase potential value'
    }
  ];

  return (
    <aside className="sidebar">
      <h3 className="sidebar-title">Function Modules</h3>
      <div className="sidebar-modules">
        {modules.map((module) => (
          <div 
            key={module.id} 
            className={`sidebar-module ${selectedModule === module.id ? 'active' : ''}`}
            onClick={() => onModuleSelect(module.id)}
          >
            <div className="sidebar-module-icon">{module.icon}</div>
            <div className="sidebar-module-content">
              <h4 className="sidebar-module-title">{module.title}</h4>
              <p className="sidebar-module-desc">{module.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};

export default Sidebar;

