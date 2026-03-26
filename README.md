<div align="center">
  <h1>🧹 Data Janitor CLI</h1>
  <p><strong>Your Data, Spotlessly Clean. Right from the terminal.</strong></p>

  ![Python](https://img.shields.io/badge/Python-3.9+-green?style=flat-square&logo=python)
  ![Textual](https://img.shields.io/badge/UI-Textual-blue?style=flat-square)
  ![AI](https://img.shields.io/badge/AI-LLM_Powered-purple?style=flat-square)
  ![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

<br/>
<br/>

<!-- 📸 PORTFOLIO TIP: MUST REPLACE THIS WITH A REAL GIF -->
![App Demo](https://via.placeholder.com/800x450/0a0a0a/00ff41?text=PLACEHOLDER:+Insert+a+10-second+GIF+here+showing+the+app+in+action)

</div>

---

## ⚡ 10-Second Demo

Want to see it in action without configuring anything? Try the built-in demo mode!

```bash
git clone https://github.com/YOUR_USERNAME/data-janitor-cli.git
cd data-janitor-cli
pip install -r requirements.txt

# Launch straight into a demonstration!
python main.py --demo
```

---

## 🎯 What is it?

Data cleaning is often the most tedious part of any data project. Constantly writing `df.dropna()`, `df.drop_duplicates()`, and wrestling with whitespace gets repetitive.

**Data Janitor CLI** is a terminal-based UI (TUI) tool that makes data cleaning intuitive, fast, and visually appealing. Load a CSV or Excel file, let the app automatically profile the issues, and clean them interactively. 

Oh, and if you get stuck? **Ask the built-in LLM assistant** for suggestions!

### ✨ Core Features

- 🔍 **Auto-Profiling**: Instantly detects missing values, duplicates, whitespaces, and outliers (via Z-Score/IQR).
- 🖱️ **Interactive TUI**: A beautiful, nostalgic "hacker" terminal interface built with Textual.
- ⚡ **1-Click Auto Clean**: Let the engine resolve all detected issues automatically from safest to riskiest.
- 🤖 **LLM Integration**: Works seamlessly with **OpenAI, Google Gemini, and Groq** to provide data context and cleaning answers.
- ↩️ **Undo Support**: Made a mistake? Press `undo`.
- 🐍 **Pipeline Export**: Once you're done, export the exact Python `.py` script needed to replicate your cleaning steps in production!

---

## 🧠 Under the Hood (For the Geeks)

This isn't just a simple script; it's engineered with a scalable architecture:

- **UI Layer**: Powered by `Textual`, ensuring a responsive, async-ready, and gorgeous terminal experience.
- **Engine Layer**: Pure `pandas` under the hood for fast, reliable data manipulation.
- **Service Architecture**: The logic is cleanly separated into `analyzer.py` (data profiling), `cleaner.py` (transformations), and `llm_service.py` (AI interactions).
- **Graceful Degradation**: The app runs perfectly 100% offline. If you provide an API key, the LLM features unlock seamlessly.

---

## 🚀 Usage

### Interactive Menu
Load a file and type `menu` to see automatically detected issues. Type the number to clean it, or type `A` to apply all fixes automatically.

### Manual Commands
If you prefer raw control, the terminal supports direct commands:
- `clean --missing drop` (or `fill mean`, `fill median`)
- `clean --duplicates`
- `clean --whitespace`
- `clean --outliers zscore`

### AI Assistant (Optional)
Connect your favorite LLM (e.g., `llm config openai sk-...`) and just ask:
- `ask How should I handle the missing values in the 'salary' column?`

---

## 📁 Exporting Your Work

The best feature? You don't lose your work. When your data is pristine:
1. `export cleaned_data.csv` → Saves the actual cleaned file
2. `pipeline my_script.py` → **Generates the python code** that replicates everything you just did in the UI!

---

## 📄 License
MIT License — Feel free to use, modify, and distribute!

