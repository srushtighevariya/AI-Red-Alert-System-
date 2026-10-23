import { useEffect, useMemo, useRef } from "react";

// When highlights overlap, the more serious category decides the colour.
const PRIORITY = ["threat", "policy", "compliance", "sensitive", "keyword", "semantic"];

/** Splits the text into plain and highlighted segments. A segment can be
 * covered by several findings (e.g. a keyword inside an AI-flagged passage). */
function buildSegments(text, findings) {
  const located = findings.filter((finding) => finding.start_index !== null && finding.start_index !== undefined && finding.start_index < text.length);
  const cuts = new Set([0, text.length]);

  located.forEach((finding) => {
    cuts.add(finding.start_index);
    cuts.add(Math.min(finding.end_index, text.length));
  });

  const points = [...cuts].sort((a, b) => a - b);
  const segments = [];

  for (let i = 0; i < points.length - 1; i += 1) {
    const start = points[i];
    const end = points[i + 1];
    const covering = located.filter((finding) => finding.start_index < end && finding.end_index > start);

    segments.push({ start, end, findings: covering });
  }

  return segments;
}

function primaryFinding(findings) {
  // The most specific match (shortest span) is the one a click opens.
  return [...findings].sort((a, b) => a.end_index - a.start_index - (b.end_index - b.start_index))[0];
}

function DocumentViewer({ text, truncated, findings, review, categoryFilter, activeId, focusKey, onSelect }) {
  const containerRef = useRef(null);
  const segments = useMemo(() => {
    const visible = categoryFilter ? findings.filter((finding) => finding.category === categoryFilter) : findings;
    return buildSegments(text, visible);
  }, [text, findings, categoryFilter]);
  const dismissed = new Set(review?.dismissed_findings ?? []);

  useEffect(() => {
    if (!activeId || !containerRef.current) return;

    const mark = containerRef.current.querySelector(`[data-ids~="${activeId}"]`);
    if (!mark) return;

    const container = containerRef.current;
    const top = mark.offsetTop - container.clientHeight / 3;
    container.scrollTo({ top: Math.max(top, 0), behavior: "smooth" });
  }, [activeId, focusKey, categoryFilter]);

  return (
    <section className="card viewer-card">
      <div className="card-header">
        <h3>Document</h3>
        <span className="muted">Personal data masked · select a highlight</span>
      </div>

      <div className="viewer-text" ref={containerRef}>
        {segments.map((segment) => {
          const content = text.slice(segment.start, segment.end);

          if (segment.findings.length === 0) return <span key={segment.start}>{content}</span>;

          const categories = segment.findings.map((finding) => finding.category);
          const category = PRIORITY.find((item) => categories.includes(item)) || categories[0];
          const allDismissed = segment.findings.every((finding) => dismissed.has(finding.id));
          const isActive = segment.findings.some((finding) => finding.id === activeId);

          return (
            <mark
              key={segment.start}
              className={`hl cat-${category} ${allDismissed ? "dismissed" : ""} ${isActive ? "active" : ""}`}
              data-ids={segment.findings.map((finding) => finding.id).join(" ")}
              title={segment.findings.map((finding) => finding.label).join(", ")}
              role="button"
              tabIndex={0}
              onClick={() => onSelect(primaryFinding(segment.findings).id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(primaryFinding(segment.findings).id);
                }
              }}
            >
              {content}
            </mark>
          );
        })}
      </div>

      {truncated && <p className="inline-note">Only the first part of this very long document is shown.</p>}
    </section>
  );
}

export default DocumentViewer;
