# **30-Day Distributed Research Plan: "The Digital Silk Road"**

Project: Computational Comparative Narratology of Pan-Asian Folklore  
Team: 4 Members (Debarghya 🇮🇳 India, Sahar 🇮🇷 Iran, Dongxu 🇨🇳 China, Rikuto 🇯🇵 Japan)  
Duration: 30 Days  
Model: Qwen3-Next (Fine-tuned)

## ---

**🟢 Minimum Viable Scope (MVP)**

To ensure completion within the strict 30-day deadline, we will limit the scope to high-quality, deep analysis rather than broad, shallow data collection.

* **Total Data Volume:** **80 Stories** (20 per culture).  
  * *Strategy:* Small data, high quality. These will serve as "Gold Standard" seeds for Fine-Tuning (SFT).  
* **Target Motifs:**  
  1. **ATU 313 (The Magic Flight):** Focus on the nature of obstacles (Elements vs. Objects).  
  2. **ATU 402 (The Animal Bride):** Focus on the ending (Tragic/Separation vs. Happy/Union).  
* **Core Objective:** Use Qwen3's "Thinking" capability to explain *why* narrative structures differ across cultures.

## ---

**🇬🇧 English Version: Execution Plan**

### **👥 Role Allocation**

* **LLM Lead :** Responsible for Qwen3 deployment, Prompt Engineering (System 2), and QLoRA Fine-tuning.  
* **Theory Lead:** Responsible for comparative frameworks, hypothesis generation, and final report synthesis.  
* **Vis Lead:** Responsible for Python visualization scripts (NetworkX, Story Ribbons).  
* **Data Lead:** Responsible for data cleaning, formatting (JSONL), and handling multilingual encoding issues.

### **📅 Weekly Schedule**

#### **Week 1: Distributed Data Curation (The "Culture" Week)**

* **Goal:** Create the "Gold Standard" training dataset.  
* **Activity:**  
  * Each member selects **20 distinct stories** from their own culture (must include ATU 313 & 402 variants).  
  * **Annotation Task:**  
    * **Level 1 (Deep):** 5 stories with full Proppian Function tagging.  
    * **Level 2 (Motif):** 10 stories with ATU types and Character Archetypes.  
    * **Level 3 (Meta):** 20 stories with "Ending Type" and "Moral Value".  
  * **Cross-Validation Experiment:** On Day 5, ALL members annotate the *same* single story (e.g., a neutral version of *Magic Flight*) to document cultural bias.  
* **Deliverable:** 80 validated JSON files.

#### **Week 2: Engineering & Fine-Tuning (The "Engine" Week)**

* **Goal:** Teach Qwen3 to be a folklorist.  
* **Data Lead:** Merges all JSON files into train.jsonl and test.jsonl. Validates UTF-8 encoding.  
* **Model Lead:**  
  * Deploys **Qwen3-Next (32B)** on GPU cloud.  
  * Develops the System Prompt: *"You are an expert comparative mythologist..."*  
  * Runs **QLoRA Fine-Tuning** (Rank=64, Alpha=16) on the annotated data.  
* **Visual Lead:** Writes the Python skeleton code for "Story Ribbons" using placeholder data.  
* **Theory Lead:** Reviews the annotation disagreement from Week 1 and formulates the "Cultural Prism" hypothesis.

#### **Week 3: Inference & Visualization (The "Insight" Week)**

* **Goal:** Generate results and maps.  
* **Model Lead:** Runs inference on the test set and un-annotated stories. Extracts **Embeddings** for semantic analysis.  
* **Visual Lead:**  
  * Generates **Story Ribbons**: Visualizing plot trajectory (X=Time, Y=Narrative Function).  
  * Generates **Motif Networks**: Nodes=Motifs, Edges=Co-occurrence, Color=Culture.  
* **Theory Lead & JP:** Perform Human Evaluation on the model's output. Does the AI understand "Mono no aware"? Does it understand Persian "Farr"?

#### **Week 4: Synthesis & Reporting (The "Delivery" Week)**

* **Goal:** Final Report and Presentation.  
* **Theory Lead (Lead Editor):** Writes the "Comparative Analysis" and "Introduction".  
* **Model Lead:** Writes the "Methodology" (Technical implementation of Qwen3).  
* **Visual Lead:** Finalizes high-res charts and writes the "Visual Analysis" section.  
* **Data Lead:** Compiles references and data sources; writes "Future Work".  
* **All:** Translate Abstract into Hindi, Persian, Chinese, and Japanese.

## ---

**🧬 Appendix: Data Annotation Schema (JSON)**

Use this schema for Week 1 annotations. The thinking\_process field is critical for fine-tuning the model's reasoning capabilities.

JSON

{  
  "id": "CN\_01\_WhiteSnake",  
  "culture": "Chinese",  
  "title": "The Legend of the White Snake",  
  "source\_text": "\[Full text or summary of the story...\]",  
  "annotation\_level": "Deep",  
  "metadata": {  
    "atu\_type": "402",  
    "main\_motif": "Animal Bride",  
    "ending\_type": "Tragic Separation / Suppression",  
    "key\_values": \["Filial Piety", "Karma", "Forbidden Love"\]  
  },  
  "thinking\_process": "As a Chinese annotator, I interpret the Monk Fahai not as a simple villain, but as a representation of rigid celestial order/bureaucracy. He represents the 'Interdiction' function. The White Snake's theft of the magical herb is a 'Violation', but motivated by 'Loyalty' (ren/yi).",  
  "narrative\_structure":  
}  
