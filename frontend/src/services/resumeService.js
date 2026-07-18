import {
  apiRequest,
} from "./apiClient";


export async function uploadResume(file) {
  if (!file) {
    throw new Error(
      "Select a resume file first."
    );
  }

  const formData = new FormData();

  formData.append(
    "resume",
    file
  );

  return apiRequest(
    "/api/resume/upload",
    {
      method: "POST",
      body: formData,
    }
  );
}


export async function analyzeResume() {
  return apiRequest(
    "/api/resume/analyze",
    {
      method: "POST",
    }
  );
}


export async function getResumeProfile() {
  return apiRequest(
    "/api/resume/profile"
  );
}