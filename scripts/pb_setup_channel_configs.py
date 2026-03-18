#!/usr/bin/env python3
"""
Create the monk_channel_configs collection in PocketBase and seed a dev record.

Usage:
    doppler run -- pdm run python scripts/pb_setup_channel_configs.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services', 'api'))

from pocketbase import PocketBase  # noqa: E402
from pocketbase.errors import ClientResponseError  # noqa: E402

PB_URL = os.environ['POCKETBASE_API_URL']
PB_EMAIL = os.environ['POCKETBASE_BOT_EMAIL']
PB_PASSWORD = os.environ['POCKETBASE_BOT_PASSWORD']

pb = PocketBase(PB_URL)
pb.admins.auth_with_password(PB_EMAIL, PB_PASSWORD)

# --------------------------------------------------------------------------- #
# Create collection (idempotent) — check via collection record list
# --------------------------------------------------------------------------- #

try:
    pb.collection('monk_channel_configs').get_list(1, 1)
    print('Collection monk_channel_configs already exists — skipping.')
except ClientResponseError:
    # Collection doesn't exist; create it.
    # The SDK may fail to decode the creation response (version mismatch) but
    # the server-side operation still succeeds — verify afterwards.
    try:
        pb.collections.create({
            'name': 'monk_channel_configs',
            'type': 'base',
            'fields': [
                {'name': 'instance_id', 'type': 'text', 'required': True},
                {'name': 'handler', 'type': 'text', 'required': True},
                {'name': 'channel', 'type': 'text', 'required': True},
                {'name': 'config', 'type': 'json', 'required': True},
            ],
        })
    except Exception:
        pass  # SDK decode error is benign; collection is created server-side

    # Verify the collection is now accessible
    pb.collection('monk_channel_configs').get_list(1, 1)
    print('Created collection monk_channel_configs.')

# --------------------------------------------------------------------------- #
# Seed dev record for mxf/chatwoot/whatsapp (idempotent)
# --------------------------------------------------------------------------- #

try:
    pb.collection('monk_channel_configs').get_first_list_item(
        'instance_id="mxf" && handler="chatwoot" && channel="whatsapp"'
    )
    print('Dev config for mxf/chatwoot/whatsapp already exists — skipping.')
except ClientResponseError:
    pb.collection('monk_channel_configs').create({
        'instance_id': 'mxf',
        'handler': 'chatwoot',
        'channel': 'whatsapp',
        'config': {
            'url': 'https://chatwoot.example.com',
            'api_token': 'DEV_TOKEN_PLACEHOLDER',
            'account_id': 1,
            'inbox_id': 1,
            'phone_attrib': 'phone',
        },
    })
    print('Inserted dev config for mxf/chatwoot/whatsapp.')

print('Done.')
