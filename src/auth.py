import pyrebase
import json
from chat import conversation
from firebase_utils import create_session
from firebase_admin import firestore
from firebase_utils import get_all_sessions, load_session

class Auth:
    def __init__(self, config_path="firebase_admin_keys.json"):
        with open(config_path, "r") as f:
            firebase_config = json.load(f)
        firebase = pyrebase.initialize_app(firebase_config)
        self.auth = firebase.auth()

    def sign_up(self):
        print("Welcome to the ACE sign-up page!")
        user_name = input("Enter your username: ")
        
        # Check if username already exists
        db = firestore.client()
        user_ref = db.collection("users").where("username", "==", user_name).get()
        # If the query returns any documents, the username already exists
        if len(user_ref) > 0:
            print("Username already exists! Please choose a different username.")
            return None
        
        email = input("Enter your email: ")
        password = input("Enter your password: ")
        confirm_password = input("Confirm your password: ")

        if password != confirm_password:
            print("Passwords do not match!")
            return None

        try:
            user = self.auth.create_user_with_email_and_password(email, password)
            print(f"Welcome onboard, {user_name}!")
            print(f"User ID: {user['localId']}")

            db = firestore.client()
            db.collection("users").document(user['localId']).set({
                "username": user_name
                })


            # Name and create the session
            session_name = input("Enter a name for your session: ")
            session_id = create_session(user['localId'], session_name)
            print(f"Session '{session_name}' created with ID: {session_id}")
            
            # Start conversation
            conversation(user['localId'], session_id)
            return user
        except Exception as e:
            print(f"An error occurred while creating your account: {e}")
            return None

    def sign_in(self):
        print("Welcome back to ACE!")
        email = input("Enter your email: ")
        password = input("Enter your password: ")

        try:
            user = self.auth.sign_in_with_email_and_password(email, password)

            # Get the username directly from the 'users' collection
            db = firestore.client()
            user_doc = db.collection("users").document(user['localId']).get()

            if user_doc.exists:
                user_data = user_doc.to_dict()
                user_name = user_data.get("username", "User")  # Default to "User" if username not found
            else:
                user_name = "User"  # Default if the document doesn't exist

            print(f"Welcome back! {user_name}")
            print(f"User ID: {user['localId']}")

            # Ask user to create a new session or load an existing one
            while True:
                print("Enter 1 to create a new session or 2 to load an existing session.")
                session_choice = input("Choice: ")

                if session_choice == "1":
                    # Name and create the session
                    while True:
                        session_name = input("Enter a name for your session: ")

                        # Check for unique session name
                        sessions = get_all_sessions(user['localId'])
                        if session_name in [session['session_name'] for session in sessions]:
                            print("Session name already exists. Please choose a different name.")

                        else:
                            session_id = create_session(user['localId'], session_name)
                            print(f"Session '{session_name}' created with ID: {session_id}")
                            break
                    break

                elif session_choice == "2":
                    # Load existing session
                    print("Available sessions:")
                    sessions = get_all_sessions(user['localId'])

                    for i, session in enumerate(sessions):
                        print(f"{i+1}. {session['session_name']}, (Created at: {session['created_at']})")   

                    select_session = input("Enter the name of the session you want to load: ")
                    session_id = load_session(user['localId'], select_session)
                    if session_id is None:
                        print(f"No session found with the name '{select_session}'")
                        return None
                    break
                
                else:
                    print("Invalid choice. Please enter 1 or 2.")

            # Start conversation
            conversation(user['localId'], session_id)
            return user
        
        except Exception as e:
            print(f"An error occurred while signing in: {e}")
            return None

# Unit Test 
#auth_instance = Auth()
#user = auth_instance.sign_up()
#user = auth_instance.sign_in()