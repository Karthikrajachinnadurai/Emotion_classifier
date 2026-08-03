import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axiosClient from '../api/axiosClient';
import GlassCard from '../components/GlassCard';
import { User, Mail, Calendar, Shield, Trophy } from 'lucide-react';

const Profile = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [badges, setBadges] = useState([]);

  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        const dashRes = await axiosClient.get('/dashboard');
        setDashboardData(dashRes.data);
        
        const badgesRes = await axiosClient.get('/badges');
        setBadges(badgesRes.data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchProfileData();
  }, []);

  return (
    <div>
      <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '32px' }}>User Profile</h1>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '32px' }}>
        
        {/* User Info Card */}
        <GlassCard style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div style={{ width: '100px', height: '100px', borderRadius: '50%', background: 'var(--accent-gradient)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '24px' }}>
            <User size={48} color="#fff" />
          </div>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '8px' }}>{user?.name}</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
            <Mail size={16} /> {user?.email}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-secondary)', marginBottom: '24px' }}>
            <Calendar size={16} /> Member since {user?.created_at ? new Date(user.created_at).getFullYear() : '2026'}
          </div>
          <div style={{ width: '100%', height: '1px', background: 'var(--border-glass)', marginBottom: '24px' }}></div>
          
          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Total Analyses</span>
            <span style={{ fontWeight: 600 }}>{dashboardData?.history_count || 0}</span>
          </div>
          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Current Streak</span>
            <span style={{ fontWeight: 600 }}>{dashboardData?.streak || 0} Days</span>
          </div>
          <div style={{ width: '100%', display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-muted)' }}>Total Points</span>
            <span style={{ fontWeight: 600, color: '#F5C518' }}>{dashboardData?.total_points || 0} ★</span>
          </div>
        </GlassCard>

        {/* Badges Showcase */}
        <GlassCard>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
            <Trophy size={28} color="#48B8D0" />
            <h2 style={{ fontSize: '1.5rem', margin: 0 }}>Badge Showcase</h2>
          </div>
          
          {badges.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
              No badges earned yet. Keep analyzing your emotions to unlock achievements!
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))', gap: '16px' }}>
              {badges.map(badge => (
                <div key={badge.id} style={{ 
                  background: 'var(--overlay-light)', 
                  border: '1px solid var(--border-glass)', 
                  borderRadius: '12px', 
                  padding: '16px', 
                  textAlign: 'center',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <div style={{ fontSize: '2rem' }}>{badge.badge_name.split(' ')[0]}</div>
                  <div style={{ fontSize: '0.9rem', fontWeight: 600 }}>{badge.badge_name.substring(badge.badge_name.indexOf(' ')+1)}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{new Date(badge.earned_at).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

      </div>
    </div>
  );
};

export default Profile;
