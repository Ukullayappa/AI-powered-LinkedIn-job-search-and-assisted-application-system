import {
  apiRequest,
} from "./apiClient";


export async function getApplicationHistory() {
  return apiRequest(
    "/api/applications/history"
  );
}


export async function markApplicationSubmitted(
  jobId
) {
  if (!jobId) {
    throw new Error(
      "Job ID is required."
    );
  }

  return apiRequest(
    "/api/applications/mark-submitted",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        job_id: jobId,
      }),
    }
  );
}


export async function getNextPendingJob() {
  return apiRequest(
    "/api/applications/next-job"
  );
}