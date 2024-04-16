from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import asyncpg

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pool = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity; tighten this for production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

async def connect_to_db():
    global pool
    pool = await asyncpg.create_pool(
        user='postgres',
        password='admin',
        database='login',
        host='localhost'
    )

async def close_db_connection():
    await pool.close()

@app.on_event("startup")
async def startup_event():
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db_connection()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/login/")
async def login(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    async with pool.acquire() as connection:
        user_id = await connection.fetchval(
            "SELECT id FROM users WHERE username = $1 AND password = $2",
            username, password
        )
        if user_id:
            return {"message": "Login successful", "user_id": user_id}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/register/")
async def register(request: Request):
    data = await request.json()
    username = data.get("username")
    password = data.get("password")
    async with pool.acquire() as connection:
        existing_user = await connection.fetchval(
            "SELECT id FROM users WHERE username = $1",
            username
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        else:
            await connection.execute(
                "INSERT INTO users (username, password) VALUES ($1, $2)",
                username, password
            )
            return {"message": "User registered successfully"}
