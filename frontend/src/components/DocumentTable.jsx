import { useMemo, useState } from "react";
import { ChevronRight, Search } from "lucide-react";
import { ALERT_LEVELS, alertTone, formatDate, getAlertLevel, getRiskScore } from "../utils/analysis";
import { AlertBadge } from "./ui";

function DocumentTable({ documents, onOpen, showUser = false, emptyText = "No documents yet." }) {
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("All");

  const counts = useMemo(() => {
    const result = { All: documents.length, Red: 0, Yellow: 0, Green: 0 };
    documents.forEach((document) => {
      result[getAlertLevel(document)] += 1;
    });
    return result;
  }, [documents]);

  const visible = documents.filter((document) => {
    const matchesLevel = level === "All" || getAlertLevel(document) === level;
    const search = query.trim().toLowerCase();
    const matchesQuery =
      !search ||
      document.filename?.toLowerCase().includes(search) ||
      (showUser && document.uploaded_by_email?.toLowerCase().includes(search));

    return matchesLevel && matchesQuery;
  });

  return (
    <section className="card table-card">
      <div className="table-toolbar">
        <div className="search-box">
          <Search size={16} />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={showUser ? "Search file or user" : "Search file name"}
          />
        </div>

        <div className="filter-chips" role="group" aria-label="Filter by alert level">
          {["All", ...ALERT_LEVELS].map((option) => (
            <button
              key={option}
              type="button"
              className={`chip ${option === level ? "active" : ""} ${option !== "All" ? alertTone(option) : ""}`}
              onClick={() => setLevel(option)}
            >
              {option}
              <span>{counts[option]}</span>
            </button>
          ))}
        </div>
      </div>

      {visible.length === 0 ? (
        <p className="table-empty">{documents.length === 0 ? emptyText : "No documents match this filter."}</p>
      ) : (
        <div className="doc-table" role="table">
          <div className={`doc-row doc-head ${showUser ? "with-user" : ""}`} role="row">
            <span role="columnheader">Document</span>
            {showUser && <span role="columnheader">Uploaded by</span>}
            <span role="columnheader">Scanned</span>
            <span role="columnheader">Risk</span>
            <span role="columnheader">Alert</span>
            <span aria-hidden="true" />
          </div>

          {visible.map((document) => {
            const alertLevel = getAlertLevel(document);
            const riskScore = getRiskScore(document);

            return (
              <button
                key={document.document_id}
                type="button"
                className={`doc-row ${showUser ? "with-user" : ""}`}
                role="row"
                onClick={() => onOpen(document)}
              >
                <span className="doc-name" role="cell" title={document.filename}>
                  {document.filename}
                </span>
                {showUser && (
                  <span className="muted ellipsis" role="cell">
                    {document.uploaded_by_email || "Unknown"}
                  </span>
                )}
                <span className="muted" role="cell">
                  {formatDate(document.created_at)}
                </span>
                <span className="risk-cell" role="cell">
                  <span className={`risk-bar ${alertTone(alertLevel)}`}>
                    <span style={{ width: `${riskScore}%` }} />
                  </span>
                  <strong>{riskScore}</strong>
                </span>
                <span role="cell">
                  <AlertBadge level={alertLevel} size="sm" />
                </span>
                <ChevronRight className="row-arrow" size={18} aria-hidden="true" />
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

export default DocumentTable;
