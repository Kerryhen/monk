# app/sessions.py
import logging
import secrets
from dataclasses import dataclass

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pocketbase import PocketBase
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.context import enrich_wide_event
from app.settings import Settings

logger = logging.getLogger(__name__)

settings = Settings()

pb_client = PocketBase(settings.POCKETBASE_API_URL)

security = HTTPBasic()


@dataclass
class MonkSession:
    username: str


def get_monk_session(
    credentials: HTTPBasicCredentials = Depends(security),
) -> MonkSession:
    if not (
        secrets.compare_digest(credentials.username, settings.LISTMONK_USER)
        and secrets.compare_digest(credentials.password, settings.LISTMONK_TOKEN)
    ):
        enrich_wide_event({'auth': {'outcome': 'invalid_credentials', 'username': credentials.username}})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
            headers={'WWW-Authenticate': 'Basic'},
        )

    return MonkSession(username=credentials.username)


class PocketBaseSession:
    def __init__(self, admin: bool = True):
        self.admin = admin
        self.client = pb_client

        # authenticate
        try:
            if admin:
                self.auth_data = self.client.admins.auth_with_password(
                    settings.POCKETBASE_BOT_EMAIL, settings.POCKETBASE_BOT_PASSWORD
                )
            else:
                self.auth_data = self.client.collection('users').auth_with_password(
                    settings.POCKETBASE_BOT_EMAIL, settings.POCKETBASE_BOT_PASSWORD
                )
        except Exception as e:
            logger.error('pocketbase.auth_failed', extra={'error': str(e)})
            raise HTTPException(status_code=503, detail=f'PocketBase auth failed: {e}')

        if not self.auth_data.is_valid:
            logger.error('pocketbase.token_invalid', extra={'admin': admin})
            raise HTTPException(status_code=401, detail='PocketBase token invalid')


def get_pocketbase_session(admin: bool = True) -> PocketBaseSession:
    return PocketBaseSession(admin=admin)


class Monk:
    _MAX_RETRIES = 3
    _BACKOFF_FACTOR = 1  # delays: 1s, 2s, 4s

    def __init__(self, auth_creds, url, timeout=5):
        self.__url = url
        self.timeout = timeout

        retry = Retry(
            total=self._MAX_RETRIES,
            backoff_factor=self._BACKOFF_FACTOR,
            allowed_methods=False,  # retry all HTTP methods
            status_forcelist=[],  # only retry on network/timeout errors, not HTTP errors
        )
        self.__session = requests.Session()
        self.__session.mount('http://', HTTPAdapter(max_retries=retry))
        self.__session.mount('https://', HTTPAdapter(max_retries=retry))
        self.__session.auth = auth_creds

    def delete(self, params, path=None):
        url = self.__url + path if path else self.__url
        return self.__session.delete(url, params=params, timeout=self.timeout)

    def post(self, params, path=None):
        url = self.__url + path if path else self.__url
        return self.__session.post(url, json=params, timeout=self.timeout)

    def post_multipart(self, files, data, path=None):
        url = self.__url + path if path else self.__url
        return self.__session.post(url, files=files, data=data, timeout=self.timeout)

    def put(self, params, path=None):
        url = self.__url + path if path else self.__url
        return self.__session.put(url, json=params, timeout=self.timeout)

    def patch(self, params):
        return self.__session.patch(self.__url, params=params, timeout=self.timeout)

    def get(self, params, path=None):
        url = self.__url + path if path else self.__url
        return self.__session.get(url, params=params, timeout=self.timeout)
