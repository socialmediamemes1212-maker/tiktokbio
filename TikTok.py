# TikTok Bio Check Service für deine FlutterFlow App
# tiktok.py mit Proxy-Support

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re
import time
import random

def get_random_headers():
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Android 12; Mobile; rv:105.0) Gecko/105.0 Firefox/105.0',
        'Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Mobile Safari/537.36'
    ]
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def get_working_proxy():
    """Gibt eine Liste kostenloser Proxies zurück (zum Testen)"""
    # Diese Proxies sind oft instabil, aber gut zum Testen
    free_proxies = [
        # HTTP Proxies (oft funktionieren nur wenige)
        {'http': 'http://103.149.162.194:80', 'https': 'http://103.149.162.194:80'},
        {'http': 'http://47.74.152.29:8888', 'https': 'http://47.74.152.29:8888'},
        {'http': 'http://134.195.101.26:1080', 'https': 'http://134.195.101.26:1080'},
        {'http': 'http://103.155.54.185:83', 'https': 'http://103.155.54.185:83'},
        {'http': 'http://103.155.54.233:83', 'https': 'http://103.155.54.233:83'},
    ]
    return random.choice(free_proxies)

app = Flask(__name__)
CORS(app)  # Erlaubt Requests von FlutterFlow

def get_tiktok_bio(username):
    """Extrahiert die Bio von einem TikTok-Profil mit Proxy-Support"""
    
    # @ entfernen falls vorhanden
    if username.startswith('@'):
        username = username[1:]
    
    url = f"https://www.tiktok.com/@{username}"
    
    # Zufällige Headers verwenden
    headers = get_random_headers()
    
    # Random delay um weniger verdächtig zu sein
    time.sleep(random.uniform(0.5, 2.0))
    
    # Mehrere Versuche: erst ohne Proxy, dann mit verschiedenen Proxies
    attempts = [
        None,  # Kein Proxy (erster Versuch)
        get_working_proxy(),  # Proxy 1
        get_working_proxy(),  # Proxy 2
        get_working_proxy(),  # Proxy 3
    ]
    
    for attempt_num, proxy in enumerate(attempts, 1):
        try:
            print(f"Attempt {attempt_num}: {'Direct' if proxy is None else f'Proxy {proxy}'}")
            
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxy,
                timeout=15,
                verify=False  # Ignore SSL für manche Proxies
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Bio-Extraction-Methoden
                
                # Methode 1: Standard signature pattern
                signature_pattern = r'"signature":"(.*?)"'
                match = re.search(signature_pattern, html_content)
                if match:
                    bio = match.group(1)
                    bio = bio.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                    if bio and bio != "No signature found":
                        print(f"Bio found via signature pattern: {bio[:50]}...")
                        print(f"Success with: {'Direct connection' if proxy is None else f'Proxy {proxy}'}")
                        return bio
                
                # Methode 2: Webapp user-detail pattern
                webapp_pattern = r'"webapp\.user-detail":\{"userInfo":\{"user":\{[^}]*"signature":"(.*?)"'
                match = re.search(webapp_pattern, html_content)
                if match:
                    bio = match.group(1)
                    bio = bio.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                    if bio:
                        print(f"Bio found via webapp pattern: {bio[:50]}...")
                        print(f"Success with: {'Direct connection' if proxy is None else f'Proxy {proxy}'}")
                        return bio
                
                # Methode 3: UserModule pattern
                user_module_pattern = r'"UserModule":\{[^}]*"users":\{[^}]*"signature":"(.*?)"'
                match = re.search(user_module_pattern, html_content)
                if match:
                    bio = match.group(1)
                    bio = bio.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                    if bio:
                        print(f"Bio found via UserModule pattern: {bio[:50]}...")
                        print(f"Success with: {'Direct connection' if proxy is None else f'Proxy {proxy}'}")
                        return bio
                
                # Methode 4: Direkte JSON-Suche nach uniqueId
                uniqueid_pattern = rf'"uniqueId":"{re.escape(username)}"[^}}]*"signature":"(.*?)"'
                match = re.search(uniqueid_pattern, html_content, re.IGNORECASE)
                if match:
                    bio = match.group(1)
                    bio = bio.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                    if bio:
                        print(f"Bio found via uniqueId pattern: {bio[:50]}...")
                        print(f"Success with: {'Direct connection' if proxy is None else f'Proxy {proxy}'}")
                        return bio
                
                # Methode 5: Allgemeine Suche
                all_signatures = re.findall(r'"signature":"(.*?)"', html_content)
                for sig in all_signatures:
                    if sig and sig != "" and len(sig) > 5:
                        bio = sig.replace('\\n', '\n').replace('\\/', '/').replace('\\"', '"')
                        print(f"Bio found via general search: {bio[:50]}...")
                        print(f"Success with: {'Direct connection' if proxy is None else f'Proxy {proxy}'}")
                        return bio
                
                print(f"No bio found with attempt {attempt_num}")
                    
            elif response.status_code == 404:
                print(f"TikTok user @{username} not found")
                return None
            elif response.status_code == 403:
                print(f"TikTok blocked request (403) - attempt {attempt_num}")
                continue  # Try next proxy
            else:
                print(f"HTTP Error {response.status_code} - attempt {attempt_num}")
                continue
                
        except Exception as e:
            print(f"Error with attempt {attempt_num}: {e}")
            continue  # Try next proxy
    
    print("All proxy attempts failed")
    return None

@app.route('/check-bio', methods=['POST'])
def check_bio():
    """API Endpoint für Bio-Check"""
    
    try:
        data = request.json
        username = data.get('username', '').strip()
        code = data.get('code', '').strip()
        
        if not username or not code:
            return jsonify({
                'success': False,
                'error': 'Username and code are required'
            }), 400
        
        print(f"Checking bio for @{username} with code: {code}")
        
        # TikTok Bio abrufen
        bio = get_tiktok_bio(username)
        
        if bio is None:
            return jsonify({
                'success': False,
                'error': 'Could not fetch TikTok profile or bio not found',
                'username': username
            }), 404
        
        # Code in Bio suchen (case-insensitive)
        found = code.lower() in bio.lower()
        
        print(f"Bio: {bio[:100]}...")
        print(f"Code '{code}' {'FOUND' if found else 'NOT FOUND'}")
        
        return jsonify({
            'success': True,
            'found': found,
            'username': username,
            'code': code,
            'bio_preview': bio[:200] + '...' if len(bio) > 200 else bio,
            'timestamp': time.time()
        })
        
    except Exception as e:
        print(f"API Error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'tiktok-bio-checker'})

@app.route('/', methods=['GET'])
def index():
    """Info page"""
    return jsonify({
        'service': 'TikTok Bio Checker API',
        'version': '1.0.0',
        'endpoints': {
            'POST /check-bio': 'Check if code exists in TikTok bio',
            'GET /health': 'Health check'
        },
        'usage': {
            'url': '/check-bio',
            'method': 'POST',
            'body': {
                'username': 'tiktok_username',
                'code': 'verification_code'
            }
        }
    })

if __name__ == '__main__':
    # Für lokales Testen
    app.run(debug=True, host='0.0.0.0', port=5000)
