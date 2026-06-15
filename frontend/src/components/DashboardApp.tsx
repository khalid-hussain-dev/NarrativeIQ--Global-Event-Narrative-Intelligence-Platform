"use client";

import {
  Activity,
  BarChart3,
  Brain,
  CalendarDays,
  CheckCircle2,
  DatabaseZap,
  Download,
  ExternalLink,
  FileDown,
  FileText,
  Gauge,
  GitBranch,
  History,
  LayoutDashboard,
  LocateFixed,
  Maximize2,
  Menu,
  Move,
  Network,
  Pause,
  Play,
  RadioTower,
  RefreshCw,
  RotateCcw,
  Search,
  ServerCog,
  Settings2,
  ShieldCheck,
  SmilePlus,
  Sparkles,
  TrendingUp,
  UsersRound,
  X,
  ZoomIn,
  ZoomOut
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import martJson from "@/data/narrativeiq_mart.json";
import { formatCompact, formatPercent, formatScore } from "@/lib/format";
import type {
  AdminAuditEntry,
  AdminAuditResponse,
  AdminCommandResult,
  AdminStatus,
  CsvUploadResult,
  DatasetMeta,
  EnrichmentResult,
  GraphNode,
  IngestionScheduleStatus,
  NarrativeMart,
  NarrativeSummary,
  ReportExportResult,
  SavedTopicDetail,
  SavedTopicResponse,
  SavedTopicSnapshot,
  SourcePackImportResult,
  TopicIntelligence
} from "@/types/intelligence";
import { Logo } from "./Logo";

const fallbackMart = martJson as NarrativeMart;
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

const navItems = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "topic-iq", label: "Topic IQ", icon: Search },
  { id: "events", label: "Events", icon: CalendarDays },
  { id: "entities", label: "Entities", icon: UsersRound },
  { id: "sentiment", label: "Sentiment", icon: SmilePlus },
  { id: "replay", label: "Replay", icon: RadioTower },
  { id: "compare", label: "Compare", icon: BarChart3 },
  { id: "graph", label: "Graph", icon: Network },
  { id: "predictions", label: "Predictions", icon: Brain },
  { id: "quality", label: "Data Quality", icon: ShieldCheck },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "administration", label: "Administration", icon: Settings2 }
];

const sentimentColors = {
  Positive: "#3ddc97",
  Neutral: "#f6c85f",
  Negative: "#ff6b6b"
};

const graphColors: Record<string, string> = {
  Organization: "#15d8ff",
  Product: "#7c5cff",
  Topic: "#f6c85f",
  Narrative: "#3ddc97",
  Person: "#ff6b6b",
  Group: "#f6c85f",
  Location: "#72a7ff"
};

export function DashboardApp() {
  const [mart, setMart] = useState<NarrativeMart>(fallbackMart);
  const [dataSource, setDataSource] = useState<"api" | "static">("static");
  const [apiStatus, setApiStatus] = useState("Loading FastAPI mart");
  const [adminStatus, setAdminStatus] = useState<AdminStatus | null>(null);
  const [adminResult, setAdminResult] = useState<AdminCommandResult | null>(null);
  const [adminBusy, setAdminBusy] = useState<"etl" | "dry-run" | "load" | null>(null);
  const [adminAudit, setAdminAudit] = useState<AdminAuditEntry[]>([]);
  const [adminAuditStatus, setAdminAuditStatus] = useState("Loading audit log");
  const [importName, setImportName] = useState("Judge Demo Source Pack");
  const [importSourceType, setImportSourceType] = useState("news");
  const [importNotes, setImportNotes] = useState("Manual exhibition import to prove source-pack audit trail.");
  const [importContent, setImportContent] = useState(
    "NarrativeIQ exhibition proposal,manual,https://example.com/proposal\nAI regulation signal,news,https://example.com/ai-regulation"
  );
  const [importBusy, setImportBusy] = useState(false);
  const [importStatus, setImportStatus] = useState("Imported source packs are saved under datasets/imports and logged in the audit trail.");
  const [lastImportId, setLastImportId] = useState("");

  // Admin key state — persisted in localStorage so the key survives page refresh
  const [adminKey, setAdminKey] = useState<string>(() => {
    if (typeof window !== "undefined") {
      return window.localStorage.getItem("narrativeiq_admin_key") ?? "";
    }
    return "";
  });
  function handleAdminKeyChange(value: string) {
    setAdminKey(value);
    if (typeof window !== "undefined") {
      window.localStorage.setItem("narrativeiq_admin_key", value);
    }
  }

  // Enrichment state
  const [enrichBusy, setEnrichBusy] = useState(false);
  const [enrichResult, setEnrichResult] = useState<EnrichmentResult | null>(null);
  const [enrichStatus, setEnrichStatus] = useState("Run DeepSeek enrichment on imported source rows to add LLM-generated summaries.");

  // Ingestion schedule state
  const [scheduleStatus, setScheduleStatus] = useState<IngestionScheduleStatus | null>(null);
  const [scheduleBusy, setScheduleBusy] = useState(false);
  const [scheduleIntervalMinutes, setScheduleIntervalMinutes] = useState(60);
  const [scheduleTopics, setScheduleTopics] = useState("Artificial Intelligence,Climate Change");
  const [scheduleMessage, setScheduleMessage] = useState("Configure the background ingestion scheduler.");

  const [topicQuery, setTopicQuery] = useState("Artificial Intelligence in Education");
  const [topicBrief, setTopicBrief] = useState<TopicIntelligence | null>(null);
  const [topicBusy, setTopicBusy] = useState(false);
  const [topicError, setTopicError] = useState("");
  const [topicSaving, setTopicSaving] = useState(false);
  const [topicSaveStatus, setTopicSaveStatus] = useState("");
  const [savedTopics, setSavedTopics] = useState<SavedTopicSnapshot[]>([]);
  const [savedTopicsBusy, setSavedTopicsBusy] = useState(false);
  const [savedTopicsStatus, setSavedTopicsStatus] = useState("Loading saved topic snapshots");
  const [loadingSnapshot, setLoadingSnapshot] = useState<number | null>(null);
  const [reportBusy, setReportBusy] = useState(false);
  const [reportStatus, setReportStatus] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFrame, setSelectedFrame] = useState(fallbackMart.replayFrames.length - 1);
  const [playing, setPlaying] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(fallbackMart.graph.nodes[0] ?? null);
  const [compareLeftId, setCompareLeftId] = useState(fallbackMart.narratives[0]?.id ?? "");
  const [compareRightId, setCompareRightId] = useState(fallbackMart.narratives[1]?.id ?? fallbackMart.narratives[0]?.id ?? "");

  // ── Live Mode state ────────────────────────────────────────────────────────
  // When liveModeMart is set, ALL dashboard sections render live-sourced data
  // instead of the warehouse mart.
  const [liveModeMart, setLiveModeMart] = useState<NarrativeMart | null>(null);
  const [liveModeQuery, setLiveModeQuery] = useState("");
  const [liveModeLoading, setLiveModeLoading] = useState(false);
  const [liveModeError, setLiveModeError] = useState("");
  const [liveSearchInput, setLiveSearchInput] = useState("");
  const [liveNarrativesHistory, setLiveNarrativesHistory] = useState<NarrativeSummary[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = window.localStorage.getItem("narrativeiq_live_narratives_history");
        return saved ? JSON.parse(saved) : [];
      } catch {
        return [];
      }
    }
    return [];
  });

  const saveLiveNarrativesToHistory = (narratives: NarrativeSummary[]) => {
    setLiveNarrativesHistory((prev) => {
      const idsToOverwrite = new Set(narratives.map((n) => n.id));
      const filteredPrev = prev.filter((item) => !idsToOverwrite.has(item.id));
      const merged = [...filteredPrev, ...narratives];
      if (typeof window !== "undefined") {
        try {
          window.localStorage.setItem("narrativeiq_live_narratives_history", JSON.stringify(merged));
        } catch {}
      }
      return merged;
    });
  };

  // ── Multi-dataset switcher state ──────────────────────────────────────────
  const [availableDatasets, setAvailableDatasets] = useState<DatasetMeta[]>([]);
  const [activeDatasetSlug, setActiveDatasetSlug] = useState<string>("narrativeiq_mart");
  const [datasetSwitching, setDatasetSwitching] = useState(false);
  // The name entered in Admin "Run ETL" panel for creating a new named dataset.
  const [etlDatasetName, setEtlDatasetName] = useState("NarrativeIQ Warehouse");

  // ── CSV Upload state ───────────────────────────────────────────────────────────
  const [csvUploadFile, setCsvUploadFile] = useState<File | null>(null);
  const [csvUploadName, setCsvUploadName] = useState("");
  const [csvUploadBusy, setCsvUploadBusy] = useState(false);
  const [csvUploadResult, setCsvUploadResult] = useState<CsvUploadResult | null>(null);
  const [csvUploadStatus, setCsvUploadStatus] = useState("Select a CSV file from your computer to create a new dataset.");

  // ── Refresh / heartbeat state ─────────────────────────────────────────────
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);
  const [nextRefreshIn, setNextRefreshIn] = useState(60);
  const [heartbeatStatus, setHeartbeatStatus] = useState<"online" | "offline" | "pending">("pending");
  const [martUpdateBanner, setMartUpdateBanner] = useState<string | null>(null);

  // The "active mart" is the live-mode mart if set, otherwise the warehouse mart.
  const activeMart: NarrativeMart = liveModeMart ?? mart;

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE_URL}/dashboard`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        return response.json() as Promise<NarrativeMart>;
      })
      .then((apiMart) => {
        if (cancelled) {
          return;
        }
        setMart(apiMart);
        setDataSource("api");
        setApiStatus("Live FastAPI mart");
        setSelectedFrame(Math.max(0, apiMart.replayFrames.length - 1));
        setSelectedNode(apiMart.graph.nodes[0] ?? null);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        setDataSource("static");
        setApiStatus("Bundled mart fallback");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    refreshAdminStatus();
    refreshAdminAudit();
    refreshSavedTopicBriefs();
    refreshScheduleStatus();
    runTopicIntelligence("Artificial Intelligence in Education");
    fetchAvailableDatasets();
  }, []);

  useEffect(() => {
    if (!playing) {
      return;
    }

    const timer = window.setInterval(() => {
      setSelectedFrame((current) => (current + 1) % Math.max(1, mart.replayFrames.length));
    }, 950);

    return () => window.clearInterval(timer);
  }, [mart.replayFrames.length, playing]);

  useEffect(() => {
    setSelectedFrame((current) => Math.min(current, Math.max(0, mart.replayFrames.length - 1)));
  }, [mart.replayFrames.length]);

  // ── 60-second mart polling ─────────────────────────────────────────────────
  useEffect(() => {
    let seconds = 60;
    const countdown = window.setInterval(() => {
      seconds = Math.max(0, seconds - 1);
      setNextRefreshIn(seconds);
    }, 1000);
    const poll = window.setInterval(() => {
      const url = activeDatasetSlug === "narrativeiq_mart"
        ? `${API_BASE_URL}/dashboard`
        : `${API_BASE_URL}/datasets/marts/${activeDatasetSlug}`;

      fetch(url, { cache: "no-store" })
        .then((r) => r.json() as Promise<NarrativeMart>)
        .then((apiMart) => {
          setMart((prev) => {
            if (prev.generatedAt !== apiMart.generatedAt) {
              const count = apiMart.overview.totalRecords.toLocaleString();
              const ts = new Date(apiMart.generatedAt).toLocaleTimeString();
              setMartUpdateBanner(`⚡ Mart updated — ${count} records as of ${ts}`);
              window.setTimeout(() => setMartUpdateBanner(null), 9000);
            }
            return apiMart;
          });
          setDataSource("api");
          setApiStatus(activeDatasetSlug === "narrativeiq_mart" ? "Live FastAPI mart" : `Dataset: ${apiMart.datasetName ?? activeDatasetSlug}`);
          setLastRefreshed(new Date());
          seconds = 60;
          setNextRefreshIn(60);
        })
        .catch(() => { /* heartbeat will detect offline */ });
    }, 60_000);
    return () => {
      window.clearInterval(countdown);
      window.clearInterval(poll);
    };
  }, [activeDatasetSlug]);

  // ── 15-second API heartbeat ────────────────────────────────────────────────
  useEffect(() => {
    const beat = () => {
      fetch(`${API_BASE_URL}/health`, { cache: "no-store" })
        .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
        .then(() => setHeartbeatStatus("online"))
        .catch(() => setHeartbeatStatus("offline"));
    };
    beat();
    const timer = window.setInterval(beat, 15_000);
    return () => window.clearInterval(timer);
  }, []);

  // ── Live Topic Mode search ─────────────────────────────────────────────────
  function fetchAvailableDatasets() {
    fetch(`${API_BASE_URL}/datasets/marts`, { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json() as Promise<DatasetMeta[]>; })
      .then((datasets) => {
        setAvailableDatasets(datasets);
        // If we don't yet have an active slug, default to the first available.
        if (datasets.length > 0) {
          setActiveDatasetSlug((prev) => {
            const slugs = datasets.map((d) => d.slug);
            return slugs.includes(prev) ? prev : slugs[0];
          });
        }
      })
      .catch(() => { /* API offline — no datasets to show */ });
  }

  function switchDataset(slug: string) {
    if (slug === activeDatasetSlug || datasetSwitching) return;
    setDatasetSwitching(true);
    fetch(`${API_BASE_URL}/datasets/marts/${slug}`, { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json() as Promise<NarrativeMart>; })
      .then((newMart) => {
        setMart(newMart);
        setActiveDatasetSlug(slug);
        setDataSource("api");
        setApiStatus(`Dataset: ${newMart.datasetName ?? slug}`);
        setSelectedFrame(Math.max(0, newMart.replayFrames.length - 1));
        setSelectedNode(newMart.graph.nodes[0] ?? null);
        setCompareLeftId(newMart.narratives[0]?.id ?? "");
        setCompareRightId(newMart.narratives[1]?.id ?? newMart.narratives[0]?.id ?? "");
        // Exit live mode when switching datasets to avoid confusion.
        setLiveModeMart(null);
        setLiveModeQuery("");
        setLiveSearchInput("");
      })
      .catch((err: Error) => {
        setMartUpdateBanner(`⚠ Failed to switch dataset: ${err.message}`);
        window.setTimeout(() => setMartUpdateBanner(null), 6000);
      })
      .finally(() => setDatasetSwitching(false));
  }

  function uploadCsvDataset() {
    if (!csvUploadFile || csvUploadBusy) return;
    const name = csvUploadName.trim() || csvUploadFile.name.replace(/\.csv$/i, "").replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    setCsvUploadBusy(true);
    setCsvUploadStatus(`Processing '${csvUploadFile.name}' as dataset '${name}'…`);
    setCsvUploadResult(null);

    const form = new FormData();
    form.append("file", csvUploadFile);
    fetch(`${API_BASE_URL}/admin/datasets/upload?dataset_name=${encodeURIComponent(name)}`, {
      method: "POST",
      headers: adminKey ? { "X-Admin-Key": adminKey } : {},
      body: form,
    })
      .then(async (r) => {
        const payload = await r.json().catch(() => null);
        if (!r.ok) {
          const detail = payload && typeof payload.detail === "string" ? payload.detail : `Upload returned ${r.status}`;
          throw new Error(detail);
        }
        return payload as CsvUploadResult;
      })
      .then((result) => {
        setCsvUploadResult(result);
        setCsvUploadStatus(`✅ Dataset '${result.datasetName}' created — ${result.records !== undefined ? result.records.toLocaleString() : "--"} records, ${result.qualityScore}% quality.`);
        // Refresh dataset list so switcher shows the new entry.
        fetchAvailableDatasets();
        refreshAdminAudit();
      })
      .catch((err: Error) => {
        setCsvUploadStatus(`❌ Upload failed: ${err.message}`);
      })
      .finally(() => setCsvUploadBusy(false));
  }

  function runLiveMartSearch(query: string) {
    const trimmed = query.trim();
    if (!trimmed) return;
    setLiveModeLoading(true);
    setLiveModeError("");
    setLiveModeQuery(trimmed);
    fetch(`${API_BASE_URL}/topic-intelligence/live-mart?q=${encodeURIComponent(trimmed)}`, { cache: "no-store" })
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json() as Promise<NarrativeMart>; })
      .then((liveMart) => {
        setLiveModeMart(liveMart);
        saveLiveNarrativesToHistory(liveMart.narratives);
        setSelectedFrame(Math.max(0, liveMart.replayFrames.length - 1));
        setSelectedNode(liveMart.graph.nodes[0] ?? null);
        setCompareLeftId(liveMart.narratives[0]?.id ?? "");
        setCompareRightId(liveMart.narratives[1]?.id ?? liveMart.narratives[0]?.id ?? "");
      })
      .catch((err: Error) => setLiveModeError(`Live search failed: ${err.message}`))
      .finally(() => setLiveModeLoading(false));
  }

  function exitLiveMode() {
    setLiveModeMart(null);
    setLiveModeQuery("");
    setLiveModeError("");
    setLiveSearchInput("");
    setSelectedFrame(Math.max(0, mart.replayFrames.length - 1));
    setSelectedNode(mart.graph.nodes[0] ?? null);
    setCompareLeftId(mart.narratives[0]?.id ?? "");
    setCompareRightId(mart.narratives[1]?.id ?? mart.narratives[0]?.id ?? "");
  }

  const flagshipNarrative = activeMart.narratives[0] ?? fallbackMart.narratives[0];
  const replayFrame = activeMart.replayFrames[selectedFrame] ?? activeMart.replayFrames[0] ?? fallbackMart.replayFrames[0];
  const latestSentiment = activeMart.overview.sentimentDistribution;
  const forecastChart = activeMart.predictions[0]?.forecast ?? [];
  const activeNavItem = navItems.find((item) => item.id === activeSection) ?? navItems[0];
  const comparisonOptions = useMemo(() => {
    if (liveModeMart) {
      const current = liveModeMart.narratives;
      const historyFiltered = liveNarrativesHistory.filter(
        (hn) => !current.some((cn) => cn.id === hn.id)
      );
      return [...current, ...historyFiltered].slice(0, 32);
    } else {
      return mart.narratives.slice(0, 12);
    }
  }, [liveModeMart, mart.narratives, liveNarrativesHistory]);
  const compareLeft = comparisonOptions.find((item) => item.id === compareLeftId) ?? comparisonOptions[0];
  const compareRight =
    comparisonOptions.find((item) => item.id === compareRightId) ??
    comparisonOptions.find((item) => item.id !== compareLeft?.id) ??
    comparisonOptions[0];
  const comparisonTimeline = useMemo(() => {
    if (!compareLeft || !compareRight) {
      return [];
    }
    const rightByMonth = new Map(compareRight.timeline.map((point) => [point.month, point]));
    return compareLeft.timeline.map((point) => {
      const rightPoint = rightByMonth.get(point.month);
      return {
        month: point.month,
        leftStrength: point.strength,
        rightStrength: rightPoint?.strength ?? 0,
        leftInfluence: point.influence,
        rightInfluence: rightPoint?.influence ?? 0
      };
    });
  }, [compareLeft, compareRight]);
  const comparisonDelta = compareLeft && compareRight
    ? {
        strength: compareLeft.latestStrength - compareRight.latestStrength,
        growth: compareLeft.growthRate - compareRight.growthRate,
        influence: compareLeft.influenceScore - compareRight.influenceScore,
        sentiment: compareLeft.sentimentScore - compareRight.sentimentScore
      }
    : null;
  const searchResults = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      return [];
    }

    const eventResults = activeMart.events
      .filter((event) => [event.name, event.category, event.region, event.lifecycleStage].join(" ").toLowerCase().includes(query))
      .map((event) => ({
        type: "Event",
        title: event.name,
        meta: `${event.category} / ${event.lifecycleStage} / strength ${formatScore(event.narrativeStrength)}`,
        target: "events"
      }));

    const narrativeResults = activeMart.narratives
      .filter((narrative) => [narrative.topic, narrative.eventName, narrative.category, narrative.lifecycleStage].join(" ").toLowerCase().includes(query))
      .map((narrative) => ({
        type: "Narrative",
        title: narrative.topic,
        meta: `${narrative.eventName} / ${narrative.lifecycleStage} / growth ${formatPercent(narrative.growthRate)}`,
        target: "replay"
      }));

    const entityResults = activeMart.entities
      .filter((entity) => [entity.name, entity.type, entity.eventName].join(" ").toLowerCase().includes(query))
      .map((entity) => ({
        type: "Entity",
        title: entity.name,
        meta: `${entity.type} / ${formatCompact(entity.latestMentions)} latest mentions`,
        target: "graph"
      }));

    const predictionResults = activeMart.predictions
      .filter((prediction) => [prediction.narrative, prediction.eventName, prediction.direction].join(" ").toLowerCase().includes(query))
      .map((prediction) => ({
        type: "Prediction",
        title: prediction.narrative,
        meta: `${prediction.direction} / expected ${formatPercent(prediction.expectedGrowth)}`,
        target: "predictions"
      }));

    return [...eventResults, ...narrativeResults, ...entityResults, ...predictionResults].slice(0, 8);
  }, [activeMart, searchQuery]);

  function handleSectionChange(sectionId: string) {
    setActiveSection(sectionId);
    if (window.innerWidth <= 760) {
      setDrawerOpen(false);
    }
    window.requestAnimationFrame(() => {
      document.getElementById(sectionId)?.scrollIntoView({ behavior: "auto", block: "start" });
    });
  }

  function openSearchResult(result: { target: string; type: string; title: string }) {
    if (result.type === "Entity") {
      const graphNode = activeMart.graph.nodes.find((node) => node.label === result.title);
      if (graphNode) {
        setSelectedNode(graphNode);
      }
    }
    handleSectionChange(result.target);
  }

  function refreshAdminStatus() {
    fetch(`${API_BASE_URL}/admin/status`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Admin status returned ${response.status}`);
        }
        return response.json() as Promise<AdminStatus>;
      })
      .then((status) => setAdminStatus(status))
      .catch(() => setAdminStatus(null));
  }

  function refreshAdminAudit() {
    fetch(`${API_BASE_URL}/admin/audit-log?limit=8`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Audit log returned ${response.status}`);
        }
        return response.json() as Promise<AdminAuditResponse>;
      })
      .then((result) => {
        setAdminAudit(result.entries);
        setAdminAuditStatus(
          result.entries.length
            ? `${result.entries.length} recent event${result.entries.length === 1 ? "" : "s"}`
            : "No audit events yet"
        );
      })
      .catch(() => {
        setAdminAudit([]);
        setAdminAuditStatus("Audit log unavailable");
      });
  }

  function refreshSavedTopicBriefs() {
    setSavedTopicsBusy(true);

    fetch(`${API_BASE_URL}/topic-intelligence/saved?limit=8`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Saved topics returned ${response.status}`);
        }
        return response.json() as Promise<SavedTopicResponse>;
      })
      .then((result) => {
        setSavedTopics(result.snapshots);
        setSavedTopicsStatus(
          result.postgresConfigured
            ? result.snapshots.length
              ? `${result.snapshots.length} warehouse snapshot${result.snapshots.length === 1 ? "" : "s"} available`
              : "No live-topic snapshots saved yet"
            : "PostgreSQL is not configured"
        );
      })
      .catch(() => {
        setSavedTopics([]);
        setSavedTopicsStatus("Saved topic history is unavailable");
      })
      .finally(() => setSavedTopicsBusy(false));
  }

  function runTopicIntelligence(query = topicQuery) {
    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }

    setTopicQuery(trimmed);
    setTopicBusy(true);
    setTopicError("");
    setTopicSaveStatus("");

    fetch(`${API_BASE_URL}/topic-intelligence?q=${encodeURIComponent(trimmed)}`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Topic intelligence returned ${response.status}`);
        }
        return response.json() as Promise<TopicIntelligence>;
      })
      .then((brief) => setTopicBrief(brief))
      .catch(() => {
        setTopicBrief(null);
        setTopicError("Topic intelligence is unavailable. Start FastAPI or try again.");
      })
      .finally(() => setTopicBusy(false));
  }

  function saveTopicBrief() {
    if (!topicBrief) {
      return;
    }

    setTopicSaving(true);
    setTopicSaveStatus("");

    fetch(`${API_BASE_URL}/topic-intelligence/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(topicBrief)
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            payload && typeof payload.detail === "string"
              ? payload.detail
              : `Save returned ${response.status}`;
          throw new Error(detail);
        }
        return payload as { status: string; snapshotKey: number; sourcesSaved: number };
      })
      .then((result) => {
        setTopicSaveStatus(`Saved snapshot ${result.snapshotKey} with ${result.sourcesSaved} source row${result.sourcesSaved === 1 ? "" : "s"}`);
        refreshAdminStatus();
        refreshAdminAudit();
        refreshSavedTopicBriefs();
      })
      .catch((error: Error) => {
        const message = error.message.length > 160 ? `${error.message.slice(0, 157)}...` : error.message;
        setTopicSaveStatus(`Save failed: ${message}`);
      })
      .finally(() => setTopicSaving(false));
  }

  function loadSavedTopicBrief(snapshotKey: number) {
    setLoadingSnapshot(snapshotKey);
    setTopicError("");

    fetch(`${API_BASE_URL}/topic-intelligence/saved/${snapshotKey}`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Saved snapshot returned ${response.status}`);
        }
        return response.json() as Promise<SavedTopicDetail>;
      })
      .then((detail) => {
        setTopicBrief({
          ...detail.brief,
          sources: detail.sources.length ? detail.sources : detail.brief.sources
        });
        setTopicQuery(detail.brief.query || detail.snapshot.topicName);
        setTopicSaveStatus(`Loaded saved snapshot ${detail.snapshot.snapshotKey}`);
        handleSectionChange("topic-iq");
      })
      .catch(() => setTopicError("Saved snapshot could not be loaded from PostgreSQL."))
      .finally(() => setLoadingSnapshot(null));
  }

  function adminHeaders(): HeadersInit {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (adminKey) {
      headers["X-Admin-Key"] = adminKey;
    }
    return headers;
  }

  function runAdminCommand(kind: "etl" | "dry-run" | "load") {
    const endpoint =
      kind === "etl"
        ? `${API_BASE_URL}/admin/etl/run?records=50000&dataset_name=${encodeURIComponent(etlDatasetName)}`
        : `${API_BASE_URL}/admin/warehouse/load?dry_run=${kind === "dry-run" ? "true" : "false"}`;

    setAdminBusy(kind);
    setAdminResult(null);

    fetch(endpoint, { method: "POST", headers: adminHeaders() })
      .then((response) => response.json() as Promise<AdminCommandResult>)
      .then((result) => {
        setAdminResult(result);
        refreshAdminStatus();
        refreshAdminAudit();
        if (kind === "etl" && result.status === "completed") {
          // Refresh the dataset list so the new mart appears in the dropdown.
          fetchAvailableDatasets();
          return fetch(`${API_BASE_URL}/dashboard`, { cache: "no-store" })
            .then((response) => response.json() as Promise<NarrativeMart>)
            .then((apiMart) => {
              setMart(apiMart);
              setDataSource("api");
              setApiStatus("Live FastAPI mart");
            });
        }
        return undefined;
      })
      .catch(() => {
        setAdminResult({
          status: "failed",
          result: {
            command: [endpoint],
            returnCode: 1,
            durationSeconds: 0,
            stdout: "",
            stderr: "Request failed before the admin command could complete."
          }
        });
        refreshAdminAudit();
      })
      .finally(() => setAdminBusy(null));
  }

  function runEnrichment() {
    if (!lastImportId) {
      setEnrichStatus("Please import a pack first or enter an Import ID.");
      return;
    }
    setEnrichBusy(true);
    setEnrichResult(null);
    setEnrichStatus("Running DeepSeek enrichment...");

    fetch(`${API_BASE_URL}/admin/enrichment/run?importId=${encodeURIComponent(lastImportId)}`, {
      method: "POST",
      headers: adminHeaders()
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            payload && typeof payload.detail === "string"
              ? payload.detail
              : `Enrichment returned ${response.status}`;
          throw new Error(detail);
        }
        return payload as EnrichmentResult;
      })
      .then((result) => {
        setEnrichResult(result);
        setEnrichStatus(
          result.status === "ok"
            ? `Enriched ${result.enriched} rows, skipped ${result.skipped}, ${result.errors} error${result.errors === 1 ? "" : "s"}.`
            : (result.message ?? "Enrichment completed with errors.")
        );
        refreshAdminAudit();
      })
      .catch((error: Error) => {
        const message = error.message.length > 180 ? `${error.message.slice(0, 177)}...` : error.message;
        setEnrichStatus(`Enrichment failed: ${message}`);
      })
      .finally(() => setEnrichBusy(false));
  }

  function refreshScheduleStatus() {
    fetch(`${API_BASE_URL}/admin/ingestion/status`, { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error(`Schedule status returned ${response.status}`);
        return response.json() as Promise<IngestionScheduleStatus>;
      })
      .then((status) => {
        setScheduleStatus(status);
        if (status.topics && status.topics.length) {
          setScheduleTopics(status.topics.join(", "));
        }
        if (status.intervalMinutes) {
          setScheduleIntervalMinutes(status.intervalMinutes);
        }
      })
      .catch(() => setScheduleStatus(null));
  }

  function applyIngestionSchedule() {
    setScheduleBusy(true);
    setScheduleMessage("Applying schedule...");

    fetch(`${API_BASE_URL}/admin/ingestion/schedule?interval_minutes=${scheduleIntervalMinutes}&enabled=true`, {
      method: "POST",
      headers: adminHeaders()
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            payload && typeof payload.detail === "string"
              ? payload.detail
              : `Schedule returned ${response.status}`;
          throw new Error(detail);
        }
        return payload as IngestionScheduleStatus;
      })
      .then((status) => {
        setScheduleStatus(status);
        setScheduleMessage(
          `Schedule active: every ${status.intervalMinutes} min for ${status.topics ? status.topics.length : 0} topic${status.topics && status.topics.length === 1 ? "" : "s"}.`
        );
        refreshAdminAudit();
      })
      .catch((error: Error) => {
        const message = error.message.length > 180 ? `${error.message.slice(0, 177)}...` : error.message;
        setScheduleMessage(`Schedule failed: ${message}`);
      })
      .finally(() => setScheduleBusy(false));
  }

  function importSourcePack() {
    const trimmed = importContent.trim();
    if (!trimmed) {
      setImportStatus("Import content is empty. Add JSON rows or comma-separated source lines.");
      return;
    }

    setImportBusy(true);
    setImportStatus("Importing source pack");

    fetch(`${API_BASE_URL}/admin/import/source-pack`, {
      method: "POST",
      headers: adminHeaders(),
      body: JSON.stringify({
        name: importName,
        sourceType: importSourceType,
        notes: importNotes,
        content: trimmed
      })
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            payload && typeof payload.detail === "string"
              ? payload.detail
              : `Import returned ${response.status}`;
          throw new Error(detail);
        }
        return payload as SourcePackImportResult;
      })
      .then((result) => {
        setImportStatus(`Imported ${result.rowCount} row${result.rowCount === 1 ? "" : "s"} as ${result.importId}.`);
        setLastImportId(result.importId);
        refreshAdminAudit();
      })
      .catch((error: Error) => {
        const message = error.message.length > 180 ? `${error.message.slice(0, 177)}...` : error.message;
        setImportStatus(`Import failed: ${message}`);
        refreshAdminAudit();
      })
      .finally(() => setImportBusy(false));
  }

  function downloadReport() {
    const rows = [
      ["Report", activeMart.reportSummary.title],
      ["Event Focus", activeMart.reportSummary.eventFocus],
      ["Period", activeMart.reportSummary.period],
      ["Finding", activeMart.reportSummary.primaryFinding]
    ];
    const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "narrativeiq-report-summary.csv";
    anchor.click();
    URL.revokeObjectURL(url);
    setReportStatus("CSV summary exported from the current dashboard mart.");
  }

  function exportPdfReport() {
    setReportBusy(true);
    setReportStatus("Generating branded PDF report");

    let query = "";
    if (liveModeMart) {
      query = `?live_query=${encodeURIComponent(liveModeQuery)}`;
    } else if (activeDatasetSlug) {
      query = `?dataset_slug=${encodeURIComponent(activeDatasetSlug)}`;
    }

    fetch(`${API_BASE_URL}/reports/export/pdf${query}`, { method: "POST" })
      .then(async (response) => {
        const payload = await response.json().catch(() => null);
        if (!response.ok) {
          const detail =
            payload && typeof payload.detail === "string"
              ? payload.detail
              : `PDF export returned ${response.status}`;
          throw new Error(detail);
        }
        return payload as ReportExportResult;
      })
      .then((result) => {
        const anchor = document.createElement("a");
        anchor.href = `${API_BASE_URL}${result.downloadUrl}?t=${Date.now()}${query.replace("?", "&")}`;
        anchor.download = "narrativeiq_exhibition_report.pdf";
        anchor.click();
        setReportStatus(`PDF generated: ${(result.pdfBytes / 1024).toFixed(1)} KB`);
        refreshAdminAudit();
      })
      .catch((error: Error) => {
        const message = error.message.length > 180 ? `${error.message.slice(0, 177)}...` : error.message;
        setReportStatus(`PDF export failed: ${message}`);
      })
      .finally(() => setReportBusy(false));
  }

  function openHtmlReport() {
    let query = "";
    if (liveModeMart) {
      query = `&live_query=${encodeURIComponent(liveModeQuery)}`;
    } else if (activeDatasetSlug) {
      query = `&dataset_slug=${encodeURIComponent(activeDatasetSlug)}`;
    }
    window.open(`${API_BASE_URL}/reports/download/html?t=${Date.now()}${query}`, "_blank", "noopener,noreferrer");
    setReportStatus("Opened generated HTML report.");
    window.setTimeout(refreshAdminAudit, 600);
  }

  return (
    <main className={drawerOpen ? "app-shell drawer-open" : "app-shell drawer-closed"}>
      <aside className="sidebar" id="app-navigation">
        <div className="sidebar-header">
          <Logo variant="nav" />
          <button
            aria-label="Close navigation"
            className="sidebar-close"
            type="button"
            onClick={() => setDrawerOpen(false)}
            title="Close navigation"
          >
            <X size={18} />
          </button>
        </div>
        <div className="sidebar-scroll">
          <nav className="sidebar-nav" aria-label="NarrativeIQ sections">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  type="button"
                  className={activeSection === item.id ? "nav-button active" : "nav-button"}
                  key={item.id}
                  onClick={() => handleSectionChange(item.id)}
                  title={item.label}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
          <div className="sidebar-footer">
            <div className={`heartbeat-pill ${heartbeatStatus}`}>
              <span className="heartbeat-dot" />
              <span>{heartbeatStatus === "online" ? "API Live" : heartbeatStatus === "offline" ? "API Offline" : "Connecting"}</span>
            </div>
            <span>Historical through</span>
            <strong>{liveModeMart ? new Date().toISOString().slice(0, 10) : mart.historicalThrough}</strong>
            <small>{liveModeMart ? `⚡ Live: ${liveModeQuery}` : apiStatus}</small>
          </div>
        </div>
      </aside>
      {drawerOpen ? <button className="drawer-backdrop" type="button" onClick={() => setDrawerOpen(false)} aria-label="Close navigation" /> : null}

      <section className="workspace">
        {martUpdateBanner && (
          <div className="mart-update-banner">
            <span>{martUpdateBanner}</span>
            <button type="button" onClick={() => setMartUpdateBanner(null)} aria-label="Dismiss">✕</button>
          </div>
        )}

        {liveModeMart && (
          <div className="live-mode-banner">
            <RadioTower size={15} />
            <strong>Live Mode</strong>
            <span>·</span>
            <span>All sections showing real-time data for: <strong>{liveModeQuery}</strong></span>
            <span className={`live-mode-source ${liveModeMart.liveSourceMode}`}>
              {liveModeMart.liveSourceMode === "live_ingestion" ? "⚡ Live Sources" : liveModeMart.liveSourceMode === "warehouse_match" ? "📦 Warehouse Match" : "🔍 Prospective Brief"}
            </span>
            <button type="button" className="exit-live-btn" onClick={exitLiveMode}>
              <RotateCcw size={13} /> Exit Live Mode
            </button>
          </div>
        )}

        <header className="topbar">
          <div className="topbar-title">
            {!drawerOpen ? (
              <button
                aria-controls="app-navigation"
                aria-expanded={drawerOpen}
                aria-label="Open navigation drawer"
                className="drawer-toggle"
                type="button"
                onClick={() => setDrawerOpen(true)}
                title="Open navigation drawer"
              >
                <Menu size={19} />
              </button>
            ) : null}
            <div>
              <p className="eyebrow">{liveModeMart ? `⚡ Live Intelligence · ${liveModeQuery}` : "Global Event and Narrative Intelligence"}</p>
              <h1>{activeNavItem.label}</h1>
            </div>
          </div>
          <div className="topbar-right">
            {/* Dataset switcher — always shown; falls back to a single 'offline' entry */}
            <div className="dataset-switcher" title="Switch between available datasets">
              <DatabaseZap size={14} />
              {availableDatasets.length > 0 ? (
                <select
                  id="dataset-switcher-select"
                  aria-label="Switch active dataset"
                  value={activeDatasetSlug}
                  disabled={datasetSwitching}
                  onChange={(e) => switchDataset(e.target.value)}
                >
                  {availableDatasets.map((ds) => (
                    <option key={ds.slug} value={ds.slug}>
                      {ds.name}{ds.totalRecords > 0 ? ` (${(ds.totalRecords / 1000).toFixed(0)}k)` : ""}
                    </option>
                  ))}
                </select>
              ) : (
                <select disabled aria-label="Datasets (API offline)">
                  <option>{(mart.datasetName ?? "NarrativeIQ Warehouse") + ` (${(mart.overview.totalRecords / 1000).toFixed(0)}k)`}</option>
                </select>
              )}
              {datasetSwitching && <RefreshCw size={13} className="spin" />}
            </div>
            <form
              className="live-search-form"
              onSubmit={(e) => { e.preventDefault(); if (liveSearchInput.trim()) runLiveMartSearch(liveSearchInput); }}
              title="Search any topic to switch all sections to live data"
            >
              {liveModeLoading ? <RefreshCw size={15} className="spin" /> : <RadioTower size={15} />}
              <input
                aria-label="Live topic search — powers all sections with real-time data"
                placeholder={liveModeLoading ? "Fetching live data…" : "Live search any topic…"}
                value={liveSearchInput}
                disabled={liveModeLoading}
                onChange={(e) => setLiveSearchInput(e.target.value)}
              />
              <button type="submit" disabled={liveModeLoading || !liveSearchInput.trim()}>
                {liveModeLoading ? "…" : "Go Live"}
              </button>
            </form>
            <div className="search-shell">
              <Search size={16} />
              <input
                aria-label="Search narratives, entities, events"
                placeholder="Filter current data"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && searchResults[0]) {
                    openSearchResult(searchResults[0]);
                  }
                }}
              />
            </div>
          </div>
        </header>
        {liveModeError && (
          <div className="live-mode-error">
            <span>{liveModeError}</span>
            <button type="button" onClick={() => setLiveModeError("")}>✕</button>
          </div>
        )}

        {searchQuery.trim() ? (
          <section className="search-results" aria-label="Search results">
            <div>
              <span>{searchResults.length ? `${searchResults.length} result${searchResults.length === 1 ? "" : "s"}` : "No results"}</span>
              <button type="button" onClick={() => setSearchQuery("")}>Clear</button>
            </div>
            {searchResults.length ? (
              <div className="search-result-grid">
                {searchResults.map((result) => (
                  <button key={`${result.type}-${result.title}`} type="button" onClick={() => openSearchResult(result)}>
                    <span>{result.type}</span>
                    <strong>{result.title}</strong>
                    <small>{result.meta}</small>
                  </button>
                ))}
              </div>
            ) : (
              <p>Try OpenAI, AI Agents, Election Security, Cricket, or Relief Agencies.</p>
            )}
          </section>
        ) : null}

        <ModuleFocus
          mart={activeMart}
          activeSection={activeSection}
          onJump={handleSectionChange}
          onPlayReplay={() => {
            setPlaying(true);
            handleSectionChange("replay");
          }}
        />

        <section className="admin-status-strip">
          <span>{liveModeMart ? `⚡ Live Mode — ${liveModeQuery}` : apiStatus}</span>
          <strong>
            {liveModeMart
              ? `${activeMart.overview.totalRecords.toLocaleString()} live signals`
              : adminStatus
              ? `${adminStatus.warehouseFiles.files.length} warehouse files`
              : "Admin API pending"}
          </strong>
        </section>

        <section id="overview" className="landing-grid">
          <div className="landing-logo-panel">
            <Logo variant="full" />
          </div>
          <div className="landing-summary">
            <div className="dashboard-icon-row">
              <Logo variant="icon" />
              <span>{liveModeMart ? "⚡ Live Intelligence Mode" : "Warehouse-backed dashboard"}</span>
            </div>
            <h2>
              {liveModeMart
                ? `Live intelligence for: ${liveModeQuery}`
                : "Transforming digital conversations into narrative intelligence."}
            </h2>
            <p>
              {liveModeMart
                ? activeMart.reportSummary?.primaryFinding?.slice(0, 200)
                : "The dashboard reconstructs how narratives emerge, peak, decline, and influence public perception across events, entities, and sentiment streams."}
            </p>
            <div className="status-strip">
              <span>
                {liveModeMart
                  ? liveModeMart.liveSourceMode === "live_ingestion"
                    ? "⚡ Live data — Wikipedia · GDELT · Google News"
                    : liveModeMart.liveSourceMode === "warehouse_match"
                    ? "📦 Warehouse match"
                    : "🔍 Prospective brief"
                  : dataSource === "api"
                  ? "FastAPI mart connected"
                  : "ETL mart generated"}
              </span>
              <strong>{new Date(activeMart.generatedAt).toLocaleString()}</strong>
            </div>
            <div className="live-refresh-bar">
              <span className={`live-dot ${heartbeatStatus}`}>●</span>
              <span>{heartbeatStatus === "online" ? "LIVE" : heartbeatStatus === "offline" ? "OFFLINE" : "…"}</span>
              {!liveModeMart && heartbeatStatus === "online" && (
                <>
                  <span>·</span>
                  <span>Mart refreshes in {nextRefreshIn}s</span>
                  {lastRefreshed && <><span>·</span><span>Last: {lastRefreshed.toLocaleTimeString()}</span></>}
                </>
              )}
              {!liveModeMart && (
                <button
                  type="button"
                  className="refresh-now-btn"
                  title="Refresh mart from API now"
                  onClick={() => {
                    fetch(`${API_BASE_URL}/dashboard`, { cache: "no-store" })
                      .then((r) => r.json() as Promise<NarrativeMart>)
                      .then((m) => { setMart(m); setDataSource("api"); setApiStatus("Live FastAPI mart"); setLastRefreshed(new Date()); setNextRefreshIn(60); })
                      .catch(() => {});
                  }}
                >
                  <RefreshCw size={13} /> Refresh Now
                </button>
              )}
              {liveModeMart && (
                <button type="button" className="exit-live-btn-sm" onClick={exitLiveMode}>
                  <RotateCcw size={13} /> Back to Warehouse
                </button>
              )}
            </div>
          </div>
        </section>

        <section className="topic-iq-panel" id="topic-iq">
          <div className="topic-iq-copy">
            <p className="eyebrow">Topic Intelligence Search</p>
            <h2>{topicBrief ? topicBrief.query : "Search any topic"}</h2>
            <p>
              {topicBrief
                ? topicBrief.summary
                : "Generate a topic brief from the current NarrativeIQ warehouse mart."}
            </p>
            <form
              className="topic-search-form"
              onSubmit={(event) => {
                event.preventDefault();
                runTopicIntelligence();
                handleSectionChange("topic-iq");
              }}
            >
              <Search size={17} />
              <input
                aria-label="Generate topic intelligence"
                value={topicQuery}
                onChange={(event) => setTopicQuery(event.target.value)}
                placeholder="Enter a topic"
              />
              <button type="submit" disabled={topicBusy}>
                <Brain size={17} />
                <span>{topicBusy ? "Generating" : "Generate Brief"}</span>
              </button>
            </form>
            <div className="topic-example-row">
              {["Pakistan Elections", "Climate Risk", "Cricket Sponsorship", "AI in Education"].map((example) => (
                <button key={example} type="button" onClick={() => runTopicIntelligence(example)} disabled={topicBusy}>
                  {example}
                </button>
              ))}
            </div>
            <div className="topic-action-row">
              <button type="button" onClick={saveTopicBrief} disabled={!topicBrief || topicSaving}>
                <DatabaseZap size={17} />
                <span>{topicSaving ? "Saving Brief" : "Save Brief"}</span>
              </button>
              <span>{topicSaveStatus || "Saved briefs become PostgreSQL live-topic snapshots."}</span>
            </div>
            {topicError ? <p className="topic-error">{topicError}</p> : null}
          </div>

          <div className="topic-iq-detail">
            <div className="topic-mode-strip">
              <span>
                {topicBrief?.mode === "live_ingestion"
                  ? "Live ingestion"
                  : topicBrief?.mode === "warehouse_match"
                    ? "Warehouse match"
                    : "Prospective brief"}
              </span>
              <strong>{topicBrief ? `${topicBrief.confidence}% confidence` : "Waiting for topic"}</strong>
            </div>
            <div className="topic-metric-grid">
              <article>
                <span>Influence</span>
                <strong>{topicBrief ? formatScore(topicBrief.influenceScore) : "--"}</strong>
              </article>
              <article>
                <span>Strength</span>
                <strong>{topicBrief ? formatScore(topicBrief.narrativeStrength) : "--"}</strong>
              </article>
              <article>
                <span>Sentiment</span>
                <strong>{topicBrief?.sentimentLabel ?? "--"}</strong>
              </article>
              <article>
                <span>Stage</span>
                <strong>{topicBrief?.lifecycleStage ?? "--"}</strong>
              </article>
            </div>
            <div className="topic-evidence-grid">
              <article>
                <span>Total Signals</span>
                <strong>{topicBrief?.evidence ? formatCompact(topicBrief.evidence.totalSignals) : "--"}</strong>
              </article>
              <article>
                <span>Reference</span>
                <strong>{topicBrief?.evidence ? formatCompact(topicBrief.evidence.referenceSignals) : "--"}</strong>
              </article>
              <article>
                <span>News Signals</span>
                <strong>{topicBrief?.evidence ? formatCompact(topicBrief.evidence.newsSignals) : "--"}</strong>
              </article>
              <article>
                <span>Sources</span>
                <strong>{topicBrief?.evidence ? formatCompact(topicBrief.evidence.sourceClusters) : "--"}</strong>
              </article>
            </div>
            <div className="topic-chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={topicBrief?.timeline ?? []}>
                  <CartesianGrid stroke="#202a3f" strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fill: "#9ca8ba", fontSize: 11 }} minTickGap={18} />
                  <YAxis tick={{ fill: "#9ca8ba", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#0d1324", border: "1px solid #26324a", color: "#f8fbff" }} itemStyle={{ color: "#f8fbff" }} labelStyle={{ color: "#15d8ff" }} />
                  <Line dataKey="strength" stroke="#15d8ff" strokeWidth={2} dot={false} />
                  <Line dataKey="influence" stroke="#3ddc97" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="topic-iq-lists">
            <div>
              <PanelHeader icon={GitBranch} title="Related Narratives" kicker={topicBrief?.event.name ?? "Warehouse context"} />
              <div className="topic-list">
                {(topicBrief?.narratives ?? activeMart.narratives.slice(0, 4)).slice(0, 4).map((narrative) => (
                  <button
                    className={topicBrief?.mode === "live_ingestion" ? "topic-static-item" : undefined}
                    key={narrative.id}
                    type="button"
                    onClick={() => {
                      if (topicBrief?.mode !== "live_ingestion") {
                        handleSectionChange("replay");
                      }
                    }}
                    title={topicBrief?.mode === "live_ingestion" ? "Live-topic narratives are shown in this panel." : "Open narrative replay"}
                  >
                    <strong>{narrative.topic}</strong>
                    <span>{narrative.eventName} / {narrative.lifecycleStage} / {formatScore(narrative.latestStrength)}</span>
                  </button>
                ))}
              </div>
            </div>
            <div>
              <PanelHeader icon={UsersRound} title="Influence Entities" kicker="Top matches" />
              <div className="topic-list">
                {(topicBrief?.entities ?? activeMart.entities.slice(0, 4)).slice(0, 4).map((entity) => (
                  <button
                    key={`${entity.name}-${entity.eventName}`}
                    type="button"
                    onClick={() => {
                      const graphNode = activeMart.graph.nodes.find((node) => node.label === entity.name);
                      if (graphNode) {
                        setSelectedNode(graphNode);
                        handleSectionChange("graph");
                      }
                    }}
                    title={activeMart.graph.nodes.some((node) => node.label === entity.name) ? "Open matching graph node" : "Live-topic entity is not in the warehouse graph yet"}
                  >
                    <strong>{entity.name}</strong>
                    <span>{entity.type} / {formatCompact(entity.latestMentions)} mentions</span>
                  </button>
                ))}
              </div>
            </div>
            <div className="topic-source-note">
              <strong>Source note</strong>
              <p>{topicBrief?.sourceNote ?? "Topic intelligence appears here after generation."}</p>
            </div>
          </div>
        </section>

        <section className="live-history-panel">
          <div className="section-title-row">
            <PanelHeader icon={History} title="Live Warehouse History" kicker="PostgreSQL topic snapshots" />
            <button type="button" onClick={refreshSavedTopicBriefs} disabled={savedTopicsBusy}>
              <RefreshCw size={16} />
              <span>{savedTopicsBusy ? "Refreshing" : "Refresh"}</span>
            </button>
          </div>
          <div className="history-status">
            <span>{savedTopicsStatus}</span>
            <strong>{savedTopics.length ? `${savedTopics.length} latest` : "No rows"}</strong>
          </div>
          {savedTopics.length ? (
            <div className="history-grid">
              {savedTopics.map((snapshot) => (
                <article key={snapshot.snapshotKey}>
                  <div>
                    <span>Snapshot {snapshot.snapshotKey}</span>
                    <small>{new Date(snapshot.measuredAt).toLocaleString()}</small>
                  </div>
                  <strong>{snapshot.topicName}</strong>
                  <p>{snapshot.summary}</p>
                  <div className="history-metrics">
                    <span>{formatScore(snapshot.confidence)}% confidence</span>
                    <span>{formatCompact(snapshot.totalSignals)} signals</span>
                    <span>{formatCompact(snapshot.sourcesSaved)} sources</span>
                  </div>
                  <button type="button" onClick={() => loadSavedTopicBrief(snapshot.snapshotKey)} disabled={loadingSnapshot === snapshot.snapshotKey}>
                    <FileText size={15} />
                    <span>{loadingSnapshot === snapshot.snapshotKey ? "Loading" : "Load Brief"}</span>
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <div className="empty-history">
              <DatabaseZap size={24} />
              <span>Save a Topic IQ brief to create the first live-topic warehouse row.</span>
            </div>
          )}
        </section>

        <section className="metric-grid" aria-label="Platform metrics">
          <Metric icon={DatabaseZap} label={liveModeMart ? "Live signals" : "Raw content records"} value={formatCompact(activeMart.overview.totalRecords)} />
          <Metric icon={CalendarDays} label="Active events" value={String(activeMart.overview.activeEvents)} />
          <Metric icon={GitBranch} label="Active narratives" value={String(activeMart.overview.activeNarratives)} />
          <Metric icon={Gauge} label="Narrative health" value={formatScore(activeMart.overview.narrativeHealthScore)} />
          <Metric icon={ShieldCheck} label={liveModeMart ? "Confidence score" : "Warehouse quality"} value={`${formatScore(activeMart.overview.warehouseQualityScore)}%`} />
        </section>

        <section className="dashboard-grid">
          <article className="panel panel-large" id="events">
            <PanelHeader icon={Activity} title="Event Monitor" kicker={liveModeMart ? `Live: ${liveModeQuery}` : "Current warehouse snapshot"} />
            <div className="event-list">
              {activeMart.events.map((event) => (
                <div className="event-row" key={event.id}>
                  <div>
                    <strong>{event.name}</strong>
                    <span>{event.category} / {event.region}</span>
                  </div>
                  <div className="event-metrics">
                    <Badge tone={event.sentimentLabel}>{event.sentimentLabel}</Badge>
                    <span>{event.lifecycleStage}</span>
                    <strong>{formatScore(event.narrativeStrength)}</strong>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="panel" id="sentiment">
            <PanelHeader icon={BarChart3} title="Sentiment Mix" kicker="Latest month" />
            <div className="chart-frame compact">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={latestSentiment} dataKey="value" nameKey="label" innerRadius={62} outerRadius={92} paddingAngle={4}>
                    {latestSentiment.map((entry) => (
                      <Cell key={entry.label} fill={sentimentColors[entry.label]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: "#0d1324", border: "1px solid #26324a", color: "#f8fbff" }} itemStyle={{ color: "#f8fbff" }} labelStyle={{ color: "#15d8ff" }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="legend-row">
              {latestSentiment.map((item) => (
                <span key={item.label}>
                  <i style={{ background: sentimentColors[item.label] }} />
                  {item.label} {formatCompact(item.value)}
                </span>
              ))}
            </div>
          </article>

          <article className="panel panel-wide">
            <PanelHeader icon={TrendingUp} title={liveModeMart ? `Narrative Evolution — ${liveModeQuery}` : "Flagship Narrative Evolution"} kicker={flagshipNarrative.topic} />
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={flagshipNarrative.timeline}>
                  <defs>
                    <linearGradient id="strengthFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#15d8ff" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#15d8ff" stopOpacity={0.03} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#202a3f" strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fill: "#9ca8ba", fontSize: 11 }} minTickGap={28} />
                  <YAxis tick={{ fill: "#9ca8ba", fontSize: 11 }} domain={["auto", "auto"]} />
                  <Tooltip contentStyle={{ background: "#0d1324", border: "1px solid #26324a", color: "#f8fbff" }} itemStyle={{ color: "#f8fbff" }} labelStyle={{ color: "#15d8ff" }} />
                  <Area type="monotone" dataKey="strength" stroke="#15d8ff" fill="url(#strengthFill)" strokeWidth={2} />
                  <Line type="monotone" dataKey="influence" stroke="#7c5cff" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="panel" id="entities">
            <PanelHeader icon={Sparkles} title="Intelligence Feed" kicker={liveModeMart ? "Live source signals" : "AI-ready insights"} />
            <div className="feed-list">
              {topicBrief && !liveModeMart && (
                <div className="feed-item live-signal-card">
                  <Badge tone="High">⚡ Live Signal</Badge>
                  <strong>{topicBrief.query}</strong>
                  <p>{topicBrief.summary.slice(0, 160)}{topicBrief.summary.length > 160 ? "…" : ""}</p>
                  <small>{topicBrief.confidence}% confidence · {topicBrief.lifecycleStage} · {topicBrief.mode === "live_ingestion" ? "Live" : "Warehouse"}</small>
                </div>
              )}
              {activeMart.intelligenceFeed.map((item) => (
                <div className="feed-item" key={item.title}>
                  <Badge tone={item.severity}>{item.severity}</Badge>
                  <strong>{item.title}</strong>
                  <p>{item.body}</p>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="panel panel-wide" id="replay">
            <PanelHeader icon={RadioTower} title="Narrative Replay Mode" kicker={liveModeMart ? `Live: ${liveModeQuery}` : "Artificial Intelligence Revolution"} />
            <div className="replay-layout">
              <div className="replay-stage">
                <span>{replayFrame.label}</span>
                <h3>{replayFrame.dominantNarrative}</h3>
                <p>{replayFrame.stage} stage with sentiment score {replayFrame.sentiment} and strength {replayFrame.strength}.</p>
                <div className="replay-bars">
                  {replayFrame.activeNarratives.map((item) => (
                    <div key={item.topic}>
                      <span>{item.topic}</span>
                      <div>
                        <i style={{ width: `${item.strength}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="replay-controls">
                <button className="replay-play-button" onClick={() => setPlaying((value) => !value)} title={playing ? "Pause replay" : "Play replay"}>
                  {playing ? <Pause size={18} /> : <Play size={18} />}
                  <span>{playing ? "Pause Replay" : "Play Replay"}</span>
                </button>
                <input
                  type="range"
                  min={0}
                  max={activeMart.replayFrames.length - 1}
                  value={selectedFrame}
                  onChange={(event) => {
                    setPlaying(false);
                    setSelectedFrame(Number(event.target.value));
                  }}
                  aria-label="Replay timeline"
                />
              </div>
            </div>
          </article>

          <article className="panel" id="predictions">
            <PanelHeader icon={Brain} title="Prediction Center" kicker={activeMart.predictions[0]?.narrative ?? "Forecast"} />
            <div className="chart-frame compact">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastChart}>
                  <CartesianGrid stroke="#202a3f" strokeDasharray="3 3" />
                  <XAxis dataKey="period" tick={{ fill: "#9ca8ba", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#9ca8ba", fontSize: 11 }} domain={["auto", "auto"]} />
                  <Tooltip contentStyle={{ background: "#0d1324", border: "1px solid #26324a", color: "#f8fbff" }} itemStyle={{ color: "#f8fbff" }} labelStyle={{ color: "#15d8ff" }} />
                  <Line dataKey="strength" stroke="#3ddc97" strokeWidth={2} />
                  <Line dataKey="confidence" stroke="#f6c85f" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="prediction-list">
              {activeMart.predictions.slice(0, 3).map((prediction) => (
                <div key={prediction.narrative}>
                  <strong>{prediction.narrative}</strong>
                  <span>{prediction.direction} / {formatPercent(prediction.expectedGrowth)}</span>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="panel panel-full" id="compare">
            <PanelHeader icon={BarChart3} title="Narrative Comparison Engine" kicker="Popularity, growth, sentiment, influence" />
            {compareLeft && compareRight ? (
              <>
                <div className="comparison-controls">
                  <label>
                    <span>Narrative A</span>
                    <select value={compareLeft.id} onChange={(event) => setCompareLeftId(event.target.value)}>
                      {comparisonOptions.map((narrative) => (
                        <option key={narrative.id} value={narrative.id}>
                          {narrative.topic}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Narrative B</span>
                    <select value={compareRight.id} onChange={(event) => setCompareRightId(event.target.value)}>
                      {comparisonOptions.map((narrative) => (
                        <option key={narrative.id} value={narrative.id}>
                          {narrative.topic}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
                <div className="comparison-grid">
                  <NarrativeCompareCard narrative={compareLeft} label="Narrative A" tone="cyan" />
                  <NarrativeCompareCard narrative={compareRight} label="Narrative B" tone="mint" />
                  <div className="comparison-delta-card">
                    <span>Delta</span>
                    <strong>{comparisonDelta && comparisonDelta.strength >= 0 ? "A leads" : "B leads"}</strong>
                    <div>
                      <small>Strength {comparisonDelta ? formatScore(Math.abs(comparisonDelta.strength)) : "--"}</small>
                      <small>Growth {comparisonDelta ? formatPercent(Math.abs(comparisonDelta.growth)) : "--"}</small>
                      <small>Influence {comparisonDelta ? formatScore(Math.abs(comparisonDelta.influence)) : "--"}</small>
                      <small>Sentiment {comparisonDelta ? formatScore(Math.abs(comparisonDelta.sentiment)) : "--"}</small>
                    </div>
                  </div>
                </div>
                <div className="chart-frame comparison-chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={comparisonTimeline}>
                      <CartesianGrid stroke="#202a3f" strokeDasharray="3 3" />
                      <XAxis dataKey="month" tick={{ fill: "#9ca8ba", fontSize: 11 }} minTickGap={24} />
                      <YAxis tick={{ fill: "#9ca8ba", fontSize: 11 }} domain={["auto", "auto"]} />
                      <Tooltip contentStyle={{ background: "#0d1324", border: "1px solid #26324a", color: "#f8fbff" }} itemStyle={{ color: "#f8fbff" }} labelStyle={{ color: "#15d8ff" }} />
                      <Line name={compareLeft.topic} dataKey="leftStrength" stroke="#15d8ff" strokeWidth={2} dot={false} />
                      <Line name={compareRight.topic} dataKey="rightStrength" stroke="#3ddc97" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </>
            ) : (
              <div className="empty-history">
                <GitBranch size={24} />
                <span>At least two narratives are required for comparison.</span>
              </div>
            )}
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="panel panel-wide" id="graph">
            <PanelHeader icon={Network} title="Knowledge Graph Explorer" kicker={liveModeMart ? `Live: ${liveModeQuery}` : "Entity and narrative relationships"} />
            <KnowledgeGraph mart={activeMart} selectedNode={selectedNode} onSelectNode={setSelectedNode} />
          </article>

          <article className="panel">
            <PanelHeader icon={GitBranch} title="Top Entities" kicker="Influence ranking" />
            <div className="entity-list">
              {activeMart.entities.slice(0, 7).map((entity, index) => (
                <div className="entity-row" key={entity.name}>
                  <span>{index + 1}</span>
                  <div>
                    <strong>{entity.name}</strong>
                    <small>{entity.type} / {entity.eventName}</small>
                  </div>
                  <b>{formatCompact(entity.latestMentions)}</b>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="dashboard-grid">
          <article className="panel panel-wide">
            <PanelHeader icon={BarChart3} title="Top Growing Topics" kicker={liveModeMart ? `Live: ${liveModeQuery}` : "Trend velocity"} />
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activeMart.topGrowingTopics.slice(0, 8)}>
                  <CartesianGrid stroke="#202a3f" strokeDasharray="3 3" />
                  <XAxis dataKey="topic" tick={{ fill: "#9ca8ba", fontSize: 11 }} interval={0} angle={-18} textAnchor="end" height={72} />
                  <YAxis tick={{ fill: "#9ca8ba", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#0d1324", border: "1px solid #26324a", color: "#f8fbff" }} itemStyle={{ color: "#f8fbff" }} labelStyle={{ color: "#15d8ff" }} />
                  <Bar dataKey="growthRate" fill="#15d8ff" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </article>

          <article className="panel" id="quality">
            <PanelHeader icon={ShieldCheck} title="Data Quality" kicker={liveModeMart ? "Live signal quality" : "ETL profiling"} />
            <div className="quality-list">
              {activeMart.dataQuality.slice(0, 7).map((row) => (
                <div key={row.dataset}>
                  <span>{row.dataset}</span>
                  <strong>{formatScore(row.quality_score)}%</strong>
                  <div><i style={{ width: `${row.quality_score}%` }} /></div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="report-panel" id="reports">
          <div className="report-brand">
            <Logo variant="report" />
          </div>
          <div className="report-copy">
            <p className="eyebrow">Analyst report preview</p>
            <h2>{activeMart.reportSummary.title}</h2>
            <p>{activeMart.reportSummary.primaryFinding}</p>
            <div className="report-meta">
              <span>{activeMart.reportSummary.eventFocus}</span>
              <span>{activeMart.reportSummary.period}</span>
              <span>{formatCompact(activeMart.overview.totalRecords)} records</span>
            </div>
            {reportStatus ? <small className="report-status">{reportStatus}</small> : null}
          </div>
          <div className="report-actions">
            <button className="primary-button" type="button" onClick={exportPdfReport} disabled={reportBusy}>
              <FileDown size={17} />
              <span>{reportBusy ? "Exporting PDF" : "Export PDF"}</span>
            </button>
            <button className="secondary-button" type="button" onClick={openHtmlReport}>
              <ExternalLink size={17} />
              <span>Open HTML</span>
            </button>
            <button className="secondary-button" type="button" onClick={downloadReport}>
              <Download size={17} />
              <span>Export CSV</span>
            </button>
          </div>
        </section>

        <section className="admin-panel" id="administration">
          <div>
            <PanelHeader icon={ServerCog} title="Administration" kicker="ETL and warehouse control" />
            <div className="admin-metric-grid">
              <article>
                <span>Mart Records</span>
                <strong>{formatCompact(activeMart.overview.totalRecords)}</strong>
              </article>
              <article>
                <span>Warehouse Files</span>
                <strong>{adminStatus?.warehouseFiles.files.length ?? 0}</strong>
              </article>
              <article>
                <span>Quality Score</span>
                <strong>{formatScore(activeMart.overview.warehouseQualityScore)}%</strong>
              </article>
              <article>
                <span>PostgreSQL</span>
                <strong>{adminStatus?.postgresConfigured ? "Configured" : "Pending"}</strong>
              </article>
            </div>
          </div>

          <div className="admin-actions">
            {/* Dataset Name field for creating a named mart on ETL run */}
            <label className="admin-dataset-name-field">
              <span>Dataset Name</span>
              <input
                id="admin-etl-dataset-name"
                type="text"
                placeholder="e.g. Tech Trends 2024"
                value={etlDatasetName}
                onChange={(e) => setEtlDatasetName(e.target.value)}
                maxLength={80}
                title="Human-readable name for this dataset. Creates a new mart file without overwriting others."
              />
            </label>
            <button type="button" onClick={() => runAdminCommand("etl")} disabled={adminBusy !== null}>
              <DatabaseZap size={17} />
              <span>{adminBusy === "etl" ? "Running ETL" : "Run ETL"}</span>
            </button>
            <button type="button" onClick={() => runAdminCommand("dry-run")} disabled={adminBusy !== null}>
              <CheckCircle2 size={17} />
              <span>{adminBusy === "dry-run" ? "Checking Loader" : "Check Loader"}</span>
            </button>
            <button
              type="button"
              onClick={() => runAdminCommand("load")}
              disabled={adminBusy !== null || !adminStatus?.postgresConfigured}
              title={adminStatus?.postgresConfigured ? "Load generated warehouse CSVs into PostgreSQL" : adminStatus?.databaseHint}
            >
              <ServerCog size={17} />
              <span>{adminBusy === "load" ? "Loading Warehouse" : "Load Warehouse"}</span>
            </button>
          </div>

          <div className="admin-result">
            <strong>{adminResult ? `Last command: ${adminResult.status}` : "Last command: none"}</strong>
            {adminResult ? (
              <p>
                Exit {adminResult.result.returnCode} in {adminResult.result.durationSeconds}s
                {adminResult.result.stderr ? ` / ${adminResult.result.stderr.split("\n")[0]}` : ""}
              </p>
            ) : (
              <p>{adminStatus?.databaseHint ?? "Admin API status will appear here once FastAPI responds."}</p>
            )}
          </div>

          {/* ── Mart Source Mix ────────────────────────────────────── */}
          <div className="admin-source-mix-panel">
            <div className="admin-audit-heading">
              <div>
                <span>Mart Source Mix</span>
                <strong>Record distribution across available sources</strong>
              </div>
            </div>
            <div className="admin-source-mix-list">
              {adminStatus?.warehouseStats?.source_mix || mart.warehouseStats?.source_mix ? (
                Object.entries(adminStatus?.warehouseStats?.source_mix ?? mart.warehouseStats?.source_mix ?? {}).map(([sourceName, count]) => (
                  <article key={sourceName}>
                    <span>{sourceName}</span>
                    <strong>{formatCompact(count as number)}</strong>
                  </article>
                ))
              ) : (
                <p>No source mix stats available. Please run ETL first.</p>
              )}
            </div>
          </div>

          {/* ── Admin Key ─────────────────────────────────────────── */}
          <div className="admin-key-panel">
            <div className="admin-key-heading">
              <div>
                <span>Admin Authentication</span>
                <strong>X-Admin-Key header for protected endpoints</strong>
              </div>
              <ShieldCheck size={17} />
            </div>
            <label className="admin-import-field">
              <span>Admin Key</span>
              <input
                id="admin-key-input"
                type="password"
                placeholder="Enter NARRATIVEIQ_ADMIN_KEY from .env"
                value={adminKey}
                onChange={(event) => handleAdminKeyChange(event.target.value)}
                autoComplete="current-password"
              />
            </label>
            <p className="admin-key-hint">
              {adminKey ? "🔒 Key saved in browser — sent with all admin POST requests." : "⚠ No key set — admin POST requests will be rejected if NARRATIVEIQ_ADMIN_KEY is configured on the server."}
            </p>
          </div>

          {/* ── Upload CSV Dataset ─────────────────────────────────── */}
          <div className="admin-csv-upload-panel">
            <div className="admin-import-heading">
              <div>
                <span>Upload CSV Dataset</span>
                <strong>Convert any CSV into a switchable dashboard dataset</strong>
              </div>
              <button type="button" onClick={uploadCsvDataset} disabled={csvUploadBusy || !csvUploadFile}>
                <DatabaseZap size={15} />
                <span>{csvUploadBusy ? "Processing…" : "Upload & Convert"}</span>
              </button>
            </div>
            <div className="admin-csv-upload-body">
              <label className="admin-csv-file-label" htmlFor="csv-file-input">
                <div className="admin-csv-dropzone">
                  {csvUploadFile ? (
                    <>
                      <CheckCircle2 size={22} style={{ color: "var(--mint)" }} />
                      <span>{csvUploadFile.name}</span>
                      <small>{(csvUploadFile.size / 1024).toFixed(1)} KB selected</small>
                    </>
                  ) : (
                    <>
                      <FileDown size={22} style={{ color: "var(--cyan)" }} />
                      <span>Click to select a CSV file</span>
                      <small>Any structured CSV — housing, shipments, sales, logs, etc.</small>
                    </>
                  )}
                </div>
                <input
                  id="csv-file-input"
                  type="file"
                  accept=".csv"
                  style={{ display: "none" }}
                  onChange={(e) => {
                    const f = e.target.files?.[0] ?? null;
                    setCsvUploadFile(f);
                    if (f) {
                      const autoName = f.name.replace(/\.csv$/i, "").replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
                      setCsvUploadName(autoName);
                      setCsvUploadStatus(`Ready to convert '${f.name}'.`);
                    }
                  }}
                />
              </label>
              <label className="admin-dataset-name-field">
                <span>Dataset Name</span>
                <input
                  id="csv-upload-dataset-name"
                  type="text"
                  placeholder="e.g. Housing Prices 2024"
                  value={csvUploadName}
                  onChange={(e) => setCsvUploadName(e.target.value)}
                  maxLength={80}
                />
              </label>
            </div>
            {csvUploadResult && csvUploadResult.records !== undefined && (
              <div className="admin-csv-result-grid">
                <article>
                  <span>Records</span>
                  <strong>{csvUploadResult.records.toLocaleString()}</strong>
                </article>
                <article>
                  <span>Quality</span>
                  <strong>{csvUploadResult.qualityScore}%</strong>
                </article>
                <article>
                  <span>Slug</span>
                  <strong style={{ fontSize: "11px" }}>{csvUploadResult.datasetSlug}</strong>
                </article>
              </div>
            )}
            <p>{csvUploadStatus}</p>
          </div>

          {/* ── Source Pack Import ─────────────────────────────────── */}
          <div className="admin-import-panel">
            <div className="admin-import-heading">
              <div>
                <span>Source Pack Import</span>
                <strong>Upload/import audit trail</strong>
              </div>
              <button type="button" onClick={importSourcePack} disabled={importBusy}>
                <FileDown size={15} />
                <span>{importBusy ? "Importing" : "Import Pack"}</span>
              </button>
            </div>
            <div className="admin-import-grid">
              <label>
                <span>Pack Name</span>
                <input value={importName} onChange={(event) => setImportName(event.target.value)} />
              </label>
              <label>
                <span>Source Type</span>
                <select value={importSourceType} onChange={(event) => setImportSourceType(event.target.value)}>
                  <option value="news">News</option>
                  <option value="social">Social</option>
                  <option value="forum">Forum</option>
                  <option value="reference">Reference</option>
                  <option value="manual">Manual</option>
                </select>
              </label>
            </div>
            <label className="admin-import-field">
              <span>Notes</span>
              <input value={importNotes} onChange={(event) => setImportNotes(event.target.value)} />
            </label>
            <label className="admin-import-field">
              <span>Rows</span>
              <textarea
                value={importContent}
                onChange={(event) => setImportContent(event.target.value)}
                spellCheck={false}
              />
            </label>
            <p>{importStatus}</p>
          </div>

          {/* ── DeepSeek Enrichment ───────────────────────────────── */}
          <div className="admin-enrichment-panel">
            <div className="admin-import-heading">
              <div>
                <span>LLM Enrichment</span>
                <strong>DeepSeek enrichment of imported source rows</strong>
              </div>
              <button type="button" onClick={runEnrichment} disabled={enrichBusy}>
                <Sparkles size={15} />
                <span>{enrichBusy ? "Enriching" : "Run Enrichment"}</span>
              </button>
            </div>
            <label className="admin-import-field">
              <span>Import ID to Enrich</span>
              <input
                placeholder="import_..."
                value={lastImportId}
                onChange={(event) => setLastImportId(event.target.value)}
              />
            </label>
            {enrichResult ? (
              <div className="admin-enrichment-stats">
                <article>
                  <span>Enriched</span>
                  <strong>{enrichResult.enriched}</strong>
                </article>
                <article>
                  <span>Skipped</span>
                  <strong>{enrichResult.skipped}</strong>
                </article>
                <article>
                  <span>Errors</span>
                  <strong>{enrichResult.errors}</strong>
                </article>
                <article>
                  <span>Status</span>
                  <strong style={{ color: enrichResult.status === "ok" ? "#3ddc97" : "#ff6b6b" }}>{enrichResult.status.toUpperCase()}</strong>
                </article>
              </div>
            ) : null}
            <p>{enrichStatus}</p>
          </div>

          {/* ── Ingestion Schedule ────────────────────────────────── */}
          <div className="admin-schedule-panel">
            <div className="admin-import-heading">
              <div>
                <span>Scheduled Live Ingestion</span>
                <strong>
                  {scheduleStatus?.enabled
                    ? `Active — every ${scheduleStatus.intervalMinutes} min / ${scheduleStatus.runCount} run${scheduleStatus.runCount === 1 ? "" : "s"}`
                    : "Configure background ingestion"}
                </strong>
              </div>
              <button type="button" onClick={applyIngestionSchedule} disabled={scheduleBusy}>
                <RefreshCw size={15} />
                <span>{scheduleBusy ? "Applying" : "Apply Schedule"}</span>
              </button>
            </div>
            <div className="admin-import-grid">
              <label>
                <span>Interval (min)</span>
                <input
                  type="number"
                  min={5}
                  max={1440}
                  value={scheduleIntervalMinutes}
                  onChange={(event) => setScheduleIntervalMinutes(Number(event.target.value))}
                />
              </label>
              <label>
                <span>Last run</span>
                <input
                  readOnly
                  value={scheduleStatus?.lastRunAt ? new Date(scheduleStatus.lastRunAt).toLocaleString() : "Never"}
                />
              </label>
            </div>
            <label className="admin-import-field">
              <span>Topics (comma-separated)</span>
              <input
                value={scheduleTopics}
                onChange={(event) => setScheduleTopics(event.target.value)}
                placeholder="Artificial Intelligence, Climate Change, ..."
              />
            </label>
            <p>{scheduleMessage}</p>
          </div>

          {/* ── System Audit Log ──────────────────────────────────── */}
          <div className="admin-audit-panel">
            <div className="admin-audit-heading">
              <div>
                <span>System Audit Log</span>
                <strong>{adminAuditStatus}</strong>
              </div>
              <button type="button" onClick={refreshAdminAudit}>
                <RefreshCw size={15} />
                <span>Refresh</span>
              </button>
            </div>
            <div className="admin-audit-list">
              {adminAudit.length ? (
                adminAudit.map((entry) => (
                  <article key={entry.id}>
                    <div>
                      <span>{formatAuditTime(entry.timestamp)}</span>
                      <b className={`audit-pill audit-${entry.status}`}>{entry.status}</b>
                    </div>
                    <strong>{auditActionLabel(entry.action)}</strong>
                    <p>{entry.summary}</p>
                    {auditDetailText(entry) ? <small>{auditDetailText(entry)}</small> : null}
                  </article>
                ))
              ) : (
                <p>Run an ETL, warehouse load, topic save, or report export to create the first audit event.</p>
              )}
            </div>
          </div>
        </section>
      </section>

      {/* ── Social Footer ─────────────────────────────────────────────────── */}
      <footer className="app-footer">
        <div className="app-footer-inner">
          <span className="app-footer-brand">NarrativeIQ &mdash; Global Event Narrative Intelligence Platform</span>
          <div className="app-footer-socials">
            <a
              href="https://www.linkedin.com/in/khalid-hussain-dev/"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="LinkedIn"
              className="footer-social-link"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
              LinkedIn
            </a>
            <a
              href="https://github.com/khalid-hussain-dev"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
              className="footer-social-link"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg>
              GitHub
            </a>
            <a
              href="https://play.google.com/store/apps/developer?id=13+Dimensions+Studio"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Play Store"
              className="footer-social-link"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M3.18 23.76c.36.2.8.2 1.18-.02l12.84-7.41-2.8-2.8L3.18 23.76zM.54 1.3C.2 1.7 0 2.28 0 3v18c0 .72.2 1.3.54 1.7l.09.08 10.09-10.09v-.24L.63 1.22.54 1.3zm20.32 9.12l-2.88-1.66-3.17 3.17 3.17 3.16 2.9-1.67c.82-.48.82-1.52-.02-2zM4.36.26L17.2 7.67l-2.8 2.8L4.36.26z"/></svg>
              Play Store
            </a>
            <a
              href="mailto:sheikhkhalidhussain1234@gmail.com"
              aria-label="Email"
              className="footer-social-link"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
              Email
            </a>
          </div>
          <span className="app-footer-copy">&copy; {new Date().getFullYear()} Khalid Hussain &middot; Data Warehousing &amp; Big Data Lab</span>
        </div>
      </footer>
    </main>
  );
}

function auditActionLabel(action: string) {
  const labels: Record<string, string> = {
    etl_run: "ETL Run",
    warehouse_load_check: "Warehouse Check",
    warehouse_load: "Warehouse Load",
    topic_snapshot_save: "Topic Snapshot Save",
    source_pack_import: "Source Pack Import",
    report_pdf_export: "PDF Export",
    report_download: "Report Download"
  };
  return labels[action] ?? action.replaceAll("_", " ");
}

function formatAuditTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function auditDetailText(entry: AdminAuditEntry) {
  const details = entry.details ?? {};
  const pieces: string[] = [];
  if (typeof details.returnCode === "number") {
    pieces.push(`exit ${details.returnCode}`);
  }
  if (typeof details.durationSeconds === "number") {
    pieces.push(`${details.durationSeconds}s`);
  }
  if (typeof details.records === "number") {
    pieces.push(`${formatCompact(details.records)} records`);
  }
  if (typeof details.rowCount === "number") {
    pieces.push(`${formatCompact(details.rowCount)} imported rows`);
  }
  if (typeof details.importId === "string") {
    pieces.push(details.importId);
  }
  if (typeof details.snapshotKey === "number") {
    pieces.push(`snapshot ${details.snapshotKey}`);
  }
  if (typeof details.sourcesSaved === "number") {
    pieces.push(`${details.sourcesSaved} sources`);
  }
  if (typeof details.pdfBytes === "number") {
    pieces.push(`${(details.pdfBytes / 1024).toFixed(1)} KB`);
  }
  if (typeof details.postgresConfigured === "boolean") {
    pieces.push(details.postgresConfigured ? "PostgreSQL configured" : "PostgreSQL pending");
  }
  return pieces.join(" / ");
}

function ModuleFocus({
  mart,
  activeSection,
  onJump,
  onPlayReplay
}: {
  mart: NarrativeMart;
  activeSection: string;
  onJump: (sectionId: string) => void;
  onPlayReplay: () => void;
}) {
  const topEvent = mart.events[0];
  const topNarrative = mart.narratives[0];
  const topEntity = mart.entities[0];
  const topPrediction = mart.predictions[0];
  const qualityScore = mart.overview.warehouseQualityScore;

  const content: Record<string, { title: string; body: string; stat: string; actionLabel: string; actionTarget?: string }> = {
    overview: {
      title: "Executive intelligence view",
      body: "A warehouse-backed operating picture for active events, narrative growth, sentiment movement, and entity influence.",
      stat: `${formatCompact(mart.overview.totalRecords)} records`,
      actionLabel: "Open event monitor",
      actionTarget: "events"
    },
    "topic-iq": {
      title: "Topic intelligence search",
      body: "Search any topic, generate live public-source intelligence, save it into PostgreSQL, and reload saved warehouse snapshots.",
      stat: "Live + warehouse",
      actionLabel: "Open Topic IQ",
      actionTarget: "topic-iq"
    },
    events: {
      title: topEvent.name,
      body: `${topEvent.category} narrative is currently ${topEvent.lifecycleStage.toLowerCase()} with ${formatScore(topEvent.influenceScore)} influence.`,
      stat: `${formatScore(topEvent.narrativeStrength)} strength`,
      actionLabel: "Review event cards",
      actionTarget: "events"
    },
    entities: {
      title: topEntity.name,
      body: `${topEntity.name} is the leading influence signal with ${formatCompact(topEntity.latestMentions)} latest-period mentions.`,
      stat: `${formatScore(topEntity.mentionStrength)} influence`,
      actionLabel: "Open graph",
      actionTarget: "graph"
    },
    sentiment: {
      title: "Sentiment evolution",
      body: "Latest sentiment mix is generated from warehouse sentiment facts, grouped across all active event packs.",
      stat: `${formatCompact(mart.overview.sentimentDistribution.reduce((sum, item) => sum + item.value, 0))} signals`,
      actionLabel: "View sentiment mix",
      actionTarget: "sentiment"
    },
    replay: {
      title: "Narrative replay mode",
      body: "Replay the event month by month as narratives appear, peak, decline, and mutate.",
      stat: `${mart.replayFrames.length} frames`,
      actionLabel: "Play replay"
    },
    compare: {
      title: "Narrative comparison engine",
      body: "Compare two narratives across strength, growth, influence, sentiment, and month-by-month trajectory.",
      stat: "A vs B",
      actionLabel: "Open comparison",
      actionTarget: "compare"
    },
    graph: {
      title: "Knowledge graph explorer",
      body: "Entity and narrative relationships support zoom, pan, fit view, selected-node focus, and direct neighborhood expansion.",
      stat: `${mart.graph.nodes.length} nodes`,
      actionLabel: "Open graph",
      actionTarget: "graph"
    },
    predictions: {
      title: topPrediction.narrative,
      body: `${topPrediction.narrative} is forecast as ${topPrediction.direction.toLowerCase()} with ${formatPercent(topPrediction.expectedGrowth)} expected movement.`,
      stat: topPrediction.direction,
      actionLabel: "View forecast",
      actionTarget: "predictions"
    },
    quality: {
      title: "ETL data quality",
      body: "Completeness, consistency, uniqueness, and timeliness scores are calculated during the ETL profiling stage.",
      stat: `${formatScore(qualityScore)}% quality`,
      actionLabel: "Open quality report",
      actionTarget: "quality"
    },
    reports: {
      title: mart.reportSummary.title,
      body: `${mart.reportSummary.primaryFinding} Export the branded report as PDF, HTML, or CSV from this module.`,
      stat: "PDF ready",
      actionLabel: "Open reports",
      actionTarget: "reports"
    },
    administration: {
      title: "ETL and warehouse control",
      body: "Operational controls expose the generated mart, warehouse CSVs, data quality profile, and PostgreSQL load path.",
      stat: `${Object.keys(mart.warehouseStats.facts).length} fact groups`,
      actionLabel: "Open admin",
      actionTarget: "administration"
    }
  };

  const selected = content[activeSection] ?? content.overview;

  return (
    <section className="module-focus" aria-live="polite">
      <div>
        <span>Active module</span>
        <h2>{selected.title}</h2>
        <p>{selected.body}</p>
      </div>
      <strong>{selected.stat}</strong>
      <button
        type="button"
        onClick={() => {
          if (activeSection === "replay") {
            onPlayReplay();
            return;
          }
          onJump(selected.actionTarget ?? activeSection);
        }}
      >
        {selected.actionLabel}
      </button>
    </section>
  );
}

function NarrativeCompareCard({
  narrative,
  label,
  tone
}: {
  narrative: NarrativeSummary;
  label: string;
  tone: "cyan" | "mint";
}) {
  return (
    <div className={`comparison-card comparison-card-${tone}`}>
      <span>{label}</span>
      <strong>{narrative.topic}</strong>
      <small>{narrative.eventName} / {narrative.lifecycleStage}</small>
      <div>
        <p>
          <b>{formatScore(narrative.latestStrength)}</b>
          <span>Strength</span>
        </p>
        <p>
          <b>{formatPercent(narrative.growthRate)}</b>
          <span>Growth</span>
        </p>
        <p>
          <b>{formatScore(narrative.influenceScore)}</b>
          <span>Influence</span>
        </p>
        <p>
          <b>{formatScore(narrative.sentimentScore)}</b>
          <span>Sentiment</span>
        </p>
      </div>
    </div>
  );
}

function Metric({
  icon: Icon,
  label,
  value
}: {
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  value: string;
}) {
  return (
    <article className="metric-card">
      <Icon size={18} />
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function PanelHeader({
  icon: Icon,
  title,
  kicker
}: {
  icon: React.ComponentType<{ size?: number }>;
  title: string;
  kicker: string;
}) {
  return (
    <div className="panel-header">
      <div>
        <Icon size={18} />
        <h2>{title}</h2>
      </div>
      <span>{kicker}</span>
    </div>
  );
}

function Badge({ tone, children }: { tone: string; children: React.ReactNode }) {
  return <span className={`badge badge-${tone.toLowerCase()}`}>{children}</span>;
}

function KnowledgeGraph({
  mart,
  selectedNode,
  onSelectNode
}: {
  mart: NarrativeMart;
  selectedNode: GraphNode | null;
  onSelectNode: (node: GraphNode) => void;
}) {
  const defaultViewBox = { x: 0, y: 0, width: 720, height: 420 };
  const [viewBox, setViewBox] = useState(defaultViewBox);
  const [dragStart, setDragStart] = useState<{
    clientX: number;
    clientY: number;
    viewBox: typeof defaultViewBox;
  } | null>(null);
  const [expandedNodeId, setExpandedNodeId] = useState<string | null>(null);
  const coreNodes = useMemo(() => mart.graph.nodes.slice(0, 16), [mart.graph.nodes]);
  const selectedLinks = useMemo(() => {
    if (!selectedNode) {
      return [];
    }
    return mart.graph.links.filter((link) => link.source === selectedNode.id || link.target === selectedNode.id);
  }, [mart.graph.links, selectedNode]);
  const isExpanded = Boolean(selectedNode && expandedNodeId === selectedNode.id);
  const nodes = useMemo(() => {
    const visibleIds = new Set(coreNodes.map((node) => node.id));
    if (selectedNode) {
      visibleIds.add(selectedNode.id);
    }
    if (isExpanded) {
      selectedLinks.forEach((link) => {
        visibleIds.add(link.source);
        visibleIds.add(link.target);
      });
    }
    return mart.graph.nodes.filter((node) => visibleIds.has(node.id));
  }, [coreNodes, isExpanded, mart.graph.nodes, selectedLinks, selectedNode]);
  const nodeIds = useMemo(() => new Set(nodes.map((node) => node.id)), [nodes]);
  const visibleLinks = useMemo(
    () => mart.graph.links.filter((link) => nodeIds.has(link.source) && nodeIds.has(link.target)),
    [mart.graph.links, nodeIds]
  );
  const connectedNodeIds = useMemo(() => {
    const ids = new Set<string>();
    if (selectedNode) {
      ids.add(selectedNode.id);
    }
    selectedLinks.forEach((link) => {
      ids.add(link.source);
      ids.add(link.target);
    });
    return ids;
  }, [selectedLinks, selectedNode]);
  const relationshipRows = useMemo(() => {
    if (!selectedNode) {
      return [];
    }
    return selectedLinks.map((link) => {
      const neighborId = link.source === selectedNode.id ? link.target : link.source;
      return {
        link,
        neighbor: mart.graph.nodes.find((node) => node.id === neighborId) ?? null,
      };
    });
  }, [mart.graph.nodes, selectedLinks, selectedNode]);
  const positions = useMemo(() => {
    const center = { x: 360, y: 205 };
    const orderedNodes =
      isExpanded && selectedNode
        ? [
            ...nodes.filter((node) => node.id === selectedNode.id),
            ...nodes.filter((node) => node.id !== selectedNode.id),
          ]
        : nodes;
    return Object.fromEntries(
      orderedNodes.map((node, index) => {
        if (index === 0) {
          return [node.id, center];
        }
        const angle = (Math.PI * 2 * index) / Math.max(1, orderedNodes.length - 1);
        const radius = index % 2 === 0 ? 164 : 124;
        return [
          node.id,
          {
            x: Number((center.x + Math.cos(angle) * radius).toFixed(2)),
            y: Number((center.y + Math.sin(angle) * radius).toFixed(2))
          }
        ];
      })
    );
  }, [isExpanded, nodes, selectedNode]);

  function zoomGraph(factor: number) {
    setViewBox((current) => {
      const nextWidth = Math.max(220, Math.min(980, current.width * factor));
      const nextHeight = Math.max(128, Math.min(572, current.height * factor));
      return {
        x: current.x + (current.width - nextWidth) / 2,
        y: current.y + (current.height - nextHeight) / 2,
        width: nextWidth,
        height: nextHeight,
      };
    });
  }

  function fitVisibleGraph() {
    const visiblePositions = nodes.map((node) => positions[node.id]).filter(Boolean);
    if (!visiblePositions.length) {
      return;
    }
    const padding = 76;
    const minX = Math.min(...visiblePositions.map((position) => position.x));
    const maxX = Math.max(...visiblePositions.map((position) => position.x));
    const minY = Math.min(...visiblePositions.map((position) => position.y));
    const maxY = Math.max(...visiblePositions.map((position) => position.y));
    let width = maxX - minX + padding * 2;
    let height = maxY - minY + padding * 2;
    const targetAspect = 720 / 420;
    if (width / height > targetAspect) {
      height = width / targetAspect;
    } else {
      width = height * targetAspect;
    }
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    setViewBox({ x: centerX - width / 2, y: centerY - height / 2, width, height });
  }

  function centerSelectedNode() {
    if (!selectedNode || !positions[selectedNode.id]) {
      return;
    }
    const position = positions[selectedNode.id];
    const width = 330;
    const height = 192.5;
    setViewBox({ x: position.x - width / 2, y: position.y - height / 2, width, height });
  }

  function resetGraphView() {
    setViewBox(defaultViewBox);
    setExpandedNodeId(null);
  }

  function handlePointerDown(event: React.PointerEvent<SVGSVGElement>) {
    if (event.button !== 0) {
      return;
    }
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragStart({ clientX: event.clientX, clientY: event.clientY, viewBox });
  }

  function handlePointerMove(event: React.PointerEvent<SVGSVGElement>) {
    if (!dragStart) {
      return;
    }
    const bounds = event.currentTarget.getBoundingClientRect();
    const deltaX = ((event.clientX - dragStart.clientX) / Math.max(1, bounds.width)) * dragStart.viewBox.width;
    const deltaY = ((event.clientY - dragStart.clientY) / Math.max(1, bounds.height)) * dragStart.viewBox.height;
    setViewBox({
      ...dragStart.viewBox,
      x: dragStart.viewBox.x - deltaX,
      y: dragStart.viewBox.y - deltaY,
    });
  }

  function handleWheel(event: React.WheelEvent<SVGSVGElement>) {
    event.preventDefault();
    zoomGraph(event.deltaY > 0 ? 1.12 : 0.88);
  }

  return (
    <div className="graph-layout">
      <div className="graph-stage">
        <div className="graph-toolbar" aria-label="Graph controls">
          <button type="button" onClick={() => zoomGraph(0.82)} aria-label="Zoom in" title="Zoom in">
            <ZoomIn size={16} />
          </button>
          <button type="button" onClick={() => zoomGraph(1.18)} aria-label="Zoom out" title="Zoom out">
            <ZoomOut size={16} />
          </button>
          <button type="button" onClick={fitVisibleGraph} aria-label="Fit visible graph" title="Fit visible graph">
            <Maximize2 size={16} />
          </button>
          <button
            type="button"
            onClick={centerSelectedNode}
            disabled={!selectedNode}
            aria-label="Center selected node"
            title="Center selected node"
          >
            <LocateFixed size={16} />
          </button>
          <button
            type="button"
            onClick={() => setExpandedNodeId(isExpanded ? null : selectedNode?.id ?? null)}
            disabled={!selectedNode || !selectedLinks.length}
            aria-label={isExpanded ? "Collapse selected node" : "Expand selected node"}
            aria-pressed={isExpanded}
            title={isExpanded ? "Collapse selected node" : "Expand selected node"}
          >
            <GitBranch size={16} />
          </button>
          <button type="button" onClick={resetGraphView} aria-label="Reset graph view" title="Reset graph view">
            <RotateCcw size={16} />
          </button>
          <span className="graph-pan-indicator" title="Drag canvas to pan" aria-label="Pan graph">
            <Move size={15} />
          </span>
        </div>
        <svg
          className={dragStart ? "graph-canvas is-dragging" : "graph-canvas"}
          viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
          role="img"
          aria-label="Narrative knowledge graph"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={() => setDragStart(null)}
          onPointerCancel={() => setDragStart(null)}
          onWheel={handleWheel}
        >
        {visibleLinks.map((link) => {
          const source = positions[link.source];
          const target = positions[link.target];
          if (!source || !target) {
            return null;
          }
          const active = Boolean(selectedNode && (link.source === selectedNode.id || link.target === selectedNode.id));
          return (
            <line
              key={`${link.source}-${link.target}`}
              className={active ? "graph-link is-active" : "graph-link"}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              strokeWidth={Math.max(1, link.strength * 3)}
            />
          );
        })}
        {nodes.map((node) => {
          const position = positions[node.id];
          const isSelected = selectedNode?.id === node.id;
          const isLinked = connectedNodeIds.has(node.id) && !isSelected;
          return (
            <g
              className={`graph-node${isSelected ? " is-selected" : ""}${isLinked ? " is-linked" : ""}`}
              key={node.id}
              onClick={() => onSelectNode(node)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectNode(node);
                }
              }}
              tabIndex={0}
            >
              <circle
                cx={position.x}
                cy={position.y}
                r={isSelected ? 21 : isLinked ? 18 : 16}
                fill={graphColors[node.type] ?? "#15d8ff"}
              />
              <text x={position.x} y={position.y + 34} textAnchor="middle">
                {node.label.length > 16 ? `${node.label.slice(0, 15)}...` : node.label}
              </text>
            </g>
          );
        })}
        </svg>
      </div>
      <div className="graph-detail">
        <span>Selected node</span>
        <strong>{selectedNode?.label ?? "Select a node"}</strong>
        <p>{selectedNode?.type ?? "Relationship intelligence"} with score {selectedNode ? formatScore(selectedNode.score) : "--"}.</p>
        <div className="graph-detail-stats">
          <small>{nodes.length} visible nodes</small>
          <small>{visibleLinks.length} visible links</small>
          <small>{Math.round((720 / viewBox.width) * 100)}% zoom</small>
        </div>
        <div className="graph-neighborhood">
          <span>Neighborhood</span>
          {relationshipRows.length ? (
            relationshipRows.slice(0, 5).map(({ link, neighbor }) => (
              <button
                key={`${link.source}-${link.target}`}
                type="button"
                onClick={() => {
                  if (neighbor) {
                    onSelectNode(neighbor);
                  }
                }}
              >
                <strong>{neighbor?.label ?? (link.source === selectedNode?.id ? link.target : link.source)}</strong>
                <small>{link.type.replaceAll("_", " ")} / {formatScore(link.strength * 100)} strength</small>
              </button>
            ))
          ) : (
            <p>No direct relationship rows in the current mart.</p>
          )}
        </div>
      </div>
    </div>
  );
}
