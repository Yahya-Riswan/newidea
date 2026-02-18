from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./zahi_stores.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Store(Base):
    __tablename__ = "stores"
    id = Column(Integer, primary_key=True, index=True)
    subdomain = Column(String, unique=True, index=True)
    name = Column(String)
    plan = Column(String) # "free", "pro", "ultrapro"

Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- HTML Templates ---
TEMPLATES = {
    "free": """
        <div class="bg-gray-100 min-h-screen p-8">
            <nav class="text-gray-600 mb-10">Free Plan Store</nav>
            <h1 class="text-4xl font-bold text-gray-800">{name}</h1>
            <p class="mt-4">Welcome to our basic catalog.</p>
            <div class="mt-8 p-4 bg-white shadow rounded">Product List (Standard)</div>
        </div>
    """,
    "pro": """
        <div class="bg-blue-50 min-h-screen p-8">
            <nav class="flex justify-between items-center mb-10">
                <span class="text-2xl font-bold text-blue-600">{name}</span>
                <button class="bg-blue-600 text-white px-4 py-2 rounded">Cart (0)</button>
            </nav>
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-white p-6 rounded-xl shadow-lg border border-blue-100">Featured Product</div>
                <div class="bg-white p-6 rounded-xl shadow-lg border border-blue-100">Best Seller</div>
            </div>
        </div>
    """,
    "ultrapro": """
        <div class="bg-black text-white min-h-screen p-8 font-serif">
            <header class="border-b border-gray-800 pb-6 mb-10 flex justify-between">
                <h1 class="text-5xl uppercase tracking-widest">{name}</h1>
                <span class="text-gold-500">Premium Luxury Experience</span>
            </header>
            <div class="h-96 bg-gray-900 rounded-3xl flex items-center justify-center text-3xl">
                Exclusive Collection Banner
            </div>
            <footer class="mt-20 text-center text-gray-500">Powered by Zahi UltraPro</footer>
        </div>
    """
}

@app.get("/", response_class=HTMLResponse)
async def serve_store(request: Request, db: Session = Depends(get_db)):
    # Render and other proxies often put the original domain in 'x-forwarded-host'
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    
    # Logic: if host is 'pappu.zahi.co.in', subdomain is 'pappu'
    parts = host.split('.')
    if len(parts) > 2:
        subdomain = parts[0]
    else:
        subdomain = "www" # Default/Main site

    store = db.query(Store).filter(Store.subdomain == subdomain).first()
    
    if not store:
        return "<h1>Welcome to Zahi.co.in</h1><p>Start your store today!</p>"

    content = TEMPLATES.get(store.plan, TEMPLATES["free"]).format(name=store.name)
    return f"<html><head><script src='https://cdn.tailwindcss.com'></script></head><body>{content}</body></html>"

# --- Admin API to create a store for testing ---
@app.post("/create-store/")
def create_new_store(subdomain: str, name: str, plan: str, db: Session = Depends(get_db)):
    new_store = Store(subdomain=subdomain, name=name, plan=plan.lower())
    db.add(new_store)
    db.commit()
    return {{"message": "Store created!"}}
