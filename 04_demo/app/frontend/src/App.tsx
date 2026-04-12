import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import {
  CheckCircle2,
  CircleAlert,
  Download,
  FileDown,
  FileUp,
  FlaskConical,
  LoaderCircle,
  MessageSquareMore,
  Play,
  Printer,
  SendHorizonal,
  Sparkles,
  TestTubeDiagonal,
  Upload,
  X,
} from "lucide-react";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Textarea } from "./components/ui/textarea";
import {
  askRunChat,
  approveRun,
  buildRunPdfUrl,
  createRun,
  downloadRunPdf,
  dropRun,
  reviewRun,
  updateRunReportPayload,
  uploadReport,
} from "./lib/api";
import type {
  EvidenceSourceSummary,
  ReportDraftUpdatePayload,
  ReportKind,
  RunChatCitation,
  RunResponse,
  UploadedReport,
} from "./lib/backend";
import { cn } from "./lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./components/ui/dialog";

const starterPrompts = [
  "Summarize the pathogenic findings",
  "Why was this case escalated?",
  "What evidence supports this report?",
];

const pipelineSteps = [
  {
    id: "upload",
    title: "Upload report",
    body: "Store the PDF and validate the report kind.",
  },
  {
    id: "extract",
    title: "Extract structured fields",
    body: "Pull the case summary and variant payload into a normalized shape.",
  },
  {
    id: "evidence",
    title: "Query evidence services",
    body: "Call the live ClinVar, VEP, and SpliceAI endpoints for the demo case.",
  },
  {
    id: "review",
    title: "Prepare clinician lane",
    body: "Assemble the review draft, evidence rail, and final approval actions.",
  },
] as const;

type ChatMessage = {
  role: "assistant" | "user";
  text: string;
  citations?: RunChatCitation[];
  grounded?: boolean;
  error?: boolean;
};

type PipelineMode = "idle" | "uploading" | "creating_run" | "ready" | "error";

type ActionMode =
  | "idle"
  | "approving"
  | "dropping"
  | "downloading_pdf"
  | "saving_draft";

type SessionRun = {
  slotLabel: string;
  run: RunResponse;
  upload: UploadedReport;
};

type EvidenceCard = {
  id: string;
  title: string;
  body?: string;
  badge?: string;
  badgeVariant?: "default" | "success" | "warning" | "danger";
  scoreLabel?: string;
  subLabel?: string;
  progress?: number;
  warnings: string[];
};

const EDITOR_FIELDS: Array<{
  key: keyof Omit<ReportDraftUpdatePayload, "review_note">;
  label: string;
}> = [
  { key: "patient_context", label: "Patient & Referral Context" },
  { key: "clinical_phenotype", label: "Relevant Clinical Findings" },
  { key: "ai_clinical_summary", label: "Genomic Finding Summary" },
  { key: "expanded_evidence", label: "Evidence Snapshot" },
  { key: "acmg_classification", label: "Classification Snapshot" },
  { key: "clinical_integration", label: "Interpretation for This Patient" },
  { key: "expected_symptoms", label: "Gene-/Disease-Associated Features Reference" },
  { key: "recommendations", label: "Recommended Next Steps" },
  { key: "limitations", label: "Limitations & Uncertainty" },
];

const surfaceReveal: Variants = {
  hidden: { opacity: 0, y: 18 },
  show: (delay = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.48, ease: "easeOut", delay },
  }),
};

export default function App() {
  const [sessionRuns, setSessionRuns] = useState<SessionRun[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<string | null>(null);
  const [reportKind] = useState<ReportKind>("test");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [pipelineMode, setPipelineMode] = useState<PipelineMode>("idle");
  const [actionMode, setActionMode] = useState<ActionMode>("idle");
  const [uiError, setUiError] = useState<string | null>(null);
  const [noteDrafts, setNoteDrafts] = useState<Record<string, string>>({});
  const [editorOpen, setEditorOpen] = useState(false);
  const [reportDraft, setReportDraft] =
    useState<ReportDraftUpdatePayload | null>(null);
  const [previewVersion, setPreviewVersion] = useState<number>(0);
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessagesByRun, setChatMessagesByRun] = useState<
    Record<string, ChatMessage[]>
  >({});
  const [chatSending, setChatSending] = useState(false);
  const [autoOpenedRuns, setAutoOpenedRuns] = useState<Record<string, true>>(
    {},
  );
  const fileInputRef = useRef<HTMLInputElement>(null);

  const activeSession =
    sessionRuns.find((item) => item.run.run_id === selectedRunId) ??
    sessionRuns[0] ??
    null;
  const evidenceCards = activeSession
    ? buildEvidenceCards(activeSession.run.evidence)
    : [];
  const activeEvidenceId =
    selectedEvidence &&
    evidenceCards.some((card) => card.id === selectedEvidence)
      ? selectedEvidence
      : (evidenceCards[0]?.id ?? null);
  const selectedEvidenceCard =
    evidenceCards.find((card) => card.id === activeEvidenceId) ??
    evidenceCards[0] ??
    null;
  const noteValue = activeSession
    ? (noteDrafts[activeSession.run.run_id] ??
      activeSession.run.review_note ??
      "")
    : "";
  const isWorking =
    pipelineMode === "uploading" || pipelineMode === "creating_run";
  const chatAvailable =
    activeSession?.run.run_status === "completed" ||
    activeSession?.run.run_status === "degraded";
  const messages = activeSession
    ? (chatMessagesByRun[activeSession.run.run_id] ?? [
        buildStarterMessage(activeSession),
      ])
    : [];

  useEffect(() => {
    if (!selectedRunId && sessionRuns.length > 0) {
      setSelectedRunId(sessionRuns[0].run.run_id);
    }
  }, [selectedRunId, sessionRuns]);

  useEffect(() => {
    if (!activeSession || !chatAvailable) {
      setChatOpen(false);
      return;
    }
    if (autoOpenedRuns[activeSession.run.run_id]) {
      return;
    }
    setChatMessagesByRun((current) => ({
      ...current,
      [activeSession.run.run_id]: current[activeSession.run.run_id] ?? [
        buildStarterMessage(activeSession),
      ],
    }));
    setChatOpen(true);
    setAutoOpenedRuns((current) => ({
      ...current,
      [activeSession.run.run_id]: true,
    }));
  }, [activeSession, autoOpenedRuns, chatAvailable]);

  const caseReference = activeSession
    ? formatCaseReference(activeSession.run.patient_id)
    : "Awaiting run";
  const reportDate = activeSession
    ? formatDate(activeSession.upload.created_at)
    : "Not yet generated";
  const reportTitle =
    activeSession?.upload.extracted_case.report_title ||
    "Whole Exome Sequencing Report";
  const executiveSummary = activeSession
    ? activeSession.run.report_payload.ai_clinical_summary ||
      activeSession.upload.extracted_case.summary ||
      activeSession.run.report_payload.clinical_phenotype ||
      "No summary is available for the selected run yet."
    : "Upload a genomic report to create a review-ready case workspace populated by the backend pipeline.";
  const summaryHighlight =
    activeSession?.run.report_payload.variant_summary_rows[0]?.gene ||
    activeSession?.upload.extracted_case.variants[0]?.gene ||
    null;
  const variantRows = activeSession ? buildVariantRows(activeSession) : [];
  const totalReportCount = sessionRuns.length;
  const tabsToRender = sessionRuns.slice(0, 3);
  const overflowCount = Math.max(sessionRuns.length - tabsToRender.length, 0);
  const statusMessage = getStatusMessage({
    pipelineMode,
    activeSession,
    pendingFile,
    uiError,
  });
  const isApproved = activeSession?.run.review_status === "approved";
  const isDropped = activeSession?.run.review_status === "dropped";
  const previewPdfUrl = activeSession
    ? buildRunPdfUrl(activeSession.run.run_id, previewVersion)
    : null;

  async function handleRunPipeline() {
    if (!pendingFile) {
      setUiError("Choose a PDF report before running the pipeline.");
      fileInputRef.current?.focus();
      return;
    }

    setUiError(null);
    setPipelineMode("uploading");

    try {
      const uploaded = await uploadReport(pendingFile, reportKind);
      const patientId = buildPatientId(uploaded.report.report_id);
      setPipelineMode("creating_run");

      const run = await createRun({
        patient_id: patientId,
        report_ids: [uploaded.report.report_id],
      });

      const nextSession: SessionRun = {
        slotLabel: String(sessionRuns.length + 1).padStart(2, "0"),
        run,
        upload: uploaded.report,
      };

      setSessionRuns((current) => [nextSession, ...current]);
      setSelectedRunId(run.run_id);
      setNoteDrafts((current) => ({
        ...current,
        [run.run_id]: run.review_note ?? "",
      }));
      if (run.run_status === "completed" || run.run_status === "degraded") {
        setChatMessagesByRun((current) => ({
          ...current,
          [run.run_id]: [buildStarterMessage(nextSession)],
        }));
        setChatOpen(true);
        setAutoOpenedRuns((current) => ({
          ...current,
          [run.run_id]: true,
        }));
      }
      setPendingFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setPipelineMode("ready");
    } catch (error) {
      setPipelineMode("error");
      setUiError(getErrorMessage(error));
    }
  }

  async function handleApprove() {
    if (!activeSession || actionMode !== "idle" || isApproved || isDropped) {
      return;
    }

    setUiError(null);
    setActionMode("approving");

    try {
      let nextRun = activeSession.run;

      if (
        noteValue.trim() &&
        activeSession.run.review_status === "pending_review"
      ) {
        const reviewResult = await reviewRun(activeSession.run.run_id, {
          reviewer_name: "Clinician workspace",
          review_note: noteValue.trim(),
        });

        nextRun = {
          ...nextRun,
          review_status: reviewResult.review_status,
          review_note: reviewResult.review_note,
          reviewed_at: reviewResult.reviewed_at,
        };
      }

      const approveResult = await approveRun(activeSession.run.run_id);

      updateSessionRun(activeSession.run.run_id, (current) => ({
        ...nextRun,
        ...current,
        review_status: approveResult.review_status,
        review_note: approveResult.review_note ?? nextRun.review_note,
        reviewed_at: approveResult.reviewed_at ?? nextRun.reviewed_at,
        approved_pdf_path: approveResult.download_path,
      }));
    } catch (error) {
      setUiError(getErrorMessage(error));
    } finally {
      setActionMode("idle");
    }
  }

  async function handleDrop() {
    if (!activeSession || actionMode !== "idle" || isApproved || isDropped) {
      return;
    }

    setUiError(null);
    setActionMode("dropping");

    try {
      const dropResult = await dropRun(
        activeSession.run.run_id,
        noteValue.trim() || undefined,
      );
      updateSessionRun(activeSession.run.run_id, (current) => ({
        ...current,
        review_status: dropResult.review_status,
        review_note: dropResult.review_note ?? current.review_note,
        reviewed_at: dropResult.reviewed_at ?? current.reviewed_at,
      }));
    } catch (error) {
      setUiError(getErrorMessage(error));
    } finally {
      setActionMode("idle");
    }
  }

  async function handleDownloadPdf() {
    if (!activeSession || !isApproved || actionMode !== "idle") {
      return;
    }

    setUiError(null);
    setActionMode("downloading_pdf");

    try {
      const blob = await downloadRunPdf(activeSession.run.run_id);
      const blobUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = blobUrl;
      anchor.download = `${formatCaseReference(activeSession.run.patient_id).toLowerCase()}-approved-report.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      setUiError(getErrorMessage(error));
    } finally {
      setActionMode("idle");
    }
  }

  function openEditor() {
    if (!activeSession || isApproved || isDropped) {
      return;
    }

    setReportDraft({
      patient_context: activeSession.run.report_payload.patient_context ?? "",
      clinical_phenotype:
        activeSession.run.report_payload.clinical_phenotype ?? "",
      ai_clinical_summary:
        activeSession.run.report_payload.ai_clinical_summary ?? "",
      expanded_evidence:
        activeSession.run.report_payload.expanded_evidence ?? "",
      acmg_classification:
        activeSession.run.report_payload.acmg_classification ?? "",
      clinical_integration:
        activeSession.run.report_payload.clinical_integration ?? "",
      expected_symptoms:
        activeSession.run.report_payload.expected_symptoms ?? "",
      recommendations: activeSession.run.report_payload.recommendations ?? "",
      limitations: activeSession.run.report_payload.limitations ?? "",
      review_note: noteValue,
    });
    setPreviewVersion(Date.now());
    setEditorOpen(true);
  }

  function updateDraftField(
    field: keyof ReportDraftUpdatePayload,
    value: string,
  ) {
    setReportDraft((current) => ({
      ...(current ?? {}),
      [field]: value,
    }));
  }

  async function handleSaveDraft() {
    if (!activeSession || !reportDraft || actionMode !== "idle") {
      return;
    }

    setUiError(null);
    setActionMode("saving_draft");

    try {
      const updatedRun = await updateRunReportPayload(
        activeSession.run.run_id,
        reportDraft,
      );
      updateSessionRun(activeSession.run.run_id, () => updatedRun);
      setNoteDrafts((current) => ({
        ...current,
        [activeSession.run.run_id]: updatedRun.review_note ?? "",
      }));
      setReportDraft({
        patient_context: updatedRun.report_payload.patient_context ?? "",
        clinical_phenotype: updatedRun.report_payload.clinical_phenotype ?? "",
        ai_clinical_summary:
          updatedRun.report_payload.ai_clinical_summary ?? "",
        expanded_evidence: updatedRun.report_payload.expanded_evidence ?? "",
        acmg_classification:
          updatedRun.report_payload.acmg_classification ?? "",
        clinical_integration:
          updatedRun.report_payload.clinical_integration ?? "",
        expected_symptoms: updatedRun.report_payload.expected_symptoms ?? "",
        recommendations: updatedRun.report_payload.recommendations ?? "",
        limitations: updatedRun.report_payload.limitations ?? "",
        review_note: updatedRun.review_note ?? "",
      });
      setPreviewVersion(Date.now());
    } catch (error) {
      setUiError(getErrorMessage(error));
    } finally {
      setActionMode("idle");
    }
  }

  function updateSessionRun(
    runId: string,
    updater: (run: RunResponse) => RunResponse,
  ) {
    setSessionRuns((current) =>
      current.map((item) =>
        item.run.run_id === runId
          ? {
              ...item,
              run: updater(item.run),
            }
          : item,
      ),
    );
  }

  function handleNoteChange(value: string) {
    if (!activeSession) {
      return;
    }

    setNoteDrafts((current) => ({
      ...current,
      [activeSession.run.run_id]: value,
    }));
  }

  function handleChooseFile() {
    fileInputRef.current?.click();
  }

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;

    if (!activeSession || !chatAvailable || chatSending) {
      return;
    }

    setChatMessagesByRun((current) => ({
      ...current,
      [activeSession.run.run_id]: [
        ...(current[activeSession.run.run_id] ?? [
          buildStarterMessage(activeSession),
        ]),
        { role: "user", text: trimmed },
      ],
    }));
    setChatInput("");
    setChatOpen(true);
    setChatSending(true);

    try {
      const response = await askRunChat(activeSession.run.run_id, {
        question: trimmed,
      });
      setChatMessagesByRun((current) => ({
        ...current,
        [activeSession.run.run_id]: [
          ...(current[activeSession.run.run_id] ?? [
            buildStarterMessage(activeSession),
          ]),
          {
            role: "assistant",
            text: response.answer,
            citations: response.citations,
            grounded: response.grounded,
          },
        ],
      }));
    } catch (error) {
      setChatMessagesByRun((current) => ({
        ...current,
        [activeSession.run.run_id]: [
          ...(current[activeSession.run.run_id] ?? [
            buildStarterMessage(activeSession),
          ]),
          {
            role: "assistant",
            text: getErrorMessage(error),
            grounded: false,
            error: true,
          },
        ],
      }));
    } finally {
      setChatSending(false);
    }
  }

  return (
    <div className="min-h-screen bg-[color:var(--canvas)] text-[color:var(--ink)]">
      <motion.header
        className="sticky top-0 z-30 border-b border-[color:var(--line)]/85 bg-white/90 backdrop-blur-2xl"
        initial="hidden"
        animate="show"
        variants={surfaceReveal}
        custom={0}
      >
        <div className="mx-auto flex max-w-[1840px] flex-col gap-4 px-5 py-4 sm:px-8 xl:flex-row xl:items-center xl:justify-between xl:px-10 xl:py-5">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:gap-6">
            <div className="flex items-center gap-4">
              <div className="grid h-12 w-12 place-items-center overflow-hidden rounded-[18px] border border-[color:var(--line)] bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(244,248,249,0.92))] shadow-[0_12px_28px_rgba(31,47,56,0.06)]">
                <img
                  src="/favicon.svg"
                  alt=""
                  className="block h-6 w-6 shrink-0 object-contain scale-[1.22] translate-x-[1.5px] -translate-y-[0.75px]"
                />
              </div>
              <div className="text-[30px] font-semibold tracking-[-0.055em] text-[color:var(--ink)]">
                magicgene
              </div>
            </div>

            <nav className="flex flex-wrap items-center gap-3 text-[12px] font-semibold text-[color:var(--muted-ink)]">
              <motion.div
                whileHover={{ y: -1 }}
                className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/80 px-4 py-2 shadow-[0_8px_18px_rgba(31,47,56,0.04)]"
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[color:var(--muted)]">
                  Batch status
                </span>
                <span className="text-[color:var(--teal)]">Active</span>
              </motion.div>
              <motion.div
                key={caseReference}
                initial={{ opacity: 0.65, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.22 }}
                className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line)] bg-white/80 px-4 py-2 shadow-[0_8px_18px_rgba(31,47,56,0.04)]"
              >
                <span className="text-[10px] uppercase tracking-[0.18em] text-[color:var(--muted)]">
                  Selected
                </span>
                <span>{caseReference}</span>
              </motion.div>
            </nav>
          </div>

          <motion.div
            whileHover={{ y: -1 }}
            className="hidden items-center gap-3 rounded-full border border-[color:var(--line)] bg-white/84 px-4 py-2.5 text-[12px] font-semibold text-[color:var(--muted-ink)] shadow-[0_8px_18px_rgba(31,47,56,0.04)] md:inline-flex"
          >
            <Sparkles className="h-3.5 w-3.5 text-[color:var(--teal)]" />
            {activeSession
              ? formatReviewLabel(activeSession.run.review_status)
              : "Review lane waiting"}
          </motion.div>
        </div>
      </motion.header>

      <motion.section
        className="border-b border-[color:var(--line)] bg-[color:var(--wash)]/88"
        initial="hidden"
        animate="show"
        variants={surfaceReveal}
        custom={0.06}
      >
        <div className="mx-auto grid max-w-[1840px] gap-6 px-5 py-6 sm:px-8 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.9fr)_220px] xl:items-center xl:gap-8 xl:px-10 xl:py-7">
          <div>
            <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.2em] text-[color:var(--muted-ink)]">
              Submit reports
            </p>

            <div className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="sr-only"
                  onChange={(event) => {
                    setPendingFile(event.target.files?.[0] ?? null);
                    setUiError(null);
                  }}
                />

                <motion.button
                  type="button"
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={handleChooseFile}
                  className="inline-flex h-12 items-center gap-3 rounded-[18px] border border-[color:var(--line-strong)] bg-white/90 px-5 text-[15px] font-semibold text-[color:var(--ink)] shadow-[0_10px_24px_rgba(31,47,56,0.05)] backdrop-blur-sm transition-colors hover:border-[color:var(--teal-soft)] hover:bg-white"
                >
                  <FileUp
                    className="h-4 w-4 text-[color:var(--teal)]"
                    strokeWidth={2.1}
                  />
                  {pendingFile ? "Replace PDF" : "Choose PDF"}
                </motion.button>

                {tabsToRender.length ? (
                  <Tabs
                    value={selectedRunId ?? tabsToRender[0].run.run_id}
                    onValueChange={setSelectedRunId}
                  >
                    <TabsList className="flex-wrap">
                      {tabsToRender.map((item) => (
                        <motion.div
                          key={item.run.run_id}
                          whileHover={{ y: -2 }}
                        >
                          <TabsTrigger value={item.run.run_id}>
                            {item.slotLabel}
                          </TabsTrigger>
                        </motion.div>
                      ))}
                      {overflowCount > 0 ? (
                        <motion.div whileHover={{ y: -2 }}>
                          <TabsTrigger
                            value={selectedRunId ?? tabsToRender[0].run.run_id}
                            className="border-dashed text-[color:var(--muted-ink)]"
                          >
                            +{overflowCount}
                          </TabsTrigger>
                        </motion.div>
                      ) : null}
                    </TabsList>
                  </Tabs>
                ) : null}
              </div>

              <motion.p
                key={`${pendingFile?.name ?? "none"}-${totalReportCount}`}
                initial={{ opacity: 0.5, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.22 }}
                className="text-[15px] leading-6 text-[color:var(--muted-ink)]"
              >
                {pendingFile
                  ? `${pendingFile.name} ready for ${reportKind} processing`
                  : totalReportCount > 0
                    ? `${totalReportCount} reports created in this session`
                    : "Choose a PDF report to start the demo pipeline"}
              </motion.p>
            </div>
          </div>

          <div className="xl:border-l xl:border-[color:var(--line)] xl:pl-8">
            <motion.div
              whileHover={{ y: -2 }}
              className="inline-flex items-center gap-4 rounded-[20px] border border-[color:var(--line)] bg-white/92 px-5 py-4 shadow-[0_12px_28px_rgba(31,47,56,0.05)] backdrop-blur-sm"
            >
              <FlaskConical
                className="h-5 w-5 text-[color:var(--teal)]"
                strokeWidth={1.8}
              />
              <span className="text-[14px] leading-6 font-medium text-[color:var(--ink)]">
                {statusMessage}
              </span>
            </motion.div>
          </div>

          <div className="flex justify-end">
            <Button
              size="lg"
              className="min-w-[210px] rounded-[18px] text-[16px] tracking-[-0.02em]"
              onClick={handleRunPipeline}
              disabled={!pendingFile || isWorking}
            >
              {isWorking ? (
                <LoaderCircle
                  className="h-4 w-4 animate-spin"
                  strokeWidth={2.2}
                />
              ) : (
                <Play
                  className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5"
                  strokeWidth={2.2}
                />
              )}
              {pipelineMode === "creating_run"
                ? "Creating run"
                : isWorking
                  ? "Uploading report"
                  : "Run pipeline"}
            </Button>
          </div>
        </div>
      </motion.section>

      <div className="mx-auto max-w-[1840px] px-5 pb-8 pt-6 sm:px-6 xl:px-8 xl:pb-10 xl:pt-7">
        <motion.main
          className="overflow-visible rounded-[30px] border-0 bg-transparent shadow-none"
          initial="hidden"
          animate="show"
          variants={surfaceReveal}
          custom={0.12}
        >
          <div className="grid 2xl:grid-cols-[minmax(0,1fr)_420px]">
            <section className="relative px-7 py-9 sm:px-10 xl:px-12 xl:py-11">
              <div className="pointer-events-none absolute inset-x-0 top-0 h-28 " />

              <div
                className={cn(
                  "relative mb-8 flex flex-col gap-5 xl:mb-10 xl:flex-row xl:items-start xl:justify-between",
                  !activeSession &&
                    "rounded-[24px] border border-[color:var(--line)]/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(244,249,250,0.92))] px-7 py-7 shadow-[0_14px_34px_rgba(31,47,56,0.04)]",
                )}
              >
                <div>
                  <h1 className="text-[32px] font-semibold tracking-[-0.055em] sm:text-[36px] xl:text-[40px]">
                    {activeSession ? "Selected report" : "Submit report"}
                  </h1>
                  <motion.p
                    key={caseReference}
                    initial={{ opacity: 0.6, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.22 }}
                    className="mt-3 max-w-3xl text-[15px] leading-7 text-[color:var(--muted-ink)] xl:text-[16px]"
                  >
                    {activeSession ? (
                      <>
                        Internal Case Reference:{" "}
                        <span className="font-medium text-[color:var(--teal)]">
                          #{caseReference}
                        </span>
                      </>
                    ) : (
                      "This workspace becomes the clinician review lane after the backend completes the run."
                    )}
                  </motion.p>
                </div>

                {activeSession ? (
                  <div className="flex items-center gap-3 pt-0 text-[color:var(--muted-ink)] xl:pt-2">
                    <ActionIcon
                      label="Print report"
                      icon={Printer}
                      disabled={!isApproved}
                      onClick={handleDownloadPdf}
                    />
                    <ActionIcon
                      label="Download report"
                      icon={Download}
                      disabled={!isApproved}
                      onClick={handleDownloadPdf}
                    />
                  </div>
                ) : null}
              </div>

              <motion.section
                layout
                className="rounded-[28px] border border-[color:var(--line)]/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(246,250,251,0.92))] px-7 py-8 shadow-[0_18px_44px_rgba(31,47,56,0.05)] backdrop-blur-sm sm:px-8 xl:px-10 xl:py-9"
              >
                <div className="mb-8 flex flex-col gap-6 xl:mb-9 xl:flex-row xl:items-start xl:justify-between">
                  <div className="max-w-4xl">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[color:var(--teal)]">
                      {activeSession
                        ? "Genomic referral support"
                        : "Pipeline intake"}
                    </p>
                    <h2 className="mt-4 max-w-[760px] text-[38px] leading-[1] font-semibold tracking-[-0.055em] sm:text-[42px] xl:text-[48px]">
                      {activeSession
                        ? reportTitle
                        : "Upload a report and let the backend populate this review surface"}
                    </h2>
                  </div>

                  <div className="rounded-[20px] border border-[color:var(--line)] bg-[color:var(--teal-ghost)] px-5 py-4 text-left xl:min-w-[180px] xl:text-right">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                      {activeSession ? "Report date" : "Current state"}
                    </p>
                    <AnimatePresence mode="wait">
                      <motion.p
                        key={reportDate}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.24 }}
                        className="mt-2 text-[26px] font-semibold tracking-[-0.04em] text-[color:var(--ink)] xl:text-[30px]"
                      >
                        {activeSession
                          ? reportDate
                          : formatPipelineMode(pipelineMode)}
                      </motion.p>
                    </AnimatePresence>
                  </div>
                </div>

                {activeSession ? (
                  <>
                    <div className="grid gap-8 md:grid-cols-3 md:gap-10">
                      <Detail
                        label="Case ID"
                        value={formatCaseReference(
                          activeSession.run.patient_id,
                        )}
                      />
                      <Detail label="Age" value="Not provided" />
                      <Detail label="Sex" value="Not provided" />
                    </div>

                    <motion.section
                      whileHover={{ y: -2 }}
                      className="mt-12 grid gap-6 border-y border-[color:var(--line)]/90 py-8 xl:grid-cols-[180px_minmax(0,1fr)] xl:gap-8"
                    >
                      <div>
                        <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[color:var(--muted-ink)]">
                          Executive summary
                        </p>
                      </div>
                      <AnimatePresence mode="wait">
                        <motion.p
                          key={executiveSummary}
                          initial={{ opacity: 0, y: 8 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -8 }}
                          transition={{ duration: 0.24 }}
                          className="max-w-5xl text-[17px] leading-8 text-[color:var(--muted-ink)] xl:text-[18px] xl:leading-9"
                        >
                          {renderSummary(executiveSummary, summaryHighlight)}
                        </motion.p>
                      </AnimatePresence>
                    </motion.section>

                    <section className="mt-10">
                      <div className="hidden grid-cols-[1fr_2.2fr_1.5fr_1.4fr] border-b border-[color:var(--line)] pb-4 text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)] lg:grid">
                        <span>Gene</span>
                        <span>Variant</span>
                        <span>Genomic locus</span>
                        <span>Classification</span>
                      </div>

                      <div className="divide-y divide-[color:var(--line)]/90">
                        <AnimatePresence mode="popLayout">
                          {variantRows.map((item, index) => (
                            <motion.div
                              key={`${activeSession.run.run_id}-${item.gene}-${item.variant}`}
                              layout
                              initial={{ opacity: 0, y: 8 }}
                              animate={{ opacity: 1, y: 0 }}
                              exit={{ opacity: 0, y: -8 }}
                              transition={{
                                duration: 0.22,
                                delay: index * 0.03,
                              }}
                            >
                              <motion.div
                                whileHover={{
                                  backgroundColor: "rgba(255,255,255,0.72)",
                                }}
                                className="hidden grid-cols-[1fr_2.2fr_1.5fr_1.4fr] items-center rounded-2xl px-1 py-7 lg:grid"
                              >
                                <span className="text-[30px] font-semibold tracking-[-0.045em] text-[color:var(--teal)]">
                                  {item.gene}
                                </span>
                                <span className="text-[18px] tracking-[-0.02em]">
                                  {item.variant}
                                </span>
                                <span className="text-[18px] tracking-[-0.02em] text-[color:var(--muted-ink)]">
                                  {item.genomicLocus}
                                </span>
                                <Badge
                                  variant={item.classificationVariant}
                                  className="w-fit text-sm tracking-[0.08em]"
                                >
                                  {item.classification}
                                </Badge>
                              </motion.div>

                              <motion.div
                                whileHover={{ y: -2 }}
                                className="space-y-3 py-5 lg:hidden"
                              >
                                <div className="flex items-center justify-between gap-4">
                                  <span className="text-[24px] font-semibold tracking-[-0.04em] text-[color:var(--teal)]">
                                    {item.gene}
                                  </span>
                                  <Badge
                                    variant={item.classificationVariant}
                                    className="w-fit text-xs tracking-[0.08em]"
                                  >
                                    {item.classification}
                                  </Badge>
                                </div>
                                <p className="text-base font-medium">
                                  {item.variant}
                                </p>
                                <p className="text-sm uppercase tracking-[0.12em] text-[color:var(--muted-ink)]">
                                  {item.genomicLocus}
                                </p>
                              </motion.div>
                            </motion.div>
                          ))}
                        </AnimatePresence>
                      </div>
                    </section>

                    <section className="mt-10 grid gap-6 border-t border-[color:var(--line)]/90 pt-8 xl:grid-cols-3 xl:gap-8">
                      <InlineNote
                        label="Clinical integration"
                        value={
                          activeSession.run.report_payload
                            .clinical_integration ||
                          "Awaiting clinician interpretation."
                        }
                      />
                      <InlineNote
                        label="Recommendations"
                        value={
                          activeSession.run.report_payload.recommendations ||
                          "No recommendation available."
                        }
                      />
                      <InlineNote
                        label="Limitations"
                        value={
                          activeSession.run.report_payload.limitations ||
                          "No limitations captured for this run."
                        }
                      />
                    </section>
                  </>
                ) : (
                  <section className="grid gap-8 xl:grid-cols-[minmax(0,1.12fr)_300px] xl:items-start">
                    <motion.div
                      whileHover={{ y: -2 }}
                      className="grid gap-6 rounded-[24px] border border-[color:var(--line)]/80 bg-white/82 px-6 py-6 shadow-[0_12px_30px_rgba(31,47,56,0.04)]"
                    >
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                          Intake briefing
                        </p>
                        <p className="mt-4 max-w-3xl text-[16px] leading-7 text-[color:var(--muted-ink)] xl:text-[16px] xl:leading-7">
                          Choose a genomic report PDF and run the demo pipeline.
                          The backend will upload the report, create a run, call
                          the live evidence services, and then populate this
                          review workspace with the completed result.
                        </p>
                      </div>

                      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                        <Button
                          variant="secondary"
                          size="lg"
                          className="h-12 justify-start rounded-[18px] text-[15px]"
                          onClick={handleChooseFile}
                        >
                          <Upload className="h-4 w-4" strokeWidth={2.1} />
                          {pendingFile ? pendingFile.name : "Select report PDF"}
                        </Button>
                        <Button
                          size="lg"
                          className="h-12 rounded-[18px] text-[15px]"
                          onClick={handleRunPipeline}
                          disabled={!pendingFile || isWorking}
                        >
                          {isWorking ? (
                            <LoaderCircle
                              className="h-4 w-4 animate-spin"
                              strokeWidth={2.1}
                            />
                          ) : (
                            <Play className="h-4 w-4" strokeWidth={2.1} />
                          )}
                          {isWorking ? "Running pipeline" : "Start review lane"}
                        </Button>
                      </div>

                      {uiError ? (
                        <div className="rounded-[22px] border border-[color:var(--danger-border)] bg-[color:var(--danger-faint)] px-5 py-4 text-sm text-[color:var(--danger)]">
                          {uiError}
                        </div>
                      ) : null}
                    </motion.div>

                    <div className="rounded-[24px] border border-[color:var(--line)]/80 bg-[linear-gradient(180deg,rgba(240,246,247,0.92),rgba(235,242,243,0.96))] px-6 py-6 shadow-[0_12px_30px_rgba(31,47,56,0.04)]">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                        Selected input
                      </p>
                      <div className="mt-5 space-y-4 text-sm text-[color:var(--muted-ink)]">
                        <div>
                          <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                            File
                          </span>
                          <span className="mt-2 block text-base text-[color:var(--ink)]">
                            {pendingFile ? pendingFile.name : "No file chosen"}
                          </span>
                        </div>
                        <div>
                          <span className="block text-[10px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                            Report kind
                          </span>
                          <span className="mt-2 block text-base text-[color:var(--ink)]">
                            {reportKind}
                          </span>
                        </div>
                      </div>
                    </div>
                  </section>
                )}
              </motion.section>
            </section>

            <aside className="bg-transparent px-6 py-8 sm:px-8 xl:px-9 xl:py-10">
              <div className="2xl:sticky 2xl:top-28">
                <div className="rounded-[24px] border border-[color:var(--line)]/80 bg-white/78 px-6 py-6 shadow-[0_14px_32px_rgba(31,47,56,0.05)] backdrop-blur-sm">
                  <div className="mb-6 flex items-center gap-3">
                    <TestTubeDiagonal
                      className="h-4.5 w-4.5 text-[color:var(--teal)]"
                      strokeWidth={1.8}
                    />
                    <h3 className="text-[20px] font-semibold tracking-[-0.03em] text-[color:var(--ink)] xl:text-[22px]">
                      {activeSession ? "Evidence" : "Pipeline"}
                    </h3>
                  </div>

                  {activeSession ? (
                    <div className="divide-y divide-[color:var(--line)]/80">
                      {evidenceCards.map((card, index) => {
                        const isSelectedCard =
                          selectedEvidenceCard?.id === card.id;
                        return (
                          <motion.button
                            key={card.id}
                            type="button"
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                              duration: 0.24,
                              delay: 0.1 + index * 0.04,
                            }}
                            whileHover={{ x: 2 }}
                            onMouseEnter={() => setSelectedEvidence(card.id)}
                            onFocus={() => setSelectedEvidence(card.id)}
                            className={cn(
                              "group w-full rounded-[20px] px-1 py-5 text-left transition-colors duration-200",
                              isSelectedCard
                                ? "text-[color:var(--ink)]"
                                : "text-[color:var(--muted-ink)]",
                            )}
                          >
                            <div className="flex items-start justify-between gap-4">
                              <div>
                                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                                  {card.title}
                                </p>
                                {card.body ? (
                                  <p className="mt-4 max-w-sm text-[16px] leading-8 text-[color:var(--ink)]">
                                    {card.body}
                                  </p>
                                ) : null}
                                {card.warnings.length ? (
                                  <div className="mt-3 flex flex-wrap gap-2">
                                    {card.warnings.map((warning) => (
                                      <Badge
                                        key={warning}
                                        variant="warning"
                                        className="tracking-[0.12em]"
                                      >
                                        {formatWarning(warning)}
                                      </Badge>
                                    ))}
                                  </div>
                                ) : null}
                              </div>

                              <div className="shrink-0 text-right">
                                {card.badge ? (
                                  <Badge variant={card.badgeVariant}>
                                    {card.badge}
                                  </Badge>
                                ) : null}
                                {card.scoreLabel ? (
                                  <>
                                    <p className="font-mono text-[18px] font-semibold uppercase text-[color:var(--teal)] xl:text-[20px]">
                                      {card.scoreLabel}
                                    </p>
                                    {card.subLabel ? (
                                      <p className="mt-2 text-sm text-[color:var(--muted-ink)]">
                                        {card.subLabel}
                                      </p>
                                    ) : null}
                                  </>
                                ) : null}
                              </div>
                            </div>

                            {typeof card.progress === "number" ? (
                              <div className="mt-6">
                                <div className="h-1.5 rounded-full bg-[color:var(--line)]">
                                  <motion.div
                                    className="h-1.5 rounded-full"
                                    initial={{ width: 0 }}
                                    animate={{
                                      width: `${Math.max(card.progress * 100, 8)}%`,
                                    }}
                                    transition={{
                                      duration: 0.8,
                                      ease: "easeOut",
                                      delay: 0.32,
                                    }}
                                    style={{
                                      background:
                                        "linear-gradient(90deg, var(--impact) 0%, #ca675f 100%)",
                                    }}
                                  />
                                </div>
                              </div>
                            ) : null}
                          </motion.button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="space-y-5">
                      {pipelineSteps.map((step, index) => {
                        const state = getPipelineStepState(
                          step.id,
                          pipelineMode,
                        );
                        return (
                          <motion.div
                            key={step.id}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{
                              duration: 0.24,
                              delay: 0.1 + index * 0.04,
                            }}
                            className="grid grid-cols-[auto_1fr] gap-4"
                          >
                            <div
                              className={cn(
                                "mt-1 h-3.5 w-3.5 rounded-full border",
                                pipelineDotClassName(state),
                              )}
                            />
                            <div>
                              <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-[color:var(--muted-ink)]">
                                {step.title}
                              </p>
                              <p className="mt-2.5 text-[14px] leading-6 text-[color:var(--ink)]">
                                {step.body}
                              </p>
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <motion.section
                  initial="hidden"
                  animate="show"
                  variants={surfaceReveal}
                  custom={0.22}
                  className="mt-6 rounded-[24px] border border-[color:var(--line)]/80 bg-white/72 px-6 py-6 shadow-[0_14px_32px_rgba(31,47,56,0.05)] backdrop-blur-sm"
                >
                  <div className="mb-6 flex items-center gap-3">
                    <CircleAlert
                      className="h-4.5 w-4.5 text-[color:var(--teal)]"
                      strokeWidth={1.8}
                    />
                    <h3 className="text-[20px] font-semibold tracking-[-0.03em] text-[color:var(--ink)] xl:text-[22px]">
                      Clinician review
                    </h3>
                  </div>

                  {activeSession ? (
                    <>
                      <Button
                        variant="secondary"
                        size="lg"
                        className="mb-4 h-[3.6rem] w-full justify-between rounded-[20px] text-base"
                        onClick={openEditor}
                        disabled={
                          isApproved || isDropped || actionMode !== "idle"
                        }
                      >
                        <span className="font-bold">Preview & Edit Report</span>
                      </Button>

                      <div className="mb-4 flex items-center justify-between gap-4">
                        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                          Internal notes
                        </p>
                        <div className="flex items-center gap-2">
                          {noteValue.length > 0 ? (
                            <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--teal)]">
                              {noteValue.length} chars
                            </span>
                          ) : null}
                          <Badge
                            variant={reviewBadgeVariant(
                              activeSession.run.review_status,
                            )}
                          >
                            {formatReviewLabel(activeSession.run.review_status)}
                          </Badge>
                        </div>
                      </div>

                      <Textarea
                        value={noteValue}
                        onChange={(event) =>
                          handleNoteChange(event.target.value)
                        }
                        placeholder="Provide clinical rationale for approval or dropping..."
                        className="bg-white/72"
                        disabled={
                          isApproved || isDropped || actionMode !== "idle"
                        }
                      />

                      <div className="mt-6 grid gap-4 sm:grid-cols-2">
                        <Button
                          variant="outline"
                          size="lg"
                          className="h-[4.25rem] rounded-[20px] text-[20px]"
                          onClick={handleDrop}
                          disabled={
                            isApproved || isDropped || actionMode !== "idle"
                          }
                        >
                          {actionMode === "dropping" ? (
                            <LoaderCircle className="h-5 w-5 animate-spin" />
                          ) : null}
                          Drop
                        </Button>
                        <Button
                          size="lg"
                          className="h-[4.25rem] rounded-[20px] text-[20px]"
                          onClick={handleApprove}
                          disabled={
                            isApproved || isDropped || actionMode !== "idle"
                          }
                        >
                          {actionMode === "approving" ? (
                            <LoaderCircle className="h-5 w-5 animate-spin" />
                          ) : (
                            <CheckCircle2
                              className="h-5 w-5 transition-transform duration-200 group-hover:rotate-6"
                              strokeWidth={2.1}
                            />
                          )}
                          {isApproved ? "Approved" : "Approve"}
                        </Button>
                      </div>

                      <motion.div
                        initial={false}
                        animate={{
                          opacity: isApproved ? 1 : 0.72,
                          y: isApproved ? 0 : 4,
                        }}
                        className="mt-4"
                      >
                        <Button
                          variant={isApproved ? "secondary" : "ghost"}
                          size="lg"
                          className={cn(
                            "h-[4rem] w-full justify-between rounded-[18px] px-5 text-base",
                            !isApproved && "pointer-events-none",
                          )}
                          onClick={handleDownloadPdf}
                          disabled={!isApproved || actionMode !== "idle"}
                        >
                          <span className="inline-flex items-center gap-3">
                            {actionMode === "downloading_pdf" ? (
                              <LoaderCircle
                                className="h-4.5 w-4.5 animate-spin"
                                strokeWidth={2}
                              />
                            ) : (
                              <FileDown
                                className="h-4.5 w-4.5"
                                strokeWidth={2}
                              />
                            )}
                            Download approved PDF
                          </span>
                          <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                            {isApproved ? "ready" : "approve first"}
                          </span>
                        </Button>
                      </motion.div>

                      {(activeSession.run.warnings.length ||
                        selectedEvidenceCard?.warnings.length) && (
                        <div className="mt-6 rounded-[22px] border border-[color:var(--line)] bg-white/52 px-4 py-4">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                            Runtime warnings
                          </p>
                          <div className="mt-3 flex flex-wrap gap-2">
                            {activeSession.run.warnings.map((warning) => (
                              <Badge key={warning} variant="warning">
                                {formatWarning(warning)}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="space-y-4">
                      <p className="text-sm leading-7 text-[color:var(--muted-ink)]">
                        The clinician note field, approval controls, and
                        approved PDF action appear here after a run completes.
                      </p>
                      <div className="rounded-2xl border border-dashed border-[color:var(--line-strong)] bg-white/24 px-4 py-4 text-sm text-[color:var(--muted-ink)]">
                        Review actions remain inactive until the backend returns
                        a completed run payload.
                      </div>
                    </div>
                  )}

                  {uiError ? (
                    <div className="mt-6 rounded-[20px] border border-[color:var(--danger-border)] bg-[color:var(--danger-faint)] px-4 py-4 text-sm text-[color:var(--danger)]">
                      {uiError}
                    </div>
                  ) : null}
                </motion.section>
              </div>
            </aside>
          </div>
        </motion.main>
      </div>

      <Dialog open={editorOpen} onOpenChange={setEditorOpen}>
        <DialogContent className="h-[min(92vh,960px)] max-h-[92vh] overflow-hidden p-0">
          {activeSession && reportDraft ? (
            <div className="grid h-full min-h-0 grid-cols-1 xl:grid-cols-[minmax(0,520px)_minmax(0,1fr)]">
              <div className="min-h-0 overflow-y-auto overscroll-contain border-b border-[color:var(--line)] bg-white/70 px-6 py-6 xl:border-b-0 xl:border-r xl:px-7 xl:py-7">
                <DialogHeader className="pr-14">
                  <DialogTitle>Preview & Edit Report</DialogTitle>
                  <DialogDescription>
                    Update the textual draft, save the run payload, and refresh
                    the preview before approval freezes the report.
                  </DialogDescription>
                </DialogHeader>

                <div className="mt-6 rounded-[24px] border border-[color:var(--line)] bg-[color:var(--summary-bg)]/75 px-4 py-4">
                  <div className="grid gap-4 text-sm text-[color:var(--muted-ink)] sm:grid-cols-2">
                    <ReadOnlyMeta
                      label="Case ID"
                      value={formatCaseReference(activeSession.run.patient_id)}
                    />
                    <ReadOnlyMeta
                      label="Review state"
                      value={formatReviewLabel(activeSession.run.review_status)}
                    />
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-[20px] border border-[color:var(--line)] bg-white/60 px-4 py-3">
                  <p className="max-w-sm text-sm leading-6 text-[color:var(--muted-ink)]">
                    Saved edits update the run payload used by preview,
                    approval, and final download.
                  </p>
                  <div className="flex gap-3">
                    <Button
                      variant="ghost"
                      onClick={() => setEditorOpen(false)}
                      disabled={actionMode !== "idle"}
                    >
                      Close
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={handleSaveDraft}
                      disabled={actionMode !== "idle"}
                    >
                      {actionMode === "saving_draft" ? (
                        <LoaderCircle className="h-4 w-4 animate-spin" />
                      ) : null}
                      Save Draft
                    </Button>
                  </div>
                </div>

                <div className="mt-6 space-y-5">
                  {EDITOR_FIELDS.map((field) => (
                    <div key={field.key}>
                      <label className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                        {field.label}
                      </label>
                      <Textarea
                        value={String(reportDraft[field.key] ?? "")}
                        onChange={(event) =>
                          updateDraftField(field.key, event.target.value)
                        }
                        className="mt-3 min-h-[132px] bg-white"
                        disabled={actionMode !== "idle"}
                      />
                    </div>
                  ))}

                  <div>
                    <label className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                      Clinician Note
                    </label>
                    <Textarea
                      value={String(reportDraft.review_note ?? "")}
                      onChange={(event) =>
                        updateDraftField("review_note", event.target.value)
                      }
                      className="mt-3 min-h-[140px] bg-white"
                      disabled={actionMode !== "idle"}
                    />
                  </div>

                  <div className="rounded-[24px] border border-[color:var(--line)] bg-white/52 px-4 py-4">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                      Variant Summary
                    </p>
                    <div className="mt-3 space-y-3">
                      {variantRows.map((item) => (
                        <div
                          key={`${item.gene}-${item.variant}`}
                          className="rounded-2xl border border-[color:var(--line)] bg-white/70 px-4 py-3"
                        >
                          <p className="text-sm font-semibold text-[color:var(--ink)]">
                            {item.gene}
                          </p>
                          <p className="mt-1 text-sm text-[color:var(--muted-ink)]">
                            {item.variant}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              </div>

              <div className="flex min-h-0 flex-col bg-[color:var(--wash)]/75">
                <div className="flex items-center justify-between gap-4 border-b border-[color:var(--line)] bg-white/65 px-5 py-4 backdrop-blur-sm">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
                      PDF Preview
                    </p>
                    <p className="mt-1 text-sm text-[color:var(--muted-ink)]">
                      Refreshes after each successful draft save.
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => setPreviewVersion(Date.now())}
                    disabled={actionMode !== "idle"}
                  >
                    <Download className="h-4 w-4" />
                    Refresh
                  </Button>
                </div>

                <div className="min-h-0 flex-1 p-4 xl:p-5">
                  <div className="h-full overflow-hidden rounded-[24px] border border-[color:var(--line)] bg-white shadow-[0_18px_50px_rgba(31,47,56,0.08)]">
                    {previewPdfUrl ? (
                      <object
                        key={previewPdfUrl}
                        data={previewPdfUrl}
                        type="application/pdf"
                        className="h-full min-h-[600px] w-full bg-white"
                        aria-label="Report PDF preview"
                      >
                        <div className="flex h-full min-h-[600px] flex-col items-center justify-center gap-4 bg-white px-8 text-center">
                          <p className="max-w-sm text-sm text-[color:var(--muted-ink)]">
                            The inline PDF preview could not be rendered in this
                            browser view.
                          </p>
                          <a
                            href={previewPdfUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-2 rounded-full border border-[color:var(--line-strong)] px-4 py-2 text-sm font-medium text-[color:var(--ink)] transition-colors hover:border-[color:var(--teal-soft)] hover:text-[color:var(--teal)]"
                          >
                            Open preview in a new tab
                          </a>
                        </div>
                      </object>
                    ) : (
                      <div className="flex h-full min-h-[600px] items-center justify-center bg-white text-sm text-[color:var(--muted-ink)]">
                        Generate a run to preview the report.
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      <div className="fixed bottom-5 left-4 z-40 sm:bottom-6 sm:left-5">
        <AnimatePresence initial={false}>
          {chatOpen ? (
            <motion.section
              key="chat-open"
              initial={{ opacity: 0, y: 18, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.98 }}
              transition={{ duration: 0.24, ease: "easeOut" }}
              className="w-[min(92vw,380px)] overflow-hidden rounded-[28px] border border-white/12 bg-[color:var(--chat-shell)] text-white shadow-[0_24px_70px_rgba(12,20,24,0.42)] backdrop-blur-xl"
            >
              <div className="border-b border-white/10 px-5 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/58">
                      Assistant
                    </p>
                    <h3 className="mt-2 text-[22px] font-semibold tracking-[-0.04em]">
                      Talk to this report
                    </h3>
                    <p className="mt-2 max-w-xs text-sm leading-6 text-white/68">
                      {activeSession && chatAvailable
                        ? `Answers stay grounded in ${formatCaseReference(activeSession.run.patient_id)} and the currently selected report content.`
                        : "The assistant is standing by. Once a run completes, it will answer against the selected report and evidence."}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setChatOpen(false)}
                    className="rounded-2xl border border-white/10 p-2 text-white/70 transition-colors hover:bg-white/8 hover:text-white"
                    aria-label="Close assistant"
                  >
                    <X className="h-4 w-4" strokeWidth={2.1} />
                  </button>
                </div>
              </div>

              <div className="px-5 py-4">
                <div className="mb-4 flex flex-wrap gap-2">
                  {starterPrompts.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      onClick={() => sendMessage(prompt)}
                      disabled={!activeSession || !chatAvailable || chatSending}
                      className="rounded-full border border-white/10 bg-white/6 px-3 py-2 text-xs font-medium text-white/78 transition-all hover:-translate-y-0.5 hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>

                <div className="max-h-[300px] space-y-3 overflow-y-auto pr-1">
                  {!activeSession || !chatAvailable ? (
                    <div className="rounded-[20px] border border-white/10 bg-white/6 px-4 py-4 text-sm leading-6 text-white/78">
                      Generate a completed run first, then the report assistant
                      will ground itself on that case.
                    </div>
                  ) : null}
                  {messages.map((message, index) => (
                    <motion.div
                      key={`${message.role}-${index}-${message.text.slice(0, 18)}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.18 }}
                      className={cn(
                        "rounded-[20px] px-4 py-3 text-sm leading-6",
                        message.role === "assistant"
                          ? message.error
                            ? "bg-[color:var(--danger)]/18 text-white"
                            : "bg-white/8 text-white/84"
                          : "ml-auto max-w-[88%] bg-[color:var(--teal)] text-white",
                      )}
                    >
                      <p>{message.text}</p>
                      {message.role === "assistant" ? (
                        <div className="mt-3 space-y-2">
                          {message.grounded === false && !message.error ? (
                            <Badge variant="warning">Limited confidence</Badge>
                          ) : null}
                          {message.citations?.map((citation, citationIndex) => (
                            <div
                              key={`${citation.title}-${citationIndex}`}
                              className="rounded-2xl border border-white/8 bg-black/10 px-3 py-3 text-xs leading-5 text-white/76"
                            >
                              <p className="font-semibold text-white/88">
                                {citation.title}
                                {citation.section
                                  ? ` · ${citation.section}`
                                  : ""}
                              </p>
                              <p className="mt-1">{citation.snippet}</p>
                            </div>
                          ))}
                        </div>
                      ) : null}
                    </motion.div>
                  ))}
                  {chatSending ? (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="inline-flex items-center gap-3 rounded-[20px] bg-white/8 px-4 py-3 text-sm text-white/80"
                    >
                      <LoaderCircle className="h-4 w-4 animate-spin" />
                      Searching the current run...
                    </motion.div>
                  ) : null}
                </div>

                <div className="mt-4 rounded-[22px] border border-white/10 bg-white/6 p-2">
                  <div className="flex items-end gap-2">
                    <textarea
                      value={chatInput}
                      onChange={(event) => setChatInput(event.target.value)}
                      placeholder="Ask about the report findings..."
                      disabled={!activeSession || !chatAvailable || chatSending}
                      className="min-h-[74px] flex-1 resize-none bg-transparent px-3 py-2 text-sm text-white outline-none placeholder:text-white/36"
                    />
                    <button
                      type="button"
                      onClick={() => sendMessage(chatInput)}
                      disabled={!activeSession || !chatAvailable || chatSending}
                      className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-[color:var(--chat-shell)] transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-55"
                      aria-label="Send message"
                    >
                      <SendHorizonal className="h-4 w-4" strokeWidth={2.1} />
                    </button>
                  </div>
                </div>
              </div>
            </motion.section>
          ) : (
            <motion.div
              key="chat-closed"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-start gap-3"
            >
              <motion.div
                className="hidden rounded-full bg-[color:var(--sync-bg)] px-5 py-3 text-sm font-semibold uppercase tracking-[0.18em] text-white shadow-[0_16px_50px_rgba(25,42,49,0.32)] xl:inline-flex"
                animate={{ y: [0, -2, 0] }}
                transition={{
                  duration: 2.4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              >
                <LoaderCircle className="mr-3 h-4 w-4 animate-spin text-[color:var(--teal)]" />
                {activeSession && chatAvailable
                  ? "Grounded on current run"
                  : "Assistant standing by"}
              </motion.div>

              <motion.button
                type="button"
                onClick={() => setChatOpen(true)}
                whileHover={{ y: -3 }}
                whileTap={{ scale: 0.98 }}
                className="inline-flex items-center gap-3 rounded-full bg-[color:var(--chat-shell)] px-5 py-4 text-sm font-semibold uppercase tracking-[0.16em] text-white shadow-[0_22px_60px_rgba(12,20,24,0.42)]"
              >
                <MessageSquareMore
                  className="h-4.5 w-4.5 text-[color:var(--chat-accent)]"
                  strokeWidth={2.1}
                />
                Talk to report
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function ActionIcon({
  label,
  icon: Icon,
  disabled = false,
  onClick,
}: {
  label: string;
  icon: typeof Printer;
  disabled?: boolean;
  onClick?: () => void;
}) {
  return (
    <motion.button
      whileHover={disabled ? undefined : { y: -2 }}
      whileTap={disabled ? undefined : { scale: 0.97 }}
      className={cn(
        "inline-flex h-11 w-11 items-center justify-center rounded-[16px] border border-[color:var(--line)] bg-white/78 text-[color:var(--muted-ink)] shadow-[0_8px_20px_rgba(31,47,56,0.05)] transition-all hover:border-[color:var(--teal-soft)] hover:bg-white hover:text-[color:var(--teal)]",
        disabled && "cursor-not-allowed opacity-35",
      )}
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
    >
      <Icon className="h-[18px] w-[18px]" strokeWidth={1.9} />
    </motion.button>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <motion.div whileHover={{ y: -2 }}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
        {label}
      </p>
      <p className="mt-3 text-[22px] font-semibold tracking-[-0.04em] sm:text-[26px] xl:mt-4 xl:text-[30px]">
        {value}
      </p>
    </motion.div>
  );
}

function InlineNote({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
        {label}
      </p>
      <p className="mt-3 text-[15px] leading-7 text-[color:var(--muted-ink)]">
        {value}
      </p>
    </div>
  );
}

function ReadOnlyMeta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[color:var(--muted-ink)]">
        {label}
      </p>
      <p className="mt-2 text-base font-medium text-[color:var(--ink)]">
        {value}
      </p>
    </div>
  );
}

function renderSummary(summary: string, highlight: string | null) {
  if (!highlight || !summary.includes(highlight)) {
    return summary;
  }

  const [before, ...afterParts] = summary.split(highlight);
  const after = afterParts.join(highlight);

  return (
    <>
      {before}
      <span className="font-semibold text-[color:var(--teal)]">
        {highlight}
      </span>
      {after}
    </>
  );
}

function buildPatientId(reportId: string) {
  return `case-${reportId.slice(-6).toUpperCase()}`;
}

function formatCaseReference(patientId: string) {
  return patientId.toUpperCase();
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-AU", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function formatPipelineMode(mode: PipelineMode) {
  switch (mode) {
    case "uploading":
      return "Uploading";
    case "creating_run":
      return "Processing";
    case "error":
      return "Needs attention";
    case "ready":
      return "Ready";
    default:
      return "Waiting";
  }
}

function getStatusMessage({
  pipelineMode,
  activeSession,
  pendingFile,
  uiError,
}: {
  pipelineMode: PipelineMode;
  activeSession: SessionRun | null;
  pendingFile: File | null;
  uiError: string | null;
}) {
  if (uiError) {
    return uiError;
  }

  if (pipelineMode === "uploading") {
    return "Uploading the report PDF and validating the intake payload.";
  }

  if (pipelineMode === "creating_run") {
    return "Creating the run and querying the live evidence services.";
  }

  if (activeSession) {
    if (activeSession.run.run_status === "blocked") {
      return "Pipeline completed with blocking issues. Manual review is required.";
    }

    if (activeSession.run.run_status === "degraded") {
      return "Pipeline completed in degraded mode. Review fallback evidence before approving.";
    }

    return "Auto-pipeline processing complete. Review-ready draft assembled from the backend.";
  }

  if (pendingFile) {
    return "Selected report is ready. Start the pipeline to populate the clinician workspace.";
  }

  return "Choose a report PDF to start the upload, evidence retrieval, and review pipeline.";
}

function formatReviewLabel(reviewStatus: RunResponse["review_status"]) {
  switch (reviewStatus) {
    case "pending_review":
      return "Pending review";
    case "reviewed":
      return "Reviewed";
    case "approved":
      return "Approved";
    case "dropped":
      return "Dropped";
  }
}

function reviewBadgeVariant(reviewStatus: RunResponse["review_status"]) {
  switch (reviewStatus) {
    case "approved":
      return "success";
    case "dropped":
      return "danger";
    case "reviewed":
      return "default";
    case "pending_review":
      return "warning";
  }
}

function buildVariantRows(session: SessionRun) {
  const inferredClassification = extractPrimaryClassification(session.run);
  const rows = session.run.report_payload.variant_summary_rows;

  return rows.map((row) => ({
    gene: row.gene || "Unspecified",
    variant:
      [row.transcript_hgvs, row.protein_change].filter(Boolean).join(" / ") ||
      row.consequence ||
      "No variant string available",
    genomicLocus: row.genomic_hg38 || row.variation_type || "Not stated",
    classification: inferredClassification.label,
    classificationVariant: inferredClassification.variant,
  }));
}

function buildEvidenceCards(evidence: EvidenceSourceSummary[]): EvidenceCard[] {
  return evidence.map((item) => {
    const title = item.source.toUpperCase();
    const badgeVariant =
      item.status === "live"
        ? "success"
        : item.status === "fallback"
          ? "warning"
          : "default";

    if (item.source === "clinvar") {
      const classification = String(
        item.summary.classification || "Unclassified",
      );
      const reviewStatus = String(item.summary.review_status || "");
      const conditions = Array.isArray(item.summary.conditions)
        ? item.summary.conditions.join(", ")
        : "";
      return {
        id: item.source,
        title,
        body: `${classification}${reviewStatus ? ` (${reviewStatus})` : ""}${conditions ? ` — ${conditions}.` : "."}`,
        badge: item.status,
        badgeVariant,
        warnings: item.warnings,
      };
    }

    if (item.source === "vep") {
      const mostSevereConsequence = prettifyConsequence(
        String(item.summary.most_severe_consequence || "Not stated"),
      );
      const distribution = item.summary.consequence_distribution as
        | Record<string, number>
        | undefined;
      const highestValue = distribution
        ? Math.max(...Object.values(distribution)) / 100
        : 0.5;
      return {
        id: item.source,
        title,
        badge: item.status,
        badgeVariant,
        scoreLabel: mostSevereConsequence,
        subLabel: `${String(item.summary.biotype || "protein coding")} transcript`,
        progress: highestValue,
        warnings: item.warnings,
      };
    }

    if (item.source === "spliceai") {
      const scores = [
        Number(item.summary.acceptor_loss || 0),
        Number(item.summary.donor_loss || 0),
        Number(item.summary.acceptor_gain || 0),
        Number(item.summary.donor_gain || 0),
      ];
      const strongestScore = Math.max(...scores);
      return {
        id: item.source,
        title,
        badge: item.status,
        badgeVariant,
        scoreLabel: strongestScore >= 0.2 ? "Splice signal" : "Non-impact",
        subLabel: `max delta ${strongestScore.toFixed(2)}`,
        body:
          strongestScore >= 0.2
            ? `Potential splice effect detected with delta scores up to ${strongestScore.toFixed(2)}.`
            : "No significant splice site alterations detected for the demo variant.",
        warnings: item.warnings,
      };
    }

    if (item.source === "franklin") {
      const functional = String(
        item.summary.functional_data || "Not available",
      );
      const population = String(
        item.summary.population_data || "Not available",
      );
      const inSilico = String(
        item.summary.in_silico_prediction || "Not available",
      );
      return {
        id: item.source,
        title,
        body: `Functional ${functional}. Population ${population}. In silico ${inSilico}.`,
        badge: item.status,
        badgeVariant,
        warnings: item.warnings,
      };
    }

    return {
      id: item.source,
      title,
      body: JSON.stringify(item.summary),
      badge: item.status,
      badgeVariant,
      warnings: item.warnings,
    };
  });
}

function extractPrimaryClassification(run: RunResponse) {
  const clinvar = run.evidence.find((item) => item.source === "clinvar");
  const label = String(clinvar?.summary.classification || "Review required");
  const lowered = label.toLowerCase();

  if (lowered.includes("pathogenic")) {
    return { label, variant: "danger" as const };
  }

  if (lowered.includes("uncertain")) {
    return { label, variant: "warning" as const };
  }

  return { label, variant: "default" as const };
}

function prettifyConsequence(value: string) {
  return value.replace(/_/g, " ");
}

function formatWarning(warning: string) {
  return warning.replace(/_/g, " ");
}

function getPipelineStepState(stepId: string, pipelineMode: PipelineMode) {
  if (pipelineMode === "error") {
    if (stepId === "upload" || stepId === "extract") {
      return "attention";
    }
    return "idle";
  }

  if (pipelineMode === "uploading") {
    return stepId === "upload" ? "active" : "idle";
  }

  if (pipelineMode === "creating_run") {
    if (stepId === "upload" || stepId === "extract") return "complete";
    if (stepId === "evidence") return "active";
    return "idle";
  }

  if (pipelineMode === "ready") {
    return "complete";
  }

  return "idle";
}

function pipelineDotClassName(
  state: "idle" | "active" | "complete" | "attention",
) {
  switch (state) {
    case "active":
      return "border-transparent bg-[color:var(--teal)] shadow-[0_0_0_6px_rgba(44,109,112,0.12)]";
    case "complete":
      return "border-transparent bg-[color:var(--teal-soft)]";
    case "attention":
      return "border-transparent bg-[color:var(--danger)]";
    case "idle":
      return "border-[color:var(--line-strong)] bg-white/70";
  }
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while communicating with the backend.";
}

function buildStarterMessage(session: SessionRun): ChatMessage {
  return {
    role: "assistant",
    text: `I can answer questions grounded in ${formatCaseReference(session.run.patient_id)}, the report draft, and the evidence returned for this run.`,
    grounded: true,
  };
}
