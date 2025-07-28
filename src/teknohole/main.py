import argparse
import requests
import os
import json
from rich.console import Console
from rich.prompt import Prompt

console = Console()

CONFIG_PATH = os.path.expanduser("~/.teknohole/config.json")
API_BASE_URL = "https://apingajiqu.teknohole.com/api"

def save_token(token):
    """Menyimpan token ke file konfigurasi."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"token": token}, f)
    console.print("🔑 Token berhasil disimpan.", style="bold green")

def load_token():
    """Memuat token dari file konfigurasi."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f).get("token")
        except (json.JSONDecodeError, KeyError):
            return None
    return None

def login(email, password):
    """Mengirim permintaan login ke API."""
    url = f"{API_BASE_URL}/akun/login"
    console.print("Mencoba login...", style="yellow")
    try:
        resp = requests.post(url, json={"email": email, "password": password})
        resp.raise_for_status()

        token = resp.json().get("access")
        if token:
            save_token(token)
            console.print("✅ Login berhasil!", style="bold green")
        else:
            console.print("❌ Login gagal: Token tidak ditemukan dalam respons.", style="bold red")
    except requests.exceptions.RequestException as e:
        console.print(f"❌ Login gagal: Terjadi kesalahan jaringan atau server. [bold red]{e}[/bold red]")
    except json.JSONDecodeError:
        console.print("❌ Login gagal: Respons dari server bukan format JSON yang valid.", style="bold red")


def api_request(endpoint):
    """Membuat permintaan GET ke endpoint API yang dilindungi."""
    token = load_token()
    if not token:
        console.print("⚠ Anda harus login terlebih dahulu. Jalankan [bold cyan]teknohole login[/bold cyan].", style="bold yellow")
        return

    headers = {"Authorization": f"Bearer {token}"}
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        
        console.print_json(data=resp.json())

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
             console.print("❌ Gagal: Token tidak valid atau kedaluwarsa. Silakan login kembali.", style="bold red")
        else:
             console.print(f"❌ Gagal: Error [bold red]{e.response.status_code}[/bold red] saat mengakses endpoint.", style="bold red")
    except requests.exceptions.RequestException as e:
        console.print(f"❌ Gagal: Terjadi kesalahan jaringan. [bold red]{e}[/bold red]")
    except json.JSONDecodeError:
        console.print("❌ Gagal: Respons dari server bukan format JSON yang valid.", style="bold red")

def main():
    """Fungsi utama untuk parsing argumen CLI."""
    parser = argparse.ArgumentParser(
        prog="teknohole", 
        description="CLI untuk berinteraksi dengan Teknohole API."
    )
    subparsers = parser.add_subparsers(dest="command", help="Perintah yang tersedia")
    subparsers.add_parser("login", help="Login ke API untuk mendapatkan token.")
    req_parser = subparsers.add_parser("get", help="Membuat GET request ke sebuah endpoint API.")
    req_parser.add_argument("endpoint", help="Endpoint API yang dituju (contoh: 'profile/')")

    args = parser.parse_args()

    if args.command == "login":
        email = Prompt.ask("[bold cyan]Masukkan email[/bold cyan]")
        password = Prompt.ask("[bold cyan]Masukkan password[/bold cyan]", password=True) # password=True akan menyembunyikan ketikan
        login(email, password)
    elif args.command == "get":
        api_request(args.endpoint)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()