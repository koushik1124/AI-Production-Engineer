import { useEffect, useState } from "react";

import "./App.css";

import {
  getIncidents,
  deleteIncident,
} from "./services/api";

import IncidentDetails from "./IncidentDetails";
import Simulator from "./Simulator";


function App() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [selectedIncidentId, setSelectedIncidentId] =
    useState(null);

  const [deletingIncidentId, setDeletingIncidentId] =
    useState(null);


  /*
   * Load incidents
   */
  async function loadIncidents() {
    try {
      setLoading(true);
      setError(null);

      const data = await getIncidents();

      setIncidents(data);
    } catch (err) {
      console.error(err);

      setError(
        "Unable to connect to the API."
      );
    } finally {
      setLoading(false);
    }
  }


  /*
   * Initial load
   */
  useEffect(() => {
    loadIncidents();
  }, []);


  /*
   * Delete incident
   */
  async function handleDeleteIncident(
    incidentId,
    incidentTitle
  ) {
    const confirmed = window.confirm(
      `Delete incident ${incidentId}?\n\n` +
      `${incidentTitle}\n\n` +
      "This action cannot be undone."
    );

    if (!confirmed) {
      return;
    }

    try {
      setDeletingIncidentId(incidentId);
      setError(null);

      await deleteIncident(incidentId);

      setIncidents((currentIncidents) =>
        currentIncidents.filter(
          (incident) =>
            incident.id !== incidentId
        )
      );
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
        "Unable to delete incident."
      );
    } finally {
      setDeletingIncidentId(null);
    }
  }


  /*
   * Dashboard statistics
   */

  const activeIncidents = incidents.filter(
    (incident) =>
      incident.status !== "resolved"
  ).length;


  const criticalIncidents = incidents.filter(
    (incident) =>
      incident.severity === "critical"
  ).length;


  const awaitingApproval = incidents.filter(
    (incident) =>
      incident.status === "waiting_approval"
  ).length;


  const resolvedIncidents = incidents.filter(
    (incident) =>
      incident.status === "resolved"
  ).length;


  /*
   * Simulator page
   */
  if (selectedIncidentId === "SIMULATOR") {
    return (
      <div className="app">

        <aside className="sidebar">

          <div className="brand">

            <div className="brand-mark">
              AI
            </div>

            <div>
              <h1>
                Production Engineer
              </h1>

              <span>
                Incident Response Platform
              </span>
            </div>

          </div>


          <nav className="navigation">

            <button
              className="nav-item"
              onClick={() =>
                setSelectedIncidentId(null)
              }
            >
              <span>▦</span>
              Dashboard
            </button>


            <button
              className="nav-item"
              onClick={() =>
                setSelectedIncidentId(null)
              }
            >
              <span>◉</span>
              Incidents
            </button>


            <button className="nav-item active">
              <span>⚡</span>
              Simulator
            </button>


            <button className="nav-item">
              <span>⚙</span>
              Settings
              <small>Soon</small>
            </button>

          </nav>


          <div className="sidebar-footer">

            <div className="system-status">

              <span className="status-dot" />

              <div>
                <strong>
                  System Operational
                </strong>

                <span>
                  All services responding
                </span>
              </div>

            </div>

          </div>

        </aside>


        <Simulator
          onInvestigate={(incidentId) =>
            setSelectedIncidentId(incidentId)
          }
        />

      </div>
    );
  }


  /*
   * Incident Details page
   */
  if (selectedIncidentId) {
    return (
      <div className="app">

        <aside className="sidebar">

          <div className="brand">

            <div className="brand-mark">
              AI
            </div>

            <div>
              <h1>
                Production Engineer
              </h1>

              <span>
                Incident Response Platform
              </span>
            </div>

          </div>


          <nav className="navigation">

            <button
              className="nav-item"
              onClick={() =>
                setSelectedIncidentId(null)
              }
            >
              <span>▦</span>
              Dashboard
            </button>


            <button className="nav-item active">
              <span>◉</span>
              Incidents
            </button>


            <button
              className="nav-item"
              onClick={() =>
                setSelectedIncidentId("SIMULATOR")
              }
            >
              <span>⚡</span>
              Simulator
            </button>


            <button className="nav-item">
              <span>⚙</span>
              Settings
              <small>Soon</small>
            </button>

          </nav>


          <div className="sidebar-footer">

            <div className="system-status">

              <span className="status-dot" />

              <div>
                <strong>
                  System Operational
                </strong>

                <span>
                  All services responding
                </span>
              </div>

            </div>

          </div>

        </aside>


        <IncidentDetails
          incidentId={selectedIncidentId}
          onBack={() =>
            setSelectedIncidentId(null)
          }
        />

      </div>
    );
  }


  /*
   * Main Dashboard
   */
  return (
    <div className="app">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-mark">
            AI
          </div>

          <div>
            <h1>
              Production Engineer
            </h1>

            <span>
              Incident Response Platform
            </span>
          </div>

        </div>


        <nav className="navigation">

          <button className="nav-item active">
            <span>▦</span>
            Dashboard
          </button>


          <button
            className="nav-item"
            onClick={() =>
              setSelectedIncidentId(null)
            }
          >
            <span>◉</span>
            Incidents
          </button>


          <button
            className="nav-item"
            onClick={() =>
              setSelectedIncidentId("SIMULATOR")
            }
          >
            <span>⚡</span>
            Simulator
          </button>


          <button className="nav-item">
            <span>⚙</span>
            Settings
            <small>Soon</small>
          </button>

        </nav>


        <div className="sidebar-footer">

          <div className="system-status">

            <span className="status-dot" />

            <div>
              <strong>
                System Operational
              </strong>

              <span>
                All services responding
              </span>
            </div>

          </div>

        </div>

      </aside>


      <main className="main-content">

        <header className="topbar">

          <div>

            <p className="eyebrow">
              OPERATIONS CENTER
            </p>

            <h2>
              Production Dashboard
            </h2>

            <p className="topbar-description">
              Monitor, investigate and safely
              resolve production incidents.
            </p>

          </div>


          <div className="topbar-actions">

            <div className="topbar-status">

              <span className="status-dot" />

              API Connected

            </div>


            <button
              className="secondary-button"
              onClick={loadIncidents}
              disabled={loading}
            >
              ↻ Refresh
            </button>

          </div>

        </header>


        <section className="dashboard-content">

          <div className="section-heading">

            <div>

              <h3>
                Production Overview
              </h3>

              <p>
                Current incident and system status.
              </p>

            </div>


            <span className="live-badge">
              ● LIVE
            </span>

          </div>


          {/* Statistics */}

          <div className="stats-grid">

            <div className="stat-card">

              <span className="stat-label">
                Active Incidents
              </span>

              <strong className="stat-value">
                {activeIncidents}
              </strong>

              <span className="stat-description">
                Currently being handled
              </span>

            </div>


            <div className="stat-card">

              <span className="stat-label">
                Critical Incidents
              </span>

              <strong className="stat-value">
                {criticalIncidents}
              </strong>

              <span className="stat-description">
                Requiring immediate attention
              </span>

            </div>


            <div className="stat-card">

              <span className="stat-label">
                Awaiting Approval
              </span>

              <strong className="stat-value">
                {awaitingApproval}
              </strong>

              <span className="stat-description">
                Waiting for human decision
              </span>

            </div>


            <div className="stat-card">

              <span className="stat-label">
                Resolved
              </span>

              <strong className="stat-value">
                {resolvedIncidents}
              </strong>

              <span className="stat-description">
                Successfully recovered
              </span>

            </div>

          </div>


          {/* Recent Incidents */}

          <section className="incidents-section">

            <div className="section-heading">

              <div>

                <h3>
                  Recent Incidents

                  <span className="count-badge">
                    {incidents.length}
                  </span>

                </h3>

                <p>
                  Latest production incidents
                  handled by the platform.
                </p>

              </div>


              <button
                className="secondary-button"
                onClick={loadIncidents}
                disabled={loading}
              >
                Refresh incidents
              </button>

            </div>


            {/* Error */}

            {error && (

              <div className="incident-card error-card">

                <div className="incident-main">

                  <h4>
                    Unable to complete request
                  </h4>

                  <p>
                    {error}
                  </p>

                </div>

              </div>

            )}


            {/* Loading */}

            {loading && (

              <div className="incident-card">

                <div className="incident-main">

                  <h4>
                    Loading incidents...
                  </h4>

                  <p>
                    Fetching incident data
                    from the API.
                  </p>

                </div>

              </div>

            )}


            {/* Empty state */}

            {!loading &&
              !error &&
              incidents.length === 0 && (

                <div className="incident-card">

                  <div className="incident-main">

                    <h4>
                      No incidents found
                    </h4>

                    <p>
                      There are currently no
                      production incidents.
                    </p>

                  </div>

                </div>

              )}


            {/* Incident List */}

            {!loading &&
              !error &&
              incidents.map((incident) => {

                const confidence =
                  incident.investigation_confidence !==
                    null &&
                    incident.investigation_confidence !==
                    undefined
                    ? Math.round(
                      incident.investigation_confidence *
                      100
                    )
                    : null;


                return (

                  <div
                    className="incident-card clickable"
                    key={incident.id}
                    onClick={() =>
                      setSelectedIncidentId(
                        incident.id
                      )
                    }
                  >

                    <div className="incident-main">

                      <div className="incident-title-row">

                        <span className="incident-id">
                          {incident.id}
                        </span>


                        <span
                          className={`severity-badge severity-${incident.severity}`}
                        >
                          {incident.severity.toUpperCase()}
                        </span>


                        <span
                          className={`status-badge status-${incident.status}`}
                        >
                          {incident.status
                            .replaceAll("_", " ")
                            .toUpperCase()}
                        </span>

                      </div>


                      <h4>
                        {incident.title}
                      </h4>


                      <p>
                        {incident.description}
                      </p>

                    </div>


                    <div className="incident-meta">

                      <div className="incident-meta-info">

                        <span>
                          {incident.service}
                        </span>


                        <span>
                          {confidence !== null
                            ? `${confidence}% confidence`
                            : "Not investigated"}
                        </span>

                      </div>


                      {/* Delete */}

                      <button
                        className="delete-incident-button"
                        onClick={(event) => {

                          event.stopPropagation();

                          handleDeleteIncident(
                            incident.id,
                            incident.title
                          );

                        }}
                        disabled={
                          deletingIncidentId ===
                          incident.id
                        }
                        title="Delete incident"
                      >

                        {deletingIncidentId ===
                          incident.id
                          ? "..."
                          : "🗑"}

                      </button>

                    </div>

                  </div>

                );
              })}

          </section>


          {/* Platform capability strip */}

          <section className="capability-strip">

            <div>
              <strong>
                AI Investigation
              </strong>

              <span>
                Evidence-based root cause analysis
              </span>
            </div>


            <div>
              <strong>
                Policy Guardrails
              </strong>

              <span>
                Risk-aware action authorization
              </span>
            </div>


            <div>
              <strong>
                Human Approval
              </strong>

              <span>
                Controlled production execution
              </span>
            </div>


            <div>
              <strong>
                Recovery Verification
              </strong>

              <span>
                Confirm recovery before resolution
              </span>
            </div>

          </section>

        </section>

      </main>

    </div>
  );
}


export default App;