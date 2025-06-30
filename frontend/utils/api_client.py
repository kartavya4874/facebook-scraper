import requests
import streamlit as st
from typing import Dict, List, Optional
import json

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token = st.session_state.get('access_token')
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _handle_response(self, response: requests.Response):
        if response.status_code == 401:
            st.session_state.clear()
            st.error("Session expired. Please login again.")
            st.rerun()
        
        if not response.ok:
            try:
                error_detail = response.json().get('detail', 'Unknown error')
            except:
                error_detail = response.text
            raise Exception(f"API Error: {error_detail}")
        
        return response.json()
    
    def register(self, email: str, password: str, full_name: str = "") -> Dict:
        data = {
            "email": email,
            "password": password,
            "full_name": full_name
        }
        response = requests.post(f"{self.base_url}/auth/register", json=data)
        return self._handle_response(response)
    
    def login(self, email: str, password: str) -> Dict:
        data = {
            "username": email,  # FastAPI OAuth2PasswordRequestForm uses 'username'
            "password": password
        }
        response = requests.post(
            f"{self.base_url}/auth/login", 
            data=data,  # form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return self._handle_response(response)
    
    def get_jobs(self) -> List[Dict]:
        response = requests.get(f"{self.base_url}/jobs/", headers=self._get_headers())
        return self._handle_response(response)
    
    def create_job(self, name: str, group_urls: List[str], config: Dict = {}) -> Dict:
        data = {
            "name": name,
            "group_urls": group_urls,
            "config": config
        }
        response = requests.post(f"{self.base_url}/jobs/", json=data, headers=self._get_headers())
        return self._handle_response(response)
    
    def get_job(self, job_id: int) -> Dict:
        response = requests.get(f"{self.base_url}/jobs/{job_id}", headers=self._get_headers())
        return self._handle_response(response)
    
    def start_job(self, job_id: int) -> Dict:
        response = requests.post(f"{self.base_url}/jobs/{job_id}/start", headers=self._get_headers())
        return self._handle_response(response)
    
    def stop_job(self, job_id: int) -> Dict:
        response = requests.post(f"{self.base_url}/jobs/{job_id}/stop", headers=self._get_headers())
        return self._handle_response(response)
    
    def delete_job(self, job_id: int) -> Dict:
        response = requests.delete(f"{self.base_url}/jobs/{job_id}", headers=self._get_headers())
        return self._handle_response(response)
    
    def get_job_posts(self, job_id: int, skip: int = 0, limit: int = 100) -> List[Dict]:
        params = {"skip": skip, "limit": limit}
        response = requests.get(
            f"{self.base_url}/data/jobs/{job_id}/posts", 
            params=params, 
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    def get_job_logs(self, job_id: int) -> List[Dict]:
        response = requests.get(f"{self.base_url}/jobs/{job_id}/logs", headers=self._get_headers())
        return self._handle_response(response)
    
    def get_user_stats(self) -> Dict:
        response = requests.get(f"{self.base_url}/data/stats", headers=self._get_headers())
        return self._handle_response(response)
    
    def export_job_data(self, job_id: int, format: str = 'csv') -> bytes:
        response = requests.get(
            f"{self.base_url}/data/jobs/{job_id}/export/{format}", 
            headers=self._get_headers()
        )
        if not response.ok:
            raise Exception(f"Export failed: {response.text}")
        return response.content

