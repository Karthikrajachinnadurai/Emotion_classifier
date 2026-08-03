import React, { useState, useEffect } from 'react';
import GlassCard from '../components/GlassCard';
import axiosClient from '../api/axiosClient';
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const Settings = () => {
  const [dailyReminder, setDailyReminder] = useState(true);
  const [dataPrivacy, setDataPrivacy] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  
  // Toast state
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => {
      setToast({ show: false, message: '', type: 'success' });
    }, 3000);
  };

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await axiosClient.get('/profile');
        if (response.data) {
          setDailyReminder(response.data.daily_reminder ?? true);
          setDataPrivacy(response.data.data_privacy ?? false);
        }
      } catch (error) {
        console.error("Failed to load settings:", error);
        showToast("Failed to load settings", "error");
      } finally {
        setIsLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await axiosClient.put('/profile', {
        daily_reminder: dailyReminder,
        data_privacy: dataPrivacy
      });
      showToast("Settings saved successfully!");
    } catch (error) {
      console.error("Failed to save settings:", error);
      showToast("Failed to save settings", "error");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Loader2 className="stt-spin" size={40} color="var(--accent-primary)" />
      </div>
    );
  }

  return (
    <div style={{ position: 'relative' }}>
      <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '32px' }}>Settings</h1>
      
      {/* Custom Toast Notification */}
      {toast.show && (
        <div style={{
          position: 'fixed',
          top: '24px',
          right: '24px',
          background: toast.type === 'success' ? '#10B981' : '#EF4444',
          color: '#fff',
          padding: '12px 20px',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000,
          animation: 'fadeIn 0.3s ease'
        }}>
          {toast.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
          <span style={{ fontWeight: 500 }}>{toast.message}</span>
        </div>
      )}
      
      <GlassCard style={{ maxWidth: '600px' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '24px' }}>Preferences</h2>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>Daily Reminder</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Get a notification to log your mood</div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={dailyReminder}
                onChange={(e) => setDailyReminder(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--accent-primary)', cursor: 'pointer' }} 
              />
            </label>
          </div>
          
          <div style={{ width: '100%', height: '1px', background: 'var(--border-glass)' }}></div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontWeight: 600 }}>Data Privacy</div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Anonymize my data for research</div>
            </div>
            <label style={{ cursor: 'pointer' }}>
              <input 
                type="checkbox" 
                checked={dataPrivacy}
                onChange={(e) => setDataPrivacy(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--accent-primary)', cursor: 'pointer' }} 
              />
            </label>
          </div>
          
          <div style={{ width: '100%', height: '1px', background: 'var(--border-glass)' }}></div>

          <button 
            className="btn-primary" 
            style={{ 
              alignSelf: 'flex-start', 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px',
              opacity: isSaving ? 0.7 : 1,
              cursor: isSaving ? 'not-allowed' : 'pointer'
            }}
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? <Loader2 size={18} className="stt-spin" /> : null}
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

export default Settings;
