# 🛡️ Danger Sensor v1.0 // LOCAL QA GATE PROTOCOL

A specialized **browser-based diagnostic tool** designed to detect signal corruption in audio waveforms and logical risks in text specifications. It functions as an objective gatekeeper using **deterministic consistency checks (as logged)**.

**Core scoring is deterministic and local: the same input yields identical scores. Optional services (e.g., transcription) never affect scoring. Every decision is traceable to versioned rules and measured features recorded in the audit log.**

* **Audio Scan**: Detects clipping, peak overflows, and data dropouts
* **Text Scan**: Analyzes ambiguity, numerical density, and responsibility gaps
* **Privacy-First**: Core scoring is local and deterministic; your data remains within the local boundary
* **Technical Framework**: Implementation of **Rule-based consistency gating under fixed constraints**

No installation required — a single-file solution for professional risk management.

---

## 🔧 Features

* **Audio Integrity Scanner**: Real-time analysis of `clip_rate`, `true_peak`, `crest_factor`, and `dropout_count`
* **Spec/Contract Analyzer**: Scans for "Poem Specs" and "Undefined Responsibilities" using weighted keyword density
* **Dynamic Calibration**: Switch between **STRICT**, **DEFAULT**, and **LENIENT** presets to match project rigidity
* **HUD Interface**: Futuristic, high-visibility dashboard for immediate decision making
* **Audit Logging**: Traceable to **versioned rules and measured features** recorded in the audit log for later export

---

## 🔍 Technical Details: Detection Logic

The Text Analyzer operates by calculating the "Constraint Density" of the input document using **rule-based thresholds (versioned) with no ML in scoring**. It categorizes keywords into three distinct layers to determine if a specification has a valid "Engineering Constraints."

### 1. Ambiguity Detection (The "Poem" Filter)

Targets "weasel words" and non-committal language that obscure technical reality. High density in this category triggers a **POEM_SPEC_RISK**.

* **Detected Patterns**: `case-by-case`, `flexible`, `optimize`, `AI-driven`, `best-effort`, `at discretion`.
* **Logic**: These words often indicate a lack of concrete planning or an attempt to shift responsibility to "as-needed" scenarios, making the path to success defined as a **boundary incompleteness (fails consistency gates)**.

### 2. Numerical Density (The Engineering Backbone)

Scans for SI units and technical abbreviations that provide objective measurement.

* **Detected Patterns**: `ms`, `dB`, `%`, `Hz`, `hours`, `SLA`, `MTBF`, `throughput`, `latency`.
* **Logic**: A specification without numbers is not engineering; it is a wish. The sensor requires a minimum density of these units to allow a **PASS** status.

### 3. Responsibility Mapping (The Contractual Interface)

Identifies legal and operational boundaries that define the "In-Scope" and "Out-of-Scope" regions.

* **Detected Patterns**: `guarantee`, `scope`, `exclusion`, `liability`, `agreement`, `specification`.
* **Logic**: This layer ensures that numerical targets are backed by clear accountability. It detects the **Forward/Reverse predictability gap** where one party may be assuming infinite risk without defined exclusions.

### 4. Decision Matrix

* **RED (CUT)**: High Ambiguity + Zero Numerics. The consistency checks fail to converge under current constraints.
* **ORANGE (HOLD)**: Numerics present but no Responsibility defined (or vice-versa). The boundary is incomplete.
* **GREEN (PASS)**: High Numerical density balanced with **Consistency / residual gate** validation.

---

## 🎮 Hosted Demo

👉 **[https://danger-sensor.dim.productions](https://danger-sensor.dim.productions/)**
*(Still runs locally in your browser)*

**Hosting only serves the static file. Analysis runs fully in-browser; no data upload is required.**

Drag and drop your files or paste text to initialize the boundary scan.

---

## 📁 Repository Structure

```
danger-sensor/
├── index.html      # Main HUD application (Single-file)
└── README.md

```

---

## 🔧 Requirements

* **Chrome, Safari, Firefox, Edge** (Latest versions recommended)
* **Audio Support**: Standard Web Audio API compatibility
* **No external libraries / no scoring API**: Pure HTML/JS/CSS implementation; no external libraries or APIs required

---

## 📬 Contact

For collaboration, technical inquiries, or licensing:
**info@dim.productions**

---

© 2026 DIMProductions.
This tool supports secure data and contract validation workflows.