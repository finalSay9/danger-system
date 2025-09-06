from fastapi import FastAPI
from routes import users,auth


app = FastAPI(
    title='CHATTING APP'
)

app.include_router(users.router, tags=['users'])
app.include_router(auth.router, tags=['auth'])


