export const ALERT_LEVELS = ["Red", "Yellow", "Green"];

// After the user marks findings as "not a risk", the reviewed score is the one shown.
export function getAlertLevel(document) {
  return document?.review?.alert_level || document?.alert_level || document?.risk_analysis?.alert_level || "Green";
}

export function getRiskScore(document) {
  return document?.review?.risk_score ?? document?.risk_score ?? document?.risk_analysis?.risk_score ?? 0;
}

export function alertTone(alertLevel) {
  return (alertLevel || "Green").toLowerCase();
}

export function formatDate(isoDate) {
  if (!isoDate) return "";

  // The backend stores UTC without a "Z" suffix.
  const date = new Date(isoDate.endsWith("Z") || isoDate.includes("+") ? isoDate : `${isoDate}Z`);

  return date.toLocaleString(undefined, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const TYPE_LABELS = {
  email_address: "Email address",
  phone_number: "Phone number",
  credit_card_number: "Card number",
  aadhaar_number: "Aadhaar number",
  aadhaar_like_number: "Aadhaar number",
  pan_number: "PAN number",
  pan_like_number: "PAN number",
  gstin: "GSTIN",
  ifsc_code: "IFSC code",
  upi_id: "UPI ID",
  bank_account_number: "Bank account number",
  bank_account_like_number: "Bank account number",
  indian_phone_number: "Phone number",
};

export function humanize(value) {
  if (!value) return "";
  if (TYPE_LABELS[value]) return TYPE_LABELS[value];

  const text = value.replaceAll("_", " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/**
 * Turns the detector outputs of one analysis into display groups:
 * [{ key, title, description, items: [{ label, detail, points, count }] }]
 * Repeated matches of the same label are merged into one item with a count.
 */
export function buildFindingGroups(analysis) {
  if (!analysis) return [];

  const groups = [
    {
      key: "threat",
      title: "Threat language",
      description: "Phrases that pressure, threaten or extort.",
      items: (analysis.threat_analysis?.threats || []).map((item) => ({
        label: item.phrase,
        points: item.risk_points,
      })),
    },
    {
      key: "policy",
      title: "Policy violations",
      description: "Instructions to bypass approvals, audits or records.",
      items: (analysis.policy_violation_analysis?.violations || []).map((item) => ({
        label: item.phrase,
        points: item.risk_points,
      })),
    },
    {
      key: "semantic",
      title: "AI model",
      description: "Risky meaning found by the AI model, even without keywords.",
      items: (analysis.semantic_analysis?.signals || []).map((item) => ({
        label: `Reads as ${item.label}`,
        detail: item.already_found_by_rules
          ? `${Math.round(item.confidence * 100)}% sure · already counted by the rules above`
          : `${Math.round(item.confidence * 100)}% sure · “${item.evidence}”`,
        points: item.points,
      })),
    },
    {
      key: "keyword",
      title: "Risky keywords",
      description: "Words often found in fraud or confidential material.",
      items: (analysis.keyword_analysis?.highlighted_sections || []).map((item) => ({
        label: item.keyword,
        detail: item.excerpt,
        points: item.risk_points,
      })),
    },
    {
      key: "sensitive",
      title: "Personal data",
      description: "Contact details and payment card numbers.",
      items: (analysis.sensitive_info_analysis?.findings || []).map((item) => ({
        label: humanize(item.type),
        detail: item.masked_value,
        points: item.risk_points,
      })),
    },
    {
      key: "compliance",
      title: "Indian ID & banking data",
      description: "Aadhaar, PAN, GSTIN, IFSC, UPI and account numbers.",
      items: (analysis.indian_compliance_analysis?.findings || []).map((item) => ({
        label: humanize(item.type),
        detail: item.masked_value,
        points: item.risk_points,
      })),
    },
    {
      key: "tampering",
      title: "Tampering signs",
      description: "Hidden characters, disguised words or duplicated text.",
      items: (analysis.tampering_analysis?.findings || []).map((item) => ({
        label: humanize(item.type),
        detail: item.description,
        points: item.risk_points,
      })),
    },
    {
      key: "anomaly",
      title: "Unusual patterns",
      description: "Shouting, symbol runs or odd formatting.",
      items: (analysis.anomaly_analysis?.anomalies || []).map((item) => ({
        label: humanize(item.type),
        detail: item.description,
        points: item.risk_points,
      })),
    },
  ];

  return groups
    .map((group) => ({ ...group, items: mergeRepeats(group.items) }))
    .filter((group) => group.items.length > 0);
}

function mergeRepeats(items) {
  const merged = new Map();

  for (const item of items) {
    const key = `${item.label}|${item.detail ?? ""}`;
    const existing = merged.get(key);

    if (existing) {
      existing.count += 1;
    } else {
      merged.set(key, { ...item, count: 1 });
    }
  }

  return [...merged.values()].sort((a, b) => b.points - a.points);
}

export function describeModelStatus(semantic) {
  if (!semantic) return "AI model: not used for this document (scanned before it was added).";
  if (semantic.status === "ok") return "AI model: on — reads meaning in English and Gujarati.";
  if (semantic.status === "disabled") return "AI model: turned off in settings — rules only.";
  if (semantic.status === "skipped") return "AI model: no text to read.";
  return "AI model: unavailable on the server — rules only.";
}

export const FINDING_CATEGORIES = {
  threat: { title: "Threat language", description: "Phrases that pressure, threaten or extort." },
  policy: { title: "Policy violations", description: "Instructions to bypass approvals, audits or records." },
  semantic: { title: "AI model", description: "Risky meaning found by the AI model, even without keywords." },
  keyword: { title: "Risky keywords", description: "Words often found in fraud or confidential material." },
  compliance: { title: "Indian ID & banking data", description: "Aadhaar, PAN, GSTIN, IFSC, UPI and account numbers." },
  sensitive: { title: "Personal data", description: "Contact details and payment card numbers." },
  tampering: { title: "Tampering signs", description: "Hidden characters, disguised words or duplicated text." },
  anomaly: { title: "Unusual patterns", description: "Shouting, symbol runs or odd formatting." },
};

/**
 * Groups findings for display: category -> groups of the same type
 * (e.g. "Phone number ×4"), keeping document order.
 * Returns [{ category, title, description, groups: [{ key, label, findings }] }].
 */
export function groupFindings(findings) {
  const categories = new Map();

  for (const finding of findings) {
    if (!categories.has(finding.category)) {
      categories.set(finding.category, { category: finding.category, ...FINDING_CATEGORIES[finding.category], groups: new Map() });
    }

    const groups = categories.get(finding.category).groups;
    const key = `${finding.category}:${finding.type}`;

    if (!groups.has(key)) groups.set(key, { key, label: finding.label, findings: [] });
    groups.get(key).findings.push(finding);
  }

  return [...categories.values()].map((category) => ({ ...category, groups: [...category.groups.values()] }));
}

/** Points a finding currently adds, after any "not a risk" decisions. */
export function effectivePoints(finding, review) {
  return review?.effective_points?.[finding.id] ?? finding.points;
}

/** One line explaining where a finding's points come from. */
export function explainPoints(finding, review, scoring) {
  const dismissed = review?.dismissed_findings?.includes(finding.id);
  const points = effectivePoints(finding, review);

  if (dismissed) return "You marked this as not a risk, so it adds no points.";
  if (finding.note) return finding.note;
  if (finding.category === "semantic") {
    return `The model is ${Math.round((finding.confidence ?? 0) * 100)}% sure; points are scaled by that confidence.`;
  }
  if (scoring === "phrase" && points === 0) return "This phrase was already counted once, so repeats add nothing.";
  if (scoring === "items" && points < finding.base_points) {
    return `Another ${finding.label.toLowerCase()} — the first counts ${finding.base_points}, each repeat adds ${points}.`;
  }
  return `Adds ${points} points to the risk score.`;
}

export const CATEGORY_SCORING = {
  threat: "phrase",
  policy: "phrase",
  keyword: "phrase",
  sensitive: "items",
  compliance: "items",
  semantic: "sum",
  tampering: "sum",
  anomaly: "sum",
};
