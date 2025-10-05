import os
import mimetypes
import httpx
from typing import Callable, Optional, Dict, Any, Generator

class WebStorage:
    DEFAULT_SERVICE_URL = 'https://storage.teknohole.com'
    MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024
    CHUNK_SIZE = 8192

    def __init__(self, api_key: str, storage_name: str, service_url: str = DEFAULT_SERVICE_URL):
        if not api_key or not storage_name:
            raise ValueError("API Key dan Storage Name diperlukan.")
        self.api_key = api_key
        self.storage_name = storage_name
        self.service_url = service_url
        self._client = httpx.Client(timeout=30.0)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get_service_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'ApiKey {self.api_key}',
            'Content-Type': 'application/json',
            'Storage': f'Storage {self.storage_name}'
        }

    def _request_to_service(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f'{self.service_url}{endpoint}'
        try:
            response = self._client.request(
                method, url, headers=self._get_service_headers(), **kwargs
            )
            response.raise_for_status()
            return {"success": True, "status": response.status_code, "data": response.json()}
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                message = error_data.get("message", "Terjadi kesalahan HTTP.")
            except ValueError:
                message = e.response.text or "Terjadi kesalahan HTTP."
            return {"success": False, "status": e.response.status_code, "message": message}
        except httpx.RequestError as e:
            return {"success": False, "status": 503, "message": f"Koneksi ke server gagal: {e}"}

    def _read_chunks(
        self, file_path: str, file_size: int, on_progress: Optional[Callable[[int], None]]
    ) -> Generator[bytes, None, None]:
        bytes_read = 0
        with open(file_path, 'rb') as f:
            while chunk := f.read(self.CHUNK_SIZE):
                bytes_read += len(chunk)
                if on_progress:
                    percent_complete = round((bytes_read * 100) / file_size)
                    on_progress(percent_complete)
                yield chunk

    def upload_file(self, file_path: str, on_progress: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File tidak ditemukan di path: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"Ukuran file melebihi batas ({self.MAX_FILE_SIZE / 1e9} GB).")

        file_name = os.path.basename(file_path)
        file_type, _ = mimetypes.guess_type(file_path)
        file_type = file_type or 'application/octet-stream'

        presign_result = self._request_to_service(
            method='POST',
            endpoint='/api/cdn/upload-url/',
            json={'fileName': file_name, 'fileType': file_type, 'fileSize': file_size},
        )

        if not presign_result.get('success'):
            return presign_result
        
        presigned_data = presign_result['data']
        upload_url = presigned_data['url']
        object_key = presigned_data['key']

        try:
            file_reader = self._read_chunks(file_path, file_size, on_progress)
            upload_response = self._client.put(
                upload_url,
                content=file_reader,
                headers={'Content-Type': file_type, 'Content-Length': str(file_size)},
            )
            upload_response.raise_for_status()
            
            return {
                'success': True, 'status': upload_response.status_code, 'data': {'key': object_key},
                'message': 'File berhasil diunggah.',
            }
        except httpx.HTTPStatusError as e:
            return {
                'success': False, 'status': e.response.status_code,
                'message': f"Gagal mengunggah ke storage: {e.response.text}",
            }
        except httpx.RequestError as e:
            return {'success': False, 'status': 503, 'message': f"Koneksi ke storage gagal: {e}"}

    def delete_file(self, object_key: str) -> Dict[str, Any]:
        if not object_key:
            raise ValueError("Object key diperlukan untuk menghapus file.")
        return self._request_to_service(
            method='DELETE',
            endpoint='/api/cdn/delete-object/',
            json={'key': object_key},
        )
    
    def close(self):
        if not self._client.is_closed:
            self._client.close()

if __name__ == '__main__':
    try:
        with WebStorage(api_key="API_KEY_ANDA", storage_name="NAMA_STORAGE_ANDA") as storage:
            file_to_upload = "contoh.txt"
            with open(file_to_upload, "w") as f:
                f.write("Ini adalah konten file contoh.")
            
            def my_progress_bar(percent):
                print(f"Progress unggah: {percent}%")
            
            result = storage.upload_file(file_to_upload, on_progress=my_progress_bar)
            print("\n--- Hasil Upload ---")
            print(result)

            if result.get('success'):
                file_key = result['data']['key']
                print(f"\nMenghapus file dengan key: {file_key}")
                delete_result = storage.delete_file(file_key)
                print("\n--- Hasil Hapus ---")
                print(delete_result)
            
            os.remove(file_to_upload)

    except ValueError as e:
        print(f"Error Konfigurasi: {e}")
    except FileNotFoundError as e:
        print(f"Error File: {e}")
