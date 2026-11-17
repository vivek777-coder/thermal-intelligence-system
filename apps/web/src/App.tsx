import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Languages, FileWarning, AlertTriangle } from 'lucide-react';
import { MapLayer } from './MapLayer';
import { IncidentPanel } from './IncidentPanel';
import { AuditViewer } from './AuditViewer';
import { ReportModal } from './ReportModal';

function App() {
  const { t, i18n } = useTranslation();
  const [incidents, setIncidents] = useState<any[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  
  const [showAuditFor, setShowAuditFor] = useState<string | null>(null);
  const [showReportModal, setShowReportModal] = useState(false);
  const [systemHealth, setSystemHealth] = useState<any>(null);

  useEffect(() => {
    const savedLang = localStorage.getItem('app_language');
    if (savedLang) {
      i18n.changeLanguage(savedLang);
    }
  }, [i18n]);

  const changeLanguage = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const lang = e.target.value;
    i18n.changeLanguage(lang);
    localStorage.setItem('app_language', lang);
  };

  const fetchIncidents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/incidents');
      if (response.ok) {
        const result = await response.json();
        setIncidents(result.data || []);
        
        // Update selected incident if data changed
        if (selectedIncident) {
          const updated = result.data.find((i: any) => i.id === selectedIncident.id);
          if (updated) setSelectedIncident(updated);
        }
      }
    } catch (err) {
      console.error("Error fetching incidents:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/system/health');
      if (response.ok) {
        const result = await response.json();
        setSystemHealth(result);
      }
    } catch (err) {
      console.error("Error fetching system health:", err);
    }
  };

  useEffect(() => {
    fetchIncidents();
    fetchSystemHealth();
    
    // Poll system health every 30 seconds
    const interval = setInterval(fetchSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const isDegraded = systemHealth?.status === 'degraded';

  return (
    <>
      {showAuditFor && (
        <AuditViewer incidentId={showAuditFor} onClose={() => setShowAuditFor(null)} />
      )}
      
      {showReportModal && (
        <ReportModal onClose={() => {
          setShowReportModal(false);
          // Refetch to see if the new report updated the fusion scores
          fetchIncidents();
        }} />
      )}

      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Globe className="text-accent" size={24} />
          <div>
            <h1 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--color-accent)' }}>
              {t('app.title')}
            </h1>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
              {t('app.subtitle')}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <button 
            onClick={() => setShowReportModal(true)}
            style={{ 
              display: 'flex', alignItems: 'center', gap: '0.5rem',
              padding: '0.5rem 1rem', border: '1px solid var(--color-accent)', 
              color: 'var(--color-accent)', backgroundColor: 'transparent',
              borderRadius: '0.25rem', cursor: 'pointer' 
            }}
          >
            <FileWarning size={16} /> Submit Public Report
          </button>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Languages size={18} className="text-secondary" />
            <select 
              value={i18n.language} 
              onChange={changeLanguage}
              style={{
                padding: '0.5rem',
                borderRadius: '0.375rem',
                border: '1px solid var(--color-border)',
                backgroundColor: 'var(--color-base)',
                color: 'var(--color-text-primary)',
                fontFamily: 'inherit',
                cursor: 'pointer'
              }}
            >
              <option value="en">English</option>
              <option value="hi">हिन्दी</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </div>
        </div>
      </header>

      {/* Degraded Mode Banner */}
      {isDegraded && (
        <div style={{
          backgroundColor: 'var(--color-severity-medium)',
          color: 'var(--color-text-primary)',
          padding: '0.5rem 1rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '0.5rem',
          fontSize: '0.875rem',
          fontWeight: 500
        }}>
          <AlertTriangle size={16} />
          <span>DEGRADED MODE: FIRMS API is unreachable. Displaying cached data from {new Date(systemHealth.services.firms_api.last_successful_fetch).toLocaleTimeString()}.</span>
        </div>
      )}

      <main style={{ 
        display: 'flex', 
        flex: 1, 
        overflow: 'hidden', 
        backgroundColor: 'var(--color-base)' 
      }}>
        {/* Left: Map Area */}
        <div style={{ flex: 1, position: 'relative' }}>
          {loading ? (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-secondary)' }}>
              {t('map.loading')}
            </div>
          ) : (
            <MapLayer 
              incidents={incidents} 
              selectedIncident={selectedIncident} 
              onSelectIncident={setSelectedIncident} 
            />
          )}
        </div>

        {/* Right: Side Panel */}
        <div style={{ 
          width: '380px', 
          backgroundColor: 'var(--color-base)',
          borderLeft: '1px solid var(--color-border)',
          padding: '1.5rem',
          boxShadow: 'var(--shadow-lg)',
          zIndex: 10
        }}>
          <IncidentPanel 
            incident={selectedIncident} 
            onOpenAudit={(id) => setShowAuditFor(id)}
          />
        </div>
      </main>
    </>
  );
}

export default App;
