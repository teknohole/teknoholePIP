# Package resmi teknohole.com

## Penggunaan WebStorage SDK

Dokumentasi ini menjelaskan cara menggunakan `WebStorage` SDK untuk mengunggah dan menghapus file.

---

### 1. Instalasi

```bash
pip install teknohole
```

---

### 2. Inisialisasi Klien

Pertama, impor kelas `WebStorage` dan buat sebuah *instance* dengan **API Key** dan **Nama Storage** Anda (didapat dari service web storage teknohole).

```python
from teknohole.web import WebStorage

# Ganti dengan kredensial Anda
api_key = "API_KEY_ANDA_YANG_SANGAT_RAHASIA"
storage_name = "NAMA_STORAGE_ANDA"

# Buat instance klien
client = WebStorage(api_key, storage_name)
```

---

### 3. Mengunggah File 🖼️

Gunakan metode `upload_file()` untuk mengunggah file. Metode ini memerlukan satu argumen: `path` (lokasi) lengkap ke file yang ingin Anda unggah.

#### Contoh Penggunaan

```python
# Asumsikan Anda memiliki file bernama 'gambar-produk.jpg' di direktori yang sama
file_path = 'gambar-produk.jpg'

print(f"Mencoba mengunggah file: {file_path}")
hasil_upload = client.upload_file(file_path)

if hasil_upload['success']:
    # Jika berhasil, simpan object_key untuk penggunaan di masa depan (misal: delete)
    object_key = hasil_upload['data']['key']
    print(f"✅ Upload Berhasil!")
    print(f"   Pesan: {hasil_upload['message']}")
    print(f"   Object Key: {object_key}")
else:
    # Jika gagal
    print(f"❌ Upload Gagal!")
    print(f"   Pesan: {hasil_upload['message']}")

# Jangan lupa untuk menyimpan object_key di database Anda jika perlu
```

#### Respons dari `upload_file()`

* **Jika Berhasil**: Anda akan menerima *dictionary* dengan `success: True` dan sebuah `data` yang berisi `key` dari objek yang diunggah.

    ```json
    {
        "success": true,
        "message": "File berhasil diunggah.",
        "data": {
            "key": "https://cdn.teknohole.com/<id-akun>/<nama-storage>/<nama-file>"
        }
    }
    ```

* **Jika Gagal**: Anda akan menerima *dictionary* dengan `success: False` dan sebuah `message` yang menjelaskan penyebab kegagalan.

    ```json
    {
        "success": false,
        "message": "File tidak ditemukan: gambar-produk.jpg"
    }
    ```
#### Modifikasi File
 Anda juga bisa memodikasi file dengan cara upload file dengan nama yang sama melalui sdk, tetapi ini akan memerlukan waktu agar file berubah sepenuhnya di CDN.

---

### 4. Menghapus File

Gunakan metode `delete_file()` untuk menghapus file. Metode ini memerlukan `object_key` yang Anda dapatkan saat berhasil mengunggah file.

### Contoh Penggunaan

```python
# Gunakan object_key yang didapat dari proses upload
key_untuk_dihapus = "https://cdn.teknohole.com/<id-akun>/<nama-storage>/<nama-file>" 

print(f"Mencoba menghapus file dengan key: {key_untuk_dihapus}")
hasil_hapus = client.delete_file(key_untuk_dihapus)

if hasil_hapus['success']:
    print(f"✅ File Berhasil Dihapus!")
else:
    print(f"❌ Gagal Menghapus File!")
    print(f"   Pesan: {hasil_hapus['message']}")
```

---

### 5. Menutup Koneksi (Penting!)

Setelah selesai menggunakan klien, sangat disarankan untuk menutup koneksi menggunakan metode `close()`. Ini akan membebaskan sumber daya jaringan. Praktik terbaik adalah menggunakan blok `try...finally` untuk memastikan koneksi selalu ditutup, bahkan jika terjadi *error*.

### Contoh Praktik Terbaik

```python
from web_client_simple import WebStorage
import os

api_key = "API_KEY_ANDA"
storage_name = "NAMA_STORAGE_ANDA"
client = WebStorage(api_key, storage_name)

# Membuat file dummy untuk diuji
with open("test_file.txt", "w") as f:
    f.write("Ini adalah file tes.")

try:
    # Lakukan semua operasi di dalam blok 'try'
    print("--- Proses Upload ---")
    upload_result = client.upload_file("test_file.txt")
    
    if upload_result['success']:
        print(f"Upload berhasil. Key: {upload_result['data']['key']}")
        
        object_key = upload_result['data']['key']
        
        print("\n--- Proses Delete ---")
        delete_result = client.delete_file(object_key)
        
        if delete_result['success']:
            print("Penghapusan berhasil.")
        else:
            print(f"Penghapusan gagal: {delete_result['message']}")
            
    else:
        print(f"Upload gagal: {upload_result['message']}")

finally:
    # Blok 'finally' akan selalu dieksekusi
    print("\nMenutup koneksi klien...")
    client.close()
    
    # Menghapus file dummy
    os.remove("test_file.txt")
    print("Selesai.")

```