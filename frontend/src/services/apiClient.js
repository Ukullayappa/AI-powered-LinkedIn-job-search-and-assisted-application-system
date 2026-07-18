const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


async function readResponse(response) {
  const responseData =
    await response
      .json()
      .catch(() => null);

  if (!response.ok) {
    const errorMessage =
      responseData?.detail ||
      responseData?.message ||
      `Request failed with status ${response.status}`;

    throw new Error(errorMessage);
  }

  return responseData;
}


export async function apiRequest(
  endpoint,
  options = {}
) {
  try {
    const response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      options
    );

    return await readResponse(response);
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        "Could not connect to the FastAPI backend.",
        {
          cause: error,
        }
      );
    }

    throw error;
  }
}


export {
  API_BASE_URL,
};