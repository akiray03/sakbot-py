# coding: utf-8

import webapp2
import urlparse
import logging
import json
import os


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
        token = os.environ.get('SLACK_TOKEN')

        if 'token' not in params:
            logging.error('token not defined')
            self.error(500)
            return
        if params['token'] != token:
            logging.error('invalid slack token: {}'.format(params['token']))
            self.error(500)
            return

        response = {'text': 'success'}

        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(response))

handlers = [
    ('/', MainPage),
    ('/webhook', WebhookHandler)
]
app = webapp2.WSGIApplication(handlers, debug=True)
