import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, History, LayoutDashboard, Loader2, LogOut, ScanSearch, ShieldCheck, Users } from "lucide-react";
import apiClient from "../api/client";
import AnalysisResult from "../components/AnalysisResult";
import DocumentTable from "../components/DocumentTable";
import OverviewView from "../components/OverviewView";
import ScanView from "../components/ScanView";
import { PageHeader } from "../components/ui";

const HISTORY_LIMIT = 100;

function DashboardPage({ user, onLogout }) {
  const isAdmin = user.role === "admin";
  const [activeView, setActiveView] = useState("overview");
  const [scanResult, setScanResult] = useState(null);
  const [openedDocument, setOpenedDocument] = useState(null);
  const [returnView, setReturnView] = useState("history");
  const [history, setHistory] = useState([]);
  const [historyError, setHistoryError] = useState("");
  const [adminDocuments, setAdminDocuments] = useState([]);
  const [adminError, setAdminError] = useState("");
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState("");

  const loadHistory = useCallback(async () => {
    try {
      const response = await apiClient.get(`/documents/history?limit=${HISTORY_LIMIT}`);
      setHistory(response.data.documents || []);
      setHistoryError("");
    } catch {
      setHistoryError("Your document history could not be loaded.");
    }
  }, []);

  async function loadAdminDocuments() {
    try {
      const response = await apiClient.get("/admin/documents?limit=100");
      setAdminDocuments(response.data.documents || []);
      setAdminError("");
    } catch {
      setAdminDocuments([]);
      setAdminError("Admin documents could not be loaded.");
    }
  }

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  function navigate(view) {
    setActiveView(view);
    window.scrollTo({ top: 0 });

    if (view === "history" || view === "overview") loadHistory();
    if (view === "admin") loadAdminDocuments();
  }

  async function openDocument(document, from = activeView) {
    if (!document) return;

    // Lists leave out the full text and findings; load the complete report.
    setOpenedDocument(document);
    setReturnView(from);
    setActiveView("report");
    setReportError("");
    setReportLoading(true);
    window.scrollTo({ top: 0 });

    try {
      const response = await apiClient.get(`/documents/${document.document_id}`);
      setOpenedDocument(response.data);
    } catch {
      setReportError("The full report could not be loaded. Showing the saved summary.");
    } finally {
      setReportLoading(false);
    }
  }

  function handleScanResult(result) {
    setScanResult(result);
    if (result) loadHistory();
  }

  /** After "not a risk" changes, keep lists and the open report in sync. */
  function handleDocumentChange(updated) {
    const sync = (documents) =>
      documents.map((document) =>
        document.document_id === updated.document_id ? { ...document, review: updated.review } : document
      );

    setHistory(sync);
    setAdminDocuments(sync);
    if (openedDocument?.document_id === updated.document_id) setOpenedDocument(updated);
    if (scanResult?.document_id === updated.document_id) setScanResult(updated);
  }

  const navItems = [
    { view: "overview", label: "Overview", icon: LayoutDashboard },
    { view: "scan", label: "Scan document", icon: ScanSearch },
    { view: "history", label: "History", icon: History },
    ...(isAdmin ? [{ view: "admin", label: "All documents", icon: Users }] : []),
  ];

  const initials = (user.full_name || user.email)
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-logo">
            <ShieldCheck size={20} />
          </div>
          <div>
            <strong>Red Alert AI</strong>
            <span>Document risk scanner</span>
          </div>
        </div>

        <nav className="nav">
          {navItems.map(({ view, label, icon: Icon }) => {
            const isActive = activeView === view || (activeView === "report" && returnView === view);

            return (
              <button
                key={view}
                type="button"
                className={isActive ? "active" : ""}
                aria-current={isActive ? "page" : undefined}
                onClick={() => navigate(view)}
              >
                <Icon size={18} />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>

        <div className="sidebar-user">
          <div className="avatar">{initials}</div>
          <div className="sidebar-user-info">
            <strong>{user.full_name}</strong>
            <span title={user.email}>{user.email}</span>
          </div>
          <button type="button" className="icon-button" onClick={onLogout} aria-label="Log out" title="Log out">
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <main className="main">
        {historyError && activeView !== "scan" && <p className="banner-error">{historyError}</p>}

        {activeView === "overview" && (
          <OverviewView
            user={user}
            history={history}
            onScan={() => navigate("scan")}
            onOpen={(document) => openDocument(document, "overview")}
            onViewHistory={() => navigate("history")}
          />
        )}

        {activeView === "scan" && (
          <ScanView analysis={scanResult} onAnalysis={handleScanResult} onChange={handleDocumentChange} />
        )}

        {activeView === "history" && (
          <>
            <PageHeader
              eyebrow="History"
              title="Your documents"
              description="Every document you have scanned. Select one to see its full report."
            />
            <DocumentTable
              documents={history}
              onOpen={(document) => openDocument(document, "history")}
              emptyText="You have not scanned any documents yet."
            />
          </>
        )}

        {activeView === "admin" && isAdmin && (
          <>
            <PageHeader
              eyebrow="Admin"
              title="All documents"
              description="Documents scanned by every user."
            />
            {adminError && <p className="banner-error">{adminError}</p>}
            <DocumentTable
              documents={adminDocuments}
              onOpen={(document) => openDocument(document, "admin")}
              showUser
              emptyText="No documents have been scanned yet."
            />
          </>
        )}

        {activeView === "report" && openedDocument && (
          <>
            <PageHeader
              eyebrow="Report"
              title="Analysis report"
              actions={
                <button type="button" className="button secondary" onClick={() => navigate(returnView)}>
                  <ArrowLeft size={16} />
                  Back
                </button>
              }
            />
            {reportError && <p className="banner-error">{reportError}</p>}
            {reportLoading ? (
              <section className="card loading-card">
                <Loader2 className="spin" size={20} />
                Loading report…
              </section>
            ) : (
              <AnalysisResult
                key={openedDocument.document_id}
                analysis={openedDocument}
                onChange={handleDocumentChange}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export default DashboardPage;
