# gophish-auto-deploy
# GoPhish Auto Deploy Script

This script automates the full deployment of [GoPhish](https://github.com/gophish/gophish) on a Linux server, including SSL setup and configuration.

## Features

- System update & dependency install
- Downloads latest GoPhish release
- Configures GoPhish with SSL
- Supports manual DNS-01 Certbot challenge
- (Optional) Namecheap API DNS automation
- Launches GoPhish with logging

## Usage

```bash
sudo python3 deploy_gophish.py
