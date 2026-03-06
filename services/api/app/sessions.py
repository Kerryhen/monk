# app/sessions.py
import logging
import secrets
from dataclasses import dataclass

import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pocketbase import PocketBase

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
        logger.warning('auth.invalid_credentials', extra={'username': credentials.username})
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
            logger.error('pocketbase.token_invalid')
            raise HTTPException(status_code=401, detail='PocketBase token invalid')


def get_pocketbase_session(admin: bool = True) -> PocketBaseSession:
    return PocketBaseSession(admin=admin)


class Monk:
    def __init__(self, auth_creds, url, timeout=5):
        self.__creds = auth_creds
        self.__url = url
        self.timeout = 5

    def delete(self, params, path=None):
        url = self.__url + path if path else self.__url
        return requests.delete(
            url,
            params=params,
            auth=self.__creds,
            timeout=self.timeout,
        )

    def post(self, params, path=None):
        url = self.__url + path if path else self.__url
        return requests.post(
            url,
            json=params,
            auth=self.__creds,
            timeout=self.timeout,
        )

    def post_multipart(self, files, data, path=None):
        url = self.__url + path if path else self.__url
        return requests.post(
            url,
            files=files,
            data=data,
            auth=self.__creds,
            timeout=self.timeout,
        )

    def put(self, params, path=None):
        url = self.__url + path if path else self.__url
        return requests.put(
            url,
            json=params,
            auth=self.__creds,
            timeout=self.timeout,
        )

    def patch(self, params):
        return requests.patch(
            self.__url,
            params=params,
            auth=self.__creds,
            timeout=self.timeout,
        )

    def get(self, params, path=None):
        url = self.__url + path if path else self.__url
        return requests.get(
            url,
            params=params,
            auth=self.__creds,
            timeout=self.timeout,
        )
