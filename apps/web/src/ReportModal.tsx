import React, { useState } from 'react';
import { FileWarning, CheckCircle } from 'lucide-react';

export const ReportModal = ({ onClose }: { onClose: () => void }) => {
  const [description, setDescription] = useState('');
  const [fireVisible, setFireVisible] = useState(false);
  const [smokeVisible, setSmokeVisible] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Hardcoded location near Jamnagar for demonstration
    const payload = {
      location: { latitude: 22.346, longitude: 69.876 },
      fire_visible: fireVisible,
      smoke_visible: smokeVisible,
      description: description
    };

    try {
      await fetch('http://localhost:8000/api/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      setSubmitted(true);
      
      // Close after 2 seconds
      setTimeout(() => {
        onClose();
      }, 2000);
      
    } catch (err) {
      console.error("Failed to submit report", err);
    }
  };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.4)',
      zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div className="bg-base" style={{ 
        width: '400px', padding: '2rem', borderRadius: '0.5rem',
        boxShadow: 'var(--shadow-lg)'
      }}>
        
        {submitted ? (
          <div style={{ textAlign: 'center', padding: '2rem 0' }}>
            <CheckCircle size={48} className="text-accent" style={{ margin: '0 auto 1rem' }} />
            <h3 style={{ margin: '0 0 0.5rem 0' }}>Report Submitted</h3>
            <p className="text-secondary" style={{ fontSize: '0.875rem' }}>
              Your eyewitness account is being fused with satellite thermal data.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
              <FileWarning className="text-accent" />
              <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Submit Public Report</h2>
            </div>
            
            <p className="text-secondary" style={{ fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              Submitting simulated report near <strong>Jamnagar Mega Refinery</strong>.
            </p>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={fireVisible} onChange={(e) => setFireVisible(e.target.checked)} />
                Flames Visible
              </label>
            </div>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                <input type="checkbox" checked={smokeVisible} onChange={(e) => setSmokeVisible(e.target.checked)} />
                Smoke Visible
              </label>
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Description (Optional)</label>
              <textarea 
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                style={{ width: '100%', padding: '0.5rem', border: '1px solid var(--color-border)', borderRadius: '0.25rem', fontFamily: 'inherit' }}
                placeholder="E.g. I see thick black smoke..."
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
              <button 
                type="button" 
                onClick={onClose}
                style={{ padding: '0.5rem 1rem', border: 'none', backgroundColor: 'transparent', cursor: 'pointer', color: 'var(--color-text-secondary)' }}
              >
                Cancel
              </button>
              <button 
                type="submit"
                style={{ padding: '0.5rem 1rem', border: 'none', backgroundColor: 'var(--color-accent)', color: 'white', borderRadius: '0.25rem', cursor: 'pointer' }}
              >
                Submit Report
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
