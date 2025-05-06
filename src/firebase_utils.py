from firestore_db import db
from firebase_admin import firestore
import uuid
import datetime

# create session
def create_session(uid, session_name):
    user_ref = db.collection("users").document(uid)
    user_ref.set({}, merge=True)  # Create user document if it doesn't exist

    session_id =  str(uuid.uuid4())
    session_ref = user_ref.collection("sessions").document(session_id)
    session_data = {
        "created_at": datetime.datetime.now(),
        "session_id": session_id,
        "session_name": session_name,
        "full_chat_history": [],
        "related_doc_ids": [],
        "metadata":{"title": "None"}
    }
    session_ref.set(session_data)
    return session_id

# Save Chat History
def update_chat_history(uid, session_id, history):
    session_ref  = db.collection("users").document(uid).collection("sessions").document(session_id)
    session_ref.update({"full_chat_history": history})

# Rename Session
def update_session_name(uid, session_id, new_name):
    session_ref = db.collection("users").document(uid).collection("sessions").document(session_id)
    session_ref.update({"session_name": new_name})

# Get all sessions
def get_all_sessions(uid):
    user_ref = db.collection("users").document(uid)
    sessions_ref = user_ref.collection("sessions")
    sessions = sessions_ref.stream()

    session_list = []
    for session in sessions:
        data = session.to_dict()
        session_list.append({
            "session_id": data.get("session_id"),
            "session_name": data.get("session_name"),
            "created_at": data.get("created_at")
       })
    return session_list

# Load Session
def load_session(uid, select_session):
    session_ref = db.collection("users").document(uid).collection("sessions")            
    query = session_ref.where("session_name", "==", select_session).limit(1)
    results = query.stream()

    session_doc = next(results, None)

    if session_doc:
        session_data = session_doc.to_dict()
        print(f"Session loaded: {session_data['session_name']}\n")
        print()
        
        for msg in session_data["full_chat_history"]:
            print(f"{msg['role']}: {msg['message']}")
        
        return session_data

    else:
        print(f"No session found with the name '{select_session}'")
        return None

def get_username(uid):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()
    
    if doc.exists:
        user_data = doc.to_dict()
        return user_data.get("username", "User")
    else:
        return "User"
