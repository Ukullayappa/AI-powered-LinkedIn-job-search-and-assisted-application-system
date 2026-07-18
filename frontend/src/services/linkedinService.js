import {
  apiRequest,
} from "./apiClient";


export async function loginLinkedIn(
  credentials
) {
  if (!credentials?.email?.trim()) {
    throw new Error(
      "Enter your LinkedIn email."
    );
  }

  if (!credentials?.password) {
    throw new Error(
      "Enter your LinkedIn password."
    );
  }

  return apiRequest(
    "/api/linkedin/login",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        email: credentials.email.trim(),
        password: credentials.password,
      }),
    }
  );
}
