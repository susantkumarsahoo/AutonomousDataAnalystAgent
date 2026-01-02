import subprocess
import sys
import time
import signal
import os
import socket
import requests
import threading

# Global process variables
processes = {}
shutdown_event = threading.Event()

def check_port(port):
    """Check if port is available, kill process if occupied"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = s.connect_ex(('localhost', port))
            
            if result == 0:  # Port is occupied
                print(f"⚠️  Port {port} is occupied. Attempting to free it...")
                try:
                    # Kill process on port (platform specific)
                    if sys.platform == "win32":
                        subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True)
                        subprocess.run(f"taskkill /F /PID $(netstat -ano | findstr :{port} | awk '{{print $5}}')", shell=True)
                    else:
                        subprocess.run(f"lsof -ti:{port} | xargs kill -9", shell=True, stderr=subprocess.DEVNULL)
                    
                    time.sleep(1)
                    print(f"✅ Port {port} freed")
                    return True
                except:
                    print(f"❌ Could not free port {port}. Please stop manually.")
                    return False
            return True
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False

def wait_for_api(url="http://localhost:8000/healthcheck", max_attempts=30):
    """Wait for API to be ready"""
    print("⏳ Waiting for FastAPI...")
    
    for i in range(max_attempts):
        if shutdown_event.is_set():
            return False
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ FastAPI ready!")
                return True
        except:
            pass
        
        sys.stdout.write(f"\r   Attempt {i+1}/{max_attempts}...")
        sys.stdout.flush()
        time.sleep(1)
    
    print("\n❌ FastAPI failed to start")
    return False

def monitor_output(process, name):
    """Monitor process output"""
    try:
        for line in iter(process.stdout.readline, ''):
            if shutdown_event.is_set():
                break
            if line and line.strip():
                print(f"[{name}] {line.rstrip()}")
    except:
        pass

def signal_handler(sig, frame):
    """Handle shutdown"""
    if shutdown_event.is_set():
        return
    
    shutdown_event.set()
    print("\n\n" + "="*60)
    print("  Stopping servers...")
    print("="*60)
    
    for name, process in processes.items():
        if process:
            print(f"⏹️  Stopping {name}...")
            try:
                process.terminate()
                process.wait(timeout=3)
            except:
                process.kill()
    
    print("\n✅ All servers stopped!")
    sys.exit(0)

def run_servers():
    """Start all servers"""
    global processes
    
    print("\n" + "="*60)
    print("  Starting Development Servers")
    print("="*60)
    
    # Check files
    files = {
        'ml_project/backend_api/fastapi_router.py': 'FastAPI',
        'ml_project/backend_api/flask_router.py': 'Flask',
        'app.py': 'Streamlit'
    }
    
    for file, name in files.items():
        if os.path.exists(file):
            print(f"✓ Found {name}")
        else:
            print(f"❌ Missing {file}")
            sys.exit(1)
    
    # Check and free ports
    ports = [(8000, 'FastAPI'), (5000, 'Flask'), (8501, 'Streamlit')]
    for port, service in ports:
        if not check_port(port):
            print(f"\n❌ Cannot free port {port} for {service}")
            sys.exit(1)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start FastAPI
        print("\n🚀 Starting FastAPI...")
        processes['FastAPI'] = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 
             'ml_project.backend_api.fastapi_router:app',
             '--host', '0.0.0.0', '--port', '8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        threading.Thread(target=monitor_output, args=(processes['FastAPI'], "FastAPI"), daemon=True).start()
        
        if not wait_for_api():
            signal_handler(None, None)
            return
        
        # Start Flask
        print("\n🚀 Starting Flask...")
        processes['Flask'] = subprocess.Popen(
            [sys.executable, '-m', 'flask', 'run'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env={**os.environ, 
                 'FLASK_APP': 'ml_project.backend_api.flask_router',
                 'FLASK_RUN_PORT': '5000',
                 'PYTHONUNBUFFERED': '1'}
        )
        
        threading.Thread(target=monitor_output, args=(processes['Flask'], "Flask"), daemon=True).start()
        time.sleep(2)
        
        # Start Streamlit
        print("\n🚀 Starting Streamlit...")
        processes['Streamlit'] = subprocess.Popen(
            [sys.executable, '-m', 'streamlit', 'run', 'app.py',
             '--server.headless', 'true',
             '--server.port', '8501'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        threading.Thread(target=monitor_output, args=(processes['Streamlit'], "Streamlit"), daemon=True).start()
        time.sleep(3)
        
        # Display URLs
        print("\n" + "="*60)
        print("✅ All servers running!")
        print("="*60)
        print("\n📍 Access URLs:")
        print("   FastAPI:    http://localhost:8000")
        print("   Docs:       http://localhost:8000/docs")
        print("   Flask:      http://localhost:5000")
        print("   Streamlit:  http://localhost:8501")
        print("\n💡 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        # Monitor processes
        while not shutdown_event.is_set():
            time.sleep(1)
            
            for name, process in processes.items():
                if process.poll() is not None:
                    print(f"\n⚠️  {name} stopped! (Exit: {process.returncode})")
                    signal_handler(None, None)
                    break
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        signal_handler(None, None)

if __name__ == "__main__":
    # Check packages
    required = ['fastapi', 'uvicorn', 'streamlit', 'flask', 'requests']
    missing = [pkg for pkg in required if not __import__('importlib').util.find_spec(pkg)]
    
    if missing:
        print(f"\n❌ Missing: {', '.join(missing)}")
        print("Install: pip install fastapi uvicorn streamlit flask requests")
        sys.exit(1)
    
    run_servers()