import { Route, Routes } from "react-router-dom";

import MainLayout from "./layouts/MainLayout.jsx";
import CandidateRanking from "./pages/CandidateRanking.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import NotFound from "./pages/NotFound.jsx";
import ResumeDetails from "./pages/ResumeDetails.jsx";
import ResumeList from "./pages/ResumeList.jsx";
import SearchPage from "./pages/SearchPage.jsx";
import UploadResume from "./pages/UploadResume.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<UploadResume />} />
        <Route path="/resumes" element={<ResumeList />} />
        <Route path="/resumes/:id" element={<ResumeDetails />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/candidate-ranking" element={<CandidateRanking />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
