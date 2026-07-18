import {
  useCallback,
  useEffect,
  useState,
} from "react";

import "./App.css";

import {
  checkBackendHealth,
  getAgentStatus,
  getApplicationHistory,
  loginLinkedIn,
  startAgent,
  stopAgent,
  uploadResume,
} from "./services";


const initialSettings = {
  keywords: "",
  location: "Bengaluru, Karnataka, India",
  date_posted_days: 3,
  maximum_jobs_to_collect: 20,
  maximum_applications: 5,
  minimum_match_score: 60,
  review_seconds: 900,
};


const initialAgentStatus = {
  run_id: "",
  status: "idle",
  stage: "idle",
  message: "Agent has not started.",
  jobs_collected: 0,
  best_jobs: 0,
  current_job_number: 0,
  current_job_id: "",
  current_job_title: "",
  submitted_count: 0,
  failed_count: 0,
  maximum_applications: 5,
  stop_requested: false,
};


const stageLabels = {
  idle: "Idle",
  starting: "Starting agent",
  analyzing_resume: "Analyzing resume",
  logging_in: "Loading LinkedIn session",
  searching_jobs: "Searching relevant jobs",
  ranking_jobs: "Ranking matching jobs",
  preparing_application: "Preparing application",
  needs_user_input: "Waiting for your answers",
  ready_for_review: "Waiting for manual submission",
  submission_detected: "Submission detected",
  moving_to_next_job: "Opening next application",
  completed: "Completed",
  failed: "Failed",
  stopped: "Stopped",
};


function getStatusBadgeClass(status) {
  const classes = {
    idle: "text-bg-secondary",
    running: "text-bg-primary",
    paused: "text-bg-warning",
    completed: "text-bg-success",
    failed: "text-bg-danger",
    stopped: "text-bg-dark",
  };

  return (
    classes[status] ||
    "text-bg-secondary"
  );
}


function App() {
  const [resumeFile, setResumeFile] =
    useState(null);

  const [linkedinEmail, setLinkedinEmail] =
    useState("");

  const [
    linkedinPassword,
    setLinkedinPassword,
  ] = useState("");

  const [
    showLinkedinPassword,
    setShowLinkedinPassword,
  ] = useState(false);

  const [
    linkedinLoggedIn,
    setLinkedinLoggedIn,
  ] = useState(false);

  const [settings, setSettings] =
    useState(initialSettings);

  const [agentStatus, setAgentStatus] =
    useState(initialAgentStatus);

  const [applications, setApplications] =
    useState([]);

  const [
    backendConnected,
    setBackendConnected,
  ] = useState(false);

  const [message, setMessage] =
    useState("");

  const [error, setError] =
    useState("");

  const [uploading, setUploading] =
    useState(false);

  const [loggingIn, setLoggingIn] =
    useState(false);

  const [
    startingAgent,
    setStartingAgent,
  ] = useState(false);

  const [
    stoppingAgent,
    setStoppingAgent,
  ] = useState(false);


  const agentIsRunning = [
    "running",
    "paused",
  ].includes(agentStatus.status);


  const manualActionRequired =
    agentStatus.status === "paused" ||
    [
      "preparing_application",
      "needs_user_input",
      "ready_for_review",
    ].includes(agentStatus.stage);


  const refreshAgentStatus = useCallback(
    async () => {
      try {
        const status =
          await getAgentStatus();

        setAgentStatus(status);
        setBackendConnected(true);
      } catch {
        setBackendConnected(false);
      }
    },
    []
  );


  const refreshApplicationHistory =
    useCallback(
      async () => {
        try {
          const history =
            await getApplicationHistory();

          setApplications(
            Array.isArray(history)
              ? history
              : []
          );
        } catch {
          setApplications([]);
        }
      },
      []
    );


  useEffect(() => {
    async function initializeDashboard() {
      try {
        await checkBackendHealth();

        setBackendConnected(true);

        await Promise.all([
          refreshAgentStatus(),
          refreshApplicationHistory(),
        ]);
      } catch {
        setBackendConnected(false);
      }
    }

    initializeDashboard();
  }, [
    refreshAgentStatus,
    refreshApplicationHistory,
  ]);


  useEffect(() => {
    const intervalId =
      window.setInterval(
        async () => {
          await refreshAgentStatus();
          await refreshApplicationHistory();
        },
        10000
      );

    return () => {
      window.clearInterval(
        intervalId
      );
    };
  }, [
    refreshAgentStatus,
    refreshApplicationHistory,
  ]);


  function clearMessages() {
    setMessage("");
    setError("");
  }


  function handleSettingsChange(event) {
    const {
      name,
      value,
      type,
    } = event.target;

    setSettings(
      (currentSettings) => ({
        ...currentSettings,

        [name]:
          type === "number"
            ? Number(value)
            : value,
      })
    );
  }


  async function handleResumeUpload() {
    clearMessages();

    if (!resumeFile) {
      setError(
        "Select a resume file first."
      );

      return;
    }

    try {
      setUploading(true);

      const result = await uploadResume(
        resumeFile
      );

      setMessage(
        result?.message ||
        "Resume uploaded successfully."
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setUploading(false);
    }
  }


  async function handleLinkedInLogin() {
    clearMessages();

    if (!linkedinEmail.trim()) {
      setError(
        "Enter your LinkedIn email."
      );

      return;
    }

    if (!linkedinPassword) {
      setError(
        "Enter your LinkedIn password."
      );

      return;
    }

    try {
      setLoggingIn(true);
      setLinkedinLoggedIn(false);

      const result =
        await loginLinkedIn({
          email: linkedinEmail,
          password: linkedinPassword,
        });

      const loginSuccessful =
        result?.status === "logged_in" &&
        result?.session_saved === true;

      setLinkedinLoggedIn(
        loginSuccessful
      );

      setMessage(
        result?.message ||
        "LinkedIn login completed."
      );

      if (loginSuccessful) {
        setLinkedinPassword("");
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoggingIn(false);
    }
  }


  async function handleStartAgent() {
    clearMessages();

    try {
      setStartingAgent(true);

      const result = await startAgent(
        settings
      );

      setMessage(
        result?.message ||
        "Agent started successfully."
      );

      await refreshAgentStatus();
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setStartingAgent(false);
    }
  }


  async function handleStopAgent() {
    clearMessages();

    try {
      setStoppingAgent(true);

      const result =
        await stopAgent();

      setAgentStatus(result);

      setMessage(
        result?.message ||
        "Stop request sent."
      );
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setStoppingAgent(false);
    }
  }


  function formatDate(dateValue) {
    if (!dateValue) {
      return "-";
    }

    const date = new Date(dateValue);

    if (
      Number.isNaN(
        date.getTime()
      )
    ) {
      return dateValue;
    }

    return date.toLocaleString();
  }


  const maximumApplications =
    agentStatus.maximum_applications ||
    settings.maximum_applications;


  const progressPercentage =
    maximumApplications > 0
      ? Math.min(
          100,
          Math.round(
            (
              agentStatus.submitted_count /
              maximumApplications
            ) * 100
          )
        )
      : 0;


  return (
    <div className="app-shell">
      <nav className="navbar bg-white border-bottom sticky-top">
        <div className="container">
          <span className="navbar-brand fw-bold text-primary">
            ApplyPilot AI
          </span>

          <span
            className={
              backendConnected
                ? "badge rounded-pill text-bg-success"
                : "badge rounded-pill text-bg-danger"
            }
          >
            {backendConnected
              ? "Backend connected"
              : "Backend disconnected"}
          </span>
        </div>
      </nav>


      <main className="container py-4 py-lg-5">
        <section className="hero-section p-4 p-lg-5 mb-4">
          <div className="row align-items-center g-4">
            <div className="col-lg-8">
              <span className="badge bg-light text-primary mb-3">
                Autonomous Job Application Assistant
              </span>

              <h1 className="display-5 fw-bold mb-3">
                Automate your job search.
              </h1>

              <p className="lead mb-0 opacity-75">
                Search, rank and prepare
                LinkedIn Easy Apply applications
                from one dashboard.
              </p>
            </div>

            <div className="col-lg-4">
              <div className="hero-stat">
                <span>
                  Submitted applications
                </span>

                <strong>
                  {agentStatus.submitted_count}
                  {" / "}
                  {maximumApplications}
                </strong>
              </div>
            </div>
          </div>
        </section>


        {message && (
          <div
            className="alert alert-success"
            role="alert"
          >
            {message}
          </div>
        )}


        {error && (
          <div
            className="alert alert-danger"
            role="alert"
          >
            {error}
          </div>
        )}


        {manualActionRequired && (
          <div
            className="alert alert-warning shadow-sm"
            role="alert"
          >
            <h2 className="h5 alert-heading">
              Action required in LinkedIn
            </h2>

            <p className="mb-0">
              Answer unknown questions in the
              visible browser. Review the final
              page and click Submit application
              manually.
            </p>
          </div>
        )}


        <div className="row g-4">
          <div className="col-lg-6">
            <section className="card dashboard-card h-100">
              <div className="card-body p-4">
                <div className="d-flex align-items-start gap-3 mb-4">
                  <span className="step-number">
                    1
                  </span>

                  <div>
                    <h2 className="h4 mb-1">
                      Upload resume
                    </h2>

                    <p className="text-body-secondary mb-0">
                      Upload the resume used for
                      matching and applications.
                    </p>
                  </div>
                </div>

                <label
                  className="form-label fw-semibold"
                  htmlFor="resumeFile"
                >
                  Resume file
                </label>

                <input
                  id="resumeFile"
                  className="form-control mb-3"
                  type="file"
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={(event) => {
                    setResumeFile(
                      event.target
                        .files?.[0] ||
                      null
                    );
                  }}
                />

                <button
                  type="button"
                  className="btn btn-primary w-100"
                  onClick={
                    handleResumeUpload
                  }
                  disabled={
                    !resumeFile ||
                    uploading
                  }
                >
                  {uploading
                    ? "Uploading..."
                    : "Upload resume"}
                </button>
              </div>
            </section>
          </div>


          <div className="col-lg-6">
            <section className="card dashboard-card h-100">
              <div className="card-body p-4">
                <div className="d-flex align-items-start gap-3 mb-4">
                  <span className="step-number">
                    2
                  </span>

                  <div className="flex-grow-1">
                    <div className="d-flex flex-wrap justify-content-between gap-2">
                      <h2 className="h4 mb-1">
                        LinkedIn login
                      </h2>

                      {linkedinLoggedIn && (
                        <span className="badge text-bg-success align-self-start">
                          Session saved
                        </span>
                      )}
                    </div>

                    <p className="text-body-secondary mb-0">
                      New users enter their
                      LinkedIn credentials here.
                    </p>
                  </div>
                </div>

                <div className="mb-3">
                  <label
                    className="form-label fw-semibold"
                    htmlFor="linkedinEmail"
                  >
                    LinkedIn email
                  </label>

                  <input
                    id="linkedinEmail"
                    className="form-control"
                    type="email"
                    value={linkedinEmail}
                    onChange={(event) => {
                      setLinkedinEmail(
                        event.target.value
                      );
                      setLinkedinLoggedIn(
                        false
                      );
                    }}
                    placeholder="name@example.com"
                    autoComplete="username"
                    disabled={loggingIn}
                  />
                </div>

                <div className="mb-3">
                  <label
                    className="form-label fw-semibold"
                    htmlFor="linkedinPassword"
                  >
                    LinkedIn password
                  </label>

                  <div className="input-group">
                    <input
                      id="linkedinPassword"
                      className="form-control"
                      type={
                        showLinkedinPassword
                          ? "text"
                          : "password"
                      }
                      value={linkedinPassword}
                      onChange={(event) => {
                        setLinkedinPassword(
                          event.target.value
                        );
                        setLinkedinLoggedIn(
                          false
                        );
                      }}
                      placeholder="Enter password"
                      autoComplete="current-password"
                      disabled={loggingIn}
                    />

                    <button
                      type="button"
                      className="btn btn-outline-secondary"
                      onClick={() => {
                        setShowLinkedinPassword(
                          (currentValue) =>
                            !currentValue
                        );
                      }}
                      disabled={loggingIn}
                    >
                      {showLinkedinPassword
                        ? "Hide"
                        : "Show"}
                    </button>
                  </div>
                </div>

                <div className="bg-body-tertiary rounded-3 p-3 mb-3">
                  <p className="small text-body-secondary mb-0">
                    Credentials are used only
                    for this local login request.
                    The backend saves the browser
                    session, not the password.
                  </p>
                </div>

                <button
                  type="button"
                  className="btn btn-dark w-100"
                  onClick={
                    handleLinkedInLogin
                  }
                  disabled={
                    loggingIn ||
                    !linkedinEmail.trim() ||
                    !linkedinPassword
                  }
                >
                  {loggingIn
                    ? "Signing in..."
                    : "Login and save session"}
                </button>
              </div>
            </section>
          </div>


          <div className="col-12">
            <section className="card dashboard-card">
              <div className="card-body p-4">
                <div className="d-flex align-items-start gap-3 mb-4">
                  <span className="step-number">
                    3
                  </span>

                  <div>
                    <h2 className="h4 mb-1">
                      Agent settings
                    </h2>

                    <p className="text-body-secondary mb-0">
                      Configure which jobs the
                      agent should collect and
                      prepare.
                    </p>
                  </div>
                </div>

                <div className="row g-3">
                  <div className="col-md-6">
                    <label
                      className="form-label"
                      htmlFor="keywords"
                    >
                      Keywords
                    </label>

                    <input
                      id="keywords"
                      className="form-control"
                      name="keywords"
                      value={settings.keywords}
                      onChange={
                        handleSettingsChange
                      }
                      placeholder="Leave empty to use resume roles"
                    />
                  </div>

                  <div className="col-md-6">
                    <label
                      className="form-label"
                      htmlFor="location"
                    >
                      Location
                    </label>

                    <input
                      id="location"
                      className="form-control"
                      name="location"
                      value={settings.location}
                      onChange={
                        handleSettingsChange
                      }
                    />
                  </div>

                  <div className="col-md-4">
                    <label
                      className="form-label"
                      htmlFor="datePosted"
                    >
                      Date posted days
                    </label>

                    <input
                      id="datePosted"
                      className="form-control"
                      type="number"
                      name="date_posted_days"
                      min="1"
                      max="30"
                      value={
                        settings.date_posted_days
                      }
                      onChange={
                        handleSettingsChange
                      }
                    />
                  </div>

                  <div className="col-md-4">
                    <label
                      className="form-label"
                      htmlFor="jobsToCollect"
                    >
                      Jobs to collect
                    </label>

                    <input
                      id="jobsToCollect"
                      className="form-control"
                      type="number"
                      name={
                        "maximum_jobs_to_collect"
                      }
                      min="5"
                      max="20"
                      value={
                        settings
                          .maximum_jobs_to_collect
                      }
                      onChange={
                        handleSettingsChange
                      }
                    />
                  </div>

                  <div className="col-md-4">
                    <label
                      className="form-label"
                      htmlFor="maximumApplications"
                    >
                      Maximum applications
                    </label>

                    <input
                      id="maximumApplications"
                      className="form-control"
                      type="number"
                      name={
                        "maximum_applications"
                      }
                      min="1"
                      max="5"
                      value={
                        settings
                          .maximum_applications
                      }
                      onChange={
                        handleSettingsChange
                      }
                    />
                  </div>

                  <div className="col-md-6">
                    <label
                      className="form-label"
                      htmlFor="minimumScore"
                    >
                      Minimum match score
                    </label>

                    <input
                      id="minimumScore"
                      className="form-control"
                      type="number"
                      name={
                        "minimum_match_score"
                      }
                      min="0"
                      max="100"
                      value={
                        settings
                          .minimum_match_score
                      }
                      onChange={
                        handleSettingsChange
                      }
                    />
                  </div>

                  <div className="col-md-6">
                    <label
                      className="form-label"
                      htmlFor="reviewSeconds"
                    >
                      Manual waiting seconds
                    </label>

                    <input
                      id="reviewSeconds"
                      className="form-control"
                      type="number"
                      name="review_seconds"
                      min="60"
                      max="1800"
                      value={
                        settings.review_seconds
                      }
                      onChange={
                        handleSettingsChange
                      }
                    />
                  </div>
                </div>

                <div className="d-flex flex-column flex-sm-row gap-2 mt-4">
                  <button
                    type="button"
                    className="btn btn-primary px-4"
                    onClick={
                      handleStartAgent
                    }
                    disabled={
                      startingAgent ||
                      agentIsRunning ||
                      !backendConnected
                    }
                  >
                    {startingAgent
                      ? "Starting..."
                      : "Start agent"}
                  </button>

                  <button
                    type="button"
                    className="btn btn-outline-danger px-4"
                    onClick={
                      handleStopAgent
                    }
                    disabled={
                      stoppingAgent ||
                      !agentIsRunning
                    }
                  >
                    {stoppingAgent
                      ? "Stopping..."
                      : "Stop agent"}
                  </button>
                </div>
              </div>
            </section>
          </div>


          <div className="col-12">
            <section className="card dashboard-card">
              <div className="card-body p-4">
                <div className="d-flex flex-column flex-md-row justify-content-between gap-3 mb-4">
                  <div>
                    <span className="text-uppercase small fw-bold text-primary">
                      Live agent status
                    </span>

                    <h2 className="h3 mt-1 mb-0">
                      {stageLabels[
                        agentStatus.stage
                      ] ||
                        agentStatus.stage}
                    </h2>
                  </div>

                  <span
                    className={
                      `badge rounded-pill fs-6 align-self-md-start ${
                        getStatusBadgeClass(
                          agentStatus.status
                        )
                      }`
                    }
                  >
                    {agentStatus.status}
                  </span>
                </div>

                <p className="text-body-secondary">
                  {agentStatus.message}
                </p>

                <div className="d-flex justify-content-between mb-2">
                  <span className="fw-semibold">
                    Submitted applications
                  </span>

                  <strong>
                    {agentStatus.submitted_count}
                    {" / "}
                    {maximumApplications}
                  </strong>
                </div>

                <div
                  className="progress mb-4"
                  role="progressbar"
                  aria-valuenow={
                    progressPercentage
                  }
                  aria-valuemin="0"
                  aria-valuemax="100"
                >
                  <div
                    className="progress-bar progress-bar-striped progress-bar-animated"
                    style={{
                      width:
                        `${progressPercentage}%`,
                    }}
                  >
                    {progressPercentage}%
                  </div>
                </div>

                <div className="row g-3">
                  {[
                    [
                      "Jobs collected",
                      agentStatus.jobs_collected,
                    ],
                    [
                      "Best matches",
                      agentStatus.best_jobs,
                    ],
                    [
                      "Current job",
                      agentStatus
                        .current_job_number,
                    ],
                    [
                      "Failed/skipped",
                      agentStatus.failed_count,
                    ],
                  ].map(
                    ([label, value]) => (
                      <div
                        className="col-6 col-lg-3"
                        key={label}
                      >
                        <div className="metric-card">
                          <span>
                            {label}
                          </span>

                          <strong>
                            {value}
                          </strong>
                        </div>
                      </div>
                    )
                  )}
                </div>

                <div className="border rounded-3 p-3 mt-4">
                  <span className="small text-body-secondary">
                    Current application
                  </span>

                  <p className="fw-semibold mb-0 mt-1">
                    {agentStatus
                      .current_job_title ||
                      "No active application"}
                  </p>
                </div>
              </div>
            </section>
          </div>


          <div className="col-12">
            <section className="card dashboard-card">
              <div className="card-body p-4">
                <div className="d-flex flex-column flex-sm-row justify-content-between gap-3 mb-4">
                  <div>
                    <span className="text-uppercase small fw-bold text-primary">
                      Application memory
                    </span>

                    <h2 className="h3 mt-1 mb-0">
                      Submitted applications
                    </h2>
                  </div>

                  <button
                    type="button"
                    className="btn btn-outline-primary align-self-sm-start"
                    onClick={
                      refreshApplicationHistory
                    }
                  >
                    Refresh history
                  </button>
                </div>

                {applications.length === 0 ? (
                  <div className="text-center bg-body-tertiary rounded-3 py-5">
                    <p className="text-body-secondary mb-0">
                      No submitted applications
                      have been recorded yet.
                    </p>
                  </div>
                ) : (
                  <div className="table-responsive">
                    <table className="table table-hover align-middle mb-0">
                      <thead className="table-light">
                        <tr>
                          <th>Job</th>
                          <th>Company</th>
                          <th>Status</th>
                          <th>Submitted</th>
                        </tr>
                      </thead>

                      <tbody>
                        {applications.map(
                          (application) => (
                            <tr
                              key={
                                application
                                  .job_id
                              }
                            >
                              <td>
                                <a
                                  className="fw-semibold text-decoration-none"
                                  href={
                                    application.url
                                  }
                                  target="_blank"
                                  rel="noreferrer"
                                >
                                  {
                                    application
                                      .title
                                  }
                                </a>
                              </td>

                              <td>
                                {application
                                  .company ||
                                  "-"}
                              </td>

                              <td>
                                <span className="badge text-bg-success">
                                  {
                                    application
                                      .status
                                  }
                                </span>
                              </td>

                              <td>
                                {formatDate(
                                  application
                                    .submitted_at
                                )}
                              </td>
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
}


export default App;
