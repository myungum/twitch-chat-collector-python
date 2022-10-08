import requests
from datetime import datetime, timedelta
import logging
from loghandler import LogHandler

MIN_VIEWER = 100
MAX_CHANNEL = 200
MAX_REQUEST = 5
TOKEN_LIFE_TIME = 60 * 60  # 1 hour
URL_GET_TOKEN = 'https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials'
URL_GET_STREAMS = 'https://api.twitch.tv/helix/streams?language=ko&first={}&after={}'


class Token:
    def __init__(self, value):
        self.value = value
        self.expired = datetime.now() + timedelta(seconds=TOKEN_LIFE_TIME)


class TwitchAPI:

    def __init__(self, conn_info: dict):
        self.client_id = conn_info['client_id']
        self.client_secret = conn_info['client_secret']
        self.token: Token = None

       # logger
        self.logger = logging.getLogger('root')
        self.logger.setLevel(logging.DEBUG)
        self.logHandler = LogHandler(logging.DEBUG, conn_info)
        self.logger.addHandler(self.logHandler)

    def get_token(self):
        # if token is unavailable, then make token
        if self.token is None or len(self.token.value) == 0 or self.token.expired < datetime.now():
            with requests.session() as s:
                res = s.post(URL_GET_TOKEN.format(
                    self.client_id, self.client_secret))
                # success
                if res.status_code == 200:
                    self.token = Token(res.json()['access_token'])
                    print('new token is created :', self.token.value)
        return self.token.value

    def get_channels_detail(self, min_viewer=MIN_VIEWER, max_channel=MAX_CHANNEL):
        headers = {
            'Client-ID': self.client_id,
            'Authorization': 'Bearer ' + self.get_token(),
            'Accept': 'application/vnd.twitchtv.v5+json'
        }

        channel_name_set = set()
        channels = []
        try:
            after = ''
            with requests.session() as s:
                for _ in range(MAX_REQUEST):
                    res = s.get(URL_GET_STREAMS.format(
                        100, after), headers=headers)
                    # success
                    if res.status_code == 200:
                        after = res.json()['pagination']['cursor']
                        for channel in res.json()['data']:
                            channel_name = channel['user_login']
                            # if channel is unique, then append to list
                            if channel_name not in channel_name_set and channel['viewer_count'] >= min_viewer:
                                if len(channel_name_set) < max_channel:
                                    channel_name_set.add(channel_name)
                                    channels.append(channel)
                                else:
                                    return channels
                    # fail
                    else:
                        self.logger.error(res.status_code)
        except ConnectionError as e:
            self.logger.error(str(e))
        return channels

    def get_channels(self, min_viewer=MIN_VIEWER, max_channel=MAX_CHANNEL):
        channels = self.get_channels_detail(
            min_viewer=min_viewer, max_channel=max_channel)
        return [channel['user_login'] for channel in channels]
