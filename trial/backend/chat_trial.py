import time
from pinecone_db import vectorize
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA  # To use retriever with LLM

# System prompt
system_prompt = """
You are ACE, an AI-powered study assistant built to help students learn smarter.

You can:
-Read and understand uploaded files (PDF, PPTX, DOCX, TXT, JPG, JPEG) to provide answers and summaries.
-Use a web search agent to fetch up-to-date info when needed.
-Your personality is chill, helpful, and intelligent — like a smart best friend who’s amazing at explaining things.

Always:
-Refer to yourself as ACE.
-Use the user’s name if they provide it.
-Use the chat history to understand the user’s needs and context.
-Answer clearly and in simple words.
-Summarize when asked.
-Avoid filler or fluff — get to the point unless the user wants detail.
-Stay honest — if something isn’t in the current documents or on the web, admit it.
-Use an encouraging tone if the user sounds stuck or stressed.

Never:
-Make up facts.
-Be too robotic or lecture-y.
-Provide harmful or dangerous advice.

Keeping in mind the above instructions answer the following question:
Here is the conversation history: {chat_history}
Question: {user_input}
Answer:
"""

# Load model with streaming enabled
model = OllamaLLM(model="gemma3:12b-it-qat", stream=True)

# Define the prompt 
prompt = ChatPromptTemplate.from_template(system_prompt)

# Create the basic prompt-only chain
chain = prompt | model

# Chat history
chat_history = ""

# Chat loop
def handel_conversation():
    global chat_history
    print("Iniitializing ACE...")
    time.sleep(1.5)
    print("Ace is ready! Type '/bye' to exit chat.")

    retriever = None

    while True:
        user_input = input("You: ")
        if user_input.lower() == "/bye":
            result = chain.invoke({"chat_history": chat_history, "user_input": "Bye!"})
            print(f"ACE: {result}")
            break

        elif user_input.lower() == "/show_history":
            print("\n-------Chat History-------")
            print(chat_history)
            print("--------------------------\n")
            continue

        elif user_input.lower() == "/upload":
            try:
                file_path = input("Enter the file path: ")
                retriever = vectorize(file_path)
                print(f"{file_path} uploaded and vectorized successfully!")
                continue
            except Exception as e:
                print(f"Error uploading file: {e}")
                continue

        elif retriever:
            qa_chain = RetrievalQA.from_chain_type(
                llm=model,
                retriever=retriever,
                chain_type="stuff"
            )
            result = qa_chain.invoke(user_input)
            print(f"ACE: {result}")
            chat_history += f"\nYou: {user_input}\nACE: {result}"
        else:
            # Default fallback to simple prompt chain
            result = chain.invoke({"chat_history": chat_history, "user_input": user_input})
            print(f"ACE: {result}")
            chat_history += f"\nYou: {user_input}\nACE: {result}"

if __name__ == "__main__":
    handel_conversation()
