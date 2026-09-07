import { useEffect, useState } from "react";

import {
    getSimulatorMetrics,
    getSimulatorLogs,
    triggerDatabaseFailure,
    triggerRedisFailure,
    triggerVerificationFailure,
    resetSimulator,
} from "./services/api";


function Simulator({
    onInvestigate,
}) {
    const [metrics, setMetrics] = useState(null);
    const [logs, setLogs] = useState([]);

    const [loading, setLoading] = useState(true);
    const [triggering, setTriggering] = useState(false);
    const [error, setError] = useState(null);
    const [successMessage, setSuccessMessage] =
        useState(null);

    const [createdIncident, setCreatedIncident] =
        useState(null);


    /*
     * Load simulator data
     */
    async function loadSimulatorData() {
        try {
            setError(null);

            const [metricsData, logsData] =
                await Promise.all([
                    getSimulatorMetrics(),
                    getSimulatorLogs(),
                ]);

            setMetrics(metricsData);
            setLogs(logsData.logs);
        } catch (err) {
            console.error(err);

            setError(
                "Unable to load simulator data."
            );
        }
    }


    /*
     * Initial load
     */
    useEffect(() => {
        async function initialize() {
            setLoading(true);

            await loadSimulatorData();

            setLoading(false);
        }

        initialize();
    }, []);


    /*
     * Database failure
     */
    async function handleDatabaseFailure() {
        try {
            setTriggering(true);
            setError(null);
            setSuccessMessage(null);

            const result =
                await triggerDatabaseFailure();

            console.log(
                "Database failure triggered:",
                result
            );

            setCreatedIncident(
                result.incident
            );

            setSuccessMessage(
                "Database connection pool failure triggered successfully."
            );

            await loadSimulatorData();

        } catch (err) {
            console.error(err);

            setError(
                "Unable to trigger database failure."
            );
        } finally {
            setTriggering(false);
        }
    }


    /*
     * Redis failure
     */
    async function handleRedisFailure() {
        try {
            setTriggering(true);
            setError(null);
            setSuccessMessage(null);

            const result =
                await triggerRedisFailure();

            console.log(
                "Redis failure triggered:",
                result
            );

            setCreatedIncident(
                result.incident
            );

            setSuccessMessage(
                "Redis service failure triggered successfully."
            );

            await loadSimulatorData();

        } catch (err) {
            console.error(err);

            setError(
                "Unable to trigger Redis failure."
            );
        } finally {
            setTriggering(false);
        }
    }


    /*
     * Verification failure
     */
    async function handleVerificationFailure() {
        try {
            setTriggering(true);
            setError(null);
            setSuccessMessage(null);

            await triggerVerificationFailure();

            setSuccessMessage(
                "Controlled verification failure injected successfully."
            );

            await loadSimulatorData();

        } catch (err) {
            console.error(err);

            setError(
                "Unable to inject verification failure."
            );
        } finally {
            setTriggering(false);
        }
    }


    /*
     * Reset simulator
     */
    async function handleReset() {
        try {
            setTriggering(true);
            setError(null);
            setSuccessMessage(null);
            setCreatedIncident(null);

            await resetSimulator();

            setSuccessMessage(
                "Simulation environment reset successfully."
            );

            await loadSimulatorData();

        } catch (err) {
            console.error(err);

            setError(
                "Unable to reset simulation environment."
            );
        } finally {
            setTriggering(false);
        }
    }


    /*
     * Investigate created incident
     */
    function handleInvestigate() {
        if (!createdIncident) {
            return;
        }

        onInvestigate(
            createdIncident.id
        );
    }


    /*
     * Loading state
     */
    if (loading) {
        return (
            <main className="main-content">

                <header className="topbar">

                    <div>
                        <p className="eyebrow">
                            SIMULATOR
                        </p>

                        <h2>
                            Production Simulator
                        </h2>
                    </div>

                    <div className="topbar-status">
                        <span className="status-dot" />
                        Simulation Environment
                    </div>

                </header>


                <section className="dashboard-content">

                    <div className="details-card">

                        <p>
                            Loading simulator data...
                        </p>

                    </div>

                </section>

            </main>
        );
    }


    /*
     * Fatal loading error
     */
    if (error && !metrics) {
        return (
            <main className="main-content">

                <header className="topbar">

                    <div>
                        <p className="eyebrow">
                            SIMULATOR
                        </p>

                        <h2>
                            Production Simulator
                        </h2>
                    </div>

                    <div className="topbar-status">
                        <span className="status-dot" />
                        Simulation Environment
                    </div>

                </header>


                <section className="dashboard-content">

                    <div className="details-card">

                        <h4>
                            Unable to load simulator
                        </h4>

                        <p>
                            {error}
                        </p>

                    </div>

                </section>

            </main>
        );
    }


    const connectionUsage =
        `${metrics.db_connections_used} / ${metrics.db_connections_max}`;


    const databaseStatus =
        metrics.database_healthy
            ? "Healthy"
            : "Unhealthy";


    const redisStatus =
        metrics.redis_healthy
            ? "Healthy"
            : "Unhealthy";


    const paymentGatewayStatus =
        metrics.payment_gateway_healthy
            ? "Healthy"
            : "Unhealthy";


    return (
        <main className="main-content">

            <header className="topbar">

                <div>
                    <p className="eyebrow">
                        SIMULATOR
                    </p>

                    <h2>
                        Production Simulator
                    </h2>
                </div>


                <div className="topbar-status">

                    <span className="status-dot" />

                    Simulation Environment

                </div>

            </header>


            <section className="dashboard-content">

                <div className="section-heading">

                    <div>

                        <h3>
                            Production Environment
                        </h3>

                        <p>
                            Simulate production conditions and
                            trigger controlled failure scenarios.
                        </p>

                    </div>

                </div>


                {/* Messages */}

                {successMessage && (
                    <div className="simulator-success">
                        {successMessage}
                    </div>
                )}


                {error && (
                    <div className="simulator-error">
                        {error}
                    </div>
                )}


                {/* Environment + Failure Scenarios */}

                <div className="details-grid simulator-grid">

                    {/* System Status */}

                    <div className="details-card">

                        <div className="card-heading">
                            System Status
                        </div>


                        <div className="simulator-status-list">

                            <div className="simulator-status-row">

                                <span>
                                    Database
                                </span>

                                <span className="health-status">

                                    <span
                                        className={
                                            metrics.database_healthy
                                                ? "status-dot"
                                                : "status-dot status-dot-error"
                                        }
                                    />

                                    {databaseStatus}

                                </span>

                            </div>


                            <div className="simulator-status-row">

                                <span>
                                    Redis
                                </span>

                                <span className="health-status">

                                    <span
                                        className={
                                            metrics.redis_healthy
                                                ? "status-dot"
                                                : "status-dot status-dot-error"
                                        }
                                    />

                                    {redisStatus}

                                </span>

                            </div>


                            <div className="simulator-status-row">

                                <span>
                                    Payment Gateway
                                </span>

                                <span className="health-status">

                                    <span
                                        className={
                                            metrics.payment_gateway_healthy
                                                ? "status-dot"
                                                : "status-dot status-dot-error"
                                        }
                                    />

                                    {paymentGatewayStatus}

                                </span>

                            </div>

                        </div>

                    </div>


                    {/* Failure Scenarios */}

                    <div className="details-card">

                        <div className="card-heading">
                            Failure Scenarios
                        </div>


                        <div className="failure-scenario">

                            <h4>
                                Database Connection Pool Exhaustion
                            </h4>

                            <p>
                                Simulates a production database
                                connection pool failure that causes
                                increased errors and latency.
                            </p>

                            <button
                                className="primary-button"
                                onClick={handleDatabaseFailure}
                                disabled={triggering}
                            >
                                {triggering
                                    ? "Triggering..."
                                    : "Trigger Database Failure"}
                            </button>

                        </div>


                        <div className="failure-scenario">

                            <h4>
                                Redis Service Failure
                            </h4>

                            <p>
                                Simulates Redis becoming unavailable,
                                causing cache failures and increased
                                application latency.
                            </p>

                            <button
                                className="primary-button"
                                onClick={handleRedisFailure}
                                disabled={triggering}
                            >
                                {triggering
                                    ? "Triggering..."
                                    : "Trigger Redis Failure"}
                            </button>

                        </div>


                        <div className="failure-scenario">

                            <h4>
                                Verification Failure
                            </h4>

                            <p>
                                Injects degraded metrics after recovery
                                so the platform can test failed
                                verification handling.
                            </p>

                            <button
                                className="secondary-button"
                                onClick={handleVerificationFailure}
                                disabled={triggering}
                            >
                                {triggering
                                    ? "Injecting..."
                                    : "Inject Verification Failure"}
                            </button>

                        </div>


                        <div className="failure-scenario">

                            <h4>
                                Reset Environment
                            </h4>

                            <p>
                                Restores the simulated production
                                environment to a healthy baseline.
                            </p>

                            <button
                                className="secondary-button"
                                onClick={handleReset}
                                disabled={triggering}
                            >
                                {triggering
                                    ? "Resetting..."
                                    : "Reset Environment"}
                            </button>

                        </div>

                    </div>

                </div>


                {/* Created Incident */}

                {createdIncident && (
                    <div className="details-card incident-created-card">

                        <div className="card-heading">
                            Incident Created
                        </div>


                        <div className="created-incident-header">

                            <div>

                                <span className="incident-id">
                                    {createdIncident.id}
                                </span>

                                <h4>
                                    {createdIncident.title}
                                </h4>

                            </div>


                            <div className="incident-title-row">

                                <span className="severity-badge">
                                    {createdIncident.severity.toUpperCase()}
                                </span>

                                <span className="status-badge">
                                    {createdIncident.status.toUpperCase()}
                                </span>

                            </div>

                        </div>


                        <p>
                            {createdIncident.description}
                        </p>


                        <button
                            className="primary-button"
                            onClick={handleInvestigate}
                        >
                            Investigate Incident
                        </button>

                    </div>
                )}


                {/* Simulation Metrics */}

                <div className="details-card">

                    <div className="card-heading">
                        Simulation Metrics
                    </div>


                    <div className="simulator-metrics">

                        <div className="simulator-metric">

                            <span>
                                Requests / Minute
                            </span>

                            <strong>
                                {metrics.requests_per_minute}
                            </strong>

                        </div>


                        <div className="simulator-metric">

                            <span>
                                Error Rate
                            </span>

                            <strong>
                                {(
                                    metrics.error_rate * 100
                                ).toFixed(0)}
                                %
                            </strong>

                        </div>


                        <div className="simulator-metric">

                            <span>
                                Latency
                            </span>

                            <strong>
                                {metrics.latency_ms} ms
                            </strong>

                        </div>


                        <div className="simulator-metric">

                            <span>
                                DB Connections
                            </span>

                            <strong>
                                {connectionUsage}
                            </strong>

                        </div>

                    </div>

                </div>


                {/* Production Logs */}

                <div className="details-card">

                    <div className="card-heading">
                        Production Logs
                    </div>


                    {logs.length === 0 ? (
                        <p>
                            No production logs recorded.
                        </p>
                    ) : (
                        <div className="simulator-logs">

                            {logs.map((log, index) => (
                                <div
                                    className="simulator-log"
                                    key={`${log}-${index}`}
                                >
                                    {log}
                                </div>
                            ))}

                        </div>
                    )}

                </div>

            </section>

        </main>
    );
}


export default Simulator;