#!/usr/bin/env python3
"""
NetSage AI Local Runner.
Executes rule checks, verifies dataset, and launches local web dashboard.
"""

import os
import subprocess
import sys
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

def run_step(title, cmd):
    print(f"\n[+] {title}...")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"Warning: {cmd} exited with code {res.returncode}")

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    print("=" * 60)
    print("      NetSage AI - Packet Tracer Troubleshooting Assistant")
    print("=" * 60)

    # 1. Rule checker
    run_step("Running Deterministic Rule Checker", [sys.executable, "scripts/rule_checker.py"])

    # 2. Build dashboard check
    run_step("Validating Dashboard & Reviewed Results", [sys.executable, "scripts/build_dashboard.py"])

    # 3. Launch Web Server
    port = 8000
    print(f"\n[+] Serving NetSage AI at: http://localhost:{port}")
    print("[+] Opening dashboard in your default browser...")
    webbrowser.open(f"http://localhost:{port}/dashboard/dashboard.html")

    server_address = ('', port)
    try:
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        print(f"[+] Server active on port {port}. Press Ctrl+C to stop.")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except OSError as e:
        if "already in use" in str(e).lower() or e.errno in (98, 10048):
            print(f"\nPort {port} already running! Dashboard is open at http://localhost:{port}/dashboard/dashboard.html")
            webbrowser.open(f"http://localhost:{port}/dashboard/dashboard.html")
        else:
            raise

if __name__ == "__main__":
    main()
