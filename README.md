# 🛒 NovaMart Assistant

A portfolio showcase and educational project modeling an **internal virtual assistant** for **NovaMart**, a fictional omnichannel retail chain.

---

## 🎯 Project Overview

The goal of this project is to demonstrate clean, modular, and professional architecture for an internal assistant serving NovaMart associates (store staff, customer support agents, and inventory management teams).

Planned use cases for the case study:
- Looking up store operational procedures and internal policies (exchanges, returns, warranties).
- Checking mock inventory availability and order fulfillment statuses.
- Providing standardized answers to common customer service inquiries.

> **Note:** This project currently implements a local, deterministic keyword search over fictional policy documents using Python's standard library. No external AI integrations, language models, or API keys are implemented at this stage.

---

## 📁 Project Structure

The layout is organized for maintainability, testability, and incremental extension:

```text
novamart-assistant/
├── .env.example              # Environment variables template (no secrets or credentials)
├── .gitignore                 # Ignored files and directories for Git (venv, caches, etc.)
├── README.md                  # Project documentation and architectural overview
├── requirements.txt           # Empty (no external dependencies required)
├── data/                      # Data storage and reference materials
│   ├── mock/                  # Fictional dataset for local simulations and testing
│   ├── policies/              # Fictional retail store policy documents
│   │   ├── customer_support.md
│   │   ├── delivery.md
│   │   ├── exchanges.md
│   │   ├── payments.md
│   │   ├── returns.md
│   │   └── warranties.md
│   └── raw/                   # Raw source documents and records
├── src/                       # Main application source code
│   ├── __init__.py            # Python package marker
│   ├── config.py              # Centralized configuration reader
│   ├── search.py              # Local keyword-based policy search engine
│   └── utils/                 # Reusable utility functions
│       └── __init__.py
└── tests/                     # Automated test suite (unit and integration tests)
    └── __init__.py
```

---

## 🔍 Local Policy Search (Deterministic, Standard Library)

The project includes a lightweight, local search module (`src/search.py`) that extracts relevant policy excerpts from the Markdown files under `data/policies/`.

### How to Run the Included Demo
Run the built-in demonstration containing questions with relevant evidence and questions with no results:

```bash
python3 -m src.search
```

### How to Run a Custom Query in Python
You can import and call `search_policies` directly from Python:

```bash
python3 -c "from src.search import search_policies; print(search_policies('What are the accepted payment methods?'))"
```

### Current Limitations
- **Keyword Overlap Does Not Guarantee an Answer:** Keyword matching only measures whether certain words appear in an excerpt. It **does not verify whether the excerpt actually answers the question**. For example, searching *"Does the standard warranty cover a damaged bicycle?"* returns `Warranty Exclusions` because the words `standard`, `warranty`, and `cover` match. However, the policy text only applies to electronics and appliances, and **does not establish whether bicycle coverage exists**.
- **No AI / Semantic Understanding:** The search relies strictly on exact keyword matching, stop-word filtering, and basic plural normalization. It does not use neural embeddings, LLMs, or vector search.
- **Vocabulary Sensitivity:** The search will not recognize synonyms or paraphrases unless the words match the policy text (e.g., searching for "reimbursement" will not match "refund").
- **Strict Evidence Requirement:** If a question contains no matching terms or only incidental matches for complex queries, the search returns an empty list (`[]`). It does not extrapolate or generate ungrounded answers.

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.9+** installed on your system.

### 2. Inspect Project Structure
To inspect the files and folders:
```bash
cd novamart-assistant
ls -la
```

### 3. Set Up Local Environment (Optional)
To create an isolated virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 🛡️ Security & Best Practices

- All documents and policies are completely fictional and created solely for portfolio demonstration.
- No real API keys, secrets, or personal data are included.
- Local configuration files (`.env`) and virtual environments (`.venv/`) are excluded via `.gitignore` to prevent accidental commits.
