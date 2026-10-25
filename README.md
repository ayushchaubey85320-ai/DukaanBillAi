# DukaanBillAi 🏪🇮🇳
### Self-Hosted, Offline & Online Conversational AI/ML Billing Agent for Indian Retail Shopkeepers

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688.svg)](https://fastapi.tiangolo.com)
[![React + Vite](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![Capacitor Android](https://img.shields.io/badge/Android-APK-3DDC84.svg)](https://capacitorjs.com)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Datasets-FFD21E.svg)](https://huggingface.co)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**DukaanBillAi** is an AI/ML conversational billing assistant built specifically for Indian retail store owners (Kirana, Medical/Pharmacy, Garments, Sweet Marts, Electronics, Restaurants).

It requires **zero external cloud LLM API keys** (no OpenAI, no Gemini, no external billing). It runs a self-hosted, calibrated TF-IDF and Logistic Regression pipeline augmented with **Hugging Face Hinglish instruction datasets** and acoustic phonetic normalizers for noisy retail environments.

---

## 🌟 Key Highlights

- **🧠 100% Self-Hosted ML Pipeline**:
  - Trained on **9,495+ synthetic & real-world retail utterances** across 27 intents.
  - Achieves **97.19% test accuracy** and **96.91% weighted F1-score**.
  - Integrated with Hugging Face datasets:
    - [`DSMJ910/hinglish-instruct-10k`](https://huggingface.co/datasets/DSMJ910/hinglish-instruct-10k)
    - [`HumynLabs/e-commerce-customersupport-hinglish-audio`](https://huggingface.co/datasets/HumynLabs/e-commerce-customersupport-hinglish-audio)
  - Sub-50ms inference latency on CPU with zero cloud costs.

- **🗣️ Vernacular & Speech-to-Text Phonetic Normalization**:
  - Understands English, Hindi (Devanagari), and mixed Hinglish numerals (*"dhai packet"*, *"dedh kilo"*, *"aadha liter"*, *"do sau pachas rupaye"*).
  - Intercepts acoustic misrecognitions from noisy microphones (e.g., *"travel"* ➔ *"chawal"*, *"dude"* ➔ *"doodh"*, *"ata"* ➔ *"atta"*).

- **🧾 Indian GST & Invoicing Engine**:
  - Automatic HSN code classification across 80+ products.
  - CGST/SGST (intra-state) vs IGST (inter-state) with reverse charge mechanism (RCM) validation.
  - Indian Rupee currency round-off (+/- ₹0.50 rule).
  - NPCI UPI QR Code Generation (compatible with PhonePe, Google Pay, Paytm, BHIM).
  - Official A4 Tax Invoice PDF generation (via ReportLab).
  - ESC/POS 80mm & 58mm thermal receipt formatting for POS printers.

- **📱 Dual Deployment (Online & Offline Mobile APK)**:
  - **Android Native App (`DukaanAI.apk`)**: Compiled using Capacitor & Gradle.
  - **Online Cloud Tunnel Support**: Works on 4G/5G mobile networks worldwide via instant cloud tunnel without requiring the phone to be on the same local Wi-Fi.
  - **Local Wi-Fi Mode**: Ultra-low latency mode when phone is connected to the shop's Wi-Fi router.

- **✅ 21 Automated Test Scenarios**:
  - All 21 real-world business scenarios passing (Kirana, Pharmacy, Garments, Restaurants, undo/cancellations, rate changes, discounts, GSTIN verification, session resets).

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│            Shopkeeper (Voice / Text Speech)            │
└───────────────────────────┬────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
    ┌──────────────────────┐  ┌──────────────────────┐
    │  Android Mobile APK  │  │   Desktop / Web UI   │
    │  (Capacitor Native)  │  │     (React/Vite)     │
    └──────────┬───────────┘  └──────────┬───────────┘
               │                         │
               └────────────┬────────────┘
                            │ HTTPS / LAN
                            ▼
    ┌────────────────────────────────────────────────────┐
    │              FastAPI Backend Server                │
    │                                                    │
    │   ┌────────────────────┐   ┌───────────────────┐   │
    │   │  Hinglish Tokenizer│   │ Offline Intent ML │   │
    │   │  & Phonetic ASR    │   │  (97.19% Acc)     │   │
    │   └─────────┬──────────┘   └─────────▲─────────┘   │
    │             │                        │             │
    │             ▼                        │             │
    │   ┌────────────────────┐   ┌─────────┴─────────┐   │
    │   │  Entity Extractor  │   │ HuggingFace 10k   │   │
    │   │  (Quantities/Units)│   │ Hinglish Corpus   │   │
    │   └─────────┬──────────┘   └───────────────────┘   │
    │             │                                      │
    │             ▼                                      │
    │   ┌────────────────────────────────────────────┐   │
    │   │ Dialogue Manager & Session State Machine   │   │
    │   └─────────────────┬──────────────────────────┘   │
    │                     │                              │
    │                     ▼                              │
    │   ┌────────────────────────────────────────────┐   │
    │   │ GST Calculator, HSN DB, UPI QR Generator   │   │
    │   └─────────────────┬──────────────────────────┘   │
    │                     │                              │
    │         ┌───────────┴───────────┐                  │
    │         ▼                       ▼                  │
    │   ┌───────────┐           ┌───────────┐            │
    │   │ A4 PDF    │           │ Thermal   │            │
    │   │ Invoice   │           │ 80mm Slip │            │
    │   └───────────┘           └───────────┘            │
    └────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 2. Clone and Setup Backend
```bash
git clone https://github.com/ayushchaubey85320-ai/DukaanBillAi.git
cd DukaanBillAi

# Install Python dependencies
pip install fastapi uvicorn scikit-learn joblib reportlab qrcode pillow pydantic

# Run Backend Server (port 8001)
python backend/run.py
```

### 3. Setup Frontend Web App
```bash
cd frontend
npm install
npm run dev -- --host --port 5174
```
Open `http://localhost:5174` in your browser.

### 4. Retrain Model with HuggingFace Data
```bash
# Fetch latest HuggingFace Hinglish datasets
python backend/app/ml/huggingface_loader.py

# Retrain model
python -m backend.app.ml.train

# Run automated 21-scenario verification
python -m unittest backend.app.tests.test_scenarios
```

---

## 📱 Android APK Installation

The compiled Android application is available at:
`apk/DukaanAI.apk`

### Installing on Phone:
1. Transfer `DukaanAI.apk` to your Android device via USB/Telegram.
2. Tap the APK to install (enable *"Install from Unknown Sources"* if prompted).
3. The app connects automatically to the live backend server.
4. Use the in-app **Server Connection Settings (Globe icon)** to switch between **Online Cloud Tunnel** (for 4G/5G) or **Local Wi-Fi**.

---

## 🧪 Scenario Coverage Matrix (21/21 Passing)

| # | Scenario | Dialect | Intent | Verification Result |
|---|---|---|---|---|
| 1 | Kirana grocery items with rates | Hinglish | `add_item` | ✅ PASSED |
| 2 | Quantity modification on existing item | Hinglish | `update_quantity` | ✅ PASSED |
| 3 | Remove specific item | Hinglish | `remove_item` | ✅ PASSED |
| 4 | Undo / cancel last added item | Hindi | `cancel_last_item` | ✅ PASSED |
| 5 | Pharmacy medicine with 12% GST | English | `add_item` | ✅ PASSED |
| 6 | Garments inter-state IGST calculation | English | `add_item` | ✅ PASSED |
| 7 | Restaurant dine-in 5% GST & roundoff | Hinglish | `add_item` | ✅ PASSED |
| 8 | Electronics HSN 18% & 28% GST | English | `add_item` | ✅ PASSED |
| 9 | Percentage discount application | Hinglish | `apply_discount` | ✅ PASSED |
| 10 | Flat rupee discount | Hinglish | `apply_discount` | ✅ PASSED |
| 11 | Customer details (name + phone masking)| English | `set_customer` | ✅ PASSED |
| 12 | Regional plural matching ("tomatoes") | English | `add_item` | ✅ PASSED |
| 13 | Low confidence fallback request | English | `fallback` | ✅ PASSED |
| 14 | Payment mode toggle (Cash/UPI) | Hinglish | `set_payment_mode`| ✅ PASSED |
| 15 | GSTIN format verification | Alphanumeric | `validate_gstin`| ✅ PASSED |
| 16 | Switch language to Hindi | Hindi | `switch_language`| ✅ PASSED |
| 17 | Switch language to English | English | `switch_language`| ✅ PASSED |
| 18 | Finalize invoice & trigger PDF | Hinglish | `finalize_bill` | ✅ PASSED |
| 19 | Thermal 80mm ESC/POS slip generation | Hinglish | `print_thermal` | ✅ PASSED |
| 20 | Inactive session timeout warning | System | `timeout` | ✅ PASSED |
| 21 | Complete session reset / new bill | Hinglish | `reset_session` | ✅ PASSED |

---

## 📄 License
This project is licensed under the MIT License.
