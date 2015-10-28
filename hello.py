# coding: utf-8

import webapp2
import urlparse
import logging
import json
import os
import re
from google.appengine.api import urlfetch
from google.appengine.api import taskqueue


def send_to_slack(channel_name, text):
    payload = {
        'channel': channel_name,
        'text': text
    }
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    logging.info(payload)
    result = urlfetch.fetch(url=webhook_url, payload=json.dumps(payload), method=urlfetch.POST)
    if result.status_code >= 400:
        logging.error(result.content)
        raise
    else:
        logging.info(result.content)


def register_delayed_message(channel, text, countdown):
    taskqueue.add(
        url='/task',
        payload=json.dumps({'channel': channel, 'text': text}),
        countdown=countdown
    )


def slack_handler(text, channel_name, channel_id, user_name, user_id, timestamp, **kwargs):
    channel = '#{}'.format(channel_name)
    user_mention = '<@{}>'.format(user_name, user_id)

    if re.search(r'ping', text):
        return '{} pong'.format(user_mention)

    if re.search(r'べんり', text):
        return ':smiley_cat: < べんり'

    if re.search(r'あとで', text):
        register_delayed_message(channel, text='{} あとで通知'.format(user_mention), countdown=30)
        return 'あとで通知するさ'

    if re.search(r'start pomodoro', text):
        register_delayed_message(channel, text='{} あと3分でpomodoro終わるよ'.format(user_mention), countdown=23*60)
        register_delayed_message(channel, text='{} pomodoro終わりだよ'.format(user_mention), countdown=25*60)
        return '{} pomodoro始めるよー'.format(user_mention)


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.write("""
        <html><head><title>Sakbot-py</title></head>
        <body>
        <a href="https://github.com/akiray03/sakbot-py">https://github.com/akiray03/sakbot-py</a>
        </body>
        </html>
        """)


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        params = {}
        for k, v in urlparse.parse_qs(self.request.body).items():
            params[k] = v[0] if len(v) == 1 else v
        logging.info(params)
        token = os.environ.get('SLACK_OUTGOING_TOKEN')

        if 'token' not in params:
            logging.error('token not defined')
            self.error(500)
            return
        if params['token'] != token:
            logging.error('invalid slack token: {}'.format(params['token']))
            self.error(500)
            return

        logging.info(params['text'])

        text = slack_handler(**params)
        response = {'text': text if text else ''}

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(response))


class TaskHandler(webapp2.RequestHandler):
    def get(self):
        channel = '#' + self.request.get('channel')
        text = self.request.get('text')
        send_to_slack(channel, text)

    def post(self):
        params = json.loads(self.request.body)
        send_to_slack(params['channel'], params['text'])

handlers = [
    ('/', MainPage),
    ('/webhook', WebhookHandler),
    ('/task', TaskHandler)
]
app = webapp2.WSGIApplication(handlers, debug=True)
