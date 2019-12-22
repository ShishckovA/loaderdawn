# -*- coding: utf-8 -*-

from html.parser import HTMLParser
import requests

class FormParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.url         = None
        self.denial_url  = None
        self.params      = {}
        self.method      = 'GET'
        self.in_form     = False
        self.in_denial   = False
        self.form_parsed = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'form':
            if self.in_form:
                raise RuntimeError('Nested form tags are not supported yet')
            else:
                self.in_form = True
        if not self.in_form:
            return

        attrs = dict((name.lower(), value) for name, value in attrs)

        if tag == 'form':
            self.url = attrs['action']
            if 'method' in attrs:
                self.method = attrs['method']
        elif tag == 'input' and 'type' in attrs and 'name' in attrs:
            if attrs['type'] in ['hidden', 'text', 'password']:
                self.params[attrs['name']] = attrs['value'] if 'value' in attrs else ''
        elif tag == 'input' and 'type' in attrs:
            if attrs['type'] == 'submit':
                self.params['submit_allow_access'] = True
        elif tag == 'div' and 'class' in attrs:
            if attrs['class'] == 'near_btn':
                self.in_denial = True
        elif tag == 'a' and 'href' in attrs and self.in_denial:
            self.denial_url = attrs['href']

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'form':
            if not self.in_form:
                raise RuntimeError('Unexpected end of <form>')
            self.form_parsed = True
            self.in_form = False
        elif tag == 'div' and self.in_denial:
            self.in_denial = False

class VKAuth(object):

    def __init__(self, email, pswd, api_v="5.80", app_id = "6401932"):

        self.session        = requests.Session()
        self.form_parser    = FormParser()
        self._user_id       = None
        self._access_token  = None
        self.response       = None

        self.permissions    = []
        self.api_v          = api_v
        self.app_id         = app_id
        self.email          = email
        self.pswd           = pswd

    def auth(self):
        api_auth_url = 'https://oauth.vk.com/authorize'
        app_id = self.app_id
        permissions = self.permissions
        redirect_uri = 'https://oauth.vk.com/blank.html'
        display = 'wap'
        api_version = self.api_v

        auth_url_template = '{0}?client_id={1}&scope={2}&redirect_uri={3}&display={4}&v={5}&response_type=token'
        auth_url = auth_url_template.format(api_auth_url, app_id, ','.join(permissions), redirect_uri, display, api_version)

        self.response = self.session.get(auth_url)

        if not self._parse_form():
            raise RuntimeError('No <form> element found. Please, check url address0')
        else:
            while not self._log_in():
                pass

    def _parse_form(self):

        self.form_parser = FormParser()
        parser = self.form_parser

        try:
            parser.feed(str(self.response.content))
        except:
            log('Unexpected error occured while looking for <form> element')
            return False

        return True

    def _submit_form(self, *params):

        parser = self.form_parser

        if parser.method == 'post':
            payload = parser.params
            payload.update(*params)
            try:
                self.response = self.session.post(parser.url, data=payload)
            except requests.exceptions.RequestException:
                pass
            except requests.exceptions.HTTPError:
                pass
            except requests.exceptions.ConnectionError:
                pass
                log("Error: ConnectionError\n")
            except requests.exceptions.Timeout:
                pass
                log("Error: Timeout\n")
            except:
                pass
                log("Unexpecred error occured")

        else:
            self.response = None

    def _log_in(self):

        self._submit_form({'email': self.email, 'pass': self.pswd})

        if not self._parse_form():
            raise RuntimeError('No <form> element found. Please, check url address1')

        if 'pass' in self.form_parser.params:
            log('Wrong email or password')
            self.email = None
            self.pswd = None
            return False
        else:
            return True

    def get_session(self):
        return self.session

    def _close(self):
        self.session.close()
        self.response = None
        self.form_parser = None
        self.security_code = None
        self.email = None
        self.pswd = None


