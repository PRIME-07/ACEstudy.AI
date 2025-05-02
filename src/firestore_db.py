import firebase_admin
from firebase_admin import credentials, firestore

# Provide Firebase Admin SDK JSON key file
cred = credentials.Certificate("firebase_admin_keys.json")

# Initialize the Firebase Admin SDK
firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

