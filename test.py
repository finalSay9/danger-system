from jose import jwt
from datetime import datetime
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key-for-testing")
ALGORITHM = "HS256"

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlZHdpbkBnbWFpbC5jb20iLCJleHAiOjE3NTcyNTkxMDEsInR5cGUiOiJhY2Nlc3MifQ.6I7NHcvAvpObRvy5F9l9grpib1TmX1o0W8RwevHj0hM"
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
print(payload)
