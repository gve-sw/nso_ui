import requests
import settings
import sqlite3
import hashlib
from requests.auth import HTTPBasicAuth
from lxml import etree
from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from config import *

# Registers a Flask application with the name of the module
#
app = Flask(__name__)

# Configuration of the Flask app: secret key for the client-side sessions and debugging mode
#
app.config.update(
    DEBUG=settings.DEBUG,
    SECRET_KEY=settings.SK
)


# Initializes the Login Manager with a "login" function
#
lm = LoginManager()
lm.init_app(app)
lm.login_view = "login"


# Simple class for user handling during the login procedure
#
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


# Returns list and number of devices, services or NEDs. Utilizes REST API to retrieve data from NSO. Defaults to
# HTTP GET, can be set to HTTP POST from the calling function for various reasons (e. g. NSO operations require POST)
#
def get_items(url, xpath, xmlns, method="GET", frr=False):

    # Constructing HTTP header and sending a request to NSO
    payload = ''
    auth = HTTPBasicAuth(NSO_USER, NSO_PASSWD)
    response = requests.request(method, url, data=payload, auth=auth)

    # Constructing XML object from the response
    root = etree.XML(response.text)

    if settings.VERBOSE:
        print response.text

    # Filtering the XML object with specified XPath and XML namespace
    items = root.xpath(xpath, namespaces={'ns': xmlns})

    # Flag to return items without further processing
    if frr:
        return items

    # Extracting text and counting the number of items for the cards in the frontend
    items = [item.text for item in items]
    items_num = len(items)
    return items, items_num


# Returns a status of the connection to NSO
#
@app.route("/nso_status")
@login_required
def nso_status():
    auth = HTTPBasicAuth(NSO_USER, NSO_PASSWD)
    response = requests.request('GET', API_ROOT, auth=auth)
    return "NSO responded: %s %s" % (str(response.status_code), str(response.reason))


# Index function (the main page). GET is normally used, POST is needed to switch the customers
#
@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@app.route("/index.html", methods=['GET', 'POST'])
@login_required
def index():

    # POST means there was a call to switch a customer. Setting current_customer to the value specified
    if request.method == "POST":
        current_customer = request.form["current_customer"]
    else:
        current_customer = ''

    # Determining NSO status to notify frontend about any problems
    status = nso_status()

    # Dictionary for a chart on the main page
    sync = {'error': 0,
            'in-sync': 0,
            'unsupported': 0,
            'out-of-sync': 0,
            }

    # Fetching all kinds of data from NSO utilizing XPath and XML NS from the config module. Variable _ used to skip
    # unneeded data. get_items is used for any item below
    devices, device_num = get_items(devices_url, device_xpath, device_xmlns)
    neds, ned_num = get_items(neds_url, ned_xpath, ned_xmlns)

    # Stripping the tailf-ned- part that is present in some NEDs
    neds = [ned.strip('tailf-ned-') for ned in neds if 'tailf-ned-' in ned]

    services, service_num = get_items(services_url, service_xpath, service_xmlns)
    serviceDeployed, _ = get_items(servicesDeployed_url, serviceDeployed_xpath, device_xmlns, method="POST")
    serviceDeployed_num = len(serviceDeployed)

    alarms_devices, _ = get_items(alarms_list_url, alarms_device_xpath, alarms_xmlns)
    alarms_types, alarm_num = get_items(alarms_list_url, alarms_type_xpath, alarms_xmlns)

    # Constructing text to depict in alarm section in the frontend
    alarms = ["%s: %s" % (device, alarm_type) for device, alarm_type in zip(alarms_devices, alarms_types)]

    # When there's no customer service (i. e. no customer selected), there will be no "Services for X" in the frontend
    customers, _ = get_items(customers_url, customer_xpath, customer_xmlns)
    customer_service, customer_service_num = get_items(customer_service_url, customer_service_xpath % current_customer,
                                                       customer_xmlns)

    sync_st, _ = get_items(checkSync_url, checkSync_xpath, device_xmlns, method="POST")

    for item in sync_st:
        sync[item] += 1

    if settings.VERBOSE:
        print sync

    # **locals() for all the local variables to populate HTML files accordingly. NSO_ROOT is imported from the config,
    # hence is not local, so we need to pass it manually
    return render_template('index.html', NSO_ROOT=NSO_ROOT, **locals())


# Login function. GET to depict the login page, POST to perform login
#
@app.route("/login", methods=['GET', 'POST'])
@app.route("/login.html", methods=['GET', 'POST'])
def login():

    # User requests login (i. e. login button pressed)
    if request.method == 'POST':

        # Taking data from the form
        username = request.form['username']
        password = request.form['password']

        # Validating the username
        auth_status = validate(username, password)

        # If username is correct, performing the login (creating session)
        if auth_status:
            user = User(username)
            login_user(user)

            # Determining the page that was originally requested (e. g. the user was trying to get /, but it requires
            # login. User was redirected to /login, and now after he's authenticated, the function should redirect
            # the user back to the requested page. If there's no such page (user requested /login to begin with),
            # just redirect the user to /
            next_page = request.args.get("next")
            if next_page is not None:
                return redirect(next_page)
            else:
                return redirect('/')

        # If username is not correct, depict the error and stay at the current page
        else:
            return render_template('login.html', login_error=True)

    # Just return the page in case of HTTP GET
    return render_template('login.html')


# Logout will delete the user session automatically using built-in function
#
@app.route("/logout")
def logout():
    logout_user()
    return redirect("login")


# Registration form. Uses POST to register a new user, GET to depict the registration page
#
@app.route("/register", methods=['GET', 'POST'])
@app.route("/register.html", methods=['GET', 'POST'])
def register():

    # User is trying to register
    if request.method == 'POST':
        username = request.form['Username']
        password = request.form['Password']
        _password = request.form['RepeatPassword']
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']

        # Various sanity checks. Weak ones ;)
        if not username:
            return render_template('register.html', username_error=True)
        if len(password) < settings.PASS_LEN:
            return render_template('register.html', password_len_error=True, PASS_LEN=settings.PASS_LEN)
        if not password == _password:
            return render_template('register.html', password_error=True)

        # Connecting to the SQLite database and checking if the username exists
        con = sqlite3.connect('static/db/user.db')
        with con:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM users where username='%s'" % username)
            row = cursor.fetchone()
            if row:
                return render_template('register.html', user_exists=True)

            # Password is stored as a MD5 hash (not salted!)
            hashed_password = hashlib.md5(password.encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES ('%s', '%s', '%s', '%s', '%s')" %
                           (username, hashed_password, first_name, last_name, email))
            return render_template('register.html', success=True)

    # Just return the page in case of HTTP GET
    return render_template('register.html')


# NOT IMPLEMENTED!
#
@app.route("/devices")
@app.route("/devices.html")
@login_required
def devices():
    return render_template('devices.html')


# Registers the user loader for the Login Manager. Uses the User class
#
@lm.user_loader
def load_user(userid):
    return User(userid)


# Validates the username and password against an SQLite DB
#
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


# Checks the MD5 of the password (used by the validate function)
#
def check_password(hashed_password, user_password):
    return hashed_password == hashlib.md5(user_password.encode()).hexdigest()


# Runs the Flask dev server
#
if __name__ == "__main__":
    app.run()
