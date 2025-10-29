from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from firebase_admin import credentials, auth, initialize_app
from typing import List, Optional
import datetime

# Initialize FastAPI app
app = FastAPI(title="Iron Lady Admin API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    initialize_app(cred)
    print("Firebase Admin initialized successfully")
except Exception as e:
    print(f"Firebase Admin initialization error: {e}")

@app.get("/")
def root():
    return {"message": "Iron Lady Admin API is running", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/users")
def get_all_users():
    """Get all Firebase users with enhanced information"""
    try:
        all_users = []
        page = auth.list_users()
        while page:
            for user in page.users:
                user_data = {
                    "uid": user.uid,
                    "email": user.email,
                    "name": user.display_name,
                    "phone": user.phone_number,
                    "email_verified": user.email_verified,
                    "disabled": user.disabled,
                    "created": user.user_metadata.creation_timestamp,
                    "last_login": user.user_metadata.last_sign_in_timestamp,
                    "providers": [provider.provider_id for provider in user.provider_data]
                }
                all_users.append(user_data)
            page = page.get_next_page()
        
        return {
            "success": True,
            "count": len(all_users),
            "users": all_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")

@app.get("/users/{user_id}")
def get_user(user_id: str):
    """Get specific user by ID"""
    try:
        user = auth.get_user(user_id)
        return {
            "uid": user.uid,
            "email": user.email,
            "name": user.display_name,
            "phone": user.phone_number,
            "email_verified": user.email_verified,
            "disabled": user.disabled,
            "created": user.user_metadata.creation_timestamp,
            "last_login": user.user_metadata.last_sign_in_timestamp,
            "providers": [provider.provider_id for provider in user.provider_data]
        }
    except auth.UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
def get_user_stats():
    """Get user statistics"""
    try:
        all_users = []
        page = auth.list_users()
        while page:
            for user in page.users:
                all_users.append(user)
            page = page.get_next_page()
        
        total_users = len(all_users)
        active_users = len([u for u in all_users if not u.disabled])
        verified_users = len([u for u in all_users if u.email_verified])
        
        # Users created this month
        current_month = datetime.datetime.now().month
        current_year = datetime.datetime.now().year
        new_this_month = len([
            u for u in all_users 
            if datetime.datetime.fromtimestamp(u.user_metadata.creation_timestamp / 1000).month == current_month and
            datetime.datetime.fromtimestamp(u.user_metadata.creation_timestamp / 1000).year == current_year
        ])
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "verified_users": verified_users,
            "new_this_month": new_this_month,
            "disabled_users": total_users - active_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)