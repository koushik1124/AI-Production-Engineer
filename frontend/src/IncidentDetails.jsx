import { useEffect, useState } from "react";

import {
    getIncident,
    getIncidentTimeline,
    getIncidentPolicy,
    investigateIncident,
    approveIncident,
    verifyIncident,
} from "./services/api";


function IncidentDetails({
    incidentId,
    onBack,
}) {
    const [incident, setIncident] = useState(null);
    const [timeline, setTimeline] = useState([]);
    const [policyDecision, setPolicyDecision] =
        useState(null);

    const [loading, setLoading] = useState(true);

    const [investigating, setInvestigating] =
        useState(false);

    const [approving, setApproving] =
        useState(false);

    const [verifying, setVerifying] =
        useState(false);

    const [error, setError] = useState(null);

    const [investigationMessage, setInvestigationMessage] =
        useState(null);

    const [approvalResult, setApprovalResult] =
        useState(null);

    const [verificationResult, setVerificationResult] =
        useState(null);


    async function loadIncidentDetails() {
        try {
            setError(null);

            const [
                incidentData,
                timelineData,
            ] = await Promise.all([
                getIncident(incidentId),
                getIncidentTimeline(incidentId),
            ]);

            setIncident(incidentData);
            setTimeline(timelineData.events);

            /*
             * Policy is only available once the AI
             * has recommended an action.
             */
            if (incidentData.recommended_action_type) {
                try {
                    const policy =
                        await getIncidentPolicy(
                            incidentId
                        );

                    setPolicyDecision(policy);

                } catch (policyError) {
                    console.error(
                        "Unable to load policy decision:",
                        policyError
                    );

                    setPolicyDecision(null);
                }

            } else {
                setPolicyDecision(null);
            }

        } catch (err) {
            console.error(err);

            setError(
                "Unable to load incident details."
            );
        }
    }


    useEffect(() => {
        async function initialize() {
            setLoading(true);

            await loadIncidentDetails();

            setLoading(false);
        }

        initialize();
    }, [incidentId]);


    async function handleInvestigation() {
        try {
            setInvestigating(true);
            setError(null);
            setInvestigationMessage(null);

            await investigateIncident(
                incidentId
            );

            setInvestigationMessage(
                "AI investigation completed successfully."
            );

            await loadIncidentDetails();

        } catch (err) {
            console.error(err);

            setError(
                "Unable to complete AI investigation."
            );
        } finally {
            setInvestigating(false);
        }
    }


    async function handleApproval() {
        try {
            setApproving(true);
            setError(null);
            setApprovalResult(null);
            setVerificationResult(null);

            const result =
                await approveIncident(
                    incidentId
                );

            setApprovalResult(result);

            await loadIncidentDetails();

        } catch (err) {
            console.error(err);

            setError(
                err.message ||
                "Unable to approve and execute the action."
            );
        } finally {
            setApproving(false);
        }
    }


    async function handleVerification() {
        try {
            setVerifying(true);
            setError(null);

            const result =
                await verifyIncident(
                    incidentId
                );

            setVerificationResult(
                result.verification
            );

            await loadIncidentDetails();

        } catch (err) {
            console.error(err);

            setError(
                err.message ||
                "Unable to verify incident recovery."
            );
        } finally {
            setVerifying(false);
        }
    }


    if (loading) {
        return (
            <main className="main-content">

                <div className="details-loading">
                    Loading incident details...
                </div>

            </main>
        );
    }


    if (error && !incident) {
        return (
            <main className="main-content">

                <div className="details-error">

                    <h3>
                        Unable to load incident
                    </h3>

                    <p>
                        {error}
                    </p>

                    <button
                        className="secondary-button"
                        onClick={onBack}
                    >
                        Back to Dashboard
                    </button>

                </div>

            </main>
        );
    }


    if (!incident) {
        return null;
    }


    const confidence =
        incident.investigation_confidence !== null &&
            incident.investigation_confidence !== undefined
            ? Math.round(
                incident.investigation_confidence * 100
            )
            : null;


    const canInvestigate =
        incident.status === "detected";


    const waitingForApproval =
        incident.status === "waiting_approval";


    const executing =
        incident.status === "executing";


    const verifyingRecovery =
        incident.status === "verifying";


    const resolved =
        incident.status === "resolved";


    /*
     * The approval button is only available when
     * the backend policy says:
     *
     * allowed = true
     * requires_approval = true
     */
    const canApprove =
        waitingForApproval &&
        policyDecision?.allowed === true &&
        policyDecision?.requires_approval === true;


    const policyBlocked =
        waitingForApproval &&
        policyDecision &&
        policyDecision.allowed === false;


    return (
        <main className="main-content">

            <header className="topbar">

                <div>

                    <button
                        className="back-button"
                        onClick={onBack}
                    >
                        ← Back to Dashboard
                    </button>

                    <p className="eyebrow">
                        INCIDENT DETAILS
                    </p>

                    <h2>
                        {incident.title}
                    </h2>

                </div>


                <div className="topbar-status">

                    <span className="status-dot" />

                    API Connected

                </div>

            </header>


            <section className="dashboard-content">

                <div className="details-header">

                    <div className="incident-title-row">

                        <span className="incident-id">
                            {incident.id}
                        </span>


                        <span className="severity-badge">
                            {incident.severity.toUpperCase()}
                        </span>


                        <span className="status-badge">
                            {incident.status.toUpperCase()}
                        </span>

                    </div>


                    <p className="details-description">
                        {incident.description}
                    </p>


                    <div className="details-meta">

                        <span>
                            Service:{" "}
                            <strong>
                                {incident.service}
                            </strong>
                        </span>


                        <span>
                            Created:{" "}
                            <strong>
                                {new Date(
                                    incident.created_at
                                ).toLocaleString()}
                            </strong>
                        </span>

                    </div>

                </div>


                {canInvestigate && (
                    <div className="details-card investigation-card">

                        <div>

                            <div className="card-heading">
                                AI Investigation
                            </div>

                            <h4>
                                Investigate this production incident
                            </h4>

                            <p>
                                The AI Production Engineer will
                                analyze the captured metrics, logs,
                                and events to determine the most
                                likely root cause and recommend the
                                safest next action.
                            </p>

                        </div>


                        <button
                            className="primary-button"
                            onClick={handleInvestigation}
                            disabled={investigating}
                        >
                            {investigating
                                ? "AI Investigating..."
                                : "Run AI Investigation"}
                        </button>

                    </div>
                )}


                {investigationMessage && (
                    <div className="simulator-success">
                        {investigationMessage}
                    </div>
                )}


                {error && (
                    <div className="simulator-error">
                        {error}
                    </div>
                )}


                {waitingForApproval && (
                    <div className="details-card approval-card">

                        <div className="card-heading">
                            Policy & Human Approval
                        </div>


                        <div className="approval-header">

                            <div>

                                <h4>
                                    Review Recommended Action
                                </h4>

                                <p>
                                    The AI investigation is complete.
                                    The Policy Engine determines whether
                                    the recommended remediation can be
                                    executed and whether human approval
                                    is required.
                                </p>

                            </div>


                            {policyDecision && (
                                <span className="approval-risk-badge">
                                    {policyDecision.risk_level.toUpperCase()}
                                    {" "}
                                    RISK
                                </span>
                            )}

                        </div>


                        {!policyDecision && (
                            <div className="approval-recommendation">

                                <span>
                                    Policy Decision
                                </span>

                                <p>
                                    Loading Policy Engine decision...
                                </p>

                            </div>
                        )}


                        {policyDecision && (
                            <>

                                <div className="approval-details">

                                    <div className="approval-detail">

                                        <span>
                                            Action
                                        </span>

                                        <strong>
                                            {policyDecision.action}
                                        </strong>

                                    </div>


                                    <div className="approval-detail">

                                        <span>
                                            Risk Level
                                        </span>

                                        <strong>
                                            {policyDecision.risk_level.toUpperCase()}
                                        </strong>

                                    </div>


                                    <div className="approval-detail">

                                        <span>
                                            Allowed
                                        </span>

                                        <strong>
                                            {policyDecision.allowed
                                                ? "YES"
                                                : "NO"}
                                        </strong>

                                    </div>


                                    <div className="approval-detail">

                                        <span>
                                            Human Approval
                                        </span>

                                        <strong>
                                            {policyDecision.requires_approval
                                                ? "REQUIRED"
                                                : "NOT REQUIRED"}
                                        </strong>

                                    </div>

                                </div>


                                <div className="approval-recommendation">

                                    <span>
                                        Policy Decision
                                    </span>

                                    <p>
                                        {policyDecision.reason}
                                    </p>

                                </div>


                                {canApprove && (
                                    <button
                                        className="primary-button approval-button"
                                        onClick={handleApproval}
                                        disabled={approving}
                                    >
                                        {approving
                                            ? "Executing Approved Action..."
                                            : "Approve & Execute"}
                                    </button>
                                )}


                                {policyBlocked && (
                                    <div className="simulator-error">

                                        <strong>
                                            Action Blocked
                                        </strong>

                                        <p>
                                            The Policy Engine has blocked
                                            this action. Autonomous execution
                                            is not permitted.
                                        </p>

                                    </div>
                                )}

                            </>
                        )}

                    </div>
                )}


                {approvalResult && (
                    <div className="details-card execution-result-card">

                        <div className="card-heading">
                            Remediation Result
                        </div>


                        <div className="execution-result">

                            <div className="execution-success">

                                <span className="result-dot" />

                                <strong>
                                    Action executed successfully
                                </strong>

                            </div>


                            {approvalResult.action_result && (
                                <p>
                                    {approvalResult.action_result.message}
                                </p>
                            )}

                        </div>


                        {approvalResult.policy_decision && (
                            <div className="verification-result">

                                <div className="verification-heading">

                                    <span>
                                        Policy Decision
                                    </span>

                                    <strong>
                                        {approvalResult.policy_decision.allowed
                                            ? "ALLOWED"
                                            : "BLOCKED"}
                                    </strong>

                                </div>

                                <p>
                                    {approvalResult.policy_decision.reason}
                                </p>

                            </div>
                        )}

                    </div>
                )}


                {verifyingRecovery && (
                    <div className="details-card verification-card">

                        <div className="card-heading">
                            Recovery Verification
                        </div>

                        <h4>
                            Verify Production Recovery
                        </h4>

                        <p>
                            The remediation action was executed successfully.
                            The system must now verify that production has
                            actually recovered before the incident can be
                            marked as resolved.
                        </p>

                        <button
                            className="primary-button"
                            onClick={handleVerification}
                            disabled={verifying}
                        >
                            {verifying
                                ? "Verifying Recovery..."
                                : "Verify Recovery"}
                        </button>

                    </div>
                )}


                {verificationResult && (
                    <div className="details-card verification-result-card">

                        <div className="card-heading">
                            Verification Result
                        </div>

                        <div className="verification-result">

                            <div className="verification-heading">

                                <span>
                                    Recovery Verification
                                </span>

                                <strong>
                                    {verificationResult.verified
                                        ? "PASSED"
                                        : "FAILED"}
                                </strong>

                            </div>


                            {verificationResult.checks?.length > 0 && (
                                <ul className="verification-list">

                                    {verificationResult.checks.map(
                                        (check, index) => (
                                            <li key={index}>
                                                ✓ {check}
                                            </li>
                                        )
                                    )}

                                </ul>
                            )}


                            {verificationResult.failed_checks?.length > 0 && (
                                <ul className="verification-list">

                                    {verificationResult.failed_checks.map(
                                        (check, index) => (
                                            <li key={index}>
                                                ✕ {check}
                                            </li>
                                        )
                                    )}

                                </ul>
                            )}

                        </div>


                        {!verificationResult.verified && (
                            <p>
                                Recovery has not yet been verified.
                                The incident remains in VERIFYING state.
                            </p>
                        )}

                    </div>
                )}


                {executing && (
                    <div className="details-card">

                        <div className="card-heading">
                            Remediation In Progress
                        </div>

                        <p>
                            The approved remediation is currently
                            being executed.
                        </p>

                    </div>
                )}


                <div className="details-grid">

                    <div className="details-card">

                        <div className="card-heading">
                            AI Diagnosis
                        </div>


                        <h4>
                            Root Cause
                        </h4>


                        <p>
                            {incident.investigation_root_cause ||
                                "Investigation not completed."}
                        </p>


                        <div className="confidence-block">

                            <span>
                                AI Confidence
                            </span>


                            <strong>
                                {confidence !== null
                                    ? `${confidence}%`
                                    : "N/A"}
                            </strong>

                        </div>

                    </div>


                    <div className="details-card">

                        <div className="card-heading">
                            Production Impact
                        </div>


                        <p>
                            {incident.investigation_impact ||
                                "Impact information unavailable."}
                        </p>

                    </div>

                </div>


                <div className="details-card">

                    <div className="card-heading">
                        Evidence
                    </div>


                    {incident.investigation_evidence.length >
                        0 ? (
                        <ul className="evidence-list">

                            {incident.investigation_evidence.map(
                                (item, index) => (
                                    <li key={index}>
                                        {item}
                                    </li>
                                )
                            )}

                        </ul>
                    ) : (
                        <p>
                            No investigation evidence available.
                        </p>
                    )}

                </div>


                <div className="details-card action-card">

                    <div className="card-heading">
                        Recommended Action
                    </div>


                    <h4>
                        {incident.recommended_action ||
                            "No remediation action recommended."}
                    </h4>


                    {incident.recommended_action_type && (
                        <div className="action-type">

                            Action type:{" "}

                            <strong>
                                {incident.recommended_action_type}
                            </strong>

                        </div>
                    )}

                </div>


                <div className="details-card">

                    <div className="card-heading">
                        Incident Timeline
                    </div>


                    <div className="timeline">

                        {timeline.length === 0 ? (
                            <p>
                                No timeline events available.
                            </p>
                        ) : (
                            timeline.map((event) => (
                                <div
                                    className="timeline-event"
                                    key={`${event.event_type}-${event.timestamp}`}
                                >

                                    <div className="timeline-dot" />


                                    <div className="timeline-content">

                                        <strong>
                                            {event.event_type.replaceAll(
                                                "_",
                                                " "
                                            )}
                                        </strong>


                                        <p>
                                            {event.message}
                                        </p>


                                        <span>
                                            {new Date(
                                                event.timestamp
                                            ).toLocaleString()}
                                        </span>

                                    </div>

                                </div>
                            ))
                        )}

                    </div>

                </div>


                {resolved && (
                    <div className="resolved-banner">

                        <span className="status-dot" />

                        <div>

                            <strong>
                                Incident Resolved
                            </strong>

                            <span>
                                Production recovery has been
                                successfully verified.
                            </span>

                        </div>

                    </div>
                )}

            </section>

        </main>
    );
}


export default IncidentDetails;