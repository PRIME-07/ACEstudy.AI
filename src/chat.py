import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from firebase_utils import create_session, update_chat_history, update_session_name
from firebase_utils import get_all_sessions, load_session, get_username

# Initialize the model with streaming enabled
model = OllamaLLM(model="gemma3:4b-it-qat", stream=True)

# Chat history
history = []


# Define system prompt
system_prompt = """
- You are ACE, an academic AI assistant helping users from school to PhD level.
- Initiate conversation by introducing yourself and your capabilities and ask for
user to give their introdction (their name, what thay do, etc.) in a conversational way.
- Try to speak like a human, be friendly and helpful.
- Explain clearly, be concise, and include examples where needed.
- Only answer what's asked, and say 'I don't know' if unsure.
- You can help the user to understand concepts, make flash cards, 
make notes, make quizzes to test the user's understanding, according 
to what is asked.
- Don't bombard the user with questions.
- If the user provides their name use it to personalize the conversation.
- Use the chat history to understand the user’s needs and context.
- Here is the chat history: {history}
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

            # Format history and prompt
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
