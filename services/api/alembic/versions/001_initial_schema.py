"""Initial schema — 15 tables with PostGIS geometry columns and spatial indexes.

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. facilities ──────────────────────────────────────────
    op.create_table(
        "facilities",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("facility_type", sa.String(length=100), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column(
            "boundary",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_facilities_location", "facilities", ["location"], postgresql_using="gist")
    op.create_index("idx_facilities_boundary", "facilities", ["boundary"], postgresql_using="gist")

    # ── 6. thermal_events (before thermal_observations due to FK) ──
    op.create_table(
        "thermal_events",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("facility_id", sa.UUID(), nullable=True),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'detected'"),
        ),
        sa.Column(
            "severity", sa.String(length=20), nullable=False, server_default=sa.text("'low'")
        ),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column(
            "bbox",
            geoalchemy2.types.Geometry(
                geometry_type="POLYGON",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=True,
        ),
        sa.Column("first_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("observation_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("is_persistent", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_thermal_events_location", "thermal_events", ["location"], postgresql_using="gist"
    )
    op.create_index("idx_thermal_events_bbox", "thermal_events", ["bbox"], postgresql_using="gist")
    op.create_index("idx_thermal_events_status", "thermal_events", ["status"])

    # ── 2. thermal_observations ────────────────────────────────
    op.create_table(
        "thermal_observations",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("satellite", sa.String(length=30), nullable=True),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=False,
        ),
        sa.Column("latitude", sa.Double(), nullable=True),
        sa.Column("longitude", sa.Double(), nullable=True),
        sa.Column("brightness", sa.Double(), nullable=True),
        sa.Column("bright_ti4", sa.Double(), nullable=True),
        sa.Column("bright_ti5", sa.Double(), nullable=True),
        sa.Column("frp", sa.Double(), nullable=True),
        sa.Column("confidence", sa.String(length=20), nullable=True),
        sa.Column("confidence_pct", sa.SmallInteger(), nullable=True),
        sa.Column("acq_date", sa.Date(), nullable=True),
        sa.Column("acq_time", sa.String(length=10), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("daynight", sa.String(length=1), nullable=True),
        sa.Column("version", sa.String(length=20), nullable=True),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_thermal_obs_location",
        "thermal_observations",
        ["location"],
        postgresql_using="gist",
    )
    op.create_index("idx_thermal_obs_observed_at", "thermal_observations", ["observed_at"])

    # ── 3. weather_observations ────────────────────────────────
    op.create_table(
        "weather_observations",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "source",
            sa.String(length=50),
            nullable=True,
            server_default=sa.text("'open-meteo'"),
        ),
        sa.Column("temperature_c", sa.Double(), nullable=True),
        sa.Column("humidity_pct", sa.Double(), nullable=True),
        sa.Column("wind_speed_ms", sa.Double(), nullable=True),
        sa.Column("wind_direction_deg", sa.Double(), nullable=True),
        sa.Column("precipitation_mm", sa.Double(), nullable=True),
        sa.Column("pressure_hpa", sa.Double(), nullable=True),
        sa.Column("aqi", sa.SmallInteger(), nullable=True),
        sa.Column("pm25", sa.Double(), nullable=True),
        sa.Column("pm10", sa.Double(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_weather_obs_location",
        "weather_observations",
        ["location"],
        postgresql_using="gist",
    )
    op.create_index("idx_weather_obs_observed_at", "weather_observations", ["observed_at"])

    # ── 4. osm_features ───────────────────────────────────────
    op.create_table(
        "osm_features",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("osm_id", sa.BigInteger(), nullable=False),
        sa.Column("osm_type", sa.String(length=20), nullable=False),
        sa.Column("feature_type", sa.String(length=100), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=True),
        sa.Column(
            "geometry",
            geoalchemy2.types.Geometry(
                geometry_type="GEOMETRY",
                srid=4326,
                spatial_index=False,
                from_text="ST_GeomFromEWKT",
                name="geometry",
            ),
            nullable=False,
        ),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("osm_type", "osm_id", name="uq_osm_type_id"),
    )
    op.create_index(
        "idx_osm_features_geometry", "osm_features", ["geometry"], postgresql_using="gist"
    )

    # ── 5. facility_thermal_baselines ──────────────────────────
    op.create_table(
        "facility_thermal_baselines",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("facility_id", sa.UUID(), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=True),
        sa.Column("hour_of_day", sa.SmallInteger(), nullable=True),
        sa.Column("season", sa.String(length=20), nullable=True),
        sa.Column("mean_brightness", sa.Double(), nullable=True),
        sa.Column("stddev_brightness", sa.Double(), nullable=True),
        sa.Column("mean_frp", sa.Double(), nullable=True),
        sa.Column("stddev_frp", sa.Double(), nullable=True),
        sa.Column("sample_count", sa.Integer(), nullable=True, server_default=sa.text("0")),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_baselines_lookup",
        "facility_thermal_baselines",
        ["facility_id", "day_of_week", "hour_of_day", "season"],
    )

    # ── 7. event_evidence ──────────────────────────────────────
    op.create_table(
        "event_evidence",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_event_evidence_event_id", "event_evidence", ["event_id"])

    # ── 8. risk_assessments ────────────────────────────────────
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("risk_score", sa.Double(), nullable=True),
        sa.Column("factors", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "assessed_by",
            sa.String(length=50),
            nullable=True,
            server_default=sa.text("'system'"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_risk_assessments_event_id", "risk_assessments", ["event_id"])

    # ── 9. cause_assessments ───────────────────────────────────
    op.create_table(
        "cause_assessments",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("probable_cause", sa.String(length=200), nullable=False),
        sa.Column("confidence_pct", sa.SmallInteger(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column(
            "contributing_factors",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "assessed_by",
            sa.String(length=50),
            nullable=True,
            server_default=sa.text("'system'"),
        ),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.CheckConstraint(
            "confidence_pct >= 0 AND confidence_pct <= 99",
            name="ck_cause_confidence_never_confirmed",
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cause_assessments_event_id", "cause_assessments", ["event_id"])

    # ── 10. alerts ─────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("risk_assessment_id", sa.UUID(), nullable=True),
        sa.Column("alert_level", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "channel",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'console'"),
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alerts_event_id", "alerts", ["event_id"])
    op.create_index("idx_alerts_status", "alerts", ["status"])

    # ── 11. alert_recipients ───────────────────────────────────
    op.create_table(
        "alert_recipients",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("alert_id", sa.UUID(), nullable=False),
        sa.Column("recipient_type", sa.String(length=30), nullable=False),
        sa.Column("recipient_address", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=True,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alert_recipients_alert_id", "alert_recipients", ["alert_id"])

    # ── 12. public_reports ─────────────────────────────────────
    op.create_table(
        "public_reports",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("full_report", sa.Text(), nullable=True),
        sa.Column(
            "locale",
            sa.String(length=20),
            nullable=True,
            server_default=sa.text("'en'"),
        ),
        sa.Column(
            "generated_by",
            sa.String(length=50),
            nullable=True,
            server_default=sa.text("'system'"),
        ),
        sa.Column("is_published", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_public_reports_event_id", "public_reports", ["event_id"])

    # ── 13. incident_timeline ──────────────────────────────────
    op.create_table(
        "incident_timeline",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", sa.UUID(), nullable=False),
        sa.Column("entry_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["thermal_events.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_incident_timeline_event_occurred",
        "incident_timeline",
        ["event_id", "occurred_at"],
    )

    # ── 14. audit_logs ─────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor", sa.String(length=200), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.UUID(), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("idx_audit_logs_occurred_at", "audit_logs", ["occurred_at"])

    # ── 15. model_versions ─────────────────────────────────────
    op.create_table(
        "model_versions",
        sa.Column("id", sa.UUID(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("model_name", sa.String(length=200), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parameters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default=sa.text("false")),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_name", "version", name="uq_model_name_version"),
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table("model_versions")
    op.drop_table("audit_logs")
    op.drop_table("incident_timeline")
    op.drop_table("public_reports")
    op.drop_table("alert_recipients")
    op.drop_table("alerts")
    op.drop_table("cause_assessments")
    op.drop_table("risk_assessments")
    op.drop_table("event_evidence")
    op.drop_table("facility_thermal_baselines")
    op.drop_table("thermal_observations")
    op.drop_table("weather_observations")
    op.drop_table("osm_features")
    op.drop_table("thermal_events")
    op.drop_table("facilities")
