"use client";

import { useState, useRef, useCallback, useEffect } from "react";

const API_BASE = "http://localhost:8000/api/v1";

/* ── Sample data ─────────────────────────── */
const SAMPLE_TEXTS = [
    {
        label: "Personal Info",
        text: `Dear John Smith,\n\nYour appointment with Dr. Sarah Johnson is confirmed for 2024-03-15 at the Springfield Medical Center, located at 742 Evergreen Terrace, Springfield, IL 62704.\n\nPlease bring your insurance card and government-issued ID. For reference, your patient ID is SSN 423-86-1234 and your contact number is +1 (555) 867-5309. Your email on file is john.smith@email.com.\n\nYour co-pay of $45.00 will be charged to your Visa card ending in 4242-8765-1234-5678.\n\nBest regards,\nSpringfield Medical Center\nIP: 192.168.1.105`
    },
    {
        label: "Employee Record",
        text: `Employee Name: Priya Sharma\nEmployee ID: EMP-2024-4589\nDepartment: Engineering, Google Inc.\nEmail: priya.sharma@company.com\nPhone: +91 9876543210\nAadhaar: 4832 7651 9043\nPAN: ABCDE1234F\nDate of Birth: 15/08/1992\nAddress: 42 MG Road, Bangalore, Karnataka 560001\nEmergency Contact: Rahul Sharma (+91 8765432109)\nSalary: $85,000 per annum`
    },
    {
        label: "Customer Support",
        text: `Ticket #CS-20240315-001\nCustomer: Maria Garcia (maria.garcia@outlook.com)\nPhone: (415) 555-0142\n\nIssue: Unable to access account. Customer verified identity with last 4 of SSN: 567-89-0123 and credit card 5412-7534-8901-2345.\n\nResolution: Password reset link sent to registered email. Account access restored at 14:32 UTC from IP 10.0.0.42.\n\nAgent: Alex Thompson\nLocation: San Francisco, CA`
    }
];

const STRATEGIES = [
    { id: "mask", name: "Masking", icon: "lock", desc: "Replace with ████ blocks" },
    { id: "tag_replace", name: "Tag Replace", icon: "label", desc: "Semantic tags like [EMAIL]" },
    { id: "anonymize", name: "Anonymize", icon: "theater_comedy", desc: "Realistic synthetic data" },
    { id: "hash", name: "Hashing", icon: "enhanced_encryption", desc: "SHA-256 crypto hashes" },
];

const ENTITY_COLORS = {
    EMAIL: { bg: "rgba(99,102,241,0.1)", color: "#6366f1", border: "rgba(99,102,241,0.25)" },
    PHONE: { bg: "rgba(6,182,212,0.1)", color: "#0891b2", border: "rgba(6,182,212,0.25)" },
    PERSON_NAME: { bg: "rgba(139,92,246,0.1)", color: "#7c3aed", border: "rgba(139,92,246,0.25)" },
    LOCATION: { bg: "rgba(16,185,129,0.1)", color: "#059669", border: "rgba(16,185,129,0.25)" },
    ADDRESS: { bg: "rgba(16,185,129,0.1)", color: "#059669", border: "rgba(16,185,129,0.25)" },
    SSN: { bg: "rgba(239,68,68,0.1)", color: "#dc2626", border: "rgba(239,68,68,0.25)" },
    AADHAAR: { bg: "rgba(239,68,68,0.1)", color: "#dc2626", border: "rgba(239,68,68,0.25)" },
    CREDIT_CARD: { bg: "rgba(245,158,11,0.1)", color: "#d97706", border: "rgba(245,158,11,0.25)" },
    IP_ADDRESS: { bg: "rgba(59,130,246,0.1)", color: "#2563eb", border: "rgba(59,130,246,0.25)" },
    DATE: { bg: "rgba(236,72,153,0.1)", color: "#db2777", border: "rgba(236,72,153,0.25)" },
    DATE_OF_BIRTH: { bg: "rgba(236,72,153,0.1)", color: "#db2777", border: "rgba(236,72,153,0.25)" },
    ORGANIZATION: { bg: "rgba(251,146,60,0.1)", color: "#ea580c", border: "rgba(251,146,60,0.25)" },
};
const DEFAULT_COLOR = { bg: "rgba(148,163,184,0.1)", color: "#64748b", border: "rgba(148,163,184,0.25)" };
const PIE_COLORS = ["#6366f1", "#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#3b82f6", "#ec4899", "#f97316", "#14b8a6"];

const LOADING_STEPS = [
    "Extracting content...", "Running regex detection...", "Running NLP analysis...",
    "Merging entities...", "Applying redaction...", "Verifying output..."
];

/* ── Mode configuration ────────────────── */
const MODES = [
    { id: "text", label: "Text Input", icon: "edit_note", accept: null },
    { id: "image", label: "Image", icon: "image", accept: ".jpg,.jpeg,.png,.webp" },
    { id: "pdf", label: "PDF", icon: "picture_as_pdf", accept: ".pdf" },
    { id: "audio", label: "Audio", icon: "mic", accept: ".mp3,.wav,.m4a,.ogg" },
    { id: "video", label: "Video", icon: "videocam", accept: ".mp4,.mov,.avi,.mkv" },
    { id: "file", label: "Other Files", icon: "upload_file", accept: ".txt,.csv,.json,.pdf,.png,.jpg,.jpeg" },
];

const MODE_API_MAP = {
    image: "/redact/image",
    pdf: "/redact/pdf",
    audio: "/redact/audio",
    video: "/redact/video",
    file: "/redact/file",
};

const CONTENT_TYPE_ICONS = {
    "image/png": "image", "image/jpeg": "image", "image/webp": "image",
    "application/pdf": "description", "audio/mpeg": "music_note", "audio/wav": "music_note",
    "video/mp4": "movie", "video/quicktime": "movie",
};

/* ──────────────────────────────────────────────────────────
   COMPLIANCE SECTION — standalone component, pure UI
   ────────────────────────────────────────────────────────── */
const REGULATIONS = [
    {
        flag: "IN",
        badge: "India · 2023",
        name: "DPDP Act 2023",
        desc: "Ensures lawful and consent-based processing of personal data in India. Our AI redaction engine minimizes exposure and supports secure compliance workflows.",
        icon: "balance",
    },
    {
        flag: "EU",
        badge: "Europe · GDPR",
        name: "GDPR",
        desc: "Mandates privacy-by-design and strict user data protection standards across the European Union. Non-compliance carries fines up to €20M or 4% of global revenue.",
        icon: "enhanced_encryption",
    },
    {
        flag: "US",
        badge: "USA · Healthcare",
        name: "HIPAA",
        desc: "Protects healthcare information through secure handling of PHI across documents, audio, and video. Violations carry penalties up to $1.9M per category per year.",
        icon: "medical_services",
    },
    {
        flag: "INTL",
        badge: "International",
        name: "ISO 27001",
        desc: "International standard for information security management systems. Demonstrates enterprise commitment to systematic risk assessment and data protection controls.",
        icon: "shield",
    },
    {
        flag: "SOC2",
        badge: "Enterprise Trust",
        name: "SOC 2",
        desc: "Enterprise-grade trust framework ensuring operational and data integrity. Validates security, availability, and confidentiality controls across our AI pipeline.",
        icon: "check_circle",
    },
];

const COMP_FEATURES = [
    {
        icon: "smart_toy",
        title: "AI-Automated Redaction",
        desc: "Multi-modal pipelines eliminate manual redaction errors across text, PDFs, images, audio, and video simultaneously.",
    },
    {
        icon: "assignment",
        title: "Full Audit Logging",
        desc: "Every redaction event is logged with entity type, confidence score, and timestamp — ready for regulatory review.",
    },
    {
        icon: "vpn_key",
        title: "Zero-Retention Policy",
        desc: "Uploaded files are processed in-memory and immediately discarded. No data persists beyond the active session.",
    },
    {
        icon: "public",
        title: "Global Standard Coverage",
        desc: "One platform covering DPDP, GDPR, HIPAA, ISO 27001, and SOC 2 — reducing compliance overhead across jurisdictions.",
    },
];

function ComplianceSection() {
    const sectionRef = useRef(null);
    const revealRefs = useRef([]);

    useEffect(() => {
        const observers = [];
        revealRefs.current.forEach((el) => {
            if (!el) return;
            const obs = new IntersectionObserver(
                ([entry]) => { if (entry.isIntersecting) { el.classList.add("visible"); obs.disconnect(); } },
                { threshold: 0.12 }
            );
            obs.observe(el);
            observers.push(obs);
        });
        return () => observers.forEach((o) => o.disconnect());
    }, []);

    const addReveal = (i) => (el) => { revealRefs.current[i] = el; };

    return (
        <section className="compliance-section" ref={sectionRef}>
            <div className="compliance-inner">

                {/* Heading */}
                <div className={`comp-heading-block comp-reveal`} ref={addReveal(0)}>
                    <div className="comp-eyebrow">
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>shield</span>
                        Compliance & Privacy
                    </div>
                    <h2 className="comp-title">
                        Why Privacy Compliance<br /><span>Matters</span>
                    </h2>
                    <p className="comp-subtitle">
                        Enterprise-grade AI redaction aligned with global data protection regulations — from GDPR to DPDP Act 2023.
                    </p>
                </div>

                {/* Regulation cards */}
                <div className="reg-cards-grid">
                    {REGULATIONS.map((reg, i) => (
                        <div
                            key={reg.name}
                            className={`reg-card comp-reveal comp-reveal-delay-${i + 1}`}
                            ref={addReveal(i + 1)}
                        >
                            <span className="reg-card-flag" style={{ fontSize: 14, fontWeight: 800, color: "var(--primary)", letterSpacing: 1 }}>{reg.flag}</span>
                            <div className="reg-card-badge">{reg.badge}</div>
                            <div className="reg-card-name">{reg.name}</div>
                            <p className="reg-card-desc">{reg.desc}</p>
                            <div className="reg-card-icon">
                                <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{reg.icon}</span>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Cinematic why-strip */}
                <div className={`comp-why-strip comp-reveal`} ref={addReveal(6)}>
                    <div className="comp-why-text">
                        <div className="comp-eyebrow" style={{ marginBottom: 18 }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>bolt</span>
                            The Problem We Solve
                        </div>
                        <h3 className="comp-why-headline">
                            AI-Driven Compliance.<br /><span>Built for Global Standards.</span>
                        </h3>
                        <p className="comp-why-body">
                            AI systems today process massive volumes of sensitive personal data across documents, calls, and video streams.
                            Enterprises face multi-million dollar regulatory penalties for breaches — and manual redaction is both error-prone and impossibly slow at scale.
                            <br /><br />
                            Cenz-AI automates the entire PII detection and redaction lifecycle across every modality, providing a single compliance engine for global operations.
                        </p>
                        <div className="comp-stat-row">
                            {[
                                { val: "€20M", label: "Max GDPR Fine" },
                                { val: "$1.9M", label: "HIPAA Penalty / Category" },
                                { val: "7", label: "Detection Engines" },
                                { val: "4", label: "Redaction Strategies" },
                            ].map((s) => (
                                <div key={s.label} className="comp-stat-card">
                                    <div className="comp-stat-val">{s.val}</div>
                                    <div className="comp-stat-label">{s.label}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Shield image */}
                    <div className="comp-why-image">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src="/compliance_shield.png" alt="AI Security Shield" />
                        <div className="comp-why-image-overlay" />
                    </div>
                </div>

                {/* Glow divider */}
                <div className="comp-glow-divider" />

                {/* Feature cards */}
                <div className={`comp-reveal`} ref={addReveal(7)}>
                    <div className="comp-heading-block" style={{ marginBottom: 40 }}>
                        <h3 className="comp-title" style={{ fontSize: 32 }}>
                            How We Deliver <span>Compliance</span>
                        </h3>
                    </div>
                    <div className="comp-features-row">
                        {COMP_FEATURES.map((f, i) => (
                            <div key={f.title} className="comp-feature-card">
                                <div className="comp-feature-icon">
                                    <span className="material-symbols-outlined">{f.icon}</span>
                                </div>
                                <div className="comp-feature-title">{f.title}</div>
                                <p className="comp-feature-desc">{f.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* CTA link */}
                <div style={{ textAlign: "center", marginTop: 56 }} className={`comp-reveal`} ref={addReveal(8)}>
                    <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 16 }}>
                        Learn how Cenz-AI maps to each regulation in depth
                    </p>
                    <a href="/privacy-compliance" className="btn btn-primary" style={{ display: "inline-flex", textDecoration: "none" }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>policy</span>
                        View Full Compliance Framework ↗
                    </a>
                </div>

            </div>
        </section>
    );
}

export default function Home() {

    const [activeTab, setActiveTab] = useState("text");
    const [inputText, setInputText] = useState("");
    const [strategy, setStrategy] = useState("mask");
    const [loading, setLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState(0);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [engineStatus, setEngineStatus] = useState(null);
    const [systemStats, setSystemStats] = useState(null);
    const [dragOver, setDragOver] = useState(false);
    const [selectedFile, setSelectedFile] = useState(null);
    // Multi-modal result for media redaction
    const [mediaResult, setMediaResult] = useState(null);
    const fileInputRef = useRef(null);

    useEffect(() => { fetchEngineStatus(); }, []);

    const fetchEngineStatus = async () => {
        try { const r = await fetch(`${API_BASE}/engines`); if (r.ok) setEngineStatus(await r.json()); } catch { }
    };
    const fetchStats = async () => {
        try { const r = await fetch(`${API_BASE}/stats`); if (r.ok) setSystemStats(await r.json()); } catch { }
    };

    /* ── Text redaction ── */
    const handleRedactText = async () => {
        if (!inputText.trim()) return;
        setLoading(true); setError(null); setResult(null); setMediaResult(null); setLoadingStep(0);
        const t = setInterval(() => setLoadingStep(p => Math.min(p + 1, 4)), 600);
        try {
            const r = await fetch(`${API_BASE}/redact/text`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: inputText, strategy }) });
            if (!r.ok) throw new Error(`API error: ${r.status}`);
            setResult(await r.json()); fetchStats();
        } catch (e) { setError(e.message); } finally { clearInterval(t); setLoading(false); setLoadingStep(0); }
    };

    /* ── File selection ── */
    const handleFileSelect = (file) => { if (!file) return; setSelectedFile(file); setResult(null); setError(null); setMediaResult(null); };

    /* ── Multi-modal redaction (image/pdf/audio/video/file) ── */
    const handleMediaRedact = async () => {
        if (!selectedFile) return;
        setLoading(true); setError(null); setResult(null); setMediaResult(null); setLoadingStep(0);
        const t = setInterval(() => setLoadingStep(p => Math.min(p + 1, 5)), 1200);

        const endpoint = MODE_API_MAP[activeTab] || "/redact/file";

        try {
            const fd = new FormData();
            fd.append("file", selectedFile);
            fd.append("strategy", strategy);
            const r = await fetch(`${API_BASE}${endpoint}`, { method: "POST", body: fd });
            if (!r.ok) {
                const errData = await r.json().catch(() => ({}));
                throw new Error(errData.detail || `API error: ${r.status}`);
            }
            const data = await r.json();

            if (activeTab === "file") {
                setResult(data);
            } else {
                setMediaResult(data);
            }
            fetchStats();
        } catch (e) { setError(e.message); } finally { clearInterval(t); setLoading(false); setLoadingStep(0); }
    };

    /* ── Download redacted file ── */
    const handleDownload = async (jobId) => {
        if (!jobId) return;
        try {
            const r = await fetch(`${API_BASE}/download/${jobId}`);

            // Check for error responses — the server returns JSON on 404
            if (!r.ok) {
                const errData = await r.json().catch(() => ({}));
                throw new Error(errData.detail || `Download failed (${r.status})`);
            }

            const contentType = r.headers.get("content-type") || "";

            // If we got JSON back instead of a file, it's an error
            if (contentType.includes("application/json")) {
                const errData = await r.json().catch(() => ({}));
                throw new Error(errData.detail || "Server returned an error instead of a file");
            }

            // Get filename from Content-Disposition header or fall back
            let downloadFilename = mediaResult?.filename || `redacted_${selectedFile?.name || "output"}`;
            const disposition = r.headers.get("content-disposition");
            if (disposition) {
                const match = disposition.match(/filename="?([^";\n]+)"?/);
                if (match) downloadFilename = match[1];
            }

            const blob = await r.blob();

            // Verify blob has actual content
            if (blob.size === 0) {
                throw new Error("Downloaded file is empty");
            }

            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = downloadFilename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            // Small delay before revoking to ensure download starts
            setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (e) {
            setError(e.message);
        }
    };

    /* ── Drag & drop ── */
    const handleDragOver = useCallback(e => { e.preventDefault(); setDragOver(true); }, []);
    const handleDragLeave = useCallback(() => setDragOver(false), []);
    const handleDrop = useCallback(e => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFileSelect(f); }, []);

    const handleClear = () => { setInputText(""); setResult(null); setError(null); setSelectedFile(null); setMediaResult(null); };
    const handleCopy = (text) => { if (text) navigator.clipboard.writeText(text); };

    const generatePieGradient = (stats) => {
        if (!stats?.by_type || Object.keys(stats.by_type).length === 0) return "conic-gradient(#f1f5f9 0deg 360deg)";
        const total = Object.values(stats.by_type).reduce((a, b) => a + b, 0);
        let cur = 0; const segs = [];
        Object.entries(stats.by_type).sort((a, b) => b[1] - a[1]).forEach(([, c], i) => {
            const d = (c / total) * 360; segs.push(`${PIE_COLORS[i % PIE_COLORS.length]} ${cur}deg ${cur + d}deg`); cur += d;
        });
        return `conic-gradient(${segs.join(", ")})`;
    };

    const isOnDashboard = !["stats", "api"].includes(activeTab);
    const isMediaMode = ["image", "pdf", "audio", "video"].includes(activeTab);
    const isFileMode = activeTab === "file";
    const coreEngines = engineStatus ? Object.entries(engineStatus) : [];
    const enginesOnline = coreEngines.filter(([, v]) => v).length;
    const totalEngines = coreEngines.length || 7;

    const currentMode = MODES.find(m => m.id === activeTab) || MODES[0];

    return (
        <div className="fade-in">
            {/* ═══ NAVBAR ═══ */}
            <nav className="glass-nav">
                <div className="glass-nav-inner">
                    <div className="nav-brand">
                        <div className="nav-logo">
                            <span className="material-symbols-outlined">shield</span>
                        </div>
                        <div>
                            <div className="nav-title">Cenz-<span className="accent">AI</span></div>
                            <div className="nav-sub">Enterprise Privacy Platform</div>
                        </div>
                    </div>
                    <div className="nav-tabs">
                        <button className={`nav-tab ${isOnDashboard ? "active" : ""}`} onClick={() => setActiveTab("text")}>Home</button>
                        <button className={`nav-tab ${activeTab === "stats" ? "active" : ""}`} onClick={() => { setActiveTab("stats"); fetchStats(); }}>Analytics</button>
                        <button className={`nav-tab ${activeTab === "api" ? "active" : ""}`} onClick={() => setActiveTab("api")}>Documentation</button>
                    </div>
                    <div className="nav-status">
                        <div className="nav-status-dot"></div>
                        <div className="nav-status-text">{engineStatus ? `${enginesOnline}/${totalEngines} Engines Online` : "Connecting..."}</div>
                    </div>
                </div>
            </nav>

            {/* ═══ HERO ═══ */}
            {isOnDashboard && (
                <>
                    {/* ═══ CINEMATIC HERO ═══ */}
                    <section className="hero-section">
                        <div className="hero-bg"></div>
                        <div className="hero-overlay"></div>
                        {/* Glowing ring arc */}
                        <div className="hero-arc"></div>
                        <div className="hero-fade"></div>
                        <div className="hero-content">
                            <div className="hero-text">
                                <div className="hero-badge">
                                    <span className="material-symbols-outlined" style={{ fontSize: "14px" }}>auto_awesome</span>
                                    Multi-Modal AI Detection
                                </div>
                                <h1 className="hero-heading">Enterprise Privacy<br /><span>AI Orchestration</span></h1>
                                <p className="hero-desc">AI-powered multi-modal PII redaction across text, images, PDFs, audio, and video — with downloadable outputs and a full audit trail.</p>
                                {/* Stat pills row */}
                                <div style={{ display: "flex", gap: 12, marginTop: 28, flexWrap: "wrap" }}>
                                    {[
                                        { label: "7 Engines", icon: "memory" },
                                        { label: "4 Strategies", icon: "tune" },
                                        { label: "Real-time", icon: "bolt" },
                                    ].map(p => (
                                        <div key={p.label} style={{
                                            display: "flex", alignItems: "center", gap: 6,
                                            padding: "6px 14px", borderRadius: "999px",
                                            background: "rgba(0,255,136,0.05)",
                                            border: "1px solid rgba(0,255,136,0.15)",
                                            fontSize: 12, fontWeight: 600, color: "rgba(0,255,136,0.85)",
                                            letterSpacing: "0.3px"
                                        }}>
                                            <span className="material-symbols-outlined" style={{ fontSize: 14 }}>{p.icon}</span>
                                            {p.label}
                                        </div>
                                    ))}
                                </div>
                            </div>
                            <div className="hero-cards">
                                <div className="hero-info-card">
                                    <div className="hero-info-icon green"><span className="material-symbols-outlined">hub</span></div>
                                    <div>
                                        <div className="hero-info-label">Modalities</div>
                                        <div className="hero-info-value">Text · Image · PDF · Audio · Video</div>
                                    </div>
                                </div>
                                <div className="hero-info-card">
                                    <div className="hero-info-icon indigo"><span className="material-symbols-outlined">security</span></div>
                                    <div>
                                        <div className="hero-info-label">Strategy</div>
                                        <div className="hero-info-value">{STRATEGIES.find(s => s.id === strategy)?.name || "Masking"}</div>
                                    </div>
                                </div>
                                <div className="hero-info-card">
                                    <div className="hero-info-icon purple"><span className="material-symbols-outlined">download</span></div>
                                    <div>
                                        <div className="hero-info-label">Downloads</div>
                                        <div className="hero-info-value">Redacted files ready</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* ═══ METRIC CARDS ═══ */}
                    <div className="metrics-row">
                        <div className="metric-card">
                            <div className="metric-top">
                                <div className="metric-icon indigo"><span className="material-symbols-outlined">visibility_off</span></div>
                                <span className="metric-badge green">Live</span>
                            </div>
                            <div className="metric-label">Total Redactions</div>
                            <div className="metric-value">{systemStats?.total_entities_detected || 0} <span>Entities</span></div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-top">
                                <div className="metric-icon purple"><span className="material-symbols-outlined">health_and_safety</span></div>
                                <span className="metric-badge green">Live</span>
                            </div>
                            <div className="metric-label">Files Processed</div>
                            <div className="metric-value">{systemStats?.total_files_processed || 0} <span>Files</span></div>
                        </div>
                        <div className="metric-card">
                            <div className="metric-top">
                                <div className="metric-icon blue"><span className="material-symbols-outlined">speed</span></div>
                                <span className="metric-badge green">Avg</span>
                            </div>
                            <div className="metric-label">Engine Latency</div>
                            <div className="metric-value">{systemStats?.avg_processing_time_ms?.toFixed(1) || "—"} <span>ms</span></div>
                        </div>
                    </div>

                    {/* Glowing section divider */}
                    <div className="glow-divider" style={{ maxWidth: 1500, margin: "32px auto 0", padding: "0 32px" }}>
                        <div style={{ height: 1, background: "linear-gradient(90deg, transparent, rgba(0,255,136,0.2), rgba(59,130,246,0.15), transparent)" }} />
                    </div>
                </>
            )}

            {/* ═══ MAIN CONTENT ═══ */}
            <div className="main-container">
                {isOnDashboard && (
                    <div className="section-card slide-up" style={{ marginTop: "36px" }}>
                        <div className="section-header">
                            <div>
                                <div className="section-title">PII Redaction Engine</div>
                                <div className="section-subtitle">Detect and sanitize PII across text, images, PDFs, audio, and video</div>
                            </div>
                            <div className="controls-right">
                                <button className="btn btn-secondary btn-sm" onClick={handleClear}>✕ Clear</button>
                                <button className="btn btn-primary" onClick={activeTab === "text" ? handleRedactText : handleMediaRedact} disabled={loading || (activeTab === "text" ? !inputText.trim() : !selectedFile)}>
                                    {loading ? "Processing..." : "🛡️ Redact PII"}
                                </button>
                            </div>
                        </div>

                        <div className="section-body">
                            {/* Strategy cards */}
                            <div className="strategy-row">
                                {STRATEGIES.map(s => (
                                    <div key={s.id} className={`strat-card ${strategy === s.id ? "active" : ""}`} onClick={() => setStrategy(s.id)}>
                                        <div className="strat-icon">
                                            <span className="material-symbols-outlined" style={{ fontSize: 24 }}>{s.icon}</span>
                                        </div>
                                        <div className="strat-name">{s.name}</div>
                                        <div className="strat-desc">{s.desc}</div>
                                    </div>
                                ))}
                            </div>

                            {/* Engine status */}
                            <div className="controls-row">
                                <div className="controls-left">
                                    {coreEngines.length > 0 && (
                                        <div className="engine-dots">
                                            {coreEngines.map(([eng, on]) => (
                                                <div key={eng} className="engine-dot">
                                                    <div className={`dot ${on ? "on" : "off"}`}></div>
                                                    {eng.replace("_", " ").toUpperCase()}
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Mode tabs — all 6 modes */}
                            <div className="mode-tabs">
                                {MODES.map(m => (
                                    <button key={m.id} className={`mode-tab ${activeTab === m.id ? "active" : ""}`} onClick={() => { setActiveTab(m.id); setResult(null); setMediaResult(null); setError(null); setSelectedFile(null); }}>
                                        <span className="material-symbols-outlined" style={{ fontSize: 18 }}>{m.icon}</span> {m.label}
                                    </button>
                                ))}
                            </div>

                            {/* ═══ TEXT MODE ═══ */}
                            {activeTab === "text" && (
                                <>
                                    <div className="sample-row">
                                        <span className="sample-label">Quick samples:</span>
                                        {SAMPLE_TEXTS.map((s, i) => (
                                            <button key={i} className="sample-pill" onClick={() => setInputText(s.text)}>{s.label}</button>
                                        ))}
                                    </div>
                                    <div className="text-panels">
                                        <div className="text-panel">
                                            <div className="panel-label">
                                                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>input</span>
                                                    Input Text
                                                </span>
                                                <span className="chars">{inputText.length} chars</span>
                                            </div>
                                            <textarea className="text-area" value={inputText} onChange={e => setInputText(e.target.value)} placeholder="Paste text containing PII here..." />
                                        </div>
                                        <div className="text-panel">
                                            <div className="panel-label">
                                                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>output</span>
                                                    Redacted Output
                                                </span>
                                                {result && <button className="btn btn-secondary btn-sm" onClick={() => handleCopy(result?.redacted_text)}>
                                                    <span className="material-symbols-outlined" style={{ fontSize: 14 }}>content_copy</span>
                                                    Copy
                                                </button>}
                                            </div>
                                            <textarea className="text-area redacted" value={result?.redacted_text || ""} readOnly placeholder="Redacted text will appear here..." />
                                        </div>
                                    </div>
                                </>
                            )}

                            {/* ═══ MEDIA UPLOAD MODES (image/pdf/audio/video/file) ═══ */}
                            {activeTab !== "text" && (
                                <>
                                    <div className={`upload-zone ${dragOver ? "drag-over" : ""}`} onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop} onClick={() => fileInputRef.current?.click()}>
                                        <input ref={fileInputRef} type="file" accept={currentMode.accept || "*"} onChange={e => { const f = e.target.files?.[0]; if (f) handleFileSelect(f); }} />
                                        <div className="upload-icon">
                                            <span className="material-symbols-outlined" style={{ fontSize: 48, color: "var(--primary)" }}>{currentMode.icon}</span>
                                        </div>
                                        <div className="upload-title">{selectedFile ? selectedFile.name : `Drop ${currentMode.label} files here or click to browse`}</div>
                                        <div className="upload-subtitle">
                                            {selectedFile
                                                ? `${(selectedFile.size / 1024).toFixed(1)} KB — Ready for redaction`
                                                : `Accepted: ${currentMode.accept || "all file types"}`
                                            }
                                        </div>
                                        {!selectedFile && (
                                            <div className="format-badges">
                                                {(currentMode.accept || ".txt").split(",").map(f => <span key={f} className="format-badge">{f.toUpperCase()}</span>)}
                                            </div>
                                        )}
                                    </div>

                                    {/* ═══ MEDIA RESULT — Download + Audit ═══ */}
                                    {mediaResult && !loading && (
                                        <div className="media-result-card slide-up" style={{ marginTop: 20 }}>
                                            {/* Download bar */}
                                            <div className="download-bar">
                                                <div className="download-info">
                                                    <span className="material-symbols-outlined" style={{ fontSize: 32, color: "var(--primary)" }}>
                                                        {activeTab === "image" ? "image" : activeTab === "pdf" ? "picture_as_pdf" : activeTab === "audio" ? "audio_file" : "video_file"}
                                                    </span>
                                                    <div>
                                                        <div className="download-filename">redacted_{selectedFile?.name || "output"}</div>
                                                        <div className="download-meta">
                                                            {mediaResult.total_entities || 0} entities redacted
                                                            {" · "}
                                                            {mediaResult.processing_time_ms?.toFixed(0) || "—"}ms
                                                            {mediaResult.total_pages && ` · ${mediaResult.total_pages} pages`}
                                                            {mediaResult.audio_duration_ms && ` · ${(mediaResult.audio_duration_ms / 1000).toFixed(1)}s`}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="download-actions">
                                                    <button className="btn btn-primary" onClick={() => handleDownload(mediaResult.job_id)} disabled={!mediaResult.job_id}>
                                                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>download</span>
                                                        Download Redacted File
                                                    </button>
                                                    <button className="btn btn-secondary btn-sm" onClick={() => handleCopy(JSON.stringify(mediaResult.audit_log || mediaResult.per_page_audit || mediaResult.visual_audit || [], null, 2))}>
                                                        📋 Copy Audit Log
                                                    </button>
                                                </div>
                                            </div>

                                            {/* Result metrics */}
                                            <div className="results-metrics" style={{ marginTop: 16 }}>
                                                <div className="result-metric highlight">
                                                    <div className="result-metric-icon">
                                                        <span className="material-symbols-outlined">search</span>
                                                    </div>
                                                    <div className="result-metric-val">{mediaResult.total_entities || 0}</div>
                                                    <div className="result-metric-label">Entities Found</div>
                                                </div>
                                                <div className="result-metric">
                                                    <div className="result-metric-icon">
                                                        <span className="material-symbols-outlined">bolt</span>
                                                    </div>
                                                    <div className="result-metric-val">{mediaResult.processing_time_ms?.toFixed(0) || "—"}<span>ms</span></div>
                                                    <div className="result-metric-label">Processing Time</div>
                                                </div>
                                                {mediaResult.total_beep_segments !== undefined && (
                                                    <div className="result-metric">
                                                        <div className="result-metric-icon">
                                                            <span className="material-symbols-outlined">volume_up</span>
                                                        </div>
                                                        <div className="result-metric-val">{mediaResult.total_beep_segments}</div>
                                                        <div className="result-metric-label">Beep Segments</div>
                                                    </div>
                                                )}
                                                {mediaResult.total_pages !== undefined && (
                                                    <div className="result-metric">
                                                        <div className="result-metric-icon">
                                                            <span className="material-symbols-outlined">description</span>
                                                        </div>
                                                        <div className="result-metric-val">{mediaResult.total_pages}</div>
                                                        <div className="result-metric-label">Pages</div>
                                                    </div>
                                                )}
                                                {mediaResult.total_visual_redactions !== undefined && (
                                                    <div className="result-metric">
                                                        <div className="result-metric-icon">
                                                            <span className="material-symbols-outlined">visibility</span>
                                                        </div>
                                                        <div className="result-metric-val">{mediaResult.total_visual_redactions}</div>
                                                        <div className="result-metric-label">Visual Redactions</div>
                                                    </div>
                                                )}
                                                {mediaResult.image_dimensions && (
                                                    <div className="result-metric">
                                                        <div className="result-metric-icon">
                                                            <span className="material-symbols-outlined">architecture</span>
                                                        </div>
                                                        <div className="result-metric-val" style={{ fontSize: 16 }}>{mediaResult.image_dimensions.width}×{mediaResult.image_dimensions.height}</div>
                                                        <div className="result-metric-label">Dimensions</div>
                                                    </div>
                                                )}
                                            </div>

                                            {/* Transcript for audio/video */}
                                            {(mediaResult.original_transcript || mediaResult.audio_result?.original_transcript) && (
                                                <div style={{ marginTop: 16 }}>
                                                    <div className="text-panels">
                                                        <div className="text-panel">
                                                            <div className="panel-label">
                                                                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>record_voice_over</span>
                                                                    Original Transcript
                                                                </span>
                                                            </div>
                                                            <textarea className="text-area" value={mediaResult.original_transcript || mediaResult.audio_result?.original_transcript || ""} readOnly style={{ minHeight: 150 }} />
                                                        </div>
                                                        <div className="text-panel">
                                                            <div className="panel-label">
                                                                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                                    <span className="material-symbols-outlined" style={{ fontSize: 16 }}>voice_over_off</span>
                                                                    Redacted Transcript
                                                                </span>
                                                            </div>
                                                            <textarea className="text-area redacted" value={mediaResult.redacted_transcript || mediaResult.audio_result?.redacted_transcript || ""} readOnly style={{ minHeight: 150 }} />
                                                        </div>
                                                    </div>
                                                </div>
                                            )}

                                            {/* OCR text for image */}
                                            {mediaResult.ocr_text && (
                                                <div style={{ marginTop: 16 }}>
                                                    <div className="panel-label">
                                                        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>spellcheck</span>
                                                            Extracted Text (OCR)
                                                        </span>
                                                    </div>
                                                    <textarea className="text-area" value={mediaResult.ocr_text} readOnly style={{ minHeight: 100 }} />
                                                </div>
                                            )}

                                            {/* Full text for PDF */}
                                            {mediaResult.full_text && (
                                                <div style={{ marginTop: 16 }}>
                                                    <div className="panel-label">
                                                        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>description</span>
                                                            Extracted PDF Text
                                                        </span>
                                                    </div>
                                                    <textarea className="text-area" value={mediaResult.full_text} readOnly style={{ minHeight: 100 }} />
                                                </div>
                                            )}

                                            {/* Audit log table */}
                                            {(mediaResult.audit_log?.length > 0 || mediaResult.per_page_audit?.length > 0) && (
                                                <div style={{ marginTop: 16, maxHeight: 320, overflowY: "auto" }}>
                                                    <div className="panel-label" style={{ marginBottom: 8 }}>
                                                        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>list_alt</span>
                                                            Audit Log
                                                        </span>
                                                    </div>
                                                    <table className="data-table">
                                                        <thead>
                                                            <tr>
                                                                <th>Entity Type</th>
                                                                <th>Value</th>
                                                                <th>Confidence</th>
                                                                <th>Details</th>
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {(mediaResult.audit_log || []).map((entry, i) => (
                                                                <tr key={i}>
                                                                    <td><span className="severity-badge low">{entry.entity_type}</span></td>
                                                                    <td style={{ color: "#DC2626", fontWeight: 500 }}>{entry.value}</td>
                                                                    <td>{entry.confidence ? `${(entry.confidence * 100).toFixed(0)}%` : "—"}</td>
                                                                    <td style={{ fontSize: 11, color: "var(--text-muted)" }}>
                                                                        {entry.start_ms !== undefined && `${entry.start_ms}ms–${entry.end_ms}ms`}
                                                                        {entry.pixel_coordinates && `${JSON.stringify(entry.pixel_coordinates.bounding_rect)}`}
                                                                        {entry.frame !== undefined && `Frame ${entry.frame}`}
                                                                    </td>
                                                                </tr>
                                                            ))}
                                                            {/* Per-page audit for PDFs */}
                                                            {(mediaResult.per_page_audit || []).flatMap((page, pi) =>
                                                                (page.redactions || []).map((r, ri) => (
                                                                    <tr key={`p${pi}-${ri}`}>
                                                                        <td><span className="severity-badge low">{r.entity_type}</span></td>
                                                                        <td style={{ color: "#DC2626", fontWeight: 500 }}>{r.value}</td>
                                                                        <td>{r.confidence ? `${(r.confidence * 100).toFixed(0)}%` : "—"}</td>
                                                                        <td style={{ fontSize: 11, color: "var(--text-muted)" }}>Page {page.page} · ({r.coordinates?.x0},{r.coordinates?.y0})→({r.coordinates?.x1},{r.coordinates?.y1})</td>
                                                                    </tr>
                                                                ))
                                                            )}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {/* Legacy file result */}
                                    {activeTab === "file" && result && !loading && (
                                        <div className="text-panels" style={{ marginTop: 20 }}>
                                            <div className="text-panel">
                                                <div className="panel-label">
                                                    <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>description</span>
                                                        Original
                                                    </span>
                                                </div>
                                                <textarea className="text-area" value={result.original_text || ""} readOnly />
                                            </div>
                                            <div className="text-panel">
                                                <div className="panel-label">
                                                    <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>output</span>
                                                        Redacted
                                                    </span>
                                                    <button className="btn btn-secondary btn-sm" onClick={() => handleCopy(result.redacted_text)}>
                                                        <span className="material-symbols-outlined" style={{ fontSize: 14 }}>content_copy</span>
                                                    </button>
                                                </div>
                                                <textarea className="text-area redacted" value={result.redacted_text || ""} readOnly />
                                            </div>
                                        </div>
                                    )}
                                </>
                            )}

                            {/* Loading */}
                            {loading && (
                                <div className="loading-card">
                                    <div className="spinner"></div>
                                    <div className="loading-text">
                                        {isMediaMode ? `Processing ${currentMode.label.toLowerCase()} redaction...` : "Processing PII detection pipeline..."}
                                    </div>
                                    <div className="loading-steps">
                                        {LOADING_STEPS.map((s, i) => (
                                            <div key={i} className={`loading-step ${i < loadingStep ? "done" : i === loadingStep ? "active" : ""}`}>
                                                {i < loadingStep ? "✅" : i === loadingStep ? "⏳" : "○"} {s}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Error */}
                            {error && (
                                <div className="error-card">
                                    <span style={{ fontSize: "1.3rem" }}>⚠️</span>
                                    <div className="error-text">{error}. Make sure backend is running: <code>uvicorn app.main:app --reload</code></div>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* ═══ TEXT RESULTS ═══ */}
                {isOnDashboard && result && !loading && activeTab === "text" && (
                    <div className="results-section slide-up">
                        <div className="results-metrics">
                            <div className="result-metric highlight">
                                <div className="result-metric-icon">🔍</div>
                                <div className="result-metric-val">{result.total_entities}</div>
                                <div className="result-metric-label">PII Entities Found</div>
                            </div>
                            <div className="result-metric">
                                <div className="result-metric-icon">⚡</div>
                                <div className="result-metric-val">{result.processing_time_ms?.toFixed(0)}<span>ms</span></div>
                                <div className="result-metric-label">Processing Time</div>
                            </div>
                            <div className="result-metric">
                                <div className="result-metric-icon">🎯</div>
                                <div className="result-metric-val">{result.stats?.avg_confidence ? (result.stats.avg_confidence * 100).toFixed(0) : "—"}<span>%</span></div>
                                <div className="result-metric-label">Avg Confidence</div>
                            </div>
                            <div className="result-metric">
                                <div className="result-metric-icon">{result.verification_passed ? "✅" : "⚠️"}</div>
                                <div className="result-metric-val" style={{ fontSize: 16 }}>{result.verification_passed ? "PASSED" : "REVIEW"}</div>
                                <div className="result-metric-label">Verification</div>
                            </div>
                        </div>

                        {result.entities_found?.length > 0 && (
                            <div className="results-grid">
                                <div className="section-card">
                                    <div className="section-header">
                                        <div><div className="section-title" style={{ fontSize: 15 }}>🏷️ Detected Entities</div></div>
                                    </div>
                                    <div className="entity-list">
                                        {result.entities_found.map((ent, i) => {
                                            const c = ENTITY_COLORS[ent.entity_type] || DEFAULT_COLOR;
                                            return (
                                                <div key={i} className="entity-tag" style={{ background: c.bg, color: c.color, borderColor: c.border }}>
                                                    <span className="type">{ent.entity_type}</span>
                                                    <span className="val">"{ent.value}"</span>
                                                    <span className="conf">{(ent.confidence * 100).toFixed(0)}%</span>
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>

                                <div className="section-card">
                                    <div className="section-header">
                                        <div><div className="section-title" style={{ fontSize: 15 }}>📊 Entity Distribution</div></div>
                                    </div>
                                    {result.stats?.by_type && (
                                        <div className="chart-area">
                                            <div className="pie-chart" style={{ background: generatePieGradient(result.stats) }}></div>
                                            <div className="chart-legend">
                                                {Object.entries(result.stats.by_type).sort((a, b) => b[1] - a[1]).map(([type, count], i) => (
                                                    <div key={type} className="legend-item">
                                                        <span className="legend-dot" style={{ background: PIE_COLORS[i % PIE_COLORS.length] }}></span>
                                                        <span className="legend-label">{type}</span>
                                                        <span className="legend-count">{count}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                    <div style={{ maxHeight: 260, overflowY: "auto" }}>
                                        <table className="data-table">
                                            <thead><tr><th>Type</th><th>Original</th><th>Redacted</th><th>Conf.</th><th>Source</th></tr></thead>
                                            <tbody>
                                                {result.entities_found.map((ent, i) => (
                                                    <tr key={i}>
                                                        <td><span className="severity-badge low">{ent.entity_type}</span></td>
                                                        <td style={{ color: "#DC2626", fontWeight: 500 }}>{ent.value}</td>
                                                        <td style={{ color: "#0F766E", fontWeight: 500 }}>{ent.redacted_value || "—"}</td>
                                                        <td>
                                                            <div className="conf-bar"><div className={`conf-fill ${ent.confidence >= 0.8 ? "high" : ent.confidence >= 0.5 ? "med" : "low"}`} style={{ width: `${ent.confidence * 100}%` }}></div></div>
                                                            {(ent.confidence * 100).toFixed(0)}%
                                                        </td>
                                                        <td style={{ textTransform: "uppercase", fontSize: 11, color: "var(--text-muted)", fontWeight: 700 }}>{ent.source}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* ═══ ANALYTICS TAB ═══ */}
                {activeTab === "stats" && (
                    <div className="slide-up">
                        <div style={{ marginBottom: 36 }}>
                            <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-1.5px", color: "#fff", fontFamily: "var(--font-heading)" }}>Analytics <span style={{ background: "var(--gradient)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Overview</span></h1>
                            <p style={{ color: "var(--text-muted)", marginTop: 8, fontSize: 14 }}>Real-time monitoring across all Cenz-AI redaction modalities.</p>
                            <div style={{ height: 1, background: "linear-gradient(90deg, rgba(0,255,136,0.3), rgba(59,130,246,0.2), transparent)", marginTop: 20 }} />
                        </div>

                        <div className="metrics-row" style={{ margin: 0, padding: 0, marginBottom: 32 }}>
                            <div className="metric-card">
                                <div className="metric-top"><div className="metric-icon indigo"><span className="material-symbols-outlined">visibility_off</span></div><span className="metric-badge green">Live</span></div>
                                <div className="metric-label">Total Redactions</div>
                                <div className="metric-value">{systemStats?.total_entities_detected || 0}</div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-top"><div className="metric-icon purple"><span className="material-symbols-outlined">folder</span></div><span className="metric-badge green">Live</span></div>
                                <div className="metric-label">Files Processed</div>
                                <div className="metric-value">{systemStats?.total_files_processed || 0}</div>
                            </div>
                            <div className="metric-card">
                                <div className="metric-top"><div className="metric-icon blue"><span className="material-symbols-outlined">policy</span></div><span className="metric-badge green">Live</span></div>
                                <div className="metric-label">Total Requests</div>
                                <div className="metric-value">{systemStats?.total_requests || 0}</div>
                            </div>
                        </div>

                        <div className="results-grid" style={{ marginBottom: 32 }}>
                            <div className="section-card">
                                <div className="section-header"><div className="section-title" style={{ fontSize: 14 }}>Detection Engines</div></div>
                                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: 12, padding: 20 }}>
                                    {engineStatus && Object.entries(engineStatus).map(([eng, on]) => (
                                        <div key={eng} style={{
                                            padding: "18px 12px",
                                            borderRadius: 12,
                                            textAlign: "center",
                                            background: on ? "rgba(0,255,136,0.05)" : "rgba(239,68,68,0.04)",
                                            border: `1px solid ${on ? "rgba(0,255,136,0.2)" : "rgba(239,68,68,0.12)"}`,
                                            boxShadow: on ? "0 0 16px rgba(0,255,136,0.06)" : "none",
                                            transition: "all 0.25s"
                                        }}>
                                            <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
                                                <div style={{
                                                    width: 8, height: 8, borderRadius: "50%",
                                                    background: on ? "var(--primary)" : "#ef4444",
                                                    boxShadow: on ? "0 0 8px var(--primary)" : "none",
                                                    animation: on ? "dotPulse 2s infinite" : "none"
                                                }} />
                                            </div>
                                            <div style={{ fontWeight: 700, fontSize: 11, textTransform: "uppercase", color: on ? "rgba(0,255,136,0.8)" : "#475569", letterSpacing: "0.5px" }}>{eng.replace("_", " ")}</div>
                                            <div style={{ fontSize: 11, color: on ? "rgba(0,255,136,0.6)" : "#ef4444", fontWeight: 600, marginTop: 3 }}>{on ? "Online" : "Offline"}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="section-card">
                                <div className="section-header"><div className="section-title" style={{ fontSize: 14 }}>Strategy Usage</div></div>
                                {systemStats?.strategy_usage && Object.keys(systemStats.strategy_usage).length > 0 ? (
                                    <div style={{ padding: 20 }}>
                                        {Object.entries(systemStats.strategy_usage).map(([strat, count]) => {
                                            const total = Object.values(systemStats.strategy_usage).reduce((a, b) => a + b, 0);
                                            const pct = ((count / total) * 100).toFixed(0);
                                            const s = STRATEGIES.find(x => x.id === strat);
                                            return (
                                                <div key={strat} className="detect-row" style={{ marginBottom: 12 }}>
                                                    <div className="detect-label">{s?.icon} {s?.name || strat}</div>
                                                    <div className="detect-bar"><div className="detect-bar-fill indigo" style={{ width: `${pct}%` }}></div></div>
                                                    <div className="detect-pct">{count}</div>
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : <div style={{ padding: 40, textAlign: "center", color: "var(--text-muted)" }}>No data yet.</div>}
                            </div>
                        </div>
                    </div>
                )}

                {/* ═══ API DOCS TAB ═══ */}
                {activeTab === "api" && (
                    <div className="slide-up">
                        <div style={{ marginBottom: 36 }}>
                            <h1 style={{ fontSize: 32, fontWeight: 700, letterSpacing: "-1.5px", color: "#fff", fontFamily: "var(--font-heading)" }}>API <span style={{ background: "var(--gradient)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>Documentation</span></h1>
                            <p style={{ color: "var(--text-muted)", marginTop: 8, fontSize: 14 }}>REST API reference for integrating Cenz-AI into your infrastructure.</p>
                            <div style={{ height: 1, background: "linear-gradient(90deg, rgba(0,255,136,0.3), rgba(59,130,246,0.2), transparent)", marginTop: 20 }} />
                        </div>

                        <div className="section-card" style={{ marginBottom: 20 }}>
                            <div className="section-header">
                                <div className="section-title" style={{ fontSize: 14 }}>📡 REST API Reference</div>
                                <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="btn btn-primary btn-sm">Swagger UI ↗</a>
                            </div>
                            <div>
                                {[
                                    { method: "POST", path: "/api/v1/redact/text", desc: "Redact PII from text" },
                                    { method: "POST", path: "/api/v1/redact/image", desc: "Redact PII from image (JPG/PNG/WEBP)" },
                                    { method: "POST", path: "/api/v1/redact/pdf", desc: "Redact PII from PDF" },
                                    { method: "POST", path: "/api/v1/redact/audio", desc: "Redact PII from audio (MP3/WAV/M4A)" },
                                    { method: "POST", path: "/api/v1/redact/video", desc: "Redact PII from video (MP4/MOV/AVI)" },
                                    { method: "POST", path: "/api/v1/redact/file", desc: "Redact PII from any file (legacy)" },
                                    { method: "POST", path: "/api/v1/redact/batch", desc: "Batch text redaction" },
                                    { method: "GET", path: "/api/v1/download/{job_id}", desc: "Download redacted file" },
                                    { method: "GET", path: "/api/v1/download/{job_id}/info", desc: "Get download job details" },
                                    { method: "GET", path: "/api/v1/strategies", desc: "List redaction strategies" },
                                    { method: "GET", path: "/api/v1/engines", desc: "Engine status" },
                                    { method: "GET", path: "/api/v1/stats", desc: "Processing statistics" },
                                    { method: "GET", path: "/api/v1/health", desc: "Health check" },
                                ].map((ep, i) => (
                                    <div key={i} className="api-row">
                                        <span className={`api-method ${ep.method.toLowerCase()}`}>{ep.method}</span>
                                        <span className="api-path">{ep.path}</span>
                                        <span className="api-desc">{ep.desc}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="section-card">
                            <div className="section-header"><div className="section-title" style={{ fontSize: 14 }}>💻 Example Usage</div></div>
                            <div style={{ padding: 20 }}>
                                <pre className="code-block">{`# Text Redaction
curl -X POST http://localhost:8000/api/v1/redact/text \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Contact John at john@email.com", "strategy": "mask"}'

# Image Redaction (returns job_id for download)
curl -X POST http://localhost:8000/api/v1/redact/image \\
  -F "file=@photo.jpg" -F "strategy=mask"

# PDF Redaction
curl -X POST http://localhost:8000/api/v1/redact/pdf \\
  -F "file=@document.pdf" -F "strategy=tag_replace"

# Audio Redaction (beeps over PII)
curl -X POST http://localhost:8000/api/v1/redact/audio \\
  -F "file=@recording.mp3" -F "strategy=mask"

# Video Redaction (blur faces + beep audio + black out text)
curl -X POST http://localhost:8000/api/v1/redact/video \\
  -F "file=@meeting.mp4" -F "strategy=mask"

# Download redacted file
curl -O http://localhost:8000/api/v1/download/{job_id}`}</pre>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* ═══ PRIVACY & COMPLIANCE SECTION ═══ */}
            <ComplianceSection />

            {/* ═══ FOOTER ═══ */}
            <footer className="site-footer">
                <div className="footer-inner">
                    <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                        <span className="footer-text" style={{ color: "#fff", fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 700 }}>Cenz-<span style={{ color: "var(--primary)", textShadow: "0 0 12px rgba(0,255,136,0.5)" }}>AI</span></span>
                        <span style={{ color: "rgba(0,255,136,0.2)" }}>|</span>
                        <span className="footer-text">v2.0.0 — Text · Image · PDF · Audio · Video</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                        <div className="footer-text">Enterprise Privacy Infrastructure Platform © 2025</div>
                        <a href="/privacy-compliance" className="nav-compliance-link">Privacy & Compliance ↗</a>
                    </div>
                </div>
            </footer>
        </div>
    );
}
