from fastapi import FastAPI
from routes import users,auth, messages, chats
from fastapi.middleware.cors import CORSMiddleware
import dangersocket




app = FastAPI(
    title='CHATTING APP'
)

app.include_router(users.router, tags=['users'])
app.include_router(auth.router, tags=['auth'])
app.include_router(messages.router, tags=['messages'])
app.include_router(chats.router, tags=['chats'])
app.include_router(dangersocket.router, tags=['socket'])




# Replace "*" with the exact frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000",  "http://192.168.43.219:3000",],  # Specify your frontend's origin
    allow_credentials=True,  # Allow cookies and Authorization headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers (e.g., Authorization, Content-Type)
)


