# 🧠 ACE – Academic Conversational Engine

ACE (Academic Conversational Engine) is an intelligent academic assistant designed for students from school to PhD level. It uses LLMs, Retrieval-Augmented Generation (RAG), and web search to provide accurate, helpful answers. Users can upload documents, ask questions, save chat sessions, and revisit past conversations with full context.


## 🚀 Features

📄 Document-Based Q&A (RAG): Upload PDFs, PPTs, DOCX, or TXT files and ask questions based on them.

🌐 Web Search (via Tavily API): If documents don’t help, ACE can search the web and answer using up-to-date information.

🧠 Smart Relevance Check: Before using documents, ACE checks if they are actually useful for answering your query.

🗃️ Session Management: Save and load chat sessions with full history and linked documents.

🔒 Firebase Integration: All data (sessions, users, chats) are stored securely using Firestore.


## 📦 Tech Stack
- Backend: Python
- LLM: gemma3:4b-it-qat
- Vector Store: Pinecone 
- Embedding model: intfloat/multilingual-e5-large
- Database: Firebase Firestore
- Web Search API: Tavily 
- Frontend: CLI-based (Web frontend coming soon)
## Setup Instructions

## 🧑‍🎓 Example Use Cases
- Ask questions from your uploaded class notes
- Generate flashcards, quizzes, and summaries
- Use web search for recent or general academic queries
- Continue past sessions and review what you discussed
## Run Locally

Clone the repository

```bash
  git clone https://github.com/PRIME-07/ACEstudy.AI.git
```

Go to the project directory

```bash
  cd ACE_AI
```

Install dependencies

```bash
  pip install -r requirements.txt
```

Run the application

```bash
  python src/main.py  
```
Now you can chat with ACE!


## 🤝 Contributing

If you're a student or developer interested in this project, feel free to fork this repo, suggest features, or fix bugs. PRs are welcome!


## 📜 License

MIT License

This project is **free to use** for any purpose — personal, academic, or commercial.

I do **not provide any warranties or guarantees**, and I’m **not responsible** for any issues that arise from using this code.


