import { effectivePoints, FINDING_CATEGORIES } from "../utils/analysis";

// Same caps the backend applies per category (app/ai/findings.py).
const CATEGORY_CAPS = { semantic: 60 };

// Documents scanned before detailed findings: use the stored detector scores.
const LEGACY_SCORES = {
  threat: (a) => a.threat_analysis?.threat_risk_score,
  policy: (a) => a.policy_violation_analysis?.policy_risk_score,
  semantic: (a) => a.semantic_analysis?.semantic_risk_score,
  keyword: (a) => a.keyword_analysis?.keyword_risk_score,
  compliance: (a) => a.indian_compliance_analysis?.compliance_risk_score,
  sensitive: (a) => a.sensitive_info_analysis?.sensitive_risk_score,
  tampering: (a) => a.tampering_analysis?.tampering_risk_score,
  anomaly: (a) => a.anomaly_analysis?.anomaly_risk_score,
};

function breakdownRows(analysis) {
  const findings = analysis.findings;
  const review = analysis.review;

  if (!findings?.length) {
    return Object.entries(LEGACY_SCORES)
      .map(([category, read]) => ({ category, points: read(analysis) ?? 0, count: null, dismissed: 0 }))
      .filter((row) => row.points > 0);
  }

  return Object.keys(FINDING_CATEGORIES)
    .map((category) => {
      const inCategory = findings.filter((finding) => finding.category === category);
      const total = inCategory.reduce((sum, finding) => sum + effectivePoints(finding, review), 0);

      return {
        category,
        points: Math.min(total, CATEGORY_CAPS[category] ?? 100),
        count: inCategory.length,
        dismissed: inCategory.filter((finding) => review?.dismissed_findings?.includes(finding.id)).length,
      };
    })
    .filter((row) => row.count > 0);
}

function describe(row) {
  const parts = [`${row.points} points`];
  if (row.count !== null) parts.push(`from ${row.count} finding${row.count === 1 ? "" : "s"}`);
  if (row.dismissed) parts.push(`${row.dismissed} marked not a risk`);
  return parts.join(" · ");
}

function ScoreBreakdown({ analysis, riskScore, tone, onSelectCategory }) {
  const rows = breakdownRows(analysis).sort((a, b) => b.points - a.points);
  const total = rows.reduce((sum, row) => sum + row.points, 0);
  const clickable = Boolean(onSelectCategory && analysis.findings?.length);

  if (rows.length === 0) return null;

  return (
    <figure className="breakdown">
      <figcaption>
        <span>Score breakdown</span>
        <span className="muted">Points by category, out of 100</span>
      </figcaption>

      <ul className="breakdown-rows">
        {rows.map((row) => {
          const content = (
            <>
              <span className="breakdown-label">{FINDING_CATEGORIES[row.category]?.title ?? row.category}</span>
              <span className="breakdown-track" aria-hidden="true">
                {row.points > 0 && <span className={`breakdown-bar ${tone}`} style={{ width: `${row.points}%` }} />}
              </span>
              <span className="breakdown-value">{row.points}</span>
              <span className="breakdown-tip" role="tooltip">
                {describe(row)}
                {clickable && " · select to see them"}
              </span>
            </>
          );

          return (
            <li key={row.category}>
              {clickable ? (
                <button
                  type="button"
                  className="breakdown-row"
                  onClick={() => onSelectCategory(row.category)}
                  aria-label={`${FINDING_CATEGORIES[row.category]?.title}: ${describe(row)}. Show these findings.`}
                >
                  {content}
                </button>
              ) : (
                <div className="breakdown-row" aria-label={`${FINDING_CATEGORIES[row.category]?.title}: ${describe(row)}`}>
                  {content}
                </div>
              )}
            </li>
          );
        })}
      </ul>

      {total > riskScore && (
        <p className="breakdown-note">
          Categories add up to {total}; the risk score is capped at 100.
        </p>
      )}
    </figure>
  );
}

export default ScoreBreakdown;
