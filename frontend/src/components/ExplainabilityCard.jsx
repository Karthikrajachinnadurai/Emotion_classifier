import React, { useState } from 'react';
import { Info, Activity, Clock, ShieldAlert } from 'lucide-react';

const ExplainabilityCard = ({ prediction }) => {
  const [expanded, setExpanded] = useState(false);

  if (!prediction) return null;

  return (
    <div style={{ marginTop: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px solid var(--border-glass)', fontSize: '0.85rem' }}>
      <div 
        onClick={() => setExpanded(!expanded)} 
        style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', color: 'var(--text-secondary)' }}
      >
        <Info size={16} /> 
        <span>AI Prediction Insights {expanded ? '(Click to hide)' : '(Click to view)'}</span>
      </div>
      
      {expanded && (
        <div style={{ padding: '12px', borderTop: '1px solid var(--border-glass)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}><Activity size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }}/> Confidence</span>
              <span style={{ fontWeight: 600 }}>{(prediction.confidence * 100).toFixed(1)}%</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: 'var(--text-muted)' }}><Clock size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }}/> Inference Time</span>
              <span style={{ fontWeight: 600 }}>{prediction.inference_time.toFixed(1)} ms</span>
            </div>
            
            {prediction.probability_distribution && (
              <div>
                <div style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>Probability Distribution:</div>
                {Object.entries(prediction.probability_distribution)
                  .sort((a,b) => b[1] - a[1])
                  .map(([emo, prob]) => (
                  <div key={emo} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <div style={{ width: '60px', textTransform: 'capitalize', fontSize: '0.8rem' }}>{emo}</div>
                    <div style={{ flex: 1, background: 'rgba(255,255,255,0.1)', height: '6px', borderRadius: '3px' }}>
                      <div style={{ width: `${prob * 100}%`, background: 'var(--accent-secondary)', height: '100%', borderRadius: '3px' }}></div>
                    </div>
                    <div style={{ width: '40px', textAlign: 'right', fontSize: '0.75rem' }}>{(prob*100).toFixed(0)}%</div>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', gap: '8px', padding: '8px', background: 'rgba(224,90,58,0.1)', borderRadius: '4px', color: '#E05A3A', marginTop: '8px' }}>
              <ShieldAlert size={16} style={{ flexShrink: 0 }} />
              <div style={{ fontSize: '0.8rem' }}>
                <strong>Disclaimer:</strong> This is an AI prediction, not a medical diagnosis. If you are in crisis, please seek professional help immediately.
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplainabilityCard;
