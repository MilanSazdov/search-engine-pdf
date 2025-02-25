# 📄 PDF Search Engine  

🔍 **PDF Search Engine** is a Python-based search engine that processes a single PDF document, builds optimized data structures, and enables efficient keyword-based search. Users can enter textual queries, and the system ranks and displays relevant search results.  

The project uses **Data Structures and Algorithms in Python** as a test document.  

---

## 🚀 Features
✔️ **Pre-indexing:** The system processes the PDF upon startup, extracting and structuring the text for fast retrieval.  
✔️ **Ranked Search Results:** Results are ranked based on keyword occurrences and additional ranking heuristics.  
✔️ **Multi-Word Queries:** Users can enter one or more words separated by spaces, and results will be ranked accordingly.  
✔️ **Logical Operators:** Supports `AND`, `OR`, and `NOT` for complex queries (e.g., `python AND algorithm NOT dictionary`).  
✔️ **Pagination:** Displays a limited number of results per page, with options to view more.  
✔️ **Graph-Based Ranking:** Page references (`See page X`) improve the ranking of linked pages.  
✔️ **Trie-Based Indexing:** Efficient word search using a trie data structure.  
✔️ **Auto-Complete & Suggestions:** Provides query completion and "Did you mean?" suggestions for misspelled words.  
✔️ **PDF Export & Highlighting:** Saves search results as a separate PDF file with highlighted keywords.  

---

## 🛠 Technologies & Dependencies
| Library       | Purpose |
|--------------|---------|
| `pdfminer.six`  | Extract text from PDF files |
| `PyPDF2`        | Read and write PDF documents |
| `networkx`      | Build a graph of page references |
| `collections`   | Optimized data structures (e.g., `defaultdict`) |
| `difflib`       | Find similar words (for auto-correction) |
| `re`            | Process regular expressions for query parsing |
| `pickle`        | Serialize and load pre-indexed search structures |

Install dependencies using:
```sh
pip install pdfminer.six PyPDF2 networkx
```
---

## 📚 Table of Contents
- [🚀 Features](#-features)  
- [🛠 Technologies & Dependencies](#-technologies--dependencies)  
- [📖 How It Works](#-how-it-works)  
- [🔧 Installation & Usage](#-installation--usage)  
- [📌 Example Search Result](#-example-search-result)  
- [⚠️ Potential Issues & Troubleshooting](#-potential-issues--troubleshooting)  
- [📜 License](#-license)  
- [📬 Contact](#-contact) 

---

## 📖 How It Works
1. **Preprocessing:**  
   - The script parses the PDF file, extracts text from each page, and constructs data structures.  
   - A **graph** is built from references like `"See page 45"`, improving search rankings.  
   - A **trie** is constructed for fast word searching.  
   - Indexed data is serialized for faster subsequent searches.  

2. **Search Execution:**  
   - Users input a search query (single or multiple words).  
   - The program processes the query using **logical operators** if provided.  
   - Results are ranked based on occurrences, graph connectivity, and additional heuristics.  

3. **Displaying Results:**  
   - The top results are shown with **page numbers and contextual snippets** where the word appears.  
   - **Pagination** allows users to navigate through results.  
   - Users can save results as a **PDF with highlighted keywords**.  

---

## 🔧 Installation & Usage

### **1️⃣ Clone the Repository**
```sh
git clone https://github.com/your-username/pdf-search-engine.git
cd pdf-search-engine
```

### **2️⃣ Install Dependencies Manually**  
Run the following command to install required Python libraries:  
```sh
pip install pdfminer.six PyPDF2 networkx
```

### **3️⃣ Run the Search Engine**  
To start the search engine, run the following command:  
```sh
python main.py
```

### **4️⃣ Enter Your Search Query**  
Example queries:  
```sh
data structures
algorithm OR graph
python NOT dictionary
```

---

## 📜 License  
This project is licensed under the [MIT License](LICENSE).  
See the LICENSE file for more details.  

---

## 🔗 Useful Links  

- 📖 [README](README.md)  
- ❤️ [Code of Conduct](CODE_OF_CONDUCT.md)  
- 📜 [MIT License](LICENSE)  

---

## 📬 Contact  
📧 **Email:** [milansazdov@gmail.com](mailto:milansazdov@gmail.com)  
🐙 **GitHub:** [MilanSazdov](https://github.com/MilanSazdov)  

---
