# author: Val Rotan

import requests
from lxml import html
import json

BASE_URL = 'localhost:8080'  # NO http://

USER = 'admin@bugzilla.org'
PASSWORD = 'password'

auth_cookie = ''


def sendReq(url, querystring):

    headers = {
        'Host': f'{BASE_URL}',
        'Connection': "keep-alive",
        'Upgrade-Insecure-Requests': "1",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        'Referer': f"http://{BASE_URL}/bugzilla/editfields.cgi",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "en-US,en;q=0.9",
        'Cookie': auth_cookie,
        'Cache-Control': "no-cache",
    }

    response = requests.request(
        "GET", url, headers=headers, params=querystring)
    return response


def sendLoginReq(url, querystring):
    headers = {
        'Host': f'{BASE_URL}',
        'Origin': f'http://{BASE_URL}',
        'Connection': "keep-alive",
        'Upgrade-Insecure-Requests': "1",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        'Referer': f"http://{BASE_URL}/bugzilla/editfields.cgi",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "en-US,en;q=0.9",
        'Cookie': auth_cookie,
        'Cache-Control': "no-cache",
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.request(
        "POST", url, headers=headers, data=querystring)
    return response


def sendOptionCreateReq(fieldname, optionvalue, token):

    data = {
        'value': optionvalue,
        'sortkey': '',
        'action': 'new',
        'field': fieldname,
        'token': token
    }
    print(data)
    url = f"http://{BASE_URL}/bugzilla/editvalues.cgi"

    headers = {
        'Host': f'{BASE_URL}',
        'Connection': "keep-alive",
        'Upgrade-Insecure-Requests': "1",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.90 Safari/537.36",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        'Referer': f"{BASE_URL}/bugzilla/editvalues.cgi",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "en-US,en;q=0.9",
        'Cookie': auth_cookie,
        'Cache-Control': "no-cache",
        'Content-type': "application/x-www-form-urlencoded",
    }

    response = requests.request("POST", url, data=data, headers=headers)
    return response


def getLoginToken():
    global auth_cookie

    url = f'http://{BASE_URL}/bugzilla/'
    querystring = {}

    response = sendReq(url, querystring)

    auth_cookie = f'{response.headers["Set-Cookie"]}; '
    print('auth_cookie', auth_cookie)

    response = sendReq(url, querystring)

    bugzilla_login_token = getToken(
        response.text, '//*[@id="mini_login_bottom"]/input[4]/@value')
    return bugzilla_login_token


def login():
    global auth_cookie

    bugzilla_login_token = getLoginToken()

    url = f'http://{BASE_URL}/bugzilla/index.cgi'
    querystring = {
        "Bugzilla_login": USER,
        "Bugzilla_password": PASSWORD,
        "Bugzilla_login_token": bugzilla_login_token,
        "GoAheadAndLogIn": "Log in"
    }

    response = sendLoginReq(url, querystring)

    # print(response.headers)
    print('Login Cookie:', response.headers["Set-Cookie"])
    auth_cookie += f'Bugzilla_login=1; {response.headers["Set-Cookie"]}; '
    print('auth_cookie', auth_cookie)

    return


def getToken(text, xp):

    tree = html.fromstring(text)
    token = tree.xpath(xp)
    # token = tree.xpath('//*[@id="type"]')

    print(token)

    return token[0]


def getFieldToken():

    url = f"http://{BASE_URL}/bugzilla/editfields.cgi"
    querystring = {"action": "add"}

    response = sendReq(url, querystring)

    token = getToken(response.text, '//*[@id="add_field"]/p/input[2]/@value')
    return token


def getOptionToken(fieldname):

    print('creating option token')

    url = f"http://{BASE_URL}/bugzilla/editvalues.cgi"
    querystring = {"action": "add", "field": fieldname}

    response = sendReq(url, querystring)

    # print(response.text)

    token = getToken(
        response.text, '//*[@id="bugzilla-body"]/form/input[4]/@value')
    return token


def loadFields():

    fields = []
    with open('fields.json') as json_file:
        data = json.load(json_file)
        fields = data['fields']

    for field in fields:
        field['name'] = 'cf_' + field['name']

    return fields


def createSimpleField(fieldBean):

    print(' - Creating simple field : %s' % fieldBean['name'])
    token = getFieldToken()
    field = Field(fieldBean['name'], fieldBean['type'], token)

    url = f"http://{BASE_URL}/bugzilla/editfields.cgi"
    querystring = {'name': field.name, 'type': field.type, 'token': field.token, 'enter_bug': field.enter_bug, 'desc': field.desc, 'obsolete': field.obsolete,
                   'sortkey': field.sortkey, 'long_desc': field.long_desc, 'visibility_field_id': field.visibility_field_id, 'action': field.action}

    response = sendReq(url, querystring)

    # print(response.text)

    return response


def createDropdownOption(fieldBean, option):

    print(' - Creating option : "%s" for %s' % (option, fieldBean['name']))
    token = getOptionToken(fieldBean['name'])
    response = sendOptionCreateReq(fieldBean['name'], option, token)

    # print(response.text)

    return response


def createDropdownField(fieldBean):

    print(' - Creating dropdown field : %s' % fieldBean['name'])
    response = createSimpleField(fieldBean)

    # print(response.text)

    for option in fieldBean['options']:
        createDropdownOption(fieldBean, option)

    return response


def createFields(fieldBeans):

    n = 0
    for fieldBean in fieldBeans:

        print('Loading field : %s; Type %s' %
              (fieldBean['name'], fieldBean['type']))
        if fieldBean['type'] == '2':
            createDropdownField(fieldBean)
        else:
            createSimpleField(fieldBean)
        n += 1
        print('%s / %s' % (n, len(fieldBeans)))
    return 'done'


def main():

    login()

    fields = loadFields()
    print('Loaded %s fields' % len(fields))

    # print(fields)

    createFields(fields)
    # status = submitField(field)
    # print('Field submitted : %s' % status)


class Field:
    def __init__(self, name, type, token, enter_bug=1, desc=None, obsolete=0, sortkey=None, long_desc=None, visibility_field_id=None, action='new'):
        self.name = name
        self.token = token
        self.type = type

        if enter_bug:
            self.enter_bug = enter_bug
        else:
            self.enter_bug = ''

        if desc:
            self.desc = desc
        else:
            self.desc = name[3:]

        if obsolete:
            self.obsolete = obsolete
        else:
            self.obsolete = ''

        if sortkey:
            self.sortkey = sortkey
        else:
            self.sortkey = ''

        if long_desc:
            self.long_desc = long_desc
        else:
            self.long_desc = name

        if visibility_field_id:
            self.visibility_field_id = visibility_field_id
        else:
            self.visibility_field_id = ''

        if action:
            self.action = action
        else:
            self.action = ''

    def __str__(self):
        return '%s %s %s %s %s %s %s %s %s %s' % (self.name, self.type, self.token, self.enter_bug, self.desc, self.obsolete, self.sortkey, self.long_desc, self.visibility_field_id, self.action)


if __name__ == '__main__':
    main()
