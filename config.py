# NSO CORE
NSO_USER = "admin"
NSO_PASSWD = "admin"
NSO_ROOT = "http://localhost:8080"
API_ROOT = NSO_ROOT + '/api'

# URLs
CONF_URL = API_ROOT + '/config'
OPER_URL = API_ROOT + '/operational'
checkSync_url = API_ROOT + '/running/devices/_operations/check-sync'
devices_url = OPER_URL + "/devices"
neds_url = OPER_URL + "/devices"
services_url = OPER_URL + "/ncs-state/internal/callpoints/servicepoint"
servicesDeployed_url = API_ROOT + '/running/services/_operations/check-sync'
alarms_list_url = OPER_URL + '/alarms/alarm-list'
customers_url = CONF_URL + '/customers'


# Customer Service
# Includes a binding to a service: <service-id>/l3vpn:l3vpn[l3vpn:name='abc']</service-id>
customer_service_url = API_ROOT + '/operational/customers/customer'

# XML NS
device_xmlns = ned_xmlns = customer_xmlns = "http://tail-f.com/ns/ncs"
service_xmlns = "http://tail-f.com/yang/ncs-monitoring"
alarms_xmlns = "http://tail-f.com/ns/ncs-alarms"
customer_service_xmlns = "http://tail-f.com/ns/rest"

# XPATH
device_xpath = ".//ns:device/ns:name"
ned_xpath = ".//ns:device-module/ns:name"
service_xpath = "./ns:servicepoint/ns:id"
checkSync_xpath = ".//ns:result"
serviceDeployed_xpath = ".//ns:service-id"
alarms_device_xpath = ".//ns:device"
alarms_type_xpath = ".//ns:type"
customer_xpath = ".//ns:id"
customer_service_xpath = './/ns:customer[descendant::ns:id[text()="%s"]]/ns:customer-service'
