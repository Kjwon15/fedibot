import logging
import logging.config
import os
from pprint import pprint
from mastodon import Mastodon, StreamListener

API_BASE_URL = os.getenv('API_BASE_URL')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')


logger = logging.getLogger('fedibot')


class PublicListener(StreamListener):

    def __init__(self, api):
        self.api = api
        self.me = api.account_verify_credentials()
        self.refresh_following()

    def on_update(self, status):
        account = status['account']
        acct = account['acct']

        if acct in self.followings:
            logger.debug(f'Already following {acct}')
            return

        if self.is_local_account(acct):
            logger.debug(f'{acct} is local account, skipping')
            return

        if account['locked']:
            logger.debug(f'{acct} is locked account, skipping')
            return

        logger.info(f'New account: {acct}')
        self.api.account_follow(account['id'])
        self.refresh_following()

    def on_notification(self, notification):
        pprint(notification)

    def handle_heartbeat(self):
        logger.debug('Handling heartbeat')
        self.refresh_following()

    @staticmethod
    def is_local_account(acct):
        return '@' not in acct

    def refresh_following(self):
        self.followings = {
            account['acct']
            for account in self.api.account_following(self.me['id'])
        }

        logger.info(f'Currently following {len(self.followings)} users')


def main():
    mastodon = Mastodon(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        access_token=ACCESS_TOKEN,
        api_base_url=API_BASE_URL,
    )

    listener = PublicListener(mastodon)
    mastodon.public_stream(listener)


if __name__ == '__main__':
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'normal': {
                'format': '%(asctime)s:%(name)s:%(levelname)s:%(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %z',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'normal',
                'level': 'DEBUG',
            }
        },
        'loggers': {
            'fedibot': {
                'handlers': ['console'],
                'level': 'DEBUG',
                'propagate': False,
            },
        },
        'root': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
    })
    logger.info('Starting')
    main()
