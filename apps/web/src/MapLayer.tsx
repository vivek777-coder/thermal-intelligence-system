import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';

// Fix for default leaflet icons in React
import L from 'leaflet';
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// A simple component to re-center the map when an incident is selected
function RecenterAutomatically({ lat, lng }: { lat: number, lng: number }) {
  const map = useMap();
  React.useEffect(() => {
    map.setView([lat, lng], 13);
  }, [lat, lng, map]);
  return null;
}

export const MapLayer = ({ 
  incidents, 
  selectedIncident, 
  onSelectIncident 
}: { 
  incidents: any[], 
  selectedIncident: any,
  onSelectIncident: (incident: any) => void 
}) => {
  
  // Default to Jamnagar coordinates for demonstration
  const center: [number, number] = [22.345, 69.876];

  const getSeverityColor = (severity: string) => {
    switch (severity?.toUpperCase()) {
      case 'LOW': return '#4CAF50';
      case 'MEDIUM': return '#FFC107';
      case 'HIGH': return '#FF9800';
      case 'CRITICAL': return '#F44336';
      default: return '#2F4858'; // accent color
    }
  };

  return (
    <MapContainer 
      center={center} 
      zoom={6} 
      scrollWheelZoom={true} 
      style={{ height: '100%', width: '100%', zIndex: 1 }}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      
      {selectedIncident && (
        <RecenterAutomatically 
          lat={selectedIncident.location.latitude} 
          lng={selectedIncident.location.longitude} 
        />
      )}

      {incidents.map((incident) => {
        const isSelected = selectedIncident?.id === incident.id;
        const color = getSeverityColor(incident.risk?.severity);
        
        return (
          <CircleMarker
            key={incident.id}
            center={[incident.location.latitude, incident.location.longitude]}
            pathOptions={{ 
              color: color, 
              fillColor: color, 
              fillOpacity: 0.6,
              weight: isSelected ? 3 : 1
            }}
            radius={isSelected ? 16 : 10}
            eventHandlers={{
              click: () => onSelectIncident(incident),
            }}
          >
            <Popup>
              <strong>{incident.facility?.name}</strong><br />
              Severity: {incident.risk?.severity}<br />
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectIncident(incident);
                }}
                style={{
                  marginTop: '8px',
                  padding: '4px 8px',
                  backgroundColor: 'var(--color-accent)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                View Details
              </button>
            </Popup>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
};
