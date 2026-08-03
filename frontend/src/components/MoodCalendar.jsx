import React from 'react';

const EMOTION_COLORS = {
  joy: '#F5C518',
  love: '#E8405A',
  surprise: '#1ABC9C',
  sadness: '#5B8DEF',
  fear: '#9B59B6',
  anger: '#E05A3A',
  crisis: '#FF0000',
  None: 'var(--overlay-light)'
};

const MoodCalendar = ({ history }) => {
  // 28 days representing the last 4 weeks.
  const days = [];
  const today = new Date();
  
  const historyMap = {};
  history.forEach(h => {
    const d = new Date(h.created_at).toISOString().split('T')[0];
    if (!historyMap[d]) historyMap[d] = h.predicted_emotion;
  });

  for (let i = 27; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const dateStr = d.toISOString().split('T')[0];
    days.push({
      date: dateStr,
      emotion: historyMap[dateStr] || 'None'
    });
  }

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px' }}>
        {['S','M','T','W','T','F','S'].map((d,i) => (
          <div key={i} style={{ textAlign: 'center', fontSize: '0.7rem', color: 'var(--text-muted)' }}>{d}</div>
        ))}
        {days.map((day, i) => (
          <div 
            key={i} 
            title={`${day.date}: ${day.emotion}`}
            style={{
              aspectRatio: '1/1',
              background: EMOTION_COLORS[day.emotion],
              borderRadius: '4px',
              opacity: day.emotion === 'None' ? 1 : 0.8
            }}
          ></div>
        ))}
      </div>
    </div>
  );
};

export default MoodCalendar;
