from __future__ import absolute_import
import abc
import logging
import hashlib
import hmac
import six
import requests

__version__ = '6.1.0'

logger = logging.getLogger(__name__)


DEFAULT_API_VERSION = 2.12


class MessengerClient(object):

    # https://developers.facebook.com/docs/messenger-platform/send-messages#messaging_types
    MESSAGING_TYPES = {
        'RESPONSE',
        'UPDATE',
        'MESSAGE_TAG',
    }

    # https://developers.facebook.com/docs/messenger-platform/reference/send-api/#payload
    NOTIFICATION_TYPES = {
        'REGULAR',
        'SILENT_PUSH',
        'NO_PUSH'
    }

    def __init__(self, page_access_token, **kwargs):
        """
            @required:
                page_access_token
            @optional:
                session
                api_version
                app_secret
        """

        self.page_access_token = page_access_token
        self.session = kwargs.get('session', requests.Session())
        self.api_version = kwargs.get('api_version', DEFAULT_API_VERSION)
        self.graph_url = 'https://graph.facebook.com/v{api_version}'.format(api_version=self.api_version)
        self.app_secret = kwargs.get('app_secret')

    @property
    def auth_args(self):
        if not hasattr(self, '_auth_args'):
            auth = {
                'access_token': self.page_access_token
            }
            if self.app_secret is not None:
                appsecret_proof = self.generate_appsecret_proof()
                auth['appsecret_proof'] = appsecret_proof
            self._auth_args = auth
        return self._auth_args

    def get_user_data(self, recipient_id, fields=None, timeout=None):
        params = {}

        if isinstance(fields, six.string_types):
            params['fields'] = fields
        elif isinstance(fields, (list, tuple)):
            params['fields'] = ','.join(fields)
        else:
            params['fields'] = 'first_name,last_name,profile_pic,locale,timezone,gender'

        params.update(self.auth_args)

        r = self.session.get(
            '{graph_url}/{recipient_id}'.format(graph_url=self.graph_url, recipient_id=recipient_id),
            params=params,
            timeout=timeout
        )
        return r.json()

    def send(self, payload, recipient_id, messaging_type='RESPONSE', notification_type='REGULAR',
             timeout=None, tag=None):
        if messaging_type not in self.MESSAGING_TYPES:
            raise ValueError('`{}` is not a valid `messaging_type`'.format(messaging_type))

        if notification_type not in self.NOTIFICATION_TYPES:
            raise ValueError('`{}` is not a valid `notification_type`'.format(notification_type))

        body = {
            'messaging_type': messaging_type,
            'notification_type': notification_type,
            'recipient': {
                'id': recipient_id,
            },
            'message': payload,
        }

        if tag:
            body['tag'] = tag

        r = self.session.post(
            '{graph_url}/me/messages'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json=body,
            timeout=timeout
        )
        return r.json()

    def send_action(self, sender_action, recipient_id, timeout=None):
        r = self.session.post(
            '{graph_url}/me/messages'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'recipient': {
                    'id': recipient_id,
                },
                'sender_action': sender_action
            },
            timeout=timeout
        )
        return r.json()

    def subscribe_app_to_page(self, timeout=None):
        r = self.session.post(
            '{graph_url}/me/subscribed_apps'.format(graph_url=self.graph_url),
            params=self.auth_args,
            timeout=timeout
        )
        return r.json()

    def set_messenger_profile(self, data, timeout=None):
        r = self.session.post(
            '{graph_url}/me/messenger_profile'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json=data,
            timeout=timeout
        )
        return r.json()

    def delete_get_started(self, timeout=None):
        r = self.session.delete(
            '{graph_url}/me/messenger_profile'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'fields': [
                    'get_started'
                ],
            },
            timeout=timeout
        )
        return r.json()

    def delete_ice_breakers(self, timeout=None):
        r = self.session.delete(
            '{graph_url}/me/messenger_profile'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'fields': [
                    'ice_breakers'
                ],
            },
            timeout=timeout
        )
        return r.json()

    def delete_persistent_menu(self, timeout=None):
        r = self.session.delete(
            '{graph_url}/me/messenger_profile'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'fields': [
                    'persistent_menu'
                ],
            },
            timeout=timeout
        )
        return r.json()

    def link_account(self, account_linking_token, timeout=None):
        r = self.session.post(
            '{graph_url}/me'.format(graph_url=self.graph_url),
            params=dict({
                'fields': 'recipient',
                'account_linking_token': account_linking_token
            }, **self.auth_args),
            timeout=timeout
        )
        return r.json()

    def unlink_account(self, psid, timeout=None):
        r = self.session.post(
            '{graph_url}/me/unlink_accounts'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'psid': psid
            },
            timeout=timeout
        )
        return r.json()

    def update_whitelisted_domains(self, domains, timeout=None):
        if not isinstance(domains, list):
            domains = [domains]
        r = self.session.post(
            '{graph_url}/me/messenger_profile'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'whitelisted_domains': domains
            },
            timeout=timeout
        )
        return r.json()

    def remove_whitelisted_domains(self, timeout=None):
        r = self.session.delete(
            '{graph_url}/me/messenger_profile'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'fields':[
                    'whitelisted_domains'
                ],
            },
            timeout=timeout
        )
        return r.json()

    def upload_attachment(self, attachment, timeout=None):
        if not attachment.url:
            raise ValueError('Attachment must have `url` specified')
        if attachment.quick_replies:
            raise ValueError('Attachment may not have `quick_replies`')
        r = self.session.post(
            '{graph_url}/me/message_attachments'.format(graph_url=self.graph_url),
            params=self.auth_args,
            json={
                'message':  attachment.to_dict()
            },
            timeout=timeout
        )
        return r.json()

    def generate_appsecret_proof(self):
        """
            @outputs:
                appsecret_proof: HMAC-SHA256 hash of page access token
                    using app_secret as the key
        """
        app_secret = str(self.app_secret).encode('utf8')
        access_token = str(self.page_access_token).encode('utf8')

        return hmac.new(app_secret, access_token, hashlib.sha256).hexdigest()


class BaseMessenger(object):
    __metaclass__ = abc.ABCMeta

    last_message = {}

    def __init__(self, page_access_token, app_secret=None):
        self.page_access_token = page_access_token
        self.app_secret = app_secret
        self.client = MessengerClient(self.page_access_token, app_secret=self.app_secret)

    @abc.abstractmethod
    def account_linking(self, message):
        """Method to handle `account_linking`"""

    @abc.abstractmethod
    def message(self, message):
        """Method to handle `messages`"""

    @abc.abstractmethod
    def delivery(self, message):
        """Method to handle `message_deliveries`"""

    @abc.abstractmethod
    def optin(self, message):
        """Method to handle `messaging_optins`"""

    @abc.abstractmethod
    def postback(self, message):
        """Method to handle `messaging_postbacks`"""

    @abc.abstractmethod
    def read(self, message):
        """Method to handle `message_reads`"""

    def handle(self, payload):
        for entry in payload['entry']:
            for message in entry['messaging']:
                self.last_message = message
                if message.get('account_linking'):
                    return self.account_linking(message)
                elif message.get('delivery'):
                    return self.delivery(message)
                elif message.get('message'):
                    return self.message(message)
                elif message.get('optin'):
                    return self.optin(message)
                elif message.get('postback'):
                    return self.postback(message)
                elif message.get('read'):
                    return self.read(message)

    def get_user(self, fields=None, timeout=None):
        return self.client.get_user_data(self.get_user_id(), fields=fields, timeout=timeout)

    def send(self, payload, messaging_type='RESPONSE', notification_type='REGULAR', timeout=None, tag=None):
        return self.client.send(payload, self.get_user_id(), messaging_type=messaging_type,
                                notification_type=notification_type, timeout=timeout, tag=tag)

    def send_action(self, sender_action, timeout=None):
        return self.client.send_action(sender_action, self.get_user_id(), timeout=timeout)

    def get_user_id(self):
        return self.last_message['sender']['id']

    def subscribe_app_to_page(self, timeout=None):
        return self.client.subscribe_app_to_page(timeout=timeout)

    def set_messenger_profile(self, data, timeout=None):
        return self.client.set_messenger_profile(data, timeout=timeout)

    def delete_get_started(self, timeout=None):
        return self.client.delete_get_started(timeout=timeout)

    def link_account(self, account_linking_token, timeout=None):
        return self.client.link_account(account_linking_token, timeout=timeout)

    def unlink_account(self, psid, timeout=None):
        return self.client.unlink_account(psid, timeout=timeout)

    def add_whitelisted_domains(self, domains, timeout=None):
        return self.client.update_whitelisted_domains(domains, timeout=timeout)

    def remove_whitelisted_domains(self, timeout=None):
        return self.client.remove_whitelisted_domains(timeout=timeout)

    def upload_attachment(self, attachment, timeout=None):
        return self.client.upload_attachment(attachment, timeout=timeout)
