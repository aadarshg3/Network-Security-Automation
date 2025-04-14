from ncclient import manager
import xml.dom.minidom

# Device login details
device = {
    "host": "192.0.2.1",
    "port": 830,
    "username": "admin",
    "password": "admin123",
    "hostkey_verify": False
}

# NETCONF filter to get specific interface config
filter = """
<filter>
  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
    <interface>
      <name>GigabitEthernet1</name>
    </interface>
  </interfaces>
</filter>
"""

# Connect and retrieve config
with manager.connect(**device) as m:
    config = m.get_config("running", filter=filter).data_xml
    pretty_config = xml.dom.minidom.parseString(config).toprettyxml()
    print(pretty_config)


# =============OUTPUT===========
'''
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name>GigabitEthernet1</name>
    <description>Uplink to ISP</description>
    <enabled>true</enabled>
  </interface>
</interfaces>


'''