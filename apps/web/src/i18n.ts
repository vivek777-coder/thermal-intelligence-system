import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      "app": {
        "title": "Industrial Thermal Intelligence",
        "subtitle": "Emergency Decision-Support Platform"
      },
      "map": {
        "loading": "Loading map data...",
        "layers": "Map Layers"
      },
      "panel": {
        "no_selection": "Select an incident on the map to view details.",
        "incident_details": "Incident Details",
        "facility": "Facility",
        "coordinates": "Coordinates",
        "classification": "Classification",
        "risk_score": "Risk Score",
        "probable_cause": "Probable Cause",
        "weather": "Weather Conditions",
        "alerts_sent": "Alerts Dispatched"
      },
      "severity": {
        "LOW": "Low",
        "MEDIUM": "Medium",
        "HIGH": "High",
        "CRITICAL": "Critical"
      }
    }
  },
  hi: {
    translation: {
      "app": {
        "title": "औद्योगिक तापीय खुफिया",
        "subtitle": "आपातकालीन निर्णय-समर्थन मंच"
      },
      "map": {
        "loading": "मानचित्र डेटा लोड हो रहा है...",
        "layers": "मानचित्र परतें"
      },
      "panel": {
        "no_selection": "विवरण देखने के लिए मानचित्र पर एक घटना का चयन करें।",
        "incident_details": "घटना का विवरण",
        "facility": "सुविधा",
        "coordinates": "निर्देशांक",
        "classification": "वर्गीकरण",
        "risk_score": "जोखिम स्कोर",
        "probable_cause": "संभावित कारण",
        "weather": "मौसम की स्थिति",
        "alerts_sent": "अलर्ट भेजे गए"
      },
      "severity": {
        "LOW": "कम",
        "MEDIUM": "मध्यम",
        "HIGH": "उच्च",
        "CRITICAL": "गंभीर"
      }
    }
  },
  hinglish: {
    translation: {
      "app": {
        "title": "Industrial Thermal Intelligence",
        "subtitle": "Emergency Decision-Support Platform"
      },
      "map": {
        "loading": "Map data load ho raha hai...",
        "layers": "Map Layers"
      },
      "panel": {
        "no_selection": "Details dekhne ke liye map par ek incident select karein.",
        "incident_details": "Incident Details",
        "facility": "Facility",
        "coordinates": "Coordinates",
        "classification": "Classification",
        "risk_score": "Risk Score",
        "probable_cause": "Probable Cause",
        "weather": "Weather Conditions",
        "alerts_sent": "Alerts Bheje Gaye"
      },
      "severity": {
        "LOW": "Low",
        "MEDIUM": "Medium",
        "HIGH": "High",
        "CRITICAL": "Critical"
      }
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "en", // default
    fallbackLng: "en",
    interpolation: {
      escapeValue: false 
    }
  });

export default i18n;
