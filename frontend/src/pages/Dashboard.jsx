import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import axiosClient from '../api/axiosClient';
import GlassCard from '../components/GlassCard';
import ExplainabilityCard from '../components/ExplainabilityCard';
import SpeechRecorder from '../components/SpeechRecorder';
import { Flame, Star, Activity, Sparkles, Send } from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [insights, setInsights] = useState([]);
  
  const [text, setText] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchDashboard();
    fetchHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const fetchDashboard = async () => {
    try {
      const dashRes = await axiosClient.get('/dashboard');
      setDashboardData(dashRes.data);
      
      const insightsRes = await axiosClient.get('/insights');
      setInsights(insightsRes.data.insights);
    } catch (error) {
      console.error(error);
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axiosClient.get('/history');
      // format to match chat structure, limit to 5
      const recent = res.data.slice(0, 5).reverse().map(h => ({
        id: h.id,
        userMsg: h.original_message,
        aiMsg: h.cbt_response,
        prediction: {
          emotion: h.predicted_emotion,
          confidence: h.confidence,
          inference_time: h.inference_time,
          probability_distribution: h.probability_distribution ? JSON.parse(h.probability_distribution) : null,
          is_crisis: h.is_crisis
        }
      }));
      setChatHistory(recent);
    } catch (err) {
      console.error(err);
    }
  };

  // ── Speech-to-Text callback ──────────────────────────────────────────────
  // Populates the text field with the transcript so the user can
  // review it before clicking Send. Does NOT auto-submit.
  const handleTranscript = useCallback((transcribedText) => {
    setText(transcribedText);
  }, []);

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    
    setLoading(true);
    const userText = text;
    setText('');
    
    // Optimistic UI update for user message
    setChatHistory(prev => [...prev, { id: Date.now(), userMsg: userText, aiMsg: null, prediction: null }]);
    
    try {
      const res = await axiosClient.post('/predict', { text: userText });
      
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[newHist.length - 1].aiMsg = res.data.cbt_response;
        newHist[newHist.length - 1].prediction = res.data;
        return newHist;
      });
      fetchDashboard();
    } catch (error) {
      console.error(error);
      setChatHistory(prev => {
        const newHist = [...prev];
        newHist[newHist.length - 1].aiMsg = "Sorry, I couldn't process that right now.";
        return newHist;
      });
    } finally {
      setLoading(false);
    }
  };

  if (!dashboardData) return <div>Loading dashboard...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: 'calc(100vh - 64px)' }}>
      {/* Top Banner */}
      <div style={{ marginBottom: '24px' }}>
        <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '8px' }}>
          Welcome back, {user?.name}!
        </h1>
        <div style={{ display: 'flex', gap: '8px', color: 'var(--text-secondary)' }}>
          <Sparkles size={18} color="#F5C518" /> 
          {insights.length > 0 ? insights[0] : "Let's check in on your emotions today."}
        </div>
      </div>

      {/* Stats Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px', marginBottom: '24px', flexShrink: 0 }}>
        <GlassCard style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ padding: '12px', background: 'rgba(245,197,24,0.15)', borderRadius: '12px', color: '#F5C518' }}><Star size={24} /></div>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Wellness Points</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{dashboardData.total_points}</div>
          </div>
        </GlassCard>
        <GlassCard style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ padding: '12px', background: 'rgba(232,64,90,0.15)', borderRadius: '12px', color: '#E8405A' }}><Flame size={24} /></div>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Current Streak</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{dashboardData.streak} Days</div>
          </div>
        </GlassCard>
        <GlassCard style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ padding: '12px', background: 'rgba(108,99,255,0.15)', borderRadius: '12px', color: '#6C63FF' }}><Activity size={24} /></div>
          <div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Today's Emotion</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, textTransform: 'capitalize' }}>{dashboardData.recent_mood}</div>
          </div>
        </GlassCard>
      </div>

      {/* Chat Interface */}
      <GlassCard style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: 0 }}>
        <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {chatHistory.length === 0 && (
            <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: 'auto', marginBottom: 'auto' }}>
              No recent conversations. How are you feeling today?
            </div>
          )}
          
          {chatHistory.map((chat) => (
            <div key={chat.id} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* User Bubble */}
              <div style={{ alignSelf: 'flex-end', background: 'var(--accent-gradient)', padding: '12px 16px', borderRadius: '16px', borderBottomRightRadius: '4px', maxWidth: '70%' }}>
                {chat.userMsg}
              </div>
              
              {/* AI Bubble */}
              <div style={{ alignSelf: 'flex-start', maxWidth: '80%' }}>
                <div style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', padding: '12px 16px', borderRadius: '16px', borderBottomLeftRadius: '4px' }}>
                  <div dangerouslySetInnerHTML={{ __html: chat.aiMsg ? chat.aiMsg.replace(/\n/g, '<br/>') : 'Analyzing...' }}></div>
                </div>
                {chat.prediction && <ExplainabilityCard prediction={chat.prediction} />}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        {/* Input Area */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid var(--border-glass)', background: 'rgba(10, 12, 19, 0.5)' }}>
          <form onSubmit={handlePredict} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            {/* 🎙 Mic button — populates text field on transcript, does not auto-predict */}
            <SpeechRecorder
              onTranscript={handleTranscript}
              disabled={loading}
            />
            <input 
              type="text" 
              className="input-field" 
              style={{ flex: 1, borderRadius: '50px', padding: '12px 24px' }}
              placeholder="Type or speak how you're feeling..." 
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={loading}
            />
            <button type="submit" disabled={loading} style={{ background: 'var(--accent-gradient)', border: 'none', width: '48px', height: '48px', borderRadius: '50%', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
              <Send size={20} />
            </button>
          </form>
        </div>
      </GlassCard>
    </div>
  );
};

export default Dashboard;
