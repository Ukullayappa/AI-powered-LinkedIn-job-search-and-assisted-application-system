import {
  StrictMode,
  Suspense,
  lazy,
} from "react";

import {
  createRoot,
} from "react-dom/client";

import "./index.css";


const publicDemoMode =
  import.meta.env.VITE_PUBLIC_DEMO_MODE ===
  "true";


const RootApplication = publicDemoMode
  ? lazy(() => import("./PublicDemo.jsx"))
  : lazy(() => import("./App.jsx"));


createRoot(
  document.getElementById("root")
).render(
  <StrictMode>
    <Suspense
      fallback={
        <div className="container py-5 text-center">
          Loading ApplyPilot AI...
        </div>
      }
    >
      <RootApplication />
    </Suspense>
  </StrictMode>
);