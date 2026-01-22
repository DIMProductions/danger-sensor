# 🛡️ Danger Sensor v1.0 // Physical Boundary Protocol

A specialized **browser-based diagnostic tool** designed to detect physical corruption in audio waveforms and logical "landmines" in text specifications. It functions as an objective gatekeeper using deterministic physical boundaries.

* **Audio Scan**: Detects clipping, peak overflows, and data dropouts
* **Text Scan**: Analyzes ambiguity, numerical density, and responsibility gaps
* **Privacy-First**: 100% local processing; your data never leaves the browser
* **Three-Pillar Protocol**: Implementation of Pinching, Boundary Temporal Asymmetry, and Readout

No installation required — a single-file solution for professional risk management.

---

## 🔧 Features

* **Audio Integrity Scanner**: Real-time analysis of `clip_rate`, `true_peak`, `crest_factor`, and `dropout_count`
* **Spec/Contract Analyzer**: Scans for "Poem Specs" and "Undefined Responsibilities" using weighted keyword density
* **Dynamic Calibration**: Switch between **STRICT**, **DEFAULT**, and **LENIENT** presets to match project rigidity
* **HUD Interface**: Futuristic, high-visibility dashboard for immediate decision making
* **Audit Logging**: Automatically records scan results to browser local storage for later export

---

## 🔍 Technical Details: Detection Logic

The Text Analyzer operates by calculating the "Boundary Density" of the input document. It categorizes keywords into three distinct layers to determine if a specification has a valid "Engineering Boundary."

### 1. Ambiguity Detection (The "Poem" Filter)
Targets "weasel words" and non-committal language that obscure technical reality. High density in this category triggers a **POEM_SPEC_RISK**.
- **Detected Patterns**: `case-by-case`, `flexible`, `optimize`, `AI-driven`, `best-effort`, `at discretion`.
- **Logic**: These words often indicate a lack of concrete planning or an attempt to shift responsibility to "as-needed" scenarios, making the path to success geometrically undefined.

### 2. Numerical Density (The Engineering Backbone)
Scans for SI units and technical abbreviations that provide objective measurement.
- **Detected Patterns**: `ms`, `dB`, `%`, `Hz`, `hours`, `SLA`, `MTBF`, `throughput`, `latency`.
- **Logic**: A specification without numbers is not engineering; it is a wish. The sensor requires a minimum density of these units to allow a **PASS** status.

### 3. Responsibility Mapping (The Contractual Interface)
Identifies legal and operational boundaries that define the "In-Scope" and "Out-of-Scope" regions.
- **Detected Patterns**: `guarantee`, `scope`, `exclusion`, `liability`, `agreement`, `specification`.
- **Logic**: This layer ensures that numerical targets are backed by clear accountability. It detects the "Boundary Asymmetry" where one party may be assuming infinite risk without defined exclusions.

### 4. Decision Matrix
- **RED (CUT)**: High Ambiguity + Zero Numerics. The "interpretation path" is too wide to converge on a result.
- **ORANGE (HOLD)**: Numerics present but no Responsibility defined (or vice-versa). The boundary is incomplete.
- **GREEN (PASS)**: High Numerical density balanced with clear Responsibility definitions.

---

## 🎮 Try It Online

👉 **[https://danger-sensor.dim.productions](https://danger-sensor.dim.productions/)**

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
* **No Dependencies**: Pure HTML/JS/CSS implementation; no external libraries or APIs required

---

## 📬 Contact

For collaboration, technical inquiries, or licensing:

**info@dim.productions**

---

© 2026 DIMProductions.

This tool is part of the Three-Pillar Protocol for secure data and contract validation.

