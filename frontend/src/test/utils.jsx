import { render } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { ToastProvider } from "../context/ToastContext.jsx";

/**
 * Render a component inside the providers the real app supplies, so tests
 * exercise components exactly as they run in production rather than a
 * stripped-down variant that hides provider-dependent bugs.
 */
export function renderWithProviders(ui, { route = "/", path } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <ToastProvider>
        {path ? (
          <Routes>
            <Route path={path} element={ui} />
          </Routes>
        ) : (
          ui
        )}
      </ToastProvider>
    </MemoryRouter>,
  );
}

/** A realistic `POST /resumes/{id}/classify` payload. */
export const CLASSIFICATION_RESULT = {
  resume_id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  predicted_role: "DATA-ENGINEER",
  confidence: 0.081383,
  top_predictions: [
    { role: "DATA-ENGINEER", confidence: 0.081383 },
    { role: "QA-ENGINEER", confidence: 0.070455 },
    { role: "DEVOPS-ENGINEER", confidence: 0.059354 },
  ],
  classifier_version: "XGBoost (balanced) (tuned) (2026-08-09T17:32:03+00:00)",
};

/** A realistic `GET /resumes/{id}/details` payload. */
export const RESUME_DETAILS = {
  resume: {
    id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    filename: "jane_doe_resume.pdf",
    status: "UPLOADED",
    file_size: 245678,
    content_type: "application/pdf",
    is_parsed: true,
    created_at: "2026-08-05T10:15:30Z",
    updated_at: "2026-08-05T10:15:35Z",
  },
  parsed: {
    personal_info: {
      full_name: "Jane Doe",
      email: "jane.doe@example.com",
      phone: "+1 555-123-4567",
      address: "San Francisco, CA",
      summary: "Backend engineer with 6 years of experience.",
    },
    skills: ["Docker", "FastAPI", "Python"],
    education: [
      {
        institution: "MIT",
        degree: "B.Tech",
        field_of_study: "Computer Science",
        start_date: "2015-08-01",
        end_date: "2019-05-01",
        grade: "8.7 CGPA",
      },
    ],
    experience: [
      {
        company: "Google",
        job_title: "Software Engineer",
        location: "Mountain View, CA",
        start_date: "2020-01-01",
        end_date: null,
        is_current: true,
        description: "Building scalable backend systems.",
      },
    ],
    projects: [
      {
        name: "Resume Parser",
        description: "Extracts structured data from PDF resumes.",
        technologies: "Python, FastAPI",
      },
    ],
    certifications: [
      { name: "AWS Certified Solutions Architect", issuer: "Amazon", date: "2021-06-01" },
    ],
    social_profiles: [{ platform: "LINKEDIN", url: "linkedin.com/in/janedoe" }],
  },
};
