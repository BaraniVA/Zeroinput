# 🧠 ZeroInput

**ZeroInput** is a privacy-first, intelligent workflow assistant for Windows that learns how *you* use your computer—then proactively suggests helpful actions. Powered by a neural network and local language models, it adapts to your habits and context to boost productivity with smart, on-device automation.

---

## 🚀 Features

- **Personalized Learning** – Learns from your unique usage patterns via neural networks.  
- **Context-Aware Suggestions** – Offers real-time, relevant actions based on what you're doing.  
- **Privacy-First** – All data stays *local*. Nothing is uploaded, ever.  
- **Smart Automation** – Accept and execute suggestions instantly with a single hotkey.  
- **Continuous Adaptation** – Improves over time through a built-in feedback loop.  
- **Multi-Source Intelligence** – Uses a blend of ML, LLMs, and rule-based logic.

---

## 🧩 How It Works

1. **Context Tracking**  
   Monitors your active windows, files, and processes.

2. **Pattern Recognition**  
   Detects behavioral patterns to anticipate your next move.

3. **Local LLM Suggestions**  
   Uses local large language models to generate human-like prompts.

4. **Feedback Loop**  
   Learns from which suggestions you accept or ignore.

5. **Hotkey Execution**  
   Execute any suggestion with a single keystroke.

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/zeroinput.git
cd zeroinput
python -m venv venv
venv\Scripts\activate   # or source venv/bin/activate on WSL/Linux
pip install -r requirements.txt
```

---

## 🎮 Usage

```bash
python main.py
```

---

## 🛠 Requirements

- Windows OS  
- Python 3.8+  
- *(Optional)* [Ollama](https://ollama.com) for enhanced local LLM capabilities

---

## 📁 Project Structure

```
main.py                   # Entry point  
agent/
├── context_tracker.py    # Tracks windows, files, and processes  
├── action_executor.py    # Executes context-based suggestions  
├── hotkey_manager.py     # Handles global hotkey input  
└── ml/                   # Neural network models and data logic  
zeroinput_memory.json     # Local context memory  
zeroinput_feedback.json   # Feedback for adaptive learning
```

---

## 📈 Roadmap

- Cross-device pattern sync (privacy-focused)  
- Deeper content and workflow awareness  
- Expanded automation and integrations  
- Visual dashboard for insight and control  

---

## 🤝 Contributing

Pull requests, feature ideas, and bug reports are welcome! Open an issue or start a discussion to get involved.

---

## 📜 License

MIT License

---

**ZeroInput** — *Your adaptive, local-first AI workflow assistant.*

