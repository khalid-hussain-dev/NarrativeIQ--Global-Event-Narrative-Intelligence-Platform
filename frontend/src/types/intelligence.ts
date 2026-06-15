export type SentimentLabel = "Positive" | "Neutral" | "Negative";

export interface SentimentDistribution {
  label: SentimentLabel;
  value: number;
}

export interface Overview {
  totalRecords: number;
  activeEvents: number;
  activeNarratives: number;
  narrativeHealthScore: number;
  warehouseQualityScore: number;
  sentimentDistribution: SentimentDistribution[];
}

export interface EventSummary {
  id: string;
  name: string;
  category: string;
  region: string;
  narrativeStrength: number;
  growthRate: number;
  influenceScore: number;
  sentimentScore: number;
  sentimentLabel: SentimentLabel;
  lifecycleStage: string;
}

export interface NarrativeTimelinePoint {
  date: string;
  month: string;
  strength: number;
  growth: number;
  influence: number;
  sentiment: number;
  volume: number;
  stage: string;
}

export interface NarrativeSummary {
  id: string;
  eventId: string;
  eventName: string;
  topic: string;
  category: string;
  latestStrength: number;
  growthRate: number;
  influenceScore: number;
  sentimentScore: number;
  lifecycleStage: string;
  relatedNarratives: string[];
  timeline: NarrativeTimelinePoint[];
}

export interface GrowingTopic {
  topic: string;
  eventName: string;
  trendScore: number;
  growthRate: number;
  momentum: number;
}

export interface EntitySummary {
  name: string;
  type: string;
  totalMentions: number;
  latestMentions: number;
  mentionStrength: number;
  eventName: string;
  timeline: Array<{ date: string; mentions: number; strength: number }>;
}

export interface SentimentTimelinePoint {
  date: string;
  positive: number;
  neutral: number;
  negative: number;
}

export interface Prediction {
  narrative: string;
  eventName: string;
  expectedGrowth: number;
  direction: string;
  forecast: Array<{ period: string; strength: number; confidence: number }>;
}

export interface GraphNode {
  id: string;
  label: string;
  type: string;
  score: number;
}

export interface GraphLink {
  source: string;
  target: string;
  type: string;
  strength: number;
}

export interface ReplayFrame {
  date: string;
  label: string;
  dominantNarrative: string;
  stage: string;
  strength: number;
  sentiment: number;
  activeNarratives: Array<{ topic: string; strength: number; stage: string }>;
}

export interface QualityRow {
  dataset: string;
  record_count: number;
  completeness: number;
  uniqueness: number;
  consistency: number;
  timeliness: number;
  quality_score: number;
}

export interface IntelligenceFeedItem {
  title: string;
  body: string;
  severity: "High" | "Medium" | "Low";
}

export interface NarrativeMart {
  generatedAt: string;
  historicalThrough: string;
  /** Present only when the mart was synthesised from live sources via /topic-intelligence/live-mart */
  liveMode?: boolean;
  liveQuery?: string;
  liveSourceMode?: "live_ingestion" | "warehouse_match" | "prospective_brief";
  /** Present when the mart was generated with a --dataset-name argument. */
  datasetName?: string;
  datasetSlug?: string;
  overview: Overview;
  warehouseStats: {
    dimensions: Record<string, number>;
    facts: Record<string, number>;
    source_mix?: Record<string, number>;
  };
  events: EventSummary[];
  narratives: NarrativeSummary[];
  topGrowingTopics: GrowingTopic[];
  entities: EntitySummary[];
  sentimentTimeline: SentimentTimelinePoint[];
  predictions: Prediction[];
  graph: {
    nodes: GraphNode[];
    links: GraphLink[];
  };
  replayFrames: ReplayFrame[];
  dataQuality: QualityRow[];
  intelligenceFeed: IntelligenceFeedItem[];
  reportSummary: {
    title: string;
    eventFocus: string;
    period: string;
    primaryFinding: string;
    recommendedDemoFlow: string[];
  };
}

export interface DatasetMeta {
  slug: string;
  name: string;
  filename: string;
  generatedAt: string;
  totalRecords: number;
  sizeBytes: number;
}

export interface CsvUploadResult {
  status: "created";
  datasetName: string;
  datasetSlug: string;
  filename: string;
  records: number;
  qualityScore: number;
  martPath: string;
}

export interface AdminStatus {
  generatedAt: string;
  historicalThrough: string;
  records: number;
  warehouseQualityScore: number;
  warehouseStats: {
    dimensions: Record<string, number>;
    facts: Record<string, number>;
    source_mix?: Record<string, number>;
  };
  warehouseFiles: {
    exists: boolean;
    totalBytes: number;
    files: Array<{ name: string; bytes: number }>;
  };
  postgresConfigured: boolean;
  databaseHint: string;
}

export interface AdminCommandResult {
  status: "completed" | "failed";
  postgresConfigured?: boolean;
  records?: number;
  generatedAt?: string;
  warehouseQualityScore?: number;
  result: {
    command: string[];
    returnCode: number;
    durationSeconds: number;
    stdout: string;
    stderr: string;
  };
}

export interface AdminAuditEntry {
  id: string;
  timestamp: string;
  action: string;
  status: string;
  summary: string;
  details: Record<string, unknown>;
}

export interface AdminAuditResponse {
  logPath: string;
  entries: AdminAuditEntry[];
}

export interface SourcePackImportResult {
  status: "imported";
  importId: string;
  name: string;
  sourceType: string;
  rowCount: number;
  artifactPath: string;
  auditId: string;
}

export interface SavedTopicSnapshot {
  snapshotKey: number;
  topicKey: number;
  topicName: string;
  canonicalTitle: string;
  measuredAt: string;
  mode: string;
  confidence: number;
  narrativeStrength: number;
  influenceScore: number;
  sentimentLabel: SentimentLabel;
  lifecycleStage: string;
  totalSignals: number;
  newsSignals: number;
  referenceSignals: number;
  sourceClusters: number;
  sourcesSaved: number;
  summary: string;
}

export interface SavedTopicResponse {
  postgresConfigured: boolean;
  snapshots: SavedTopicSnapshot[];
}

export interface SavedTopicDetail {
  snapshot: SavedTopicSnapshot & {
    sourceNote: string;
  };
  brief: TopicIntelligence;
  sources: Array<{
    type: string;
    title: string;
    url?: string | null;
    domain?: string | null;
    publishedAt?: string | null;
  }>;
}

export interface ReportExportResult {
  status: "generated" | "failed";
  htmlPath: string;
  pdfPath: string;
  pdfBytes: number;
  downloadUrl: string;
  htmlUrl: string;
  result?: {
    command: string[];
    returnCode: number;
    durationSeconds: number;
    stdout: string;
    stderr: string;
  };
}

export interface TopicIntelligence {
  query: string;
  mode: "live_ingestion" | "warehouse_match" | "prospective_brief";
  generatedAt: string;
  summary: string;
  sourceNote: string;
  confidence: number;
  event: EventSummary;
  influenceScore: number;
  narrativeStrength: number;
  sentimentScore: number;
  sentimentLabel: SentimentLabel;
  lifecycleStage: string;
  narratives: NarrativeSummary[];
  entities: EntitySummary[];
  sentimentDistribution: Array<SentimentDistribution & { share: number }>;
  timeline: Array<{ month: string; strength: number; influence: number; sentiment: number }>;
  evidence?: {
    totalSignals: number;
    newsSignals: number;
    referenceSignals: number;
    sourceClusters: number;
  };
  sources?: Array<{
    type: string;
    title: string;
    url?: string | null;
    domain?: string | null;
    publishedAt?: string | null;
  }>;
  relatedTopics: string[];
  recommendedActions: string[];
}

export interface EnrichmentResult {
  status: "ok" | "error";
  enriched: number;
  skipped: number;
  errors: number;
  outputDir: string;
  message?: string;
}

export interface IngestionScheduleStatus {
  enabled: boolean;
  intervalMinutes: number;
  topics: string[];
  lastRunAt: string | null;
  nextRunAt: string | null;
  runCount: number;
}

