import React from 'react';
import GlassCard from '../components/GlassCard';

const Settings = () => {
  return (
    <div>
      <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '32px' }}>Settings</h1>
      
      <GlassCard style={{ maxWidth: '600px' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '24px' }}>Preferences</h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>Daily Reminder</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Get a notification to log your mood</div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input type="checkbox" defaultChecked style={{ width: '18px', height: '18px' }} />
            </label>
          </div>
          
          <div style={{ width: '100%', height: '1px', background: 'var(--border-glass)' }}></div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>Data Privacy</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Anonymize my data for research</div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input type="checkbox" style={{ width: '18px', height: '18px' }} />
            </label>
          </div>
          
          <div style={{ width: '100%', height: '1px', background: 'var(--border-glass)' }}></div>

          <button className="btn-primary" style={{ alignSelf: 'flex-start' }}>Save Changes</button>
        </div>
      </GlassCard>
    </div>
  );
};

export default Settings;
