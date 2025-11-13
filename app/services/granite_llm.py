import json
from typing import Any, Dict, Optional

import requests

from app.core.config import settings


DEFAULT_MODEL_ID = "ibm/granite-3-8b-instruct"

# Rank Granite instruct models by preference so we can gracefully fall back.
FALLBACK_MODEL_ORDER = [
    "ibm/granite-3-8b-instruct",
    "ibm/granite-3-3-8b-instruct",
    "ibm/granite-3-2-8b-instruct",
    "ibm/granite-3-2b-instruct",
]

FOUNDATION_MODELS_VERSION = "2024-05-01"


class GraniteLLM:
    def __init__(self):
        self.api_key = settings.watsonx_api_key or ""
        self.project_id = settings.watsonx_project_id or ""
        self.url = (
            settings.watsonx_url.rstrip("/")
            if getattr(settings, "watsonx_url", None)
            else "https://us-south.ml.cloud.ibm.com"
        )
        self.model_id = (settings.watsonx_model_id or DEFAULT_MODEL_ID).strip()
        self.token = self._get_iam_token()
        self.available_models: set[str] = (
            self._load_available_models() if self.token else set()
        )
        self._select_supported_model()

    def _get_iam_token(self) -> Optional[str]:
        """Obtain IAM access token using API key"""
        if not self.api_key:
            print("[Granite LLM] Watsonx API key is not configured. Skipping token request.")
            return None

        try:
            response = requests.post(
                "https://iam.cloud.ibm.com/identity/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": self.api_key
                },
                timeout=15
            )
            response.raise_for_status()
            return response.json().get("access_token")
        except Exception as e:
            print(f"[Granite LLM] IAM Token Error: {e}")
            return None

    def _make_request(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Make request to IBM Watsonx Granite LLM"""
        if not self.token:
            print("[Granite LLM] No valid IAM token available.")
            return None

        if not self.project_id:
            print("[Granite LLM] Watsonx project id is missing; cannot issue requests.")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        payload = {
            "model_id": self.model_id or DEFAULT_MODEL_ID,
            "input": prompt,
            "project_id": self.project_id,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "top_k": 50,
                "top_p": 1.0,
                "repetition_penalty": 1.1,
            },
        }

        try:
            response = requests.post(
                f"{self.url}/ml/v1-beta/generation/text?version=2024-05-01",
                headers=headers,
                json=payload,
                timeout=30,
            )

            response.raise_for_status()
            result = response.json()
            return result.get("results", [{}])[0].get("generated_text", "")
        except requests.exceptions.HTTPError as e:
            response_text = getattr(e.response, "text", "") if hasattr(e, "response") else ""
            print(f"[Granite LLM] HTTPError: {e} - Response: {response_text}")

            if getattr(e.response, "status_code", None) == 404 and "model_not_supported" in response_text:
                previous_model = self.model_id
                self._select_supported_model(force_refresh=True)
                if self.model_id != previous_model:
                    print(f"[Granite LLM] Retrying with fallback model '{self.model_id}'.")
                    return self._make_request(prompt, max_tokens=max_tokens)
            return None
        except Exception as e:
            print(f"[Granite LLM] General Error: {e}")
            return None

    def _load_available_models(self) -> set[str]:
        """Fetch the available Granite models for the current tenant."""
        headers = {"Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(
                f"{self.url}/ml/v1/foundation_model_specs",
                params={"version": FOUNDATION_MODELS_VERSION},
                headers=headers,
                timeout=20,
            )
            response.raise_for_status()
            resources = response.json().get("resources", [])
            supported = set()
            for item in resources:
                model_id = item.get("model_id") if isinstance(item, dict) else None
                if model_id:
                    supported.add(str(model_id))
            return supported
        except Exception as exc:
            print(f"[Granite LLM] Unable to fetch model catalog: {exc}")
            return set()

    def _select_supported_model(self, force_refresh: bool = False) -> None:
        """Ensure we use a Granite model that is actually available."""
        if not self.token:
            return

        if force_refresh:
            self.available_models = self._load_available_models()

        if not self.available_models:
            return

        if self.model_id in self.available_models:
            return

        print(
            f"[Granite LLM] Requested model '{self.model_id}' is not available; selecting a supported alternative."
        )

        for candidate in FALLBACK_MODEL_ORDER:
            if candidate in self.available_models:
                self.model_id = candidate
                print(f"[Granite LLM] Using fallback model '{self.model_id}'.")
                return

        print("[Granite LLM] No Granite fallback models available; requests will continue to fail.")

    def ask_granite(self, prompt: str) -> str:
        system_prompt = """You are a helpful assistant for a smart city platform. 
        Provide informative, concise answers about urban sustainability, governance, and smart city technologies."""

        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        response = self._make_request(full_prompt)
        return response or "I'm sorry, I couldn't process your request at the moment."

    def generate_summary(self, text: str) -> str:
        prompt = f"""Summarize the following policy document in a clear, citizen-friendly format:\n\n{text}\n\nSummary:"""
        response = self._make_request(prompt, max_tokens=300)
        return response or "Unable to generate summary."

    def generate_eco_tip(self, topic: str) -> str:
        prompt = f"""Generate 3 practical, actionable eco-friendly tips related to "{topic}" for city residents:\n\nTips:"""
        response = self._make_request(prompt, max_tokens=200)
        return response or f"Here are some general tips for {topic}: reduce consumption, reuse materials, and recycle properly."

    def generate_city_report(self, city_name: str, kpi_data: Dict[str, Any]) -> str:
        prompt = f"""Generate a comprehensive sustainability report for {city_name} based on the following KPI data:\n\n{json.dumps(kpi_data, indent=2)}\n\nReport:"""
        response = self._make_request(prompt, max_tokens=800)
        return response or "Unable to generate report."

# Create singleton instance
granite_llm = GraniteLLM()
