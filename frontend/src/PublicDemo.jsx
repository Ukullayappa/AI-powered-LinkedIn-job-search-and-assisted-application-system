import "./App.css";


const architecture = [
  {
    number: "1",
    title: "React Dashboard",
    description:
      "A responsive dashboard deployed on Vercel.",
  },
  {
    number: "2",
    title: "FastAPI Cloud API",
    description:
      "Run management and AI services deployed on Render.",
  },
  {
    number: "3",
    title: "Supabase",
    description:
      "Stores profiles, jobs, agent runs and application history.",
  },
  {
    number: "4",
    title: "Windows Worker",
    description:
      "Runs Playwright locally for secure LinkedIn browser automation.",
  },
];


const features = [
  "Resume parsing and candidate-profile extraction",
  "Recent LinkedIn Easy Apply job collection",
  "Resume-to-job match scoring",
  "CrewAI and Groq job ranking",
  "Automatic resume upload and form filling",
  "Manual final review and submission",
  "Duplicate-application prevention",
  "Cloud-to-local worker architecture",
];


const technologies = [
  "React.js",
  "Bootstrap",
  "FastAPI",
  "Python",
  "CrewAI",
  "Groq",
  "Playwright",
  "Supabase",
  "PostgreSQL",
  "Vercel",
  "Render",
];


function PublicDemo() {
  return (
    <div className="app-shell">
      <nav className="navbar bg-white border-bottom sticky-top">
        <div className="container">
          <span className="navbar-brand fw-bold text-primary">
            ApplyPilot AI
          </span>

          <span className="badge rounded-pill text-bg-info">
            Public Demo
          </span>
        </div>
      </nav>

      <main className="container py-4 py-lg-5">
        <section className="hero-section p-4 p-lg-5 mb-4">
          <div className="row align-items-center g-4">
            <div className="col-lg-8">
              <span className="badge bg-light text-primary mb-3">
                Agentic AI Project
              </span>

              <h1 className="display-5 fw-bold mb-3">
                AI-powered job search with
                human-controlled submission.
              </h1>

              <p className="lead mb-4 opacity-75">
                ApplyPilot AI analyzes a resume,
                searches recent jobs, ranks the best
                matches and prepares LinkedIn Easy
                Apply applications through a secure
                local browser worker.
              </p>

              <div className="d-flex flex-wrap gap-2">
                <a
                  className="btn btn-light"
                  href="https://github.com/Ukullayappa/AI-powered-LinkedIn-job-search-and-assisted-application-system"
                  target="_blank"
                  rel="noreferrer"
                >
                  View GitHub Repository
                </a>

                <a
                  className="btn btn-outline-light"
                  href="#architecture"
                >
                  View Architecture
                </a>
              </div>
            </div>

            <div className="col-lg-4">
              <div className="hero-stat">
                <span>Submission policy</span>
                <strong>Human in the loop</strong>
              </div>
            </div>
          </div>
        </section>

        <div className="alert alert-info shadow-sm">
          <strong>Public showcase mode:</strong>{" "}
          resume uploads, LinkedIn credentials,
          application history and automation controls
          are disabled. Browser automation runs only
          on the owner&apos;s Windows computer.
        </div>

        <section className="row g-4 mb-4">
          <div className="col-md-4">
            <div className="card dashboard-card h-100">
              <div className="card-body p-4">
                <span className="text-uppercase small fw-bold text-primary">
                  Search
                </span>

                <h2 className="h4 mt-2">
                  Fresh job discovery
                </h2>

                <p className="text-body-secondary mb-0">
                  Collects recent LinkedIn Easy Apply
                  openings based on resume roles,
                  location and posting date.
                </p>
              </div>
            </div>
          </div>

          <div className="col-md-4">
            <div className="card dashboard-card h-100">
              <div className="card-body p-4">
                <span className="text-uppercase small fw-bold text-primary">
                  Rank
                </span>

                <h2 className="h4 mt-2">
                  AI match scoring
                </h2>

                <p className="text-body-secondary mb-0">
                  Compares job descriptions with the
                  candidate profile and selects the
                  strongest eligible matches.
                </p>
              </div>
            </div>
          </div>

          <div className="col-md-4">
            <div className="card dashboard-card h-100">
              <div className="card-body p-4">
                <span className="text-uppercase small fw-bold text-primary">
                  Apply
                </span>

                <h2 className="h4 mt-2">
                  Assisted application
                </h2>

                <p className="text-body-secondary mb-0">
                  Fills known fields automatically,
                  pauses for unknown questions and
                  requires manual final submission.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section
          id="architecture"
          className="card dashboard-card mb-4"
        >
          <div className="card-body p-4 p-lg-5">
            <span className="text-uppercase small fw-bold text-primary">
              System design
            </span>

            <h2 className="h2 mt-2 mb-4">
              Cloud-to-local architecture
            </h2>

            <div className="row g-4">
              {architecture.map((item) => (
                <div
                  className="col-md-6 col-lg-3"
                  key={item.number}
                >
                  <div className="border rounded-3 p-3 h-100">
                    <span className="step-number">
                      {item.number}
                    </span>

                    <h3 className="h5 mt-3">
                      {item.title}
                    </h3>

                    <p className="text-body-secondary mb-0">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="text-center fw-semibold mt-4">
              Vercel → Render → Supabase → Windows
              Playwright Worker
            </div>
          </div>
        </section>

        <div className="row g-4 mb-4">
          <div className="col-lg-6">
            <section className="card dashboard-card h-100">
              <div className="card-body p-4">
                <span className="text-uppercase small fw-bold text-primary">
                  Capabilities
                </span>

                <h2 className="h3 mt-2 mb-3">
                  Key features
                </h2>

                <ul className="mb-0">
                  {features.map((feature) => (
                    <li
                      className="mb-2"
                      key={feature}
                    >
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          </div>

          <div className="col-lg-6">
            <section className="card dashboard-card h-100">
              <div className="card-body p-4">
                <span className="text-uppercase small fw-bold text-primary">
                  Technology
                </span>

                <h2 className="h3 mt-2 mb-3">
                  Project stack
                </h2>

                <div className="d-flex flex-wrap gap-2">
                  {technologies.map((technology) => (
                    <span
                      className="badge rounded-pill text-bg-light border p-2"
                      key={technology}
                    >
                      {technology}
                    </span>
                  ))}
                </div>
              </div>
            </section>
          </div>
        </div>

        <section className="card dashboard-card">
          <div className="card-body p-4 p-lg-5 text-center">
            <span className="badge text-bg-success mb-3">
              Completed MVP
            </span>

            <h2 className="h2">
              Production-style Agentic AI workflow
            </h2>

            <p className="text-body-secondary mx-auto">
              Built with resume intelligence, job
              ranking, browser automation, persistent
              state, cloud deployment and manual
              approval before submission.
            </p>

            <a
              className="btn btn-primary"
              href="https://github.com/Ukullayappa/AI-powered-LinkedIn-job-search-and-assisted-application-system"
              target="_blank"
              rel="noreferrer"
            >
              Explore the Source Code
            </a>
          </div>
        </section>

        <footer className="text-center text-body-secondary py-4">
          ApplyPilot AI — Built by Uravakonda
          Kullayappa
        </footer>
      </main>
    </div>
  );
}


export default PublicDemo;