const API_BASE_URL = "http://127.0.0.1:8000";


async function apiRequest(url, options = {}) {
    const response = await fetch(
        `${API_BASE_URL}${url}`,
        options
    );

    if (!response.ok) {
        const errorData = await response.json()
            .catch(() => null);

        throw new Error(
            errorData?.detail?.message ||
            errorData?.detail ||
            `API request failed: ${response.status}`
        );
    }

    return response.json();
}


/*
 * Incidents
 */

export async function getIncidents() {
    return apiRequest("/incidents");
}


export async function getIncident(incidentId) {
    return apiRequest(
        `/incidents/${incidentId}`
    );
}

export async function deleteIncident(incidentId) {
    return apiRequest(
        `/incidents/${incidentId}`,
        {
            method: "DELETE",
        }
    );
}


export async function getIncidentTimeline(
    incidentId
) {
    return apiRequest(
        `/incidents/${incidentId}/timeline`
    );
}


/*
 * Policy
 */

export async function getIncidentPolicy(
    incidentId
) {
    return apiRequest(
        `/incidents/${incidentId}/policy`
    );
}


/*
 * AI Investigation
 */

export async function investigateIncident(
    incidentId
) {
    return apiRequest(
        `/incidents/${incidentId}/investigate`,
        {
            method: "POST",
        }
    );
}


/*
 * Human Approval
 *
 * The backend independently re-checks
 * the Policy Engine before execution.
 */

export async function approveIncident(
    incidentId
) {
    return apiRequest(
        `/incidents/${incidentId}/approve`,
        {
            method: "POST",
        }
    );
}


/*
 * Recovery Verification
 *
 * Verification is a separate backend step
 * after the approved remediation has executed.
 */

export async function verifyIncident(
    incidentId
) {
    return apiRequest(
        `/incidents/${incidentId}/verify`,
        {
            method: "POST",
        }
    );
}


/*
 * Simulator
 */

export async function getSimulatorMetrics() {
    return apiRequest(
        "/simulator/metrics"
    );
}


export async function getSimulatorLogs() {
    return apiRequest(
        "/simulator/logs"
    );
}


export async function triggerDatabaseFailure() {
    return apiRequest(
        "/simulator/failures/database",
        {
            method: "POST",
        }
    );
}


export async function resetSimulator() {
    return apiRequest(
        "/simulator/reset",
        {
            method: "POST",
        }
    );
}

export async function triggerRedisFailure() {
    return apiRequest("/simulator/failures/redis", {
        method: "POST",
    });
}

export async function triggerVerificationFailure() {
    return apiRequest("/simulator/failures/verification", {
        method: "POST",
    });
}