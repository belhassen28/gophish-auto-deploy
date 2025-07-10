#!/usr/bin/env python3

import subprocess
import os
import json
import requests
import zipfile
import shutil
import time

# ------------------ USER CONFIG ------------------
DOMAIN = "your.domain.com"
EMAIL = "admin@your.domain.com"
GOPHISH_DIR = "/opt/gophish"
NAMECHEAP_API_USER = "your_namecheap_username"
NAMECHEAP_API_KEY = "your_namecheap_api_key"
NAMECHEAP_DOMAIN = "yourdomain.com"
NAMECHEAP_HOST = "_acme-challenge"
USE_NAMECHEAP = False  # Set True for automated DNS challenge
# -------------------------------------------------

def run_cmd(cmd, check=True, capture_output=False):
    result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True)
    return result.stdout.strip() if capture_output else None

def system_update():
    print("[+] Updating system and installing dependencies...")
    run_cmd("apt update && apt upgrade -y")
    run_cmd("apt install -y unzip curl certbot")

def download_gophish():
    print("[+] Downloading GoPhish...")
    r = requests.get("https://api.github.com/repos/gophish/gophish/releases/latest")
    latest_url = next(asset['browser_download_url'] for asset in r.json()['assets'] if 'linux' in asset['name'])
    
    os.makedirs(GOPHISH_DIR, exist_ok=True)
    zip_path = "/tmp/gophish.zip"
    
    with open(zip_path, 'wb') as f:
        f.write(requests.get(latest_url).content)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(GOPHISH_DIR)

    os.chmod(os.path.join(GOPHISH_DIR, "gophish"), 0o755)

def modify_config(cert_path, key_path):
    print("[+] Modifying GoPhish config...")
    config_path = os.path.join(GOPHISH_DIR, "config.json")
    
    with open(config_path, 'r') as f:
        config = json.load(f)

    config['admin_server']['listen_url'] = '0.0.0.0:3333'
    config['admin_server']['use_tls'] = True
    config['admin_server']['cert_path'] = cert_path
    config['admin_server']['key_path'] = key_path

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def get_dns_challenge(domain):
    print("[+] Generating DNS challenge with Certbot...")
    cmd = f"certbot certonly --manual --preferred-challenges dns --email {EMAIL} --agree-tos -d {domain} --manual-public-ip-logging-ok --manual"
    run_cmd(cmd)

def namecheap_update_txt_record(host, domain, value):
    print("[+] Updating DNS via Namecheap API...")
    url = (
        f"https://api.namecheap.com/xml.response?ApiUser={NAMECHEAP_API_USER}"
        f"&ApiKey={NAMECHEAP_API_KEY}&UserName={NAMECHEAP_API_USER}"
        f"&Command=namecheap.domains.dns.setHosts&ClientIp=127.0.0.1"
        f"&SLD={domain.split('.')[0]}&TLD={domain.split('.')[1]}"
        f"&HostName1={host}&RecordType1=TXT&Address1={value}&TTL1=60"
    )
    res = requests.get(url)
    if "<Errors>" in res.text:
        raise Exception("[-] Error updating DNS record.")
    print("[+] DNS TXT record updated.")

def certbot_with_dns_api():
    print("[+] Using Certbot with DNS challenge (manual or API)...")
    if USE_NAMECHEAP:
        print("[+] Automated DNS challenge via Namecheap API...")
        print("[*] Please integrate DNS-01 record updates here for Certbot automation.")
        # This part can be extended with `certbot-dns-namecheap` plugin or your own integration.
    else:
        get_dns_challenge(DOMAIN)

def start_gophish():
    print("[+] Starting GoPhish...")
    gophish_binary = os.path.join(GOPHISH_DIR, "gophish")
    log_path = os.path.join(GOPHISH_DIR, "gophish.log")
    
    with open(log_path, "w") as f:
        subprocess.Popen([gophish_binary], cwd=GOPHISH_DIR, stdout=f, stderr=subprocess.STDOUT)
    
    print(f"[+] GoPhish is now running. Logs: {log_path}")
    print("[*] Visit https://<your-domain>:3333 to access the admin panel.")

def main():
    system_update()
    download_gophish()

    cert_path = f"/etc/letsencrypt/live/{DOMAIN}/fullchain.pem"
    key_path = f"/etc/letsencrypt/live/{DOMAIN}/privkey.pem"

    certbot_with_dns_api()
    modify_config(cert_path, key_path)
    start_gophish()

if __name__ == "__main__":
    main()
