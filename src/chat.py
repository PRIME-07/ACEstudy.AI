import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from firebase_utils import create_session, update_chat_history, update_session_name
from firebase_utils import get_all_sessions, load_session, get_username
from search_agent import search_agent
from pinecone_db import upload_file_to_pinecone, retrieve_and_verify_relevance

# Initialize the model with streaming enabled
model = OllamaLLM(model="gemma3:4b-it-qat", stream=True)

# current time
local_time = time.localtime()
current_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)

# Chat history
history = []

# Define system prompt
system_prompt = f"""
- You are ACE, an academic AI assistant helping users academically from school to PhD level.
- If you need current time and date and year, you can access it from: {current_time}
- Try to speak like a human, be friendly and helpful.
- Explain clearly, be concise, and include examples where needed.
- Only answer what's asked, and say 'I don't know' if unsure.
- You can help the user to understand concepts, make flash cards, 
make notes, make quizzes to test the user's understanding, according 
to what is asked.
- In case you don't know the answer, you can search for it online using the Tavily API understand it and then answer according to the user's query.
- If the user provides their name, use it in the conversation.
- Use the chat history to understand the user’s needs and context.
- Here is the chat history: {history}
- Before answering make sure that your response is relevant to the user's query.
"""

# Chat template with system + user message
prompt_template = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "{user_input}")
])


# Chat loop
def conversation(uid=None, session_id=None):
    print("Initializing ACE...")
    time.sleep(1.5)
    print("Ace is ready! \nType '/bye' to exit chat. \nType '/help' to explore commands.")

    while True:
        user_input = input("\nYou: ")

        if user_input.lower() == "/bye":
            formatted_history = "\n".join([f"{msg['role']}: {msg['message']}" for msg in history])
            formatted_prompt = prompt_template.format_messages(
                user_input=user_input,
                history=formatted_history
            )

            ace_response = ""
            print("ACE: ", end="", flush=True)
            for chunk in model.stream(formatted_prompt):
                print(chunk, end="", flush=True)
                ace_response += chunk

            history.append({"role": "user", "message": user_input})
            history.append({"role": "ACE", "message": ace_response})

            # Save chat history to Firestore
            update_chat_history(uid, session_id, history)
            print("\nSession ended. Chat history saved!")
            break

        elif user_input.lower() == "/show_history":
            print("\n------- Chat History -------")
            for msg in history:
                print(f"{msg['role']}: {msg['message']}")
            print("----------------------------\n")
            continue

        elif user_input.lower() == "/rename session":
            new_name = input("Enter new session name: ")
            
            # check for unique session name
            get_all_sessions(uid)
            if new_name in [session['session_name'] for session in get_all_sessions(uid)]:
                print("Session name already exists. Please choose a different name.")
                continue
            
            update_session_name(uid, session_id, new_name)
            print(f"Session renamed to '{new_name}'")
            continue

        elif user_input.lower() == "/new session":
            new_session_name = input("Enter a name for the new session: ")
            create_session(uid, session_name=new_session_name)
            print(f"New session '{new_session_name}' created.")
            continue
        
        elif user_input.lower() == "/load session":
            get_all_sessions(uid)
            
            # list all sessions
            print("----------Available sessions----------\n")
            for i, session in enumerate(get_all_sessions(uid)):
                print(f"{i+1}. {session['session_name']}, (Created at: {session['created_at']})")
            print("-------------------------------------\n")
            
            # select session to load
            select_session = input("Enter the name of the session you want to load:")
            session_data =load_session(uid, select_session)

            if session_data:
                for msg in session_data["full_chat_history"]:
                    history.append({"role": msg['role'], "message": msg['message']})
                session_id = session_data["session_id"]
            else:
                print(f"Failed to load {select_session}")
                continue

        elif user_input.lower() == "/upload":
            print("Upload Mode:\n Enter the file path to upload file, once you are done press enter")
            while True:
                file_path = input("Enter the file path: ").strip()
                if file_path == "":
                    print("Exiting Upload Mode...")
                    time.sleep(2)
                    break
                else:
                    upload_file_to_pinecone(uid, session_id, file_path)
            continue

        elif user_input.lower() == "/help":
            print("\nAvailable commands:")
            print("/bye - End the chat and save history.")
            print("/show_history - Display the chat history.")
            print("/rename session - Rename the current session.")
            print("/new session - Create a new session.")
            print("/load session - Load an existing session.")
            print("/upload - Upload a file to the current session.")
            print("----------------------------\n")
            continue

        else:
            history.append({"role": "user", "message": user_input})

            # Step 1: Document retrieval for RAG
            is_relevant, retrieved_chunks = retrieve_and_verify_relevance(user_input, uid, session_id)

            formatted_history = "\n".join([f"{msg['role']}: {msg['message']}" for msg in history])

            if is_relevant and len(retrieved_chunks)>0:  # Use RAG if relevant documents are found
                docs_content = "\n\n".join(retrieved_chunks)
                print("ACE: Scanning documents...")
                context_aware_prompt = ChatPromptTemplate.from_messages([ 
                    ("system", """
                    You are ACE, an academic AI assistant helping users from school to PhD level.
                    You answer based on uploaded documents if relevant.
                    If documents are provided, use them carefully. Otherwise, answer from general academic knowledge.
                    Chat History: {history}
                    Documents: {docs}
                    """),
                    ("user", "{user_input}")
                ])

                formatted_prompt = context_aware_prompt.format_messages(
                    user_input=user_input,
                    history=formatted_history,
                    docs=docs_content
                )


            else:
                # Step 2: Fallback to web search if RAG found no relevant information
                decision_prompt = f"""
                    You are ACE, an academic assistant that helps students from school to PhD level.

                    Your task is to decide if a web search is needed to answer the user's query.

                    Respond with:
                    - "no" if the query asks for standard academic content that is commonly found in textbooks, lectures, or syllabi.
                    - "yes" if the query is about:
                      - recent discoveries, papers, or trends
                      - real-world datasets or project ideas
                      - tools/libraries/frameworks updates
                      - institution-specific or exam-specific info
                      - ambiguous or incomplete questions needing clarification from external sources.

                    User's Query: "{user_input}"

                    Only respond with "yes" or "no".
                """

                decision = model.invoke(decision_prompt).strip()

                if "yes" in decision.lower():
                    print("ACE: Gathering information from the web...\n")
                    search_result = search_agent(user_input)
                    raw_result = search_result.get("results", [])

                    if not raw_result:
                        ace_response = "Sorry, I couldn't find any useful information online. Could you rephrase your question?"
                        print(f"ACE: {ace_response}")
                        history.append({"role": "ACE", "message": ace_response})
                        continue
                    
                    # Format combined web info
                    filtered_results = [r for r in raw_result if r.get("content")]
                    combined_info = "\n\n".join([f"Title: {r['title']}\nContent: {r['content']}" for r in filtered_results])

                    # Format chat history
                    formatted_history = "\n".join([f"{msg['role']}: {msg['message']}" for msg in history])

                    # Use a search-aware prompt template
                    search_augmented_prompt = ChatPromptTemplate.from_messages([
                        ("system", """
                        You are ACE, an academic AI assistant helping users from school to PhD level.
                        Be concise, friendly, and helpful. Use examples if helpful.
                        You recently searched the web to help the user with their question.
                        If relevant info is found, use it to answer clearly. If not, say so.

                        Here is the chat history: {history}
                        Here is the user's question: {user_input}
                        Here is the web search result you found: {web_data}
                        """),
                        ("user", "{user_input}")
                    ])

                    # Format final prompt
                    formatted_prompt = search_augmented_prompt.format_messages(
                        user_input=user_input,
                        history=formatted_history,
                        web_data=combined_info
                    )
                else:
                    # Fallback to normal prompt if no web search is needed
                    formatted_prompt = prompt_template.format_messages(
                        user_input=user_input,
                        history=formatted_history
                    )

            ace_response = ""
            print("ACE: ", end="", flush=True)
            for chunk in model.stream(formatted_prompt):
                print(chunk, end="", flush=True)
                ace_response += chunk

            history.append({"role": "ACE", "message": ace_response})


