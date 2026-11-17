"""
SQLAlchemy + GeoAlchemy2 models for the Thermal Intelligence Platform.

15 tables with PostGIS geometry columns and spatial indexes.
All geometry uses SRID 4326 (WGS 84).
"""

import uuid

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Double,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# ──────────────────────────────────────────────────────────────
# 1. facilities — Monitored industrial sites
# ──────────────────────────────────────────────────────────────
class Facility(Base):
    __tablename__ = "facilities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    facility_type = Column(String(100))
    location = Column(Geometry("POINT", srid=4326, spatial_index=False))
    boundary = Column(Geometry("POLYGON", srid=4326, spatial_index=False))
    address = Column(Text)
    region = Column(String(100))
    metadata_ = Column("metadata", JSONB)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    baselines = relationship("FacilityThermalBaseline", back_populates="facility")
    events = relationship("ThermalEvent", back_populates="facility")

    __table_args__ = (
        Index("idx_facilities_location", "location", postgresql_using="gist"),
        Index("idx_facilities_boundary", "boundary", postgresql_using="gist"),
    )


# ──────────────────────────────────────────────────────────────
# 2. thermal_observations — Raw FIRMS hotspot data
# ──────────────────────────────────────────────────────────────
class ThermalObservation(Base):
    __tablename__ = "thermal_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)
    satellite = Column(String(30))
    location = Column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    latitude = Column(Double)
    longitude = Column(Double)
    brightness = Column(Double)
    bright_ti4 = Column(Double)
    bright_ti5 = Column(Double)
    frp = Column(Double)
    confidence = Column(String(20))
    confidence_pct = Column(SmallInteger)
    acq_date = Column(Date)
    acq_time = Column(String(10))
    observed_at = Column(DateTime(timezone=True), nullable=False)
    daynight = Column(String(1))
    version = Column(String(20))
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=True)
    raw_data = Column(JSONB)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="observations")

    __table_args__ = (
        Index("idx_thermal_obs_location", "location", postgresql_using="gist"),
        Index("idx_thermal_obs_observed_at", "observed_at"),
    )


# ──────────────────────────────────────────────────────────────
# 3. weather_observations — Open-Meteo weather + AQI
# ──────────────────────────────────────────────────────────────
class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location = Column(Geometry("POINT", srid=4326, spatial_index=False), nullable=False)
    observed_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(50), default="open-meteo")
    temperature_c = Column(Double)
    humidity_pct = Column(Double)
    wind_speed_ms = Column(Double)
    wind_direction_deg = Column(Double)
    precipitation_mm = Column(Double)
    pressure_hpa = Column(Double)
    aqi = Column(SmallInteger)
    pm25 = Column(Double)
    pm10 = Column(Double)
    raw_data = Column(JSONB)
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_weather_obs_location", "location", postgresql_using="gist"),
        Index("idx_weather_obs_observed_at", "observed_at"),
    )


# ──────────────────────────────────────────────────────────────
# 4. osm_features — OpenStreetMap context
# ──────────────────────────────────────────────────────────────
class OSMFeature(Base):
    __tablename__ = "osm_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    osm_id = Column(BigInteger, nullable=False)
    osm_type = Column(String(20), nullable=False)
    feature_type = Column(String(100))
    name = Column(String(500))
    geometry = Column(Geometry("GEOMETRY", srid=4326, spatial_index=False), nullable=False)
    tags = Column(JSONB)
    fetched_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("osm_type", "osm_id", name="uq_osm_type_id"),
        Index("idx_osm_features_geometry", "geometry", postgresql_using="gist"),
    )


# ──────────────────────────────────────────────────────────────
# 5. facility_thermal_baselines — Normal thermal signatures
# ──────────────────────────────────────────────────────────────
class FacilityThermalBaseline(Base):
    __tablename__ = "facility_thermal_baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=False)
    day_of_week = Column(SmallInteger)
    hour_of_day = Column(SmallInteger)
    season = Column(String(20))
    mean_brightness = Column(Double)
    stddev_brightness = Column(Double)
    mean_frp = Column(Double)
    stddev_frp = Column(Double)
    sample_count = Column(Integer, default=0)
    computed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="baselines")

    __table_args__ = (
        Index(
            "idx_baselines_lookup",
            "facility_id",
            "day_of_week",
            "hour_of_day",
            "season",
        ),
    )


# ──────────────────────────────────────────────────────────────
# 6. thermal_events — Correlated anomaly groups
# ──────────────────────────────────────────────────────────────
class ThermalEvent(Base):
    __tablename__ = "thermal_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facilities.id"), nullable=True)
    status = Column(String(30), nullable=False, default="detected")
    severity = Column(String(20), nullable=False, default="low")
    location = Column(Geometry("POINT", srid=4326, spatial_index=False))
    bbox = Column(Geometry("POLYGON", srid=4326, spatial_index=False))
    first_observed_at = Column(DateTime(timezone=True), nullable=False)
    last_observed_at = Column(DateTime(timezone=True), nullable=False)
    observation_count = Column(Integer, default=0)
    is_persistent = Column(Boolean, default=False)
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    facility = relationship("Facility", back_populates="events")
    observations = relationship("ThermalObservation", back_populates="event")
    evidence = relationship("EventEvidence", back_populates="event")
    risk_assessments = relationship("RiskAssessment", back_populates="event")
    cause_assessments = relationship("CauseAssessment", back_populates="event")
    alerts = relationship("Alert", back_populates="event")
    public_reports = relationship("PublicReport", back_populates="event")
    timeline = relationship("IncidentTimeline", back_populates="event")

    __table_args__ = (
        Index("idx_thermal_events_location", "location", postgresql_using="gist"),
        Index("idx_thermal_events_bbox", "bbox", postgresql_using="gist"),
        Index("idx_thermal_events_status", "status"),
    )


# ──────────────────────────────────────────────────────────────
# 7. event_evidence — Supporting data per event
# ──────────────────────────────────────────────────────────────
class EventEvidence(Base):
    __tablename__ = "event_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=False)
    evidence_type = Column(String(50), nullable=False)
    source = Column(String(100))
    summary = Column(Text)
    data = Column(JSONB)
    captured_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="evidence")

    __table_args__ = (Index("idx_event_evidence_event_id", "event_id"),)


# ──────────────────────────────────────────────────────────────
# 8. risk_assessments — Deterministic risk scoring
# ──────────────────────────────────────────────────────────────
class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=False)
    risk_level = Column(String(20), nullable=False)
    risk_score = Column(Double)
    factors = Column(JSONB)
    assessed_by = Column(String(50), default="system")
    notes = Column(Text)
    assessed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="risk_assessments")
    alerts = relationship("Alert", back_populates="risk_assessment")

    __table_args__ = (Index("idx_risk_assessments_event_id", "event_id"),)


# ──────────────────────────────────────────────────────────────
# 9. cause_assessments — Probable-cause analysis
#
# RULE: Cause is ALWAYS "probable cause with confidence", NEVER
#       stated as confirmed. confidence_pct is capped at 99.
# ──────────────────────────────────────────────────────────────
class CauseAssessment(Base):
    __tablename__ = "cause_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=False)
    probable_cause = Column(String(200), nullable=False)
    confidence_pct = Column(SmallInteger, nullable=False)
    reasoning = Column(Text)
    contributing_factors = Column(JSONB)
    assessed_by = Column(String(50), default="system")
    assessed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="cause_assessments")

    __table_args__ = (
        CheckConstraint(
            "confidence_pct >= 0 AND confidence_pct <= 99",
            name="ck_cause_confidence_never_confirmed",
        ),
        Index("idx_cause_assessments_event_id", "event_id"),
    )


# ──────────────────────────────────────────────────────────────
# 10. alerts — Rule-based alert decisions (NEVER LLM-driven)
# ──────────────────────────────────────────────────────────────
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=False)
    risk_assessment_id = Column(
        UUID(as_uuid=True), ForeignKey("risk_assessments.id"), nullable=True
    )
    alert_level = Column(String(30), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text)
    channel = Column(String(30), nullable=False, default="console")
    status = Column(String(30), nullable=False, default="pending")
    sent_at = Column(DateTime(timezone=True))
    metadata_ = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="alerts")
    risk_assessment = relationship("RiskAssessment", back_populates="alerts")
    recipients = relationship("AlertRecipient", back_populates="alert")

    __table_args__ = (
        Index("idx_alerts_event_id", "event_id"),
        Index("idx_alerts_status", "status"),
    )


# ──────────────────────────────────────────────────────────────
# 11. alert_recipients — Delivery tracking
# ──────────────────────────────────────────────────────────────
class AlertRecipient(Base):
    __tablename__ = "alert_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id"), nullable=False)
    recipient_type = Column(String(30), nullable=False)
    recipient_address = Column(String(255), nullable=False)
    status = Column(String(30), default="pending")
    sent_at = Column(DateTime(timezone=True))
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    alert = relationship("Alert", back_populates="recipients")

    __table_args__ = (Index("idx_alert_recipients_alert_id", "alert_id"),)


# ──────────────────────────────────────────────────────────────
# 12. public_reports — Published incident reports
# ──────────────────────────────────────────────────────────────
class PublicReport(Base):
    __tablename__ = "public_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    full_report = Column(Text)
    locale = Column(String(20), default="en")
    generated_by = Column(String(50), default="system")
    is_published = Column(Boolean, default=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="public_reports")

    __table_args__ = (Index("idx_public_reports_event_id", "event_id"),)


# ──────────────────────────────────────────────────────────────
# 13. incident_timeline — Event chronology
# ──────────────────────────────────────────────────────────────
class IncidentTimeline(Base):
    __tablename__ = "incident_timeline"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(UUID(as_uuid=True), ForeignKey("thermal_events.id"), nullable=False)
    entry_type = Column(String(50), nullable=False)
    title = Column(String(500))
    description = Column(Text)
    metadata_ = Column("metadata", JSONB)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("ThermalEvent", back_populates="timeline")

    __table_args__ = (Index("idx_incident_timeline_event_occurred", "event_id", "occurred_at"),)


# ──────────────────────────────────────────────────────────────
# 14. audit_logs — System audit trail
# ──────────────────────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String(200), nullable=False)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(UUID(as_uuid=True))
    details = Column(JSONB)
    ip_address = Column(String(45))
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
        Index("idx_audit_logs_occurred_at", "occurred_at"),
    )


# ──────────────────────────────────────────────────────────────
# 15. model_versions — ML / analysis model tracking
# ──────────────────────────────────────────────────────────────
class ModelVersion(Base):
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(200), nullable=False)
    version = Column(String(50), nullable=False)
    description = Column(Text)
    parameters = Column(JSONB)
    metrics = Column(JSONB)
    is_active = Column(Boolean, default=False)
    activated_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("model_name", "version", name="uq_model_name_version"),)
