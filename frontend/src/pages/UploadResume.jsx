import PageHeader from "../components/PageHeader.jsx";
import UploadCard from "../components/UploadCard.jsx";
import { useToast } from "../hooks/useToast";

export default function UploadResume() {
  const toast = useToast();

  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader
        title="Upload Resume"
        subtitle="Upload a PDF resume — you can parse it into structured data right after."
      />
      <UploadCard onUploaded={() => toast.success("Resume uploaded successfully.")} />
    </div>
  );
}
