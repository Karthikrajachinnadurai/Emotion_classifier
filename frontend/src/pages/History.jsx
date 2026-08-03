import React, { useState, useEffect } from 'react';
import axiosClient from '../api/axiosClient';
import GlassCard from '../components/GlassCard';

const History = () => {
  const [history, setHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterEmotion, setFilterEmotion] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const res = await axiosClient.get('/history');
      setHistory(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const filtered = history.filter(item => {
    const matchesSearch = item.original_message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterEmotion ? item.predicted_emotion === filterEmotion : true;
    return matchesSearch && matchesFilter;
  });

  const paginated = filtered.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);
  const totalPages = Math.ceil(filtered.length / itemsPerPage);

  const emotions = [...new Set(history.map(h => h.predicted_emotion))];

  return (
    <div>
      <h1 className="gradient-text" style={{ fontSize: '2.5rem', marginBottom: '24px' }}>Analysis History</h1>
      
      <GlassCard style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          <input 
            type="text" 
            placeholder="Search messages..." 
            className="input-field" 
            style={{ flex: 1, minWidth: '200px' }}
            value={searchTerm}
            onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
          />
          <select 
            className="input-field" 
            style={{ width: '200px' }}
            value={filterEmotion}
            onChange={(e) => { setFilterEmotion(e.target.value); setCurrentPage(1); }}
          >
            <option value="">All Emotions</option>
            {emotions.map(e => <option key={e} value={e}>{e}</option>)}
          </select>
        </div>
      </GlassCard>

      <GlassCard style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--border-glass)' }}>
                <th style={{ padding: '16px' }}>Date</th>
                <th style={{ padding: '16px' }}>Emotion</th>
                <th style={{ padding: '16px' }}>Message</th>
                <th style={{ padding: '16px' }}>CBT Response</th>
              </tr>
            </thead>
            <tbody>
              {paginated.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                  <td style={{ padding: '16px', color: 'var(--text-secondary)' }}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                  <td style={{ padding: '16px', textTransform: 'capitalize', fontWeight: 600 }}>
                    {item.predicted_emotion} <br/>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{(item.confidence*100).toFixed(1)}%</span>
                  </td>
                  <td style={{ padding: '16px', maxWidth: '300px' }}>
                    <div style={{ maxHeight: '60px', overflowY: 'auto', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                      {item.original_message}
                    </div>
                  </td>
                  <td style={{ padding: '16px', maxWidth: '400px' }}>
                    <div style={{ maxHeight: '80px', overflowY: 'auto', fontSize: '0.9rem' }}>
                      {item.cbt_response}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div style={{ display: 'flex', justifyContent: 'space-between', padding: '16px', alignItems: 'center', background: 'rgba(255,255,255,0.02)' }}>
          <span style={{ color: 'var(--text-muted)' }}>Showing {paginated.length} of {filtered.length} entries</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(p => p - 1)}
              style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '4px', color: '#fff', cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
            >
              Prev
            </button>
            <button 
              disabled={currentPage === totalPages || totalPages === 0}
              onClick={() => setCurrentPage(p => p + 1)}
              style={{ padding: '6px 12px', background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '4px', color: '#fff', cursor: currentPage === totalPages || totalPages === 0 ? 'not-allowed' : 'pointer' }}
            >
              Next
            </button>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

export default History;
