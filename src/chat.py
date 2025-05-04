import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from firebase_utils import create_session, update_chat_history, update_session_name
from firebase_utils import get_all_sessions, load_session, get_username
from search_agent import search_agent

# Initialize the model with streaming enabled
model = OllamaLLM(model="gemma3:4b-it-qat", stream=True)

# Chat history
history = []

# Define system prompt
system_prompt = """
- You are ACE, an academic AI assistant helping users academically from school to PhD level.
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
            load_session(uid, select_session)

            for msg in load_session(uid, select_session)["full_chat_history"]:
                history.append({"role": msg['role'], "message": msg['message']})

            continue

        elif user_input.lower() == "/help":
            print("\nAvailable commands:")
            print("/bye - End the chat and save history.")
            print("/show_history - Display the chat history.")
            print("/rename session - Rename the current session.")
            print("/help - Show this help message.")
            print("----------------------------\n")
            continue

        else:
            history.append({"role": "user", "message": user_input})

            # Step 1: Check if a web search is needed
            decision_prompt = f"""
            Your task is to determine if a web search is required to answer the user's query accurately.
            User's Query: {user_input}
            Reply only with "yes" or "no".
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

                ace_response = ""
                print("ACE: ", end="", flush=True)
                for chunk in model.stream(formatted_prompt):
                    print(chunk, end="", flush=True)
                    ace_response += chunk

                history.append({"role": "ACE", "message": ace_response})
                continue
            
            # Default flow (no search needed)
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

            history.append({"role": "ACE", "message": ace_response})



# unit test
#if __name__ == "__main__":
#    conversation()
