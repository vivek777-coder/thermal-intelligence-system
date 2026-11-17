import { useTranslation } from 'react-i18next';
import { Flame, ShieldAlert, Navigation, Activity, CloudSun } from 'lucide-react';

export const IncidentPanel = ({ incident, onOpenAudit }: { incident: any, onOpenAudit: (id: string) => void }) => {
  const { t } = useTranslation();

  if (!incident) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        <p>{t('panel.no_selection')}</p>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'LOW': return 'var(--color-severity-low)';
      case 'MEDIUM': return 'var(--color-severity-medium)';
      case 'HIGH': return 'var(--color-severity-high)';
      case 'CRITICAL': return 'var(--color-severity-critical)';
      default: return 'var(--color-text-secondary)';
    }
  };

  const severityColor = getSeverityColor(incident.risk?.severity);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%', overflowY: 'auto', paddingRight: '0.5rem' }}>
      
      {/* Header section with explicit severity color mapping */}
      <div style={{ borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', color: 'var(--color-text-primary)' }}>{t('panel.incident_details')}</h2>
          <span style={{
            backgroundColor: severityColor,
            color: 'white',
            padding: '0.25rem 0.75rem',
            borderRadius: '999px',
            fontSize: '0.75rem',
            fontWeight: 'bold',
            letterSpacing: '0.05em'
          }}>
            {t(`severity.${incident.risk?.severity}`)}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
            ID: {incident.id}
          </p>
          <button 
            onClick={() => onOpenAudit(incident.id)}
            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem', border: '1px solid var(--color-accent)', color: 'var(--color-accent)', backgroundColor: 'transparent', borderRadius: '0.25rem', cursor: 'pointer' }}
          >
            View Audit Trail
          </button>
        </div>
      </div>

      {/* Facility & Location */}
      <div className="bg-surface border-subtle" style={{ padding: '1rem', borderRadius: '0.5rem' }}>
        <h3 style={{ fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--color-text-primary)' }}>
          <ShieldAlert size={16} /> {t('panel.facility')}
        </h3>
        <p style={{ margin: 0, fontWeight: 500 }}>{incident.facility?.name}</p>
        <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--color-text-secondary)' }}>
          Type: {incident.facility?.type}
        </p>
        
        <div style={{ marginTop: '1rem', paddingTop: '0.5rem', borderTop: '1px solid var(--color-border)' }}>
          <p style={{ margin: 0, fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Navigation size={14} className="text-secondary" />
            <span className="text-secondary">{t('panel.coordinates')}:</span> 
            {incident.location?.latitude.toFixed(4)}, {incident.location?.longitude.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Thermal Intelligence */}
      <div className="bg-surface border-subtle" style={{ padding: '1rem', borderRadius: '0.5rem' }}>
         <h3 style={{ fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--color-text-primary)' }}>
          <Flame size={16} className="text-accent" /> {t('panel.classification')}
        </h3>
        <p style={{ textTransform: 'capitalize', fontWeight: 500, margin: '0 0 0.5rem 0' }}>
          {incident.temporal?.classification}
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.875rem' }}>
          <div>
            <div className="text-secondary">FRP</div>
            <div>{incident.firms?.frp} MW</div>
          </div>
          <div>
            <div className="text-secondary">Deviation</div>
            <div>+{incident.temporal?.frpDeviation}σ</div>
          </div>
        </div>
      </div>

      {/* Probable Cause Narrative */}
      <div className="bg-surface border-subtle" style={{ padding: '1rem', borderRadius: '0.5rem' }}>
         <h3 style={{ fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--color-text-primary)' }}>
          <Activity size={16} /> {t('panel.probable_cause')}
        </h3>
        <p style={{ margin: 0, fontSize: '0.875rem', lineHeight: 1.6 }}>
          {incident.probable_cause}
        </p>
      </div>

      {/* Weather Context */}
      <div className="bg-surface border-subtle" style={{ padding: '1rem', borderRadius: '0.5rem' }}>
         <h3 style={{ fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', color: 'var(--color-text-primary)' }}>
          <CloudSun size={16} /> {t('panel.weather')}
        </h3>
        <p style={{ margin: '0 0 0.25rem 0', fontSize: '0.875rem' }}>
          <span className="text-secondary">Quality:</span> {incident.weather?.observationQuality}
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {incident.weather?.reasonCodes.map((code: string) => (
            <span key={code} style={{ backgroundColor: 'var(--color-base)', padding: '0.125rem 0.5rem', borderRadius: '0.25rem', fontSize: '0.75rem', border: '1px solid var(--color-border)' }}>
              {code}
            </span>
          ))}
        </div>
      </div>

      {/* Alerts Sent */}
      <div style={{ marginTop: 'auto', paddingTop: '1rem' }}>
         <h3 style={{ fontSize: '0.875rem', marginBottom: '0.75rem', color: 'var(--color-text-secondary)' }}>
          {t('panel.alerts_sent')}
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {incident.alerts_sent?.map((alert: string) => (
            <span key={alert} style={{ 
              backgroundColor: 'var(--color-surface)', 
              border: `1px solid var(--color-border)`,
              color: 'var(--color-accent)',
              padding: '0.25rem 0.75rem', 
              borderRadius: '999px', 
              fontSize: '0.75rem',
              fontWeight: 500
            }}>
              {alert}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
