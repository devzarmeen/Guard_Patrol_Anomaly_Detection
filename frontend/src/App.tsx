import { useEffect, useState } from "react";

import {
  getAnomalies,
  getEvaluation,
  getMetrics,
  getThresholds,
  type Anomaly,
  type EvaluationResponse,
  type Metrics,
} from "./api/anomalies";

import AnomalyMap from "./components/AnomalyMap";

import "./App.css";

type RiskFilter = "All" | "Critical" | "High" | "Medium";

const RECORDS_PER_PAGE = 10;

export default function App() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  const [mapAnomalies, setMapAnomalies] =
    useState<Anomaly[]>([]);

  const [selectedAnomaly, setSelectedAnomaly] =
    useState<Anomaly | null>(null);

  const [metrics, setMetrics] =
    useState<Metrics | null>(null);

  const [evaluation, setEvaluation] =
    useState<EvaluationResponse | null>(null);

  const [thresholds, setThresholds] = useState<Record<
    string,
    unknown
  > | null>(null);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [riskFilter, setRiskFilter] =
    useState<RiskFilter>("All");

  const [currentPage, setCurrentPage] = useState(1);

  const [totalRecords, setTotalRecords] = useState(0);

  const [totalPages, setTotalPages] = useState(0);

  // =========================================================
  // LOAD METRICS
  // =========================================================

  useEffect(() => {
    async function loadMetrics() {
      try {
        const [metricsData, evaluationData, thresholdData] =
          await Promise.all([
            getMetrics(),
            getEvaluation().catch(() => null),
            getThresholds().catch(() => null),
          ]);

        setMetrics(metricsData);
        setEvaluation(evaluationData);
        setThresholds(thresholdData);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load metrics."
        );
      }
    }

    loadMetrics();
  }, []);

  // =========================================================
  // LOAD ALL ANOMALIES FOR MAP
  // =========================================================

  useEffect(() => {
    async function loadMapAnomalies() {
      try {
        const mapData = await getAnomalies(
          1,
          1000,
          "All"
        );

        setMapAnomalies(mapData.data);
      } catch (err) {
        console.error(
          "Failed to load map anomalies:",
          err
        );
      }
    }

    loadMapAnomalies();
  }, []);

  // =========================================================
  // LOAD ANOMALIES FOR TABLE
  // =========================================================

  useEffect(() => {
    async function loadAnomalies() {
      try {
        setLoading(true);
        setError("");

        const anomalyData = await getAnomalies(
          currentPage,
          RECORDS_PER_PAGE,
          riskFilter
        );

        setAnomalies(anomalyData.data);

        setTotalRecords(anomalyData.total);

        setTotalPages(anomalyData.total_pages);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load anomaly data."
        );
      } finally {
        setLoading(false);
      }
    }

    loadAnomalies();
  }, [currentPage, riskFilter]);

  // =========================================================
  // FILTER CHANGE
  // =========================================================

  function handleFilterChange(filter: RiskFilter) {
    setRiskFilter(filter);
    setCurrentPage(1);
  }

  // =========================================================
  // PAGE NAVIGATION
  // =========================================================

  function goToPage(page: number) {
    if (page < 1 || page > totalPages) {
      return;
    }

    setCurrentPage(page);
  }

  // =========================================================
  // LOADING
  // =========================================================

  if (loading && anomalies.length === 0) {
    return (
      <div className="loading-screen">
        <div className="loading-card">
          <div className="spinner"></div>

          <h2>Loading Dashboard</h2>

          <p>Fetching anomaly data...</p>
        </div>
      </div>
    );
  }

  // =========================================================
  // ERROR
  // =========================================================

  if (error && anomalies.length === 0) {
    return (
      <div className="error-screen">
        <div className="error-card">
          <h2>API Connection Error</h2>

          <p>{error}</p>

          <button
            onClick={() =>
              window.location.reload()
            }
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // =========================================================
  // RECORD RANGE
  // =========================================================

  const startRecord =
    totalRecords === 0
      ? 0
      : (currentPage - 1) * RECORDS_PER_PAGE + 1;

  const endRecord = Math.min(
    currentPage * RECORDS_PER_PAGE,
    totalRecords
  );

  // =========================================================
  // DASHBOARD
  // =========================================================

  return (
    <div className="dashboard">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <header className="dashboard-header">

        <div>

          <p className="eyebrow">
            VIGILOX
          </p>

          <h1>
            Guard Patrol Anomaly Dashboard
          </h1>

          <p className="subtitle">
            Monitor suspicious patrol activity
            and anomaly events.
          </p>

        </div>

        <div className="status-badge">

          <span className="status-dot"></span>

          API Connected

        </div>

      </header>

      {/* ================================================= */}
      {/* METRICS */}
      {/* ================================================= */}

      <section className="metrics-grid">

        <div className="metric-card">

          <div className="metric-label">
            Total Anomalies
          </div>

          <div className="metric-value">
            {metrics?.total_anomalies ?? 0}
          </div>

          <div className="metric-description">
            Detected anomaly points
          </div>

        </div>

        <div className="metric-card critical-card">

          <div className="metric-label">
            Critical
          </div>

          <div className="metric-value">
            {metrics?.critical_anomalies ?? 0}
          </div>

          <div className="metric-description">
            Immediate investigation required
          </div>

        </div>

        <div className="metric-card high-card">

          <div className="metric-label">
            High
          </div>

          <div className="metric-value">
            {metrics?.high_anomalies ?? 0}
          </div>

          <div className="metric-description">
            High-risk anomaly points
          </div>

        </div>

        <div className="metric-card medium-card">

          <div className="metric-label">
            Medium
          </div>

          <div className="metric-value">
            {metrics?.medium_anomalies ?? 0}
          </div>

          <div className="metric-description">
            Requires monitoring
          </div>

        </div>

        <div className="metric-card alert-card">

          <div className="metric-label">
            Immediate Alerts
          </div>

          <div className="metric-value">
            {metrics?.immediate_alerts ?? 0}
          </div>

          <div className="metric-description">
            Active alerts
          </div>

        </div>

      </section>

      {evaluation && (
        <section className="evaluation-section">
          <div className="section-title">
            <div>
              <h2>Detection Evaluation</h2>
              <p>
                Precision, Recall, F1, and False Positive Rate
                across Rule-Based, Isolation Forest, and Hybrid.
                Best method: {evaluation.comparison.best_method ?? "n/a"}
              </p>
            </div>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Method</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>F1</th>
                  <th>FPR</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(evaluation.comparison.methods).map(
                  ([name, methodMetrics]) => (
                    <tr key={name}>
                      <td>
                        <strong>{name}</strong>
                      </td>
                      <td>{methodMetrics.precision.toFixed(3)}</td>
                      <td>{methodMetrics.recall.toFixed(3)}</td>
                      <td>{methodMetrics.f1.toFixed(3)}</td>
                      <td>
                        {methodMetrics.false_positive_rate.toFixed(3)}
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {thresholds && (
        <section className="evaluation-section">
          <div className="section-title">
            <div>
              <h2>Detection Thresholds</h2>
              <p>
                Loaded from config/thresholds.yaml. Update via PUT
                /api/config/thresholds without changing detection code.
              </p>
            </div>
          </div>
          <div className="table-container">
            <pre className="threshold-json">
              {JSON.stringify(thresholds, null, 2)}
            </pre>
          </div>
        </section>
      )}

      {/* ================================================= */}
      {/* MAP */}
      {/* ================================================= */}

      <section className="map-section">

        <div className="section-title">

          <div>

            <h2>
              Anomaly Map
            </h2>

            <p>
              Geographic distribution of
              detected anomalies
            </p>

          </div>

        </div>

        <AnomalyMap
          anomalies={mapAnomalies}
          onSelectAnomaly={setSelectedAnomaly}
        />

      </section>

      {/* ================================================= */}
      {/* RECORDS */}
      {/* ================================================= */}

      <section className="records-section">

        <div className="records-header">

          <div>

            <h2>
              Anomaly Records
            </h2>

            <p>
              Showing{" "}
              {startRecord}
              -
              {endRecord}
              {" "}of{" "}
              {totalRecords}
              {" "}records
            </p>

          </div>

          <div className="filters">

            {(
              [
                "All",
                "Critical",
                "High",
                "Medium",
              ] as RiskFilter[]
            ).map((filter) => (

              <button
                key={filter}
                className={`filter-button ${
                  riskFilter === filter
                    ? "active"
                    : ""
                }`}
                onClick={() =>
                  handleFilterChange(filter)
                }
              >
                {filter}
              </button>

            ))}

          </div>

        </div>

        {/* ================================================= */}
        {/* TABLE */}
        {/* ================================================= */}

        <div className="table-container">

          <table>

            <thead>

              <tr>

                <th>ID</th>

                <th>Guard ID</th>

                <th>Risk Level</th>

                <th>Score</th>

                <th>Reason</th>

                <th>Latitude</th>

                <th>Longitude</th>

              </tr>

            </thead>

            <tbody>

              {anomalies.map((anomaly) => (

                <tr
                  key={anomaly.id}
                  onClick={() =>
                    setSelectedAnomaly(anomaly)
                  }
                  className="table-row"
                >

                  <td>
                    #{anomaly.id}
                  </td>

                  <td>
                    <strong>
                      {anomaly.guard_id}
                    </strong>
                  </td>

                  <td>

                    <span
                      className={`risk-badge ${
                        anomaly.final_risk_level.toLowerCase()
                      }`}
                    >
                      {anomaly.final_risk_level}
                    </span>

                  </td>

                  <td>

                    <span className="score">
                      {anomaly.final_hybrid_score.toFixed(
                        2
                      )}
                    </span>

                  </td>

                  <td className="reason-cell">
                    {anomaly.anomaly_reason ||
                      "Unknown"}
                  </td>

                  <td>
                    {anomaly.latitude.toFixed(6)}
                  </td>

                  <td>
                    {anomaly.longitude.toFixed(6)}
                  </td>

                </tr>

              ))}

            </tbody>

          </table>

          {anomalies.length === 0 && (

            <div className="empty-state">

              <h3>
                No anomalies found
              </h3>

              <p>
                There are no records for
                this risk level.
              </p>

            </div>

          )}

        </div>

        {/* ================================================= */}
        {/* PAGINATION */}
        {/* ================================================= */}

        {totalPages > 1 && (

          <div className="pagination">

            <button
              className="page-button"
              disabled={currentPage === 1}
              onClick={() =>
                goToPage(currentPage - 1)
              }
            >
              ← Previous
            </button>

            <div className="page-numbers">

              {Array.from(
                {
                  length: totalPages,
                },
                (_, index) => index + 1
              ).map((page) => (

                <button
                  key={page}
                  className={`page-number ${
                    currentPage === page
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    goToPage(page)
                  }
                >
                  {page}
                </button>

              ))}

            </div>

            <button
              className="page-button"
              disabled={
                currentPage === totalPages
              }
              onClick={() =>
                goToPage(currentPage + 1)
              }
            >
              Next →
            </button>

          </div>

        )}

      </section>

      {/* ================================================= */}
      {/* DETAIL MODAL */}
      {/* ================================================= */}

      {selectedAnomaly && (

        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedAnomaly(null)
          }
        >

          <div
            className="modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="modal-header">

              <div>

                <p className="eyebrow">
                  ANOMALY DETAILS
                </p>

                <h2>
                  Record #{selectedAnomaly.id}
                </h2>

              </div>

              <button
                className="close-button"
                onClick={() =>
                  setSelectedAnomaly(null)
                }
              >
                ×
              </button>

            </div>

            <div className="modal-risk">

              <span
                className={`risk-badge ${
                  selectedAnomaly.final_risk_level.toLowerCase()
                }`}
              >
                {selectedAnomaly.final_risk_level}
              </span>

              <span className="modal-score">
                Score:{" "}
                {selectedAnomaly.final_hybrid_score.toFixed(
                  2
                )}
              </span>

            </div>

            <div className="details-grid">

              <div className="detail-item">

                <span>
                  Guard ID
                </span>

                <strong>
                  {selectedAnomaly.guard_id}
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Timestamp
                </span>

                <strong>
                  {new Date(
                    selectedAnomaly.timestamp
                  ).toLocaleString()}
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Speed
                </span>

                <strong>
                  {selectedAnomaly.speed_kmh.toFixed(
                    2
                  )}{" "}
                  km/h
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Time Gap
                </span>

                <strong>
                  {selectedAnomaly.time_gap_seconds.toFixed(
                    2
                  )}{" "}
                  sec
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Distance Jump
                </span>

                <strong>
                  {selectedAnomaly.distance_from_previous_m.toFixed(
                    2
                  )}{" "}
                  m
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Distance From Road
                </span>

                <strong>
                  {selectedAnomaly.distance_to_road_m.toFixed(
                    2
                  )}{" "}
                  m
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Latitude
                </span>

                <strong>
                  {selectedAnomaly.latitude.toFixed(
                    6
                  )}
                </strong>

              </div>

              <div className="detail-item">

                <span>
                  Longitude
                </span>

                <strong>
                  {selectedAnomaly.longitude.toFixed(
                    6
                  )}
                </strong>

              </div>

            </div>

            <div className="reason-box">

              <span>
                Anomaly Reason
              </span>

              <p>
                {selectedAnomaly.anomaly_reason ||
                  "No reason provided"}
              </p>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}