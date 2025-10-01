"""
Generate a test authentication token for frontend access
"""

from core.auth import create_test_token
import webbrowser
import os

def main():
    """Generate test token and create HTML file with embedded token"""
    
    # Generate token
    token = create_test_token()
    
    print("=" * 60)
    print("AuraQuant Test Token Generated")
    print("=" * 60)
    print(f"\nAuth Token: {token}\n")
    print("This token is valid for 30 minutes.")
    print("\nTo use this token in the frontend:")
    print("1. Open your browser's developer console (F12)")
    print("2. Run this command:")
    print(f"   localStorage.setItem('auth_token', '{token}');")
    print("3. Refresh the page")
    
    # Create a test HTML page with embedded token
    test_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>AuraQuant System Test</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #131722;
            color: #d1d4dc;
            padding: 40px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00ff88;
        }}
        .section {{
            background: #1e222d;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            background: #00ff88;
            color: #131722;
            text-decoration: none;
            border-radius: 4px;
            margin: 10px 10px 10px 0;
            font-weight: 600;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        .code {{
            background: #0d1117;
            padding: 10px;
            border-radius: 4px;
            font-family: monospace;
            word-break: break-all;
        }}
        .status {{
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .success {{
            background: rgba(0, 255, 136, 0.1);
            color: #00ff88;
            border: 1px solid #00ff88;
        }}
        .error {{
            background: rgba(255, 68, 68, 0.1);
            color: #ff4444;
            border: 1px solid #ff4444;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 AuraQuant System Test</h1>
        
        <div class="section">
            <h2>Authentication Status</h2>
            <div id="authStatus" class="status">Checking...</div>
            <button class="btn" onclick="setToken()">Set Auth Token</button>
            <button class="btn" onclick="checkAuth()">Check Auth</button>
        </div>
        
        <div class="section">
            <h2>API Status</h2>
            <div id="apiStatus" class="status">Checking...</div>
            <button class="btn" onclick="checkAPI()">Check API</button>
        </div>
        
        <div class="section">
            <h2>Frontend Pages</h2>
            <a href="file:///D:/New%20AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/frontend/pages/profile.html" class="btn">Open Profile Page</a>
            <a href="file:///D:/New%20AuraQuant/New_Synthetic_System_AuraQuant_Backup_2025/frontend/pages/journal.html" class="btn">Open Journal Page</a>
        </div>
        
        <div class="section">
            <h2>API Documentation</h2>
            <a href="http://localhost:8000/docs" class="btn" target="_blank">Open API Docs</a>
            <a href="http://localhost:8000/redoc" class="btn" target="_blank">Open ReDoc</a>
        </div>
        
        <div class="section">
            <h2>Your Auth Token</h2>
            <div class="code" id="tokenDisplay">{token}</div>
            <p>This token has been automatically set in your browser's localStorage.</p>
        </div>
    </div>
    
    <script>
        // Auto-set token on page load
        window.onload = function() {{
            setToken();
            checkAuth();
            checkAPI();
        }}
        
        function setToken() {{
            const token = '{token}';
            localStorage.setItem('auth_token', token);
            localStorage.setItem('auraquant_token', token);
            document.getElementById('authStatus').className = 'status success';
            document.getElementById('authStatus').textContent = '✅ Token set successfully!';
        }}
        
        function checkAuth() {{
            const token = localStorage.getItem('auth_token');
            if (token) {{
                document.getElementById('authStatus').className = 'status success';
                document.getElementById('authStatus').textContent = '✅ Authentication token found!';
            }} else {{
                document.getElementById('authStatus').className = 'status error';
                document.getElementById('authStatus').textContent = '❌ No authentication token found';
            }}
        }}
        
        async function checkAPI() {{
            try {{
                const response = await fetch('http://localhost:8000/health');
                const data = await response.json();
                if (data.status === 'healthy') {{
                    document.getElementById('apiStatus').className = 'status success';
                    document.getElementById('apiStatus').textContent = '✅ API is running and healthy!';
                }} else {{
                    document.getElementById('apiStatus').className = 'status error';
                    document.getElementById('apiStatus').textContent = '⚠️ API is running but not healthy';
                }}
            }} catch (error) {{
                document.getElementById('apiStatus').className = 'status error';
                document.getElementById('apiStatus').textContent = '❌ Cannot connect to API (ensure server is running)';
            }}
        }}
    </script>
</body>
</html>"""
    
    # Save test page
    test_page_path = os.path.join(
        "D:\\New AuraQuant\\New_Synthetic_System_AuraQuant_Backup_2025\\frontend\\pages",
        "test_system.html"
    )
    
    with open(test_page_path, 'w', encoding='utf-8') as f:
        f.write(test_html)
    
    print(f"\n✅ Test page created: {test_page_path}")
    print("\nOpening test page in browser...")
    
    # Open in browser
    webbrowser.open(f"file:///{test_page_path.replace(os.sep, '/')}")

if __name__ == "__main__":
    main()