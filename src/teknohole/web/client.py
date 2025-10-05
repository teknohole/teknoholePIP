import os
import mimetypes
import httpx
from typing import Dict, Any

class WebStorage:
    """
    SDK untuk mengunggah dan menghapus file di layanan WebStorage.
    Scope: meminta presigned URL, mengunggah file, dan menghapus file.
    """

    def __init__(self, api_key: str, storage_name: str):
        if not api_key or not storage_name:
            raise ValueError("API Key dan Storage Name diperlukan.")
        
        self.api_key = api_key
        self.storage_name = storage_name
        self.service_url = 'https://storage.teknohole.com/api'
        self._client = httpx.Client(timeout=30.0)

    def _get_service_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'ApiKey {self.api_key}',
            'Storage': f'Storage {self.storage_name}',
            'Content-Type': 'application/json',
        }

    def _request_to_service(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f'{self.service_url}{endpoint}'
        try:
            response = self._client.request(
                method, url, headers=self._get_service_headers(), **kwargs
            )
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                message = error_data.get("message", "Terjadi kesalahan HTTP.")
            except ValueError:
                message = e.response.text or "Terjadi kesalahan HTTP."
            return {"success": False, "message": message, "status": e.response.status_code}
        except httpx.RequestError as e:
            return {"success": False, "message": f"Koneksi ke server gagal: {e}"}

    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """Mengunggah satu file."""
        if not os.path.exists(file_path):
            return {"success": False, "message": f"File tidak ditemukan: {file_path}"}

        presign_payload = {
            'fileName': os.path.basename(file_path),
            'fileType': mimetypes.guess_type(file_path)[0] or 'application/octet-stream',
            'fileSize': os.path.getsize(file_path)
        }
        presign_result = self._request_to_service(
            method='POST',
            endpoint='/cdn/upload-url/',
            json=presign_payload,
        )

        if not presign_result['success']:
            return presign_result
        
        presigned_data = presign_result['data']
        upload_url = presigned_data['url']
        object_key = presigned_data['key']

        try:
            with open(file_path, 'rb') as file_data:
                upload_response = self._client.put(
                    upload_url,
                    content=file_data,
                    headers={'Content-Type': presign_payload['fileType']}
                )
                upload_response.raise_for_status()

            return {
                'success': True,
                'message': 'File berhasil diunggah.',
                'data': {'key': object_key}
            }
        except httpx.HTTPStatusError as e:
            return {
                'success': False,
                'message': f"Gagal mengunggah ke storage: {e.response.status_code} - {e.response.text}",
            }
        except httpx.RequestError as e:
            return {'success': False, 'message': f"Koneksi ke storage gagal: {e}"}

    def delete_file(self, object_key: str) -> Dict[str, Any]:
        """Menghapus file dari storage menggunakan object key-nya."""
        if not object_key:
            return {"success": False, "message": "Object key diperlukan."}
            
        return self._request_to_service(
            method='DELETE',
            endpoint='/cdn/delete-object/',
            json={'key': object_key},
        )
    
    def close(self):
        self._client.close()