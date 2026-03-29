# 🏛️ ET AI Concierge: Priya
### *Autonomous Graph-RAG Voice Advisor for the Economic Times Ecosystem*


---

## 🚀 The Vision
The Economic Times ecosystem is vast—spanning premium subscriptions, executive masterclasses, global summits, and specialized financial tools. For a user, finding the right "next step" in their financial journey often leads to information overload.

**Priya** is an autonomous, voice-native concierge that replaces traditional search with **Strategic Discovery**. By navigating a custom-built Knowledge Graph, Priya provides hyper-personalized roadmaps with 100% factual grounding and zero-hallucination.

---

## 🛠️ Technical Architecture: The "Graph-RAG" Advantage
Unlike standard RAG systems that rely on probabilistic vector similarity (which often leads to hallucinations), Priya uses a **Deterministic Knowledge Graph** built with `NetworkX`.



### Key Engineering Pillars:
1. **Multi-Hop Traversal:** The controller identifies the User Persona (e.g., *Student, Founder, HNI*) and physically traverses the graph to retrieve not just a product, but its 2nd-hop neighbors: **Cross-Sells, Linked Events, and Contextual FAQs.**
2. **Hybrid Intent Routing:** A dual-engine approach using local keyword mapping for sub-millisecond response on common intents, falling back to **Gemini 2.0 Flash** for complex natural language extraction.
3. **Voice-Native Sanitization:** A custom pipeline that programmatically strips markdown, hashes, and non-verbal cues from LLM outputs to ensure the `gTTS` engine delivers human-like speech.
4. **Stateful Session Memory:** Maintains a rolling context window to handle pronouns and follow-up queries (e.g., "Tell me more about *that* camp").

---

## 📦 Core Stack
- **Brain:** Gemini 2.0 Flash (Reasoning & Extraction)
- **Knowledge Base:** NetworkX MultiDiGraph (Deterministic Ground Truth)
- **Interface:** Streamlit (Mission Control Dashboard)
- **Voice:** `speech_recognition` (STT) & `gTTS` (TTS)
- **DevOps:** `python-dotenv` for Secure API Management

---

## 🚦 Getting Started

### 1. Prerequisites
Ensure you have Python 3.12+ installed.

### 2. Installation
```bash

git clone [https://github.com/YOUR_USERNAME/hackathon_ai.git](https://github.com/YOUR_USERNAME/hackathon_ai.git)
cd hackathon_ai
pip install -r requirements.txt
