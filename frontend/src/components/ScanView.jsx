import { useRef, useState } from "react";
import { FileUp, Loader2, RotateCcw, ScanSearch, X } from "lucide-react";
import apiClient from "../api/client";
import AnalysisResult from "./AnalysisResult";
import { PageHeader } from "./ui";

const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg"];
const MAX_SIZE_MB = 10;

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getUploadError(err) {
  const detail = err.response?.data?.detail;

  if (typeof detail === "string") return detail;
  if (!err.response) return "Cannot reach the server. Make sure the backend is running.";
  return "The document could not be analysed. Please try again.";
}

function ScanView({ analysis, onAnalysis, onChange }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  function chooseFile(candidate) {
    if (!candidate) return;

    const extension = candidate.name.slice(candidate.name.lastIndexOf(".")).toLowerCase();

    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError(`"${extension}" files are not supported. Use PDF, DOCX, TXT, PNG or JPG.`);
      return;
    }

    if (candidate.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`This file is ${formatSize(candidate.size)}. The limit is ${MAX_SIZE_MB} MB.`);
      return;
    }

    setError("");
    setFile(candidate);
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  }

  function reset() {
    setFile(null);
    setError("");
    onAnalysis(null);

    if (inputRef.current) inputRef.current.value = "";
  }

  async function handleAnalyze() {
    if (!file) return;

    setError("");
    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await apiClient.post("/documents/upload", formData);
      onAnalysis({ ...response.data, created_at: new Date().toISOString() });
    } catch (err) {
      setError(getUploadError(err));
    } finally {
      setUploading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Scanner"
        title={analysis ? "Analysis report" : "Scan a document"}
        description={
          analysis
            ? "Review the evidence before you share or approve this document."
            : "Text is extracted from your file and checked for threats, fraud, policy violations and personal data."
        }
        actions={
          analysis && (
            <button type="button" className="button secondary" onClick={reset}>
              <RotateCcw size={16} />
              Scan another
            </button>
          )
        }
      />

      {analysis ? (
        <AnalysisResult key={analysis.document_id} analysis={analysis} onChange={onChange} />
      ) : (
        <section className="card scan-card">
          <label
            className={`drop-zone ${dragging ? "dragging" : ""} ${file ? "has-file" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_EXTENSIONS.join(",")}
              onChange={(event) => chooseFile(event.target.files[0])}
              disabled={uploading}
            />

            <div className="drop-icon">
              <FileUp size={28} />
            </div>
            <strong>{dragging ? "Drop to select" : "Drag a document here, or click to browse"}</strong>
            <span>PDF, DOCX, TXT, PNG or JPG · up to {MAX_SIZE_MB} MB</span>
          </label>

          {file && (
            <div className="selected-file">
              <div className="file-icon">{file.name.split(".").pop().toUpperCase()}</div>
              <div className="selected-file-info">
                <strong title={file.name}>{file.name}</strong>
                <span>{formatSize(file.size)}</span>
              </div>
              {!uploading && (
                <button type="button" className="icon-button" onClick={reset} aria-label="Remove file">
                  <X size={18} />
                </button>
              )}
            </div>
          )}

          {error && <p className="form-error">{error}</p>}

          <button
            type="button"
            className="button primary large"
            onClick={handleAnalyze}
            disabled={!file || uploading}
          >
            {uploading ? (
              <>
                <Loader2 className="spin" size={18} />
                Analysing — scanned images can take a few seconds…
              </>
            ) : (
              <>
                <ScanSearch size={18} />
                Analyse document
              </>
            )}
          </button>
        </section>
      )}
    </>
  );
}

export default ScanView;
