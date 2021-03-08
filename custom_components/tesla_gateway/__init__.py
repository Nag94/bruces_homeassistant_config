"""
Monitors and controls the Tesla gateway.
"""
import logging

import aiohttp
import asyncio
import async_timeout
import base64
import hashlib
import json
import os
import re
import time
from urllib.parse import parse_qs
import voluptuous as vol

from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD
    )
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

DOMAIN = 'tesla_gateway'

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 100

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string, 
    }),
}, extra=vol.ALLOW_EXTRA)

tesla_base_url = 'https://owner-api.teslamotors.com'
tesla_auth_url = 'https://auth.tesla.com'

@asyncio.coroutine
def async_setup(hass, config):

    # Tesla gateway is SSL but has no valid certificates
    websession = async_get_clientsession(hass, verify_ssl=False)

    domain_config = config[DOMAIN]
    conf_user = domain_config[CONF_USERNAME]
    conf_password = domain_config[CONF_PASSWORD]  # I've hijacked this field to pass in the Token instead of the password
    access_token = None

    @asyncio.coroutine
    def login():

        # Code extracted from https://github.com/enode-engineering/tesla-oauth2/blob/bb579721726cc00f4d1c480a5ef47d9340bb2d06/tesla.py
        # Login process explained at https://tesla-api.timdorr.com/api-basics/authentication

#        authorize_url = tesla_auth_url + '/oauth2/v3/authorize'
#        callback_url = tesla_auth_url + '/void/callback'

#        headers = {
#            "User-Agent": "curl",
#            "x-tesla-user-agent": "TeslaApp/3.10.9-433/adff2e065/android/10",
#            "X-Requested-With": "com.teslamotors.tesla",
#        }
        
#        verifier_bytes = os.urandom(86)
#        code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=")
#        code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier).digest()).rstrip(b"=").decode("utf-8")
#        state = base64.urlsafe_b64encode(os.urandom(16)).rstrip(b"=").decode("utf-8")

#        params = (
#            ("client_id", "ownerapi"),
#            ("code_challenge", code_challenge),
#            ("code_challenge_method", "S256"),
#            ("redirect_uri", callback_url),
#            ("response_type", "code"),
#            ("scope", "openid email offline_access"),
#            ("state", state),
#        )

#        try:
#            # Step 1: Obtain the login page
#            _LOGGER.debug('Step 1: GET %s\nparams %s', authorize_url, params)
#            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
#                response = yield from websession.get(authorize_url,
#                    headers=headers,
#                    params=params,
#                    raise_for_status=False)

#            if response.status != 200:
#                returned_text = yield from response.text()
#                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
#                return None
 
#            returned_text = yield from response.text()
#            if not "<title>" in returned_text:
#                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
#                return None

#            # Step 2: Obtain an authorization code
#            csrf = re.search(r'name="_csrf".+value="([^"]+)"', returned_text).group(1)
#            transaction_id = re.search(r'name="transaction_id".+value="([^"]+)"', returned_text).group(1)

#            body = {
#                "_csrf": csrf,
#                "_phase": "authenticate",
#                "_process": "1",
#                "transaction_id": transaction_id,
#                "cancel": "",
#                "identity": conf_user,
#                "credential": conf_password,
#            }
            
#            _LOGGER.debug('Step 2: POST %s\nparams: %s\nbody: %s', authorize_url, params, body)
#            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
#                response = yield from websession.post(authorize_url,
#                    headers=headers,
#                    params=params,
#                    data=body,
#                    raise_for_status=False,
#                    allow_redirects=False)

#            returned_text = yield from response.text()
#            if response.status != 302 or "<title>" in returned_text:
#                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
#                return None
            
#            is_mfa = True if response.status == 200 and "/mfa/verify" in returned_text else False
#            if is_mfa:
#                _LOGGER.warning('Multi-factor authentication enabled for the account and not supported')
#                return None
            
#            # Step 3: Exchange authorization code for bearer token
#            code = parse_qs(response.headers["location"])[callback_url + '?code']

#            token_url = tesla_auth_url + '/oauth2/v3/token'
#            body = {
#                "grant_type": "authorization_code",
#                "client_id": "ownerapi",
#                "code_verifier": code_verifier.decode("utf-8"),
#                "code": code,
#                "redirect_uri": callback_url
#            }

#            _LOGGER.debug('Step 3: POST %s', token_url)
#            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
#                response = yield from websession.post(token_url,
#                    headers=headers,
#                    data=body,
#                    raise_for_status=False)

#            returned_json = yield from response.json()
#            access_token = returned_json['access_token']
#            return access_token

#        except asyncio.TimeoutError:
#            _LOGGER.warning('Timeout call %s.', response.url)

#        except aiohttp.ClientError:
#            _LOGGER.error('Client error %s.', response.url)
        
#        return None
        return conf_password

    @asyncio.coroutine
    def revoke(access_token):

        revoke_url = tesla_base_url + '/oauth/revoke'
        headers = {'Content-type': 'application/json'}
        body = {
            'token': access_token
        }

        try:
            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
                response = yield from websession.post(revoke_url,
                    headers=headers,
                    json=body,
                    raise_for_status=False)

            if response.status != 200:
                returned_text = yield from response.text()
                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
            else:
                _LOGGER.debug('revoke completed')
                return True

        except asyncio.TimeoutError:
            _LOGGER.warning('Timeout call %s.', response.url)

        except aiohttp.ClientError:
            _LOGGER.error('Client error %s.', response.url)
        
        return False

    @asyncio.coroutine
    def get_energy_site_id(access_token):
        
        list_url = tesla_base_url + '/api/1/products'
        headers = {
            'Authorization': 'Bearer ' + access_token
            }
        body = {}

        try:        
            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
                response = yield from websession.get(list_url,
                    headers=headers,
                    json=body,
                    raise_for_status=False)

            if response.status != 200:
                returned_text = yield from response.text()
                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
            else:
                returned_json = yield from response.json()
                _LOGGER.debug(returned_json)
                for r in returned_json['response']:
                    if 'energy_site_id' in r:
                        return r['energy_site_id']
                return None

        except asyncio.TimeoutError:
            _LOGGER.warning('Timeout call %s.', response.url)

        except aiohttp.ClientError:
            _LOGGER.error('Client error %s.', response.url)
        
        return None

    @asyncio.coroutine
    def set_operation(access_token,energy_site_id,service_data):

        operation_url = tesla_base_url + '/api/1/energy_sites/{}/operation'.format(energy_site_id)
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer ' + access_token
            }
        body = {
            'default_real_mode': service_data['real_mode']
            # 'backup_reserve_percent':int(service_data['backup_reserve_percent'])
            }
        _LOGGER.debug(body)

        try:
            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
                response = yield from websession.post(operation_url,
                    json=body,
                    headers=headers,
                    raise_for_status=False)

            if response.status != 200:
                returned_text = yield from response.text()
                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
            else:
                returned_json = yield from response.json()
                _LOGGER.debug('set operation successful, response: %s', returned_json)

        except asyncio.TimeoutError:
            _LOGGER.warning('Timeout call %s.', response.url)

        except aiohttp.ClientError:
            _LOGGER.error('Client error %s.', response.url)

    @asyncio.coroutine
    def async_set_operation(service):

        access_token = yield from login()
        if access_token:
            energy_site_id = yield from get_energy_site_id(access_token)
            if energy_site_id:
                yield from set_operation(access_token, energy_site_id, service.data)
            yield from revoke(access_token)

    hass.services.async_register(DOMAIN, 'set_operation', async_set_operation)

    @asyncio.coroutine
    def set_reserve(access_token,energy_site_id,service_data):

        operation_url = tesla_base_url + '/api/1/energy_sites/{}/backup'.format(energy_site_id)
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer ' + access_token
            }
        body = {
            'backup_reserve_percent': int(service_data['reserve_percent'])
            }
        _LOGGER.debug(body)

        try:
            with async_timeout.timeout(DEFAULT_TIMEOUT, loop=hass.loop):
                response = yield from websession.post(operation_url,
                    json=body,
                    headers=headers,
                    raise_for_status=False)

            if response.status != 200:
                returned_text = yield from response.text()
                _LOGGER.warning('Error %d on call %s:\n%s', response.status, response.url, returned_text)
            else:
                returned_json = yield from response.json()
                _LOGGER.debug('set reserve successful, response: %s', returned_json)

        except asyncio.TimeoutError:
            _LOGGER.warning('Timeout call %s.', response.url)

        except aiohttp.ClientError:
            _LOGGER.error('Client error %s.', response.url)

    @asyncio.coroutine
    def async_set_reserve(service):

        access_token = yield from login()
        if access_token:
            energy_site_id = yield from get_energy_site_id(access_token)
            if energy_site_id:
                yield from set_reserve(access_token, energy_site_id, service.data)
            yield from revoke(access_token)

    hass.services.async_register(DOMAIN, 'set_operation', async_set_operation)
    hass.services.async_register(DOMAIN, 'set_reserve', async_set_reserve)

    return True