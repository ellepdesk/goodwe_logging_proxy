# Goodwe logging proxy
Intercept calls from inverter to goodwe api and decode the payload

### Installation

This integration requires some magic to intercept the calls from the inverter and read the content. The request is passed to the 'real' goodwe server to be visible in SEMS.

This has the additional benefit that the calls to goodwe can now be https, as the push server from goodwe accepts this.

#### Vlan
The integration requires the inverter to be on a lan segment with a separate DNS server.

I set it up so that my IoT-wifi is routed over a vlan, and my home server is the gateway for that lan.

#### Dnsmasq
The folder dnsmasq contains a config file to be copied to /etc/dnsmasq.d/

The config sets up, for eth0.2, a dhcp server and a DNS server. The dns server forwards all requests to the LAN interface of my server, or `1.1.1.1` (CloudFlare DNS)

The spoof.hosts file contains an entry to redirect traffic to goodwe to the local server.

#### Apache2
The apache 2 folder contains a site configuration to allow requests to `www.goodwe-power.com` and reverse-proxies them to `localhost:8180`

This is only allowed for the vlan ip-range

#### Home Assistant
Copy the folder `goodweproxy` to `<config_dir>/custom_components/`.

For example: sudo cp -r goodweproxy/ /etc/docker/homeassistant/custom_components/

Envirment variable "GOODWE_PROXY_PORT" allows to adjust the proxy port. Defaults to 80
