import React, { useState, useEffect } from 'react';
import axiosClient from '../api/axiosClient';
import GlassCard from '../components/GlassCard';
import MoodCalendar from '../components/MoodCalendar';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const Analytics = () => {
  const [weeklyData, setWeeklyData] = useState(null);
  const [weeklyTrend, setWeeklyTrend] = useState([]);
  const [emotionDist, setEmotionDist] = useState([]);
  const [history, setHistory] = useState([]);
  
  const COLORS = ['#6C63FF', '#48B8D0', '#E8405A', '#F5C518', '#3DD68C', '#9FA3C0'];

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const weeklyRes = await axiosClient.get('/weekly-summary');
        setWeeklyData(weeklyRes.data);
        const trendData = Object.keys(weeklyRes.data.weekly_mood_trend).map(date => ({
          date, score: weeklyRes.data.weekly_mood_trend[date]
        }));
        setWeeklyTrend(trendData);

        const analyticsRes = await axiosClient.get('/analytics');
        const distData = Object.keys(analyticsRes.data.emotion_distribution).map(emotion => ({
          name: emotion, value: analyticsRes.data.emotion_distribution[emotion]
        }));
        setEmotionDist(distData);

        const histRes = await axiosClient.get('/history');
        setHistory(histRes.data);
      } catch (error) {
        console.error(error);
      }
    };
    fetchAnalytics();
  }, []);

  return (
    <div>
      <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '32px' }}>Deep Analytics</h1>
      
      {weeklyData && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '24px', marginBottom: '32px' }}>
          <GlassCard>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Most Frequent (7d)</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600, textTransform: 'capitalize' }}>{weeklyData.most_frequent_emotion}</div>
          </GlassCard>
          <GlassCard>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Average Mood Score</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{weeklyData.average_mood_score.toFixed(1)} / 5</div>
          </GlassCard>
          <GlassCard>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Average Confidence</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{(weeklyData.average_confidence * 100).toFixed(1)}%</div>
          </GlassCard>
          <GlassCard>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Positive / Difficult Days</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600 }}><span style={{ color: '#3DD68C' }}>{weeklyData.positive_days}</span> / <span style={{ color: '#E05A3A' }}>{weeklyData.difficult_days}</span></div>
          </GlassCard>
        </div>
      )}

      {weeklyData?.suggestions && weeklyData.suggestions.length > 0 && (
        <GlassCard style={{ marginBottom: '32px', background: 'var(--overlay-medium)', borderLeft: '4px solid var(--accent-primary)' }}>
          <h3 style={{ marginBottom: '8px' }}>Insight</h3>
          <p style={{ color: 'var(--text-secondary)' }}>{weeklyData.suggestions[0]}</p>
        </GlassCard>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '32px', marginBottom: '32px' }}>
        
        <GlassCard>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '24px' }}>Emotion Distribution (All Time)</h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={emotionDist} cx="50%" cy="50%" innerRadius={70} outerRadius={100} paddingAngle={5} dataKey="value">
                  {emotionDist.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'center', marginTop: '16px' }}>
            {emotionDist.map((entry, index) => (
              <div key={entry.name} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: COLORS[index % COLORS.length] }}></div>
                <span style={{ textTransform: 'capitalize', fontSize: '0.85rem' }}>{entry.name}</span>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '24px' }}>Mood Score Trend (Weekly)</h2>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={weeklyTrend}>
                <XAxis dataKey="date" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" />
                <Tooltip contentStyle={{ background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)' }} />
                <Bar dataKey="score" fill="#6C63FF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

      </div>

      <GlassCard>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '24px' }}>Mood Calendar (Last 4 Weeks)</h2>
        <MoodCalendar history={history} />
      </GlassCard>
    </div>
  );
};

export default Analytics;
