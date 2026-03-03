"use client";

import { useEffect, useRef } from "react";

/* ─── Hooks: scroll reveal ─────────────────────────────────── */
function useScrollReveal() {
    const refs = useRef([]);
    useEffect(() => {
        const observers = [];
        refs.current.forEach((el) => {
            if (!el) return;
            const obs = new IntersectionObserver(
                ([entry]) => {
                    if (entry.isIntersecting) {
                        el.classList.add("visible");
                        obs.disconnect();
                    }
                },
                { threshold: 0.1 }
            );
            obs.observe(el);
            observers.push(obs);
        });
        return () => observers.forEach((o) => o.disconnect());
    }, []);
    const addRef = (i) => (el) => { refs.current[i] = el; };
    return addRef;
}

/* ─── Data ──────────────────────────────────────────────────── */
const REGS_DETAILED = [
    {
        flag: "IN",
        name: "DPDP Act 2023",
        region: "India · Digital Personal Data Protection Act",
        desc: "India's landmark data privacy legislation enacted in 2023 establishes a comprehensive framework for the protection of personal data of individuals (Data Principals) collected in digital form. The Act imposes obligations on Data Fiduciaries—entities that process personal data—to ensure lawful, purpose-limited, and consent-based data handling.",
        points: [
            "Requires explicit, informed consent before processing personal data",
            "Mandates data minimisation and purpose limitation",
            "Introduces Data Protection Board of India for enforcement",
            "Penalties of up to ₹250 crore per violation",
            "Applies to all digital personal data of Indian residents",
        ],
    },
    {
        flag: "EU",
        name: "GDPR",
        region: "Europe · General Data Protection Regulation",
        desc: "The GDPR is the world's most comprehensive data protection law, applicable to any organisation processing personal data of EU residents regardless of where the organisation is located. It enshrines privacy as a fundamental right and mandates privacy-by-design as an architectural principle — not an afterthought.",
        points: [
            "Right to erasure, portability, and access for data subjects",
            "Privacy-by-design and data protection impact assessments (DPIA)",
            "72-hour breach notification requirement",
            "Fines up to €20M or 4% of global annual revenue",
            "Data Protection Officer (DPO) mandatory for large-scale processing",
        ],
    },
    {
        flag: "US",
        name: "HIPAA",
        region: "USA · Health Insurance Portability & Accountability Act",
        desc: "HIPAA establishes national standards for protecting sensitive patient health information (PHI) in the United States. It applies to covered entities (healthcare providers, insurers) and their business associates who handle PHI in any form — including calls, documents, images, and video recordings.",
        points: [
            "Protected Health Information (PHI) must be de-identified before sharing",
            "Minimum Necessary Standard for data access and sharing",
            "Administrative, physical, and technical safeguard requirements",
            "Civil penalties up to $1.9M per violation category per year",
            "Applies to audio transcripts, clinical notes, and medical images",
        ],
    },
];

const ARCH_ITEMS = [
    {
        icon: "description",
        title: "Text Redaction",
        desc: "Multi-engine NLP + regex detection identifies names, SSNs, emails, addresses, and 20+ PII types within free-form text. Redaction is applied inline, preserving document structure integrity. Supports GDPR Article 25 (data minimisation) and DPDP consent workflows.",
        tags: ["GDPR", "DPDP", "HIPAA", "SOC 2"],
    },
    {
        icon: "image",
        title: "OCR + Image Redaction",
        desc: "Combines EasyOCR and Tesseract for multi-language text extraction from images and scanned documents. PII bounding boxes are detected, then visually blackened at the pixel level — making redaction forensically irreversible. Critical for HIPAA-regulated clinical imaging.",
        tags: ["HIPAA", "ISO 27001", "GDPR"],
    },
    {
        icon: "mic",
        title: "Audio Redaction",
        desc: "Whisper ASR transcribes speech to text, NLP detects PII tokens, and the corresponding audio segments are replaced with beep tones. Complete audit logs map each redacted span back to the original waveform timestamp. Aligned with HIPAA call recording standards.",
        tags: ["HIPAA", "GDPR", "SOC 2"],
    },
    {
        icon: "movie",
        title: "Video Anonymization",
        desc: "Frame-by-frame OCR detects on-screen PII text; face detection blurs identities; and the audio track is processed through the audio redaction pipeline. Combined outputs create a fully anonymized video file compliant with DPDP, GDPR, and broadcast privacy standards.",
        tags: ["DPDP", "GDPR", "HIPAA", "ISO 27001"],
    },
];

const TRUST_ITEMS = [
    {
        icon: "lock",
        title: "AES-256 Encryption",
        desc: "All data in transit is protected with TLS 1.3. Temporary in-memory buffers use process-level isolation — no plaintext data ever touches persistent storage.",
    },
    {
        icon: "inventory_2",
        title: "Zero-Persistence Storage",
        desc: "Uploaded files are streamed directly into the redaction pipeline and deleted immediately post-processing. No file is retained beyond the active API session.",
    },
    {
        icon: "assignment",
        title: "Immutable Audit Logs",
        desc: "Every detection event is logged with: entity type, engine source, confidence score, redaction strategy applied, and UTC timestamp — ready for DPA or HIPAA audit requests.",
    },
    {
        icon: "vpn_key",
        title: "Access Control",
        desc: "Role-based access and API key authentication ensure only authorised services can invoke the redaction pipeline. Session tokens expire after inactivity.",
    },
];

/* ─── Component ─────────────────────────────────────────────── */
export default function PrivacyCompliancePage() {
    const addRef = useScrollReveal();

    return (
        <div className="priv-page fade-in">

            {/* ── NAVBAR ── */}
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
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                        <a href="/" className="btn btn-secondary btn-sm" style={{ textDecoration: "none" }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>arrow_back</span>
                            Back to Platform
                        </a>
                        <a href="/" className="btn btn-primary btn-sm" style={{ textDecoration: "none" }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>shield</span>
                            Try Redaction
                        </a>
                    </div>
                </div>
            </nav>

            {/* ── HERO ── */}
            <div className="priv-hero">
                <div className="priv-hero-bg" />
                <div className="priv-hero-overlay" />
                <div className="priv-hero-content">
                    <div className="comp-eyebrow" style={{ margin: "0 auto 20px" }}>
                        <span className="material-symbols-outlined" style={{ fontSize: 16 }}>public</span>
                        Global Privacy & Compliance Framework
                    </div>
                    <h1 className="priv-hero-title">
                        Privacy. Compliance.<br /><span>By Design.</span>
                    </h1>
                    <p className="priv-hero-sub">
                        Cenz-AI is architected from the ground up to support enterprise compliance across DPDP, GDPR, HIPAA, ISO 27001, and SOC 2 — delivering AI-powered PII redaction that meets the highest global regulatory standards.
                    </p>
                    <div className="priv-hero-tags">
                        {["DPDP Act 2023", "GDPR", "HIPAA", "ISO 27001", "SOC 2"].map((t) => (
                            <span key={t} className="priv-hero-tag">{t}</span>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── PAGE BODY ── */}
            <div className="priv-container">

                {/* image mosaic */}
                <div className="priv-image-mosaic comp-reveal" ref={addRef(0)}>
                    <div className="priv-mosaic-img">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src="/compliance_globe.png" alt="Global data compliance" />
                        <div className="priv-mosaic-img-overlay" />
                        <div style={{
                            position: "absolute", bottom: 20, left: 20, zIndex: 2,
                            background: "rgba(3,7,18,0.8)", backdropFilter: "blur(12px)",
                            border: "1px solid rgba(0,255,136,0.2)", borderRadius: 10,
                            padding: "10px 16px"
                        }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--primary)", textTransform: "uppercase", letterSpacing: "1.5px" }}>Global Coverage</div>
                            <div style={{ fontSize: 13, color: "#fff", fontWeight: 600, marginTop: 2 }}>5 Major Regulatory Frameworks</div>
                        </div>
                    </div>
                    <div className="priv-mosaic-img">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src="/compliance_shield.png" alt="AI security shield" />
                        <div className="priv-mosaic-img-overlay" />
                        <div style={{
                            position: "absolute", bottom: 20, left: 20, zIndex: 2,
                            background: "rgba(3,7,18,0.8)", backdropFilter: "blur(12px)",
                            border: "1px solid rgba(0,255,136,0.2)", borderRadius: 10,
                            padding: "10px 16px"
                        }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: "var(--primary)", textTransform: "uppercase", letterSpacing: "1.5px" }}>Secure by Design</div>
                            <div style={{ fontSize: 13, color: "#fff", fontWeight: 600, marginTop: 2 }}>7-Engine Detection Stack</div>
                        </div>
                    </div>
                </div>

                {/* ── SECTION 1: Regulation Breakdown ── */}
                <div className="priv-section comp-reveal" ref={addRef(1)}>
                    <div className="priv-section-label">
                        <div className="priv-section-dot" />
                        <span className="priv-section-tag">Regulation Breakdown</span>
                    </div>
                    <h2 className="priv-section-title">Key Regulatory Frameworks</h2>
                    <p className="priv-section-sub">
                        Detailed compliance mapping for the three primary data privacy regulations our platform is engineered to support.
                    </p>
                    <div className="priv-reg-grid">
                        {REGS_DETAILED.map((reg) => (
                            <div key={reg.name} className="priv-reg-card">
                                <div className="priv-reg-card-header">
                                    <div className="priv-reg-card-flag-wrap" style={{ fontSize: 14, fontWeight: 800, color: "var(--primary)", letterSpacing: 1 }}>{reg.flag}</div>
                                    <div>
                                        <div className="priv-reg-card-name">{reg.name}</div>
                                        <div className="priv-reg-card-region">{reg.region}</div>
                                    </div>
                                </div>
                                <div className="priv-reg-card-body">
                                    <p className="priv-reg-card-desc">{reg.desc}</p>
                                    <ul className="priv-reg-card-points">
                                        {reg.points.map((p) => <li key={p}>{p}</li>)}
                                    </ul>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* ISO + SOC 2 compact strip */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 20 }}>
                        {[
                            { flag: "INTL", name: "ISO 27001", region: "International Security Standard", desc: "Provides a systematic approach to managing sensitive company and customer information. Our development and operational pipelines align with ISO 27001 Annex A controls for access management, cryptographic controls, and incident response." },
                            { flag: "SOC2", name: "SOC 2 Type II", region: "Enterprise Trust & Operational Integrity", desc: "Validates that our platform meets the AICPA Trust Services Criteria for security, availability, processing integrity, confidentiality, and privacy. An independent audit validates our operational adherence to these controls." },
                        ].map((r) => (
                            <div key={r.name} className="priv-reg-card">
                                <div className="priv-reg-card-header">
                                    <div className="priv-reg-card-flag-wrap" style={{ fontSize: 13, fontWeight: 800, color: "var(--primary)", letterSpacing: 1 }}>{r.flag}</div>
                                    <div>
                                        <div className="priv-reg-card-name">{r.name}</div>
                                        <div className="priv-reg-card-region">{r.region}</div>
                                    </div>
                                </div>
                                <div className="priv-reg-card-body">
                                    <p className="priv-reg-card-desc">{r.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="comp-glow-divider" />

                {/* ── SECTION 2: AI Compliance Architecture ── */}
                <div className="priv-section comp-reveal" ref={addRef(2)}>
                    <div className="priv-section-label">
                        <div className="priv-section-dot" />
                        <span className="priv-section-tag">AI Architecture</span>
                    </div>
                    <h2 className="priv-section-title">How Our AI Supports Regulatory Requirements</h2>
                    <p className="priv-section-sub">
                        Each detection modality in Cenz-AI is mapped to specific regulatory obligations — ensuring compliance is embedded into the redaction pipeline, not bolted on.
                    </p>
                    <div className="priv-arch-grid">
                        {ARCH_ITEMS.map((item) => (
                            <div key={item.title} className="priv-arch-card">
                                <div className="priv-arch-icon">
                                    <span className="material-symbols-outlined">{item.icon}</span>
                                </div>
                                <div style={{ flex: 1 }}>
                                    <div className="priv-arch-title">{item.title}</div>
                                    <p className="priv-arch-desc">{item.desc}</p>
                                    <div className="priv-arch-tags">
                                        {item.tags.map((tag) => (
                                            <span key={tag} className="priv-arch-tag">{tag}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="comp-glow-divider" />

                {/* ── SECTION 3: Trust & Security ── */}
                <div className="priv-section comp-reveal" ref={addRef(3)}>
                    <div className="priv-section-label">
                        <div className="priv-section-dot" />
                        <span className="priv-section-tag">Security Commitments</span>
                    </div>
                    <h2 className="priv-section-title">Trust & Security Architecture</h2>
                    <p className="priv-section-sub">
                        Every layer of Cenz-AI is designed with security-first principles — protecting your data throughout the entire processing lifecycle.
                    </p>
                    <div className="priv-trust-grid">
                        {TRUST_ITEMS.map((item) => (
                            <div key={item.title} className="priv-trust-card">
                                <div className="priv-trust-icon">
                                    <span className="material-symbols-outlined">{item.icon}</span>
                                </div>
                                <div className="priv-trust-title">{item.title}</div>
                                <p className="priv-trust-desc">{item.desc}</p>
                            </div>
                        ))}
                    </div>

                    {/* Compliance commitment strip */}
                    <div style={{
                        marginTop: 28,
                        padding: "28px 32px",
                        borderRadius: 16,
                        background: "rgba(0,255,136,0.04)",
                        border: "1px solid rgba(0,255,136,0.12)",
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                        gap: 20,
                        alignItems: "center",
                    }}>
                        {[
                            { val: "0 bytes", label: "Persistent Storage" },
                            { val: "TLS 1.3", label: "Transport Security" },
                            { val: "AES-256", label: "Encryption Standard" },
                            { val: "100%", label: "In-Memory Processing" },
                            { val: "Full", label: "Audit Logging" },
                        ].map((s) => (
                            <div key={s.label} style={{ textAlign: "center" }}>
                                <div style={{
                                    fontFamily: "var(--font-heading)", fontSize: 22, fontWeight: 700,
                                    color: "var(--primary)", letterSpacing: "-0.5px", marginBottom: 4
                                }}>{s.val}</div>
                                <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.8px", fontWeight: 600 }}>{s.label}</div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="comp-glow-divider" />

                {/* ── CTA ── */}
                <div className="priv-cta-band comp-reveal" ref={addRef(4)}>
                    <div style={{
                        position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
                        backgroundImage: "url('/cyber_hero_bg.png')",
                        backgroundSize: "cover", backgroundPosition: "center",
                        filter: "brightness(0.08) saturate(1.5)", zIndex: 0
                    }} />
                    <h2 className="priv-cta-title">
                        Ready to Build <span>Compliant AI?</span>
                    </h2>
                    <p className="priv-cta-sub">
                        Start redacting PII across all modalities today — with full regulatory alignment built in from day one.
                    </p>
                    <div className="priv-cta-buttons">
                        <a href="/" className="btn btn-primary" style={{ textDecoration: "none" }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>shield</span>
                            Start Redacting PII
                        </a>
                        <a href="/" className="btn btn-secondary" style={{ textDecoration: "none" }}>
                            <span className="material-symbols-outlined" style={{ fontSize: 16 }}>code</span>
                            View API Documentation
                        </a>
                    </div>
                </div>

            </div>

            {/* ── FOOTER ── */}
            <footer className="site-footer">
                <div className="footer-inner">
                    <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
                        <span style={{ color: "#fff", fontFamily: "var(--font-heading)", fontSize: 13, fontWeight: 700 }}>
                            Cenz-<span style={{ color: "var(--primary)", textShadow: "0 0 12px rgba(0,255,136,0.5)" }}>AI</span>
                        </span>
                        <span style={{ color: "rgba(0,255,136,0.2)" }}>|</span>
                        <span className="footer-text">Privacy & Compliance Framework</span>
                    </div>
                    <div className="footer-text">Enterprise Privacy Infrastructure Platform © 2025</div>
                </div>
            </footer>
        </div>
    );
}
