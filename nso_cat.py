import requests
import settings
import sqlite3
import hashlib
from requests.auth import HTTPBasicAuth
from lxml import etree
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from config import *

app = Flask(__name__)

app.config.update(
    DEBUG=settings.DEBUG,
    SECRET_KEY=settings.SK
)


# Initializes
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"


class User(UserMixin):

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return self.id

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return self.is_authenticated()


# Returns list and number of devices, services or NEDs
#
def get_items(url, xpath, xmlns, method="GET", frr=False):
    payload = ''
    auth = HTTPBasicAuth(NSO_USER, NSO_PASSWD)

    response = requests.request(method, url, data=payload, auth=auth)
    root = etree.XML(response.text)
    if settings.VERBOSE:
        print response.text
    items = root.xpath(xpath, namespaces={'ns': xmlns})
    if frr:
        return items
    items = [item.text for item in items]
    items_num = len(items)
    return items, items_num


@app.route("/nso_status")
@login_required
def nso_status():
    auth = HTTPBasicAuth(NSO_USER, NSO_PASSWD)
    response = requests.request('GET', API_ROOT, auth=auth)
    return "NSO responded: %s %s" % (str(response.status_code), str(response.reason))


@app.route("/")
@app.route("/index")
@app.route("/index.html")
@login_required
def index():

    status = nso_status()

    sync = {'error': 0,
            'in-sync': 0,
            'unsupported': 0,
            'out-of-sync': 0,
            }

    devices, device_num = get_items(devices_url, device_xpath, device_xmlns)
    neds, ned_num = get_items(neds_url, ned_xpath, ned_xmlns)
    neds = [ned.strip('tailf-ned-') for ned in neds if 'tailf-ned-' in ned]
    services, service_num = get_items(services_url, service_xpath, service_xmlns)
    serviceDeployed, _ = get_items(servicesDeployed_url, serviceDeployed_xpath, device_xmlns, method="POST")
    serviceDeployed_num = len(serviceDeployed)

    alarms_devices, _ = get_items(alarms_list_url, alarms_device_xpath, alarms_xmlns)
    alarms_types, alarm_num = get_items(alarms_list_url, alarms_type_xpath, alarms_xmlns)
    alarms = ["%s: %s" % (device, alarm_type) for device, alarm_type in zip(alarms_devices, alarms_types)]

    sync_st, _ = get_items(checkSync_url, checkSync_xpath, device_xmlns, method="POST")

    for item in sync_st:
        sync[item] += 1

    if settings.VERBOSE:
        print sync

    return render_template('index.html', **locals())


@app.route("/login", methods=['GET', 'POST'])
@app.route("/login.html", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        auth_status = validate(username, password)
        if auth_status:
            user = User(username)
            login_user(user)
            next_page = request.args.get("next")
            if next_page is not None:
                return redirect(next_page)
            else:
                return redirect('/')
        else:
            return render_template('login.html', login_error=True)
    return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect("login")


@app.route("/register", methods=['GET', 'POST'])
@app.route("/register.html", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['Password']
        _password = request.form['RepeatPassword']
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']

        if not username:
            return render_template('register.html', username_error=True)
        if len(password) < settings.PASS_LEN:
            return render_template('register.html', password_len_error=True, PASS_LEN=settings.PASS_LEN)
        if not password == _password:
            return render_template('register.html', password_error=True)

        con = sqlite3.connect('static/db/user.db')
        with con:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM users where username='%s'" % username)
            row = cursor.fetchone()
            if row:
                return render_template('register.html', user_exists=True)

            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES ('%s', '%s', '%s', '%s', '%s')" %
                           (username, hashed_password, first_name, last_name, email))
            return render_template('register.html', success=True)

    return render_template('register.html')


@app.route("/devices")
@app.route("/devices.html")
@login_required
def devices():
    return render_template('devices.html')


@lm.user_loader
def load_user(userid):
    return User(userid)


def validate(username, password):
    con = sqlite3.connect('static/db/user.db')
    auth_status = False
    with con:
        cursor = con.cursor()
        cursor.execute("SELECT * FROM users where username='%s'" % username)
        row = cursor.fetchone()
        if not row:
            return auth_status
        if username == row[0]:
            auth_status = check_password(row[1], password)

    return auth_status


def check_password(hashed_password, user_password):
    return hashed_password == hashlib.md5(user_password.encode()).hexdigest()


if __name__ == "__main__":
    app.run()
