import React from 'react';

const RoleSelection = ({ onRoleSelect }) => {
  return (
    <section className="role-selection">
      <button className="role-btn" onClick={() => onRoleSelect('seller')}>
        Seller
      </button>
      <button className="role-btn" onClick={() => onRoleSelect('buyer')}>
        Buyer
      </button>
    </section>
  );
};

export default RoleSelection;



