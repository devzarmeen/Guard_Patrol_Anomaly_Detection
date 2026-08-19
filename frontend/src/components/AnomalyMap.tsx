import { useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import type { Anomaly } from "../api/anomalies";

interface AnomalyMapProps {
  anomalies: Anomaly[];
  onSelectAnomaly: (anomaly: Anomaly) => void;
}

function getMarkerColor(riskLevel: string) {
  switch (riskLevel) {
    case "Critical":
      return "#ef4444";

    case "High":
      return "#f97316";

    case "Medium":
      return "#eab308";

    default:
      return "#6b7280";
  }
}

function MapCenter({
  anomalies,
}: {
  anomalies: Anomaly[];
}) {
  const map = useMap();

  useEffect(() => {
    if (anomalies.length > 0) {
      const first = anomalies[0];
      map.setView([first.latitude, first.longitude], 14);
    }
  }, [anomalies, map]);

  return null;
}

export default function AnomalyMap({
  anomalies,
  onSelectAnomaly,
}: AnomalyMapProps) {
  const validAnomalies = anomalies.filter(
    (anomaly) =>
      Number.isFinite(anomaly.latitude) &&
      Number.isFinite(anomaly.longitude)
  );

  const defaultCenter: [number, number] = [
    39.995,
    116.305,
  ];

  return (
    <div className="anomaly-map-wrapper">

      <MapContainer
        center={defaultCenter}
        zoom={14}
        scrollWheelZoom={true}
        className="anomaly-leaflet-map"
      >

        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapCenter
          anomalies={validAnomalies}
        />

        {validAnomalies.map((anomaly) => {
          const markerColor = getMarkerColor(
            anomaly.final_risk_level
          );

          return (
            <CircleMarker
              key={anomaly.id}
              center={[
                anomaly.latitude,
                anomaly.longitude,
              ]}
              radius={8}
              pathOptions={{
                color: markerColor,
                fillColor: markerColor,
                fillOpacity: 0.85,
                weight: 2,
              }}
            >

              <Popup>

                <div className="map-popup">

                  <strong>
                    Anomaly #{anomaly.id}
                  </strong>

                  <p>
                    <b>Guard:</b>{" "}
                    {anomaly.guard_id}
                  </p>

                  <p>
                    <b>Risk:</b>{" "}
                    <span
                      style={{
                        color: markerColor,
                        fontWeight: 700,
                      }}
                    >
                      {anomaly.final_risk_level}
                    </span>
                  </p>

                  <p>
                    <b>Score:</b>{" "}
                    {anomaly.final_hybrid_score.toFixed(
                      2
                    )}
                  </p>

                  <p>
                    <b>Reason:</b>{" "}
                    {anomaly.anomaly_reason ||
                      "Unknown"}
                  </p>

                  <p>
                    <b>Speed:</b>{" "}
                    {anomaly.speed_kmh.toFixed(2)} km/h
                  </p>

                  <button
                    type="button"
                    className="map-details-button"
                    onClick={() =>
                      onSelectAnomaly(anomaly)
                    }
                  >
                    View Full Details
                  </button>

                </div>

              </Popup>

            </CircleMarker>
          );
        })}

      </MapContainer>

      <div className="map-legend">

        <div className="legend-item">
          <span className="legend-dot critical"></span>
          Critical
        </div>

        <div className="legend-item">
          <span className="legend-dot high"></span>
          High
        </div>

        <div className="legend-item">
          <span className="legend-dot medium"></span>
          Medium
        </div>

      </div>

    </div>
  );
}