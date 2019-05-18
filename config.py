# AUTH
NSO_USER = "admin"
NSO_PASSWD = "admin"


# URLs
API_ROOT = "http://localhost:8080/api/"
CONF_URL = "http://localhost:8080/api/config/"
OPER_URL = "http://localhost:8080/api/operational/"
checkSync_url = "http://localhost:8080/api/running/devices/_operations/check-sync"
devices_url = OPER_URL + "devices"
neds_url = OPER_URL + "devices"
services_url = OPER_URL + "ncs-state/internal/callpoints/servicepoint"
servicesDeployed_url = "http://localhost:8080/api/running/services/_operations/check-sync"
alarms_list_url = "http://localhost:8080/api/operational/alarms/alarm-list"


# Customer Service
# Includes a binding to a service: <service-id>/l3vpn:l3vpn[l3vpn:name='abc']</service-id>
customer_service_url = "http://localhost:8080/api/running/services/_operations/check-sync"

# XML NS
device_xmlns = ned_xmlns = "http://tail-f.com/ns/ncs"
service_xmlns = "http://tail-f.com/yang/ncs-monitoring"
alarms_xmlns = "http://tail-f.com/ns/ncs-alarms"

# XPATH
device_xpath = ".//ns:device/ns:name"
ned_xpath = ".//ns:device-module/ns:name"
service_xpath = "./ns:servicepoint/ns:id"
checkSync_xpath = ".//ns:result"
serviceDeployed_xpath = ".//ns:service-id"
alarms_device_xpath = ".//ns:device"
alarms_type_xpath = ".//ns:type"
