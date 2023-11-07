# Goodwe logging proxy
Intercept calls from inverter to goodwe api and decode the payload.

The result is published on MQTT, with automatic discovery.

The decoder is only implemented for single phase inverters (But if someone has the data for a 3 phase inverter this can be added)

Multiple inverters are supported without configuration.

### Installation

This integration requires some magic to intercept the calls from the inverter and read the content. The request is passed to the 'real' goodwe server to be visible in SEMS.

This has the additional benefit that the calls to goodwe can now be https, as the push server from goodwe accepts this.

#### Docker-compose
The code is run as a docker container, the compose file from the repo will pull the latest version from github and build it upon install.

#### Vlan
The integration requires the inverter to be on a lan segment with a separate DNS server.

I set it up so that my IoT-wifi is routed over a vlan, and my home server is the gateway for that lan.

It is also possible to use iptables to hijack all outgoing traffic from the inverter and process it locally.

#### Dnsmasq
The folder dnsmasq contains a config file to be copied to /etc/dnsmasq.d/

The config sets up, for eth0.2, a dhcp server and a DNS server. The dns server forwards all requests to the LAN interface of my server, or `1.1.1.1` (CloudFlare DNS)

The spoof.hosts file contains an entry to redirect traffic to goodwe to the local server.

#### MQTT
A mqtt broker is required to pass the messages from the project to Home Assistant

The url must be set in the MQTT_HOST environment variable.

#### Home Assistant
When mqtt is properly configured in HA, the inverter will be automatically added as soon as data is receieved.
