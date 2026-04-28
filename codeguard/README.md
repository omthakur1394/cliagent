

# 🛡️ CodeGuard

### Ethical AI Code Review Agent

**CodeGuard is a CLI agent that reviews your private GitHub repositories, suggests fixes, and pushes changes — with full human approval at every step.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic-purple.svg)](https://langchain-ai.github.io/langgraph/)
[![Groq](https://img.shields.io/badge/Groq-LLaMA3-orange.svg)](https://groq.com)
[![License](https://img.shields.io/badge/License-Private-red.svg)]()

</div>

---

## ✨ What It Does

CodeGuard is an agentic AI tool that:

- 🔍 **Detects open-source repos** and refuses to clone or review them (ethical boundary)
- 🤖 **Reviews your private repo** file by file using LLaMA 3.3 70B via Groq
- 🔧 **Auto-generates fixed code** for every file it reviews
- 👀 **Shows you a diff** of every change before anything is committed
- ✅ **You approve or reject** each file change individually
- 🚀 **Pushes only approved changes** to GitHub after verifying you are the repo owner
- 🧹 **Cleans up** the local workspace automatically after the session

---

## 🚀 Installation

**Linux / Mac:**
```bash
curl -fsSL https://yourusername.github.io/codeguard/install.sh | bash
```

**Windows:**
```cmd
curl -fsSL https://yourusername.github.io/codeguard/install.cmd -o install.cmd && install.cmd && del install.cmd
```

**Or via pip:**
```bash
pip install codeguard
```

---

## ⚡ Quick Start

```bash
codeguard
```

You will be prompted for:
1. Your private GitHub repo URL
2. Your Groq API Key (hidden input, never stored)
3. Your GitHub Personal Access Token (hidden input, never stored)

---

## 🔄 How It Works