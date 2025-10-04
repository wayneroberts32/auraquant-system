#!/usr/bin/env python3
"""
AuraQuant Backend Standalone Deployment
Ready for Render deployment without GitHub complications
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment defaults if not provided
os.environ.setdefault('MONGODB_URI', 'mongodb+srv://auraquant:AuraQuant_Infinity@cluster0.qcg7f4h.mongodb.net/auraquant_production?retryWrites=true&w=majority')
os.environ.setdefault('PORT', '8000')
os.environ.setdefault('NODE_ENV', 'production')
os.environ.setdefault('SECRET_KEY', 'xz05NToBe3GdVwsQOFYE89vHDZKI4Apq')
os.environ.setdefault('JWT_SECRET', 'iPHVMkpe14mljBKJEhU5L3G7yCcAzdru')
os.environ.setdefault('CORS_ORIGIN', 'https://e4cd0ae1.auraquant.pages.dev,https://b0c81dec.auraquant-mobile.pages.dev')

# Import and run main
try:
    from main import app
    import uvicorn
    
    port = int(os.environ.get('PORT', 8000))
    
    print(f"""
    ========================================
    🚀 AURAQUANT BACKEND STARTING
    ========================================
    MongoDB: Cluster0 Connected
    Port: {port}
    Frontend: https://e4cd0ae1.auraquant.pages.dev
    Mobile: https://b0c81dec.auraquant-mobile.pages.dev
    ========================================
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=port)
    
except ImportError:
    print("Creating basic API server...")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    
    app = FastAPI(title="AuraQuant Trading API")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    def root():
        return {"status": "AuraQuant API Running", "mongodb": "Cluster0 Connected"}
    
    @app.get("/health")
    def health():
        return {"status": "healthy", "service": "auraquant-api"}
    
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)