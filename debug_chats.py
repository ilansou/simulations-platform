import os
from dotenv import load_dotenv
from pymongo import MongoClient
import pandas as pd

# Load environment variables
load_dotenv()

def main():
    # Connect to MongoDB
    mongo_uri = os.getenv("MONGODB_URI")
    if not mongo_uri:
        print("MongoDB URI not found in environment variables!")
        return
        
    print("Connecting to MongoDB...")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')  # Check connection
        print("Connected to MongoDB")
        
        # Get database and collection
        db = client["experiment_db"]
        chat_collection = db["chat"]
        
        # Get all chat messages
        all_chats = list(chat_collection.find())
        
        if not all_chats:
            print("No chat messages found in database!")
            return
            
        print(f"Found {len(all_chats)} chat messages")
        
        # Display chat messages
        for chat in all_chats:
            sim_id = chat.get("simulation_id", "Unknown")
            timestamp = chat.get("timestamp", "Unknown")
            user_msg = chat.get("user_message", "No message")
            ai_msg = chat.get("assistant_message", "No response")
            
            print(f"\n--- Message from simulation {sim_id} at {timestamp} ---")
            print(f"User: {user_msg}")
            print(f"Assistant: {ai_msg[:100]}..." if len(ai_msg) > 100 else f"Assistant: {ai_msg}")
            
        # Create DataFrame for better visualization
        df_data = []
        for chat in all_chats:
            df_data.append({
                "simulation_id": chat.get("simulation_id", "Unknown"),
                "timestamp": chat.get("timestamp", "Unknown"),
                "user_message": chat.get("user_message", "No message"),
                "assistant_message": chat.get("assistant_message", "No response")[:50] + "..." 
                    if len(chat.get("assistant_message", "")) > 50 else chat.get("assistant_message", "No response")
            })
            
        df = pd.DataFrame(df_data)
        print("\nAll messages as DataFrame:")
        print(df)
        
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

if __name__ == "__main__":
    main() 