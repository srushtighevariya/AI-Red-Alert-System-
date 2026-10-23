import { AlertTriangle, CheckCircle2, FileStack, Gauge, ScanSearch, ShieldAlert } from "lucide-react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDate, getAlertLevel, getRiskScore } from "../utils/analysis";
import { AlertBadge, EmptyState, PageHeader } from "./ui";

const LEVEL_COLORS = { Red: "#dc2626", Yellow: "#d97706", Green: "#16a34a" };

function StatTile({ icon: Icon, label, value, tone }) {
  return (
    <article className={`stat-tile ${tone || ""}`}>
      <div className="stat-tile-icon">
        <Icon size={18} />
      </div>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function ScoreTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <strong>{item.filename}</strong>
      <span>
        Risk {item.score} · {item.level}
      </span>
    </div>
  );
}

function OverviewView({ user, history, onScan, onOpen, onViewHistory }) {
  const firstName = user.full_name?.split(" ")[0] || "there";
  const counts = { Red: 0, Yellow: 0, Green: 0 };
  history.forEach((document) => {
    counts[getAlertLevel(document)] += 1;
  });

  const averageRisk = history.length
    ? Math.round(history.reduce((total, document) => total + getRiskScore(document), 0) / history.length)
    : 0;

  const needsReview = history.filter((document) => getAlertLevel(document) !== "Green").slice(0, 5);

  const chartData = [...history]
    .slice(0, 12)
    .reverse()
    .map((document) => ({
      id: document.document_id,
      filename: document.filename,
      score: getRiskScore(document),
      level: getAlertLevel(document),
      label: formatDate(document.created_at),
    }));

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title={`Welcome back, ${firstName}`}
        description="A summary of the documents you have scanned."
        actions={
          <button type="button" className="button primary" onClick={onScan}>
            <ScanSearch size={16} />
            Scan a document
          </button>
        }
      />

      {history.length === 0 ? (
        <section className="card">
          <EmptyState
            icon={ScanSearch}
            title="No documents scanned yet"
            action={
              <button type="button" className="button primary" onClick={onScan}>
                Scan your first document
              </button>
            }
          >
            Upload a PDF, Word file, text file or image to get a risk score and a list of the evidence behind it.
          </EmptyState>
        </section>
      ) : (
        <>
          <section className="stat-grid">
            <StatTile icon={FileStack} label="Documents scanned" value={history.length} />
            <StatTile icon={ShieldAlert} label="Red alerts" value={counts.Red} tone="red" />
            <StatTile icon={AlertTriangle} label="Needs review (Yellow)" value={counts.Yellow} tone="yellow" />
            <StatTile icon={CheckCircle2} label="Low risk (Green)" value={counts.Green} tone="green" />
            <StatTile icon={Gauge} label="Average risk" value={averageRisk} />
          </section>

          <div className="overview-columns">
            <section className="card">
              <div className="card-header">
                <h3>Risk of recent scans</h3>
                <span className="muted">Last {chartData.length} documents</span>
              </div>

              <div className="distribution" aria-label="Alert distribution">
                {["Red", "Yellow", "Green"].map((level) =>
                  counts[level] > 0 ? (
                    <span
                      key={level}
                      className={level.toLowerCase()}
                      style={{ flexGrow: counts[level] }}
                      title={`${level}: ${counts[level]}`}
                    />
                  ) : null
                )}
              </div>

              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={chartData} margin={{ top: 8, right: 4, left: -24, bottom: 0 }}>
                  <XAxis dataKey="label" tick={false} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} ticks={[0, 30, 70, 100]} tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ScoreTooltip />} cursor={{ fill: "rgba(15, 23, 42, 0.04)" }} />
                  <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={36} minPointSize={4} onClick={(bar) => onOpen(history.find((d) => d.document_id === bar.id))} style={{ cursor: "pointer" }}>
                    {chartData.map((item) => (
                      <Cell key={item.id} fill={LEVEL_COLORS[item.level]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </section>

            <section className="card">
              <div className="card-header">
                <h3>Needs your attention</h3>
                <button type="button" className="link-button" onClick={onViewHistory}>
                  View all
                </button>
              </div>

              {needsReview.length === 0 ? (
                <div className="all-clear">
                  <CheckCircle2 size={20} />
                  <p>All your recent documents are low risk.</p>
                </div>
              ) : (
                <ul className="attention-list">
                  {needsReview.map((document) => (
                    <li key={document.document_id}>
                      <button type="button" onClick={() => onOpen(document)}>
                        <div>
                          <strong title={document.filename}>{document.filename}</strong>
                          <span>
                            Risk {getRiskScore(document)} · {formatDate(document.created_at)}
                          </span>
                        </div>
                        <AlertBadge level={getAlertLevel(document)} size="sm" />
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </>
      )}
    </>
  );
}

export default OverviewView;
