import { useEffect, useRef } from "react";
import { ChevronDown, Eye, Loader2, MapPin, RotateCcw, ThumbsDown } from "lucide-react";
import { CATEGORY_SCORING, effectivePoints, explainPoints, groupFindings } from "../utils/analysis";

function HighlightedContext({ finding }) {
  if (!finding.context) return null;

  const { context, context_match_start: start, context_match_end: end } = finding;

  return (
    <p className="finding-context">
      {context.slice(0, start)}
      <mark>{context.slice(start, end)}</mark>
      {context.slice(end)}
    </p>
  );
}

function Occurrence({ finding, review, active, busy, onShow, onToggleDismiss }) {
  const dismissed = review?.dismissed_findings?.includes(finding.id);
  const ref = useRef(null);

  useEffect(() => {
    if (active) ref.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [active]);

  return (
    <div ref={ref} className={`occurrence ${active ? "active" : ""} ${dismissed ? "dismissed" : ""}`}>
      <div className="occurrence-where">
        <MapPin size={14} />
        {finding.line ? `Line ${finding.line}` : "Applies to the whole document"}
        {finding.value && finding.category !== "semantic" && finding.value !== finding.label && (
          <span className="occurrence-value">{finding.value}</span>
        )}
        <span className={`points ${dismissed ? "zero" : ""}`}>+{effectivePoints(finding, review)}</span>
      </div>

      <HighlightedContext finding={finding} />

      <dl className="finding-guidance">
        <div>
          <dt>Why it matters</dt>
          <dd>{finding.why}</dd>
        </div>
        <div>
          <dt>What to do</dt>
          <dd>{finding.what_to_do}</dd>
        </div>
        <div>
          <dt>Points</dt>
          <dd>{explainPoints(finding, review, CATEGORY_SCORING[finding.category])}</dd>
        </div>
      </dl>

      <div className="occurrence-actions">
        {finding.start_index !== null && finding.start_index !== undefined && (
          <button type="button" className="button secondary small" onClick={() => onShow(finding.id)}>
            <Eye size={15} />
            Show in document
          </button>
        )}
        <button
          type="button"
          className="button secondary small"
          disabled={busy}
          onClick={() => onToggleDismiss([finding.id], !dismissed)}
        >
          {dismissed ? <RotateCcw size={15} /> : <ThumbsDown size={15} />}
          {dismissed ? "Count it again" : "Not a risk"}
        </button>
      </div>
    </div>
  );
}

function FindingGroup({ group, review, openGroups, activeId, busy, onToggleGroup, onShow, onToggleDismiss }) {
  const isOpen = openGroups.has(group.key);
  const ids = group.findings.map((finding) => finding.id);
  const dismissedCount = ids.filter((id) => review?.dismissed_findings?.includes(id)).length;
  const allDismissed = dismissedCount === ids.length;
  const total = group.findings.reduce((sum, finding) => sum + effectivePoints(finding, review), 0);
  const single = group.findings.length === 1 ? group.findings[0] : null;

  return (
    <li className={`finding-row ${isOpen ? "open" : ""} ${allDismissed ? "dismissed" : ""}`}>
      <button type="button" className="finding-row-head" onClick={() => onToggleGroup(group.key)} aria-expanded={isOpen}>
        <ChevronDown size={16} className="chevron" />
        <strong>{group.label}</strong>
        {group.findings.length > 1 && <span className="repeat">×{group.findings.length}</span>}
        {single && single.category !== "semantic" && single.value !== single.label && (
          <span className="row-value">{single.value}</span>
        )}
        {dismissedCount > 0 && !allDismissed && <span className="dismissed-pill">{dismissedCount} not a risk</span>}
        <span className={`points ${total === 0 ? "zero" : ""}`}>+{total}</span>
      </button>

      {isOpen && (
        <div className="finding-row-body">
          {group.findings.length > 1 && (
            <div className="group-actions">
              <span className="muted">{group.findings.length} occurrences</span>
              <button
                type="button"
                className="link-button"
                disabled={busy}
                onClick={() => onToggleDismiss(ids, !allDismissed)}
              >
                {allDismissed ? "Count all again" : `Mark all ${group.findings.length} as not a risk`}
              </button>
            </div>
          )}

          {group.findings.map((finding) => (
            <Occurrence
              key={finding.id}
              finding={finding}
              review={review}
              active={finding.id === activeId}
              busy={busy}
              onShow={onShow}
              onToggleDismiss={onToggleDismiss}
            />
          ))}
        </div>
      )}
    </li>
  );
}

function FindingsPanel({
  findings,
  review,
  categoryFilter,
  onCategoryFilter,
  openGroups,
  onToggleGroup,
  activeId,
  busy,
  error,
  onShow,
  onToggleDismiss,
}) {
  const categories = groupFindings(findings);
  const visible = categoryFilter ? categories.filter((category) => category.category === categoryFilter) : categories;
  const dismissedTotal = review?.dismissed_findings?.length ?? 0;

  return (
    <section className="card findings-card">
      <div className="card-header">
        <h3>Why this score</h3>
        {busy ? (
          <span className="muted inline-status">
            <Loader2 className="spin" size={14} /> Updating score…
          </span>
        ) : (
          <span className="muted">Select a finding to see where it is and why</span>
        )}
      </div>

      <div className="filter-chips category-chips" role="group" aria-label="Filter findings by category">
        <button type="button" className={`chip ${!categoryFilter ? "active" : ""}`} onClick={() => onCategoryFilter(null)}>
          All <span>{findings.length}</span>
        </button>
        {categories.map((category) => (
          <button
            key={category.category}
            type="button"
            className={`chip cat-${category.category} ${categoryFilter === category.category ? "active" : ""}`}
            onClick={() => onCategoryFilter(categoryFilter === category.category ? null : category.category)}
          >
            {category.title}
            <span>{category.groups.reduce((sum, group) => sum + group.findings.length, 0)}</span>
          </button>
        ))}
      </div>

      {error && <p className="form-error">{error}</p>}

      {dismissedTotal > 0 && (
        <p className="review-note">
          You marked {dismissedTotal} finding{dismissedTotal > 1 ? "s" : ""} as not a risk. Your feedback is saved to
          improve detection.
        </p>
      )}

      <div className="finding-groups">
        {visible.map((category) => (
          <article key={category.category} className={`finding-group ${category.category}`}>
            <header>
              <div>
                <h4>{category.title}</h4>
                <p>{category.description}</p>
              </div>
              <span className="count-pill">{category.groups.reduce((sum, group) => sum + group.findings.length, 0)}</span>
            </header>
            <ul className="finding-rows">
              {category.groups.map((group) => (
                <FindingGroup
                  key={group.key}
                  group={group}
                  review={review}
                  openGroups={openGroups}
                  activeId={activeId}
                  busy={busy}
                  onToggleGroup={onToggleGroup}
                  onShow={onShow}
                  onToggleDismiss={onToggleDismiss}
                />
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

export default FindingsPanel;
