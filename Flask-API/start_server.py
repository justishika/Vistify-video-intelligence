import os
import subprocess
import time
import sys

def kill_process_on_port(port):
    print(f"Checking for processes on port {port}...")
    try:
        # Find PID
        cmd = f"netstat -ano | findstr :{port}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid != '0':
                        print(f"Killing PID {pid}...")
                        subprocess.run(f"taskkill /F /PID {pid}", shell=True)
            print("Cleanup complete.")
        else:
            print("No process found on port.")
            
    except Exception as e:
        print(f"Error killing process: {e}")

if __name__ == "__main__":
    kill_process_on_port(5000)
    
    print("\nStarting Production Server (Waitress)...")
    
    # Run run_production.py
    subprocess.run([sys.executable, "run_production.py"])
