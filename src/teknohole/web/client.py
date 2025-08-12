# teknohole/web/client.py (Versi Sinkron)

import os
import mimetypes
import httpx  # <-- Hanya impor httpx, bukan AsyncClient
from typing import Callable, Optional, Dict, Any

class WebStorage:
    """
    SDK (Versi Sinkron) untuk mengunggah dan mengelola file di layanan WebStorage.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API Key diperlukan untuk menggunakan SDK ini.")
        
        self.api_key = api_key
        self.service_url = 'http://127.0.0.1:8001'
        # Gunakan httpx.Client yang sinkron
        self._client = httpx.Client(timeout=30.0)

    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'ApiKey {self.api_key}',
            'Content-Type': 'application/json',
        }

    # Hapus 'async' dari definisi method
    def _request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        try:
            # Hapus 'await' saat memanggil request
            response = self._client.request(method, url, **kwargs)
            response.raise_for_status()
            
            try:
                response_data = response.json()
            except ValueError:
                response_data = response.text

            return {
                "success": True, "status": response.status_code, "data": response_data,
                "message": response_data.get("message", "OK") if isinstance(response_data, dict) else "OK",
            }
        except httpx.HTTPStatusError as e:
            response_data = e.response.json()
            return {
                "success": False, "status": e.response.status_code, "data": response_data,
                "message": response_data.get("message") or response_data.get("detail", "Terjadi kesalahan."),
            }
        except httpx.RequestError as e:
            return {
                "success": False, "status": 500, "data": None, "message": f"Request gagal: {e}",
            }
    
    # Hapus 'async' dari definisi method
    def upload_file(self, file_path: str, on_progress: Optional[Callable[[int], None]] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File tidak ditemukan di path: {file_path}")

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        file_type, _ = mimetypes.guess_type(file_path)
        file_type = file_type or 'application/octet-stream'

        if file_size > 5 * 1024 * 1024 * 1024:
            raise ValueError("Ukuran file melebihi batas (5 GB).")

        # Panggilan _request sekarang sinkron
        presigned_url_result = self._request(
            method='POST',
            url=f'{self.service_url}/cdn/upload-url/',
            headers=self._get_headers(),
            json={'fileName': file_name, 'fileType': file_type, 'fileSize': file_size},
        )

        if not presigned_url_result['success']:
            return presigned_url_result
        
        presigned_data = presigned_url_result['data']
        upload_url = presigned_data['url']
        object_key = presigned_data['key']

        with open(file_path, 'rb') as f:
            # Generator ini sudah sinkron, jadi tidak perlu diubah
            def progress_reader():
                bytes_read = 0
                while chunk := f.read(8192):
                    bytes_read += len(chunk)
                    if on_progress:
                        percent_complete = round((bytes_read * 100) / file_size)
                        on_progress(percent_complete)
                    yield chunk

            upload_result = self._request(
                method='PUT',
                url=upload_url,
                content=progress_reader(),
                headers={'Content-Type': file_type, 'Content-Length': str(file_size)},
            )

        if not upload_result['success']:
            return upload_result

        return {
            'success': True, 'status': upload_result['status'], 'data': {'key': object_key},
            'message': 'File berhasil diunggah.',
        }

    # Hapus 'async' dari definisi method
    def delete_file(self, object_key: str) -> Dict[str, Any]:
        return self._request(
            method='DELETE',
            url=f'{self.service_url}/cdn/delete-object/',
            headers=self._get_headers(),
            json={'key': object_key},
        )
    
    # Hapus 'async' dari definisi method
    def close(self):
        self._client.close()