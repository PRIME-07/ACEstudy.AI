import time
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

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
def conversation():
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

            with open("src/chat_history/chat_history.json", "w") as f:
                json.dump(history, f, indent=4)

            print("\nSession ended. Chat history saved to `chat_history.json`.")
            break

        elif user_input.lower() == "/show_history":
            print("\n------- Chat History -------")
            for msg in history:
                print(f"{msg['role']}: {msg['message']}")
            print("----------------------------\n")
            continue

        elif user_input.lower() == "/help":
            print("\nAvailable commands:")
            print("/bye - End the chat and save history.")
            print("/show_history - Display the chat history.")
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

if __name__ == "__main__":
    conversation()
