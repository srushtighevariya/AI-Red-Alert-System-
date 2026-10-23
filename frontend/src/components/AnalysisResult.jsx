import { useRef, useState } from "react";
import { Bot, CheckCircle2, FileText, Info, RefreshCw, ShieldAlert } from "lucide-react";
import apiClient from "../api/client";
import { alertTone, buildFindingGroups, describeModelStatus, formatDate } from "../utils/analysis";
import DocumentViewer from "./DocumentViewer";
import FindingsPanel from "./FindingsPanel";
import ScoreBreakdown from "./ScoreBreakdown";
import { AlertBadge, ScoreRing } from "./ui";

const REPORT_TEXT = {
  Red: {
    title: "Red Alert Risk Report",
    overview: "This document contains serious risk indicators.",
    recommendation: "Do not share or approve this document before manual review.",
  },
  Yellow: {
    title: "Yellow Alert Risk Report",
    overview: "This document contains moderate risk indicators.",
    recommendation: "Review the detected evidence before using or sharing this document.",
  },
  Green: {
    title: "Green Alert Risk Report",
    overview: "No major risk indicators were found.",
    recommendation: "The document appears low-risk, but normal verification is still recommended.",
  },
};

/** Findings list for documents scanned before findings had details. */
function LegacyFindings({ analysis }) {
  const groups = buildFindingGroups(analysis);

  return (
    <section className="card">
      <div className="card-header">
        <h3>Why this score</h3>
      </div>

      <p className="inline-note legacy-note">
        <RefreshCw size={16} />
        This document was scanned with an older version. Scan it again to open each finding, see it highlighted in
        the document, and mark findings as not a risk.
      </p>

      {groups.length === 0 ? (
        <div className="all-clear">
          <CheckCircle2 size={20} />
          <p>No risk indicators were found in this document.</p>
        </div>
      ) : (
        <div className="finding-groups">
          {groups.map((group) => (
            <article key={group.key} className={`finding-group ${group.key}`}>
              <header>
                <div>
                  <h4>{group.title}</h4>
                  <p>{group.description}</p>
                </div>
                <span className="count-pill">{group.items.length}</span>
              </header>
              <ul>
                {group.items.map((item, index) => (
                  <li key={`${item.label}-${index}`}>
                    <div className="finding-main">
                      <strong>{item.label}</strong>
                      {item.count > 1 && <span className="repeat">×{item.count}</span>}
                      <span className="points">+{item.points}</span>
                    </div>
                    {item.detail && <p className="finding-detail">{item.detail}</p>}
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function AnalysisResult({ analysis, onChange }) {
  const original = analysis.risk_analysis;
  const review = analysis.review;
  const hasDismissals = (review?.dismissed_findings?.length ?? 0) > 0;
  const current = hasDismissals ? review : original;
  const report = REPORT_TEXT[current.alert_level] ?? analysis.risk_report;
  const tone = alertTone(current.alert_level);
  const findings = analysis.findings ?? [];
  const interactive = findings.length > 0 && Boolean(analysis.document_id);

  // focus.n changes on every request, so selecting the same finding again re-scrolls.
  const [focus, setFocus] = useState({ id: null, n: 0 });
  const activeId = focus.id;
  const focusFinding = (id) => setFocus((previous) => ({ id, n: previous.n + 1 }));
  const [openGroups, setOpenGroups] = useState(() => new Set());
  const [categoryFilter, setCategoryFilter] = useState(null);
  const [busy, setBusy] = useState(false);
  const reviewRef = useRef(null);

  // The summary was written at scan time; after a review, restate the score
  // and say how many findings the user set aside.
  const currentRiskSummary = hasDismissals
    ? analysis.summary.risk_summary.replace(
        /^\w+ alert with a risk score of \d+\/100\./,
        `After your review: ${current.alert_level} alert with a risk score of ${current.risk_score}/100 ` +
          `(originally ${original.risk_score}). You marked ${review.dismissed_findings.length} ` +
          `finding${review.dismissed_findings.length > 1 ? "s" : ""} as not a risk. Originally found:`
      )
    : analysis.summary?.risk_summary;

  /** From the score breakdown: show only that category's findings. */
  function showCategory(category) {
    setCategoryFilter(category);
    reviewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  const [error, setError] = useState("");

  function toggleGroup(key) {
    setOpenGroups((previous) => {
      const next = new Set(previous);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  /** From a highlight in the document: open the finding's group and focus it. */
  function selectFinding(id) {
    const finding = findings.find((item) => item.id === id);
    if (!finding) return;

    setOpenGroups((previous) => new Set(previous).add(`${finding.category}:${finding.type}`));
    if (categoryFilter && categoryFilter !== finding.category) setCategoryFilter(null);
    focusFinding(id);
  }

  async function toggleDismiss(ids, dismiss) {
    setBusy(true);
    setError("");

    try {
      let latestReview = review;

      // One request per finding keeps the API simple; groups are small.
      for (const id of ids) {
        const alreadyDismissed = latestReview?.dismissed_findings?.includes(id) ?? false;
        if (alreadyDismissed === dismiss) continue;

        const url = `/documents/${analysis.document_id}/findings/${id}/dismiss`;
        const response = dismiss ? await apiClient.post(url) : await apiClient.delete(url);
        latestReview = response.data.review;
      }

      onChange?.({ ...analysis, review: latestReview });
    } catch (err) {
      setError(err.response?.data?.detail || "Your change could not be saved. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="result">
      <section className={`card result-hero ${tone}`}>
        <ScoreRing score={current.risk_score} level={current.alert_level} />

        <div className="result-hero-body">
          <div className="result-file">
            <FileText size={16} />
            <span title={analysis.filename}>{analysis.filename}</span>
            {analysis.created_at && <small>{formatDate(analysis.created_at)}</small>}
          </div>

          <div className="result-title-row">
            <h2>{report.title}</h2>
            <AlertBadge level={current.alert_level} size="lg" />
          </div>

          <p className="result-overview">{report.overview}</p>

          {hasDismissals && (
            <p className="review-summary">
              Reviewed by you: originally <strong>{original.risk_score}</strong> ({original.alert_level}),{" "}
              {review.dismissed_findings.length} finding{review.dismissed_findings.length > 1 ? "s" : ""} marked as not
              a risk.
            </p>
          )}

          <div className={`recommendation ${tone}`}>
            {current.alert_level === "Green" ? <CheckCircle2 size={18} /> : <ShieldAlert size={18} />}
            <p>{report.recommendation}</p>
          </div>

          <dl className="result-facts">
            <div>
              <dt>Trust score</dt>
              <dd>{current.trust_score}</dd>
            </div>
            <div>
              <dt>Words</dt>
              <dd>{analysis.summary?.word_count ?? 0}</dd>
            </div>
            <div>
              <dt>Findings</dt>
              <dd>{interactive ? findings.length : buildFindingGroups(analysis).reduce((t, g) => t + g.items.length, 0)}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="card summary-card">
        <div className="summary-grid">
          <div>
            <h4 className="subheading first">What we found</h4>
            {analysis.summary?.risk_summary && <p className="summary-text">{currentRiskSummary}</p>}
            <ScoreBreakdown
              analysis={analysis}
              riskScore={current.risk_score}
              tone={tone}
              onSelectCategory={interactive ? showCategory : undefined}
            />
          </div>
          <div>
            <h4 className="subheading first">Key sentences</h4>
            {analysis.summary?.key_sentences?.length ? (
              <ul className="key-sentences">
                {analysis.summary.key_sentences.map((sentence) => (
                  <li key={sentence}>{sentence}</li>
                ))}
              </ul>
            ) : (
              <p className="summary-text">{analysis.summary?.summary_text || "No text was extracted."}</p>
            )}
          </div>
        </div>

        {!analysis.text_extracted && (
          <p className="inline-note">
            <Info size={16} />
            No readable text was found. If this is a photo or scan, try a sharper, straighter image.
          </p>
        )}

        <p className="model-status">
          <Bot size={15} />
          {describeModelStatus(analysis.semantic_analysis)}
        </p>
      </section>

      {interactive ? (
        <div className="review-columns" ref={reviewRef}>
          <FindingsPanel
            findings={findings}
            review={review}
            categoryFilter={categoryFilter}
            onCategoryFilter={setCategoryFilter}
            openGroups={openGroups}
            onToggleGroup={toggleGroup}
            activeId={activeId}
            busy={busy}
            error={error}
            onShow={focusFinding}
            onToggleDismiss={toggleDismiss}
          />
          <DocumentViewer
            text={analysis.document_text || ""}
            truncated={analysis.document_text_truncated}
            findings={findings}
            review={review}
            categoryFilter={categoryFilter}
            activeId={activeId}
            focusKey={focus.n}
            onSelect={selectFinding}
          />
        </div>
      ) : findings.length === 0 && analysis.findings ? (
        <section className="card">
          <div className="all-clear">
            <CheckCircle2 size={20} />
            <p>No risk indicators were found in this document.</p>
          </div>
        </section>
      ) : (
        <div className="result-columns">
          <LegacyFindings analysis={analysis} />
          {analysis.text_preview && (
            <section className="card">
              <div className="card-header">
                <h3>Extracted text</h3>
              </div>
              <pre className="text-preview">{analysis.text_preview}</pre>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

export default AnalysisResult;
