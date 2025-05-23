import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, TypeVar, Generic
from abc import ABC, abstractmethod
import requests

T = TypeVar('T')

class SearchAPIException(Exception):
    pass
class SerperAPIException(SearchAPIException):
    pass

@dataclass
class SerperConfig:
    api_key: str
    api_url: str = "https://google.serper.dev/search"
    default_location: str = 'us'
    timeout: int = 10

    @classmethod
    def from_env(cls) -> 'SerperConfig':
        """Create config from environment variables"""
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            raise SerperAPIException("SERPER_API_KEY environment variable not set")
        return cls(api_key=api_key)

class SearchResult(Generic[T]):
    def __init__(self, data: Optional[T] = None, error: Optional[str] = None):
        self.data = data
        self.error = error
        self.success = error is None

    @property
    def failed(self) -> bool:
        return not self.success

class SearchAPI(ABC):
    @abstractmethod
    def get_sources(
        self,
        query: str,
        num_results: int = 8,
        stored_location: Optional[str] = None
    ) -> SearchResult[Dict[str, Any]]:
        pass

class SerperAPI(SearchAPI):

    def __init__(self, api_key: Optional[str] = None, config: Optional[SerperConfig] = None):
        if api_key:
            self.config = SerperConfig(api_key=api_key)
        else:
            self.config = config or SerperConfig.from_env()

        self.headers = {
            'X-API-KEY': self.config.api_key,
            'Content-Type': 'application/json'
        }

    @staticmethod
    def extract_fields(items: List[Dict[str, Any]], fields: List[str]) -> List[Dict[str, Any]]:
        return [{key: item.get(key, '') for key in fields if key in item} for item in items]

    def get_sources(
        self,
        query: str,
        num_results: int = 8,
        stored_location: Optional[str] = None
    ) -> SearchResult[Dict[str, Any]]:        
        if not query.strip():
            return SearchResult(error="Query cannot be empty")

        try:
            location = (stored_location or self.config.default_location).lower()
            payload = {
                'q': query,
                'num': min(max(1, num_results), 10),
                'gl': location
            }

            response = requests.post(
                self.config.api_url,
                headers=self.headers,
                json=payload,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            data = response.json()

            results = {
                'organic': self.extract_fields(
                    data.get('organic', []),
                    ['title', 'link', 'snippet', 'date']
                ),
            }

            return SearchResult(data=results)

        except requests.RequestException as e:
            return SearchResult(error=f"API request failed: {e}")
        except Exception as e:
            return SearchResult(error=f"Unexpected error: {e}")


def create_search_api(
    serper_api_key: Optional[str] = None,
) -> SearchAPI:
    return SerperAPI(api_key=serper_api_key)
