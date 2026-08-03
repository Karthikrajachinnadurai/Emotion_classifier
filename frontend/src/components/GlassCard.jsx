import React from 'react';

const GlassCard = ({ children, style = {}, className = "" }) => {
  return (
    <div className={`glass-card ${className}`} style={style}>
      {children}
    </div>
  );
};

export default GlassCard;
