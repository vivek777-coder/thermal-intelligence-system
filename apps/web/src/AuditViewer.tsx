import { useEffect, useState } from 'react';
import { ShieldCheck, Clock } from 'lucide-react';

export const AuditViewer = ({ incidentId, onClose }: { incidentId: string, onClose: () => void }) => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAudit = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/incidents/${incidentId}/audit`);
        if (response.ok) {
          const result = await response.json();
          setLogs(result.data || []);
        }
      } catch (err) {
        console.error("Error fetching audit logs", err);
      } finally {
        setLoading(false);
      }
    };
    fetchAudit();
  }, [incidentId]);

  return (
    <div style={{
      position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(245, 239, 226, 0.95)', // var(--color-base) with opacity
      zIndex: 100, display: 'flex', flexDirection: 'column'
    }}>
      <div className="bg-surface" style={{ padding: '1.5rem', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0, color: 'var(--color-text-primary)' }}>
          <ShieldCheck size={24} className="text-accent" />
          Decision Audit Trail
        </h2>
        <button 
          onClick={onClose}
          style={{ padding: '0.5rem 1rem', border: '1px solid var(--color-border)', borderRadius: '0.25rem', backgroundColor: 'var(--color-base)', cursor: 'pointer' }}
        >
          Close Viewer
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', maxWidth: '800px', margin: '0 auto', width: '100%' }}>
        {loading ? (
          <p className="text-secondary">Loading deterministic rule engine trail...</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <p className="text-secondary" style={{ marginBottom: '1rem' }}>
              Showing exact deterministic pipeline execution for <strong>{incidentId}</strong>
            </p>
            {logs.map((log, index) => (
              <div key={index} style={{ display: 'flex', gap: '1.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ 
                    width: '32px', height: '32px', borderRadius: '50%', 
                    backgroundColor: 'var(--color-accent)', color: 'white', 
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 'bold', fontSize: '0.875rem', flexShrink: 0
                  }}>
                    {log.step}
                  </div>
                  {index < logs.length - 1 && (
                    <div style={{ width: '2px', flex: 1, backgroundColor: 'var(--color-border)', margin: '0.5rem 0' }} />
                  )}
                </div>
                
                <div className="bg-surface border-subtle" style={{ padding: '1.25rem', borderRadius: '0.5rem', flex: 1, marginBottom: index === logs.length - 1 ? 0 : '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-text-primary)' }}>{log.action}</h3>
                    <span className="text-secondary" style={{ fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={12} /> {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)', fontFamily: 'monospace' }}>
                    {log.details}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
