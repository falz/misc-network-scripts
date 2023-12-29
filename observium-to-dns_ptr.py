#! /usr/bin/env python3
#
# falz myorg 2018-12
# observium API interfaces to IPv4/IPv6 PTR records in BIND format
# 
# requirements:
#	pip install argparse ipaddress requests system
#
# usage:
#	enable observium API in its config.inc.php: $config['api']['enable'] = TRUE;
#	set proper Obesrvium credentials in this script
#
# changelog:
#	2018-12-20	initial release
#	2020-03-25	ported to python3
#	2020-06-20	fixed http 500 issue by tweaking php.ini memory_limit, made note. 
#			ignore deleted ports to very slightly speed things up
#	2021-07-15	function to cleanup interface names, including lo0.0
#
#	2021-08-17	figure out zone name, powerdns cannot use @ symbol
#
#	2023-10-13	add additional check that IP addressees are within network they're supposed to be (observium API issue)
#
# known issues:
#	If you get HTTP 500 error, check httpd error logs for php.ini's memory_limit. We increased ours from 512m to 1024m.
#
# todo:
#
#	put more stuff in functions
#
#	read from observium's config file to help filter bad_if types
#
#	attempt to group / sort the output by zone of some size (/24 for v4, /56 for v6?) would help shorten the lines.
#		technically would make no difference other than human readability
#
#	switch auth to interactive, defaulting to their cli username with optional flag to specify other user. ask for pass
#	

import argparse
import datetime
import ipaddress
import json
import re
import requests
import sys

###########################
# config variables
observium_user="observium"
observium_pass ="<somepass>"
observium_url_base ="https://observium.myorg.net/api/v0/"
observium_url_ports = observium_url_base + "ports/?deleted=0"
observium_url_addresses = observium_url_base + "address/"
observium_url_devices = observium_url_base + "devices/"
add_afi_to_ptr = True
request_timeout=15
split_hostname = ".myorg.net"

# scrub interface names, regexp match on key. ALL of these will be performed on an interface name, in the order of this dict!
interface_cleanup_dict = {
	# remove loopback (we don't want it in PTR - router)
	'^lo0.\d$'	: 	'',
	'^lo0$'		: 	'',
	# remove loopback (we don't want it in PTR - linux)
	'^lo$'	: 	'',
	# remove .0 from end of any interface (native)
	'\.0$'		: 	'',
	# replace . with -
	'\.'		: 	'-',
	# replace / with -
	'\/'		: 	'-'
}


now = datetime.datetime.now()
year = str(now.year)
month = str(f"{now:%m}")
day = str(f"{now:%d}")
ver = str("01")
serial = year + month + day + ver

ttl = "14400"
soa = "	14400	IN	SOA	ns0.myorg.net. hostmaster.myorg.net. " + serial + " 7200 1800 1209600 14400"
nameservers = [ "ns1.myorg.net.", "ns2.myorg.net." ]

###########################
# arguments and help
parser = argparse.ArgumentParser()
parser.add_argument('-n', '--network', required=True, help='Network to query, such as 10.20.0.0/14, 2001:5f0::/48, etc')
args = vars(parser.parse_args())
argnetwork = args['network']

###########################
# quick and dirty validation

#is network a valid network? also get ip version
try:
	validnetwork = ipaddress.ip_network(argnetwork)
	#this should be 6 or 4
	ipversion = str(validnetwork.version)
	observium_url_addresses= observium_url_base + "address/" + "?address=" + argnetwork
except ValueError:
	print(argnetwork + " is not a valid network")
	sys.exit(1)



###########################
# fetch addresses from API
try:
	observium_addresses = requests.get(observium_url_addresses, auth=(observium_user, observium_pass), timeout=request_timeout)
except requests.exceptions.RequestException as errormessage:
	print(errormessage)
	sys.exit(1)

#check http status code as 200
if observium_addresses.status_code != 200:
	#print(observium_addresses)
	print("ERROR: Expected HTTP status code 200 OK, but got " + str(observium_addresses.status_code) + " Check url, auth and whatnot.")
	sys.exit(1)
# Load JSON for each request
json_addresses = observium_addresses.json()


###########################
# fetch ports from API
try:
	#print(observium_url_ports)
	observium_devices = requests.get(observium_url_ports, auth=(observium_user, observium_pass), timeout=request_timeout)
except requests.exceptions.RequestException as errormessage:
	print(errormessage)
	sys.exit(1)
#check http status code as 200
if observium_devices.status_code != 200:
	print("ERROR: Expected HTTP status code 200 OK, but got " + str(observium_devices.status_code) + " Check url, auth and whatnot.")
	sys.exit(1)
# Load JSON for each request
json_ports = observium_devices.json()


###########################
# fetch devices from API
try:
	observium_devices = requests.get(observium_url_devices, auth=(observium_user, observium_pass), timeout=request_timeout)
except requests.exceptions.RequestException as errormessage:
	print(errormessage)
	sys.exit(1)
#check http status code as 200
if observium_devices.status_code != 200:
	print("ERROR: Expected HTTP status code 200 OK, but got " + str(observium_devices.status_code) + " Check url, auth and whatnot.")
	sys.exit(1)
# Load JSON for each request
json_devices = observium_devices.json()

dns_ptr_dictionary = {}

# rename some interfaces based on our standards
def clean_int(interface_cleanup_dict, interface):
	for match, replace in interface_cleanup_dict.items():
		interface = re.sub(match, replace, interface)
	return(interface)


# figure out the name of the zone, depends on ipversion and prefix length
def reverse_zone_name(prefix):
	if prefix.version == 4:
		# THIS ONLY WORKS FOR /24's!
		zonename = prefix.network_address.reverse_pointer[2:]

	elif prefix.version == 6:
		trimlength = int(2 * (128 - prefix.prefixlen) / 4)
		zonename = prefix.network_address.reverse_pointer[trimlength:]

	return(str(zonename))



# do real stuff
# create ipnetwork object for later comparisons
net = ipaddress.ip_network(argnetwork)
#print(net, type(net))

print("$TTL " + ttl)
zonename = reverse_zone_name(validnetwork)
print(zonename + "." + soa)
for ns in nameservers:
	print(zonename + ".\t" + ttl + "\tIN\tNS\t" + ns)

for address in json_addresses['addresses']:
	#things from json_addresses
	device_id = 		address['device_id']
	ip_address = 		address['ipv'+ipversion+'_address']
	ip_address_ptr = 	ipaddress.ip_address(ip_address).reverse_pointer + "."
	ip_network = 		address['ipv'+ipversion+'_network']
	ifIndex = 		address['ifIndex']
	port_id = 		address['port_id']

	# some garbage comes out of api - null ifIndex, 0's in some fields that shouldn't have them. skip these
	if ifIndex is not None and int(port_id) > 0 and int(device_id) > 0 and ipaddress.ip_address(ip_address) in net:
		# things from json_devices, requires a little validation
		hostname = 		json_devices['devices'][device_id]['hostname']
		short_hostname = 	hostname.split(split_hostname)
		device_disabled = 	json_devices['devices'][device_id]['disabled']
		device_ignore = 	json_devices['devices'][device_id]['ignore']
		device_os = 		json_devices['devices'][device_id]['os']

		#things from json_ports
		port_label_short =	json_ports['ports'][port_id]['port_label_short'].lower()

		# clean interface name
		port_label_short =	clean_int(interface_cleanup_dict, port_label_short)

		# populate dictionary. not currently used, probably could be if we wanted to move print statement out of this loop
		dns_ptr_dictionary[ip_address] = 			{}
		dns_ptr_dictionary[ip_address]['hostname'] =		hostname
		dns_ptr_dictionary[ip_address]['port_id'] =		port_id
		dns_ptr_dictionary[ip_address]['port_label_short'] =	port_label_short
		dns_ptr_dictionary[ip_address]['ipversion'] =		ipversion
		dns_ptr_dictionary[ip_address]['device_id'] =		device_id

		# don't add dash for interface if no interface specified (ie lo0)
		sep = "-"
		if not port_label_short:
			sep = ""

		if add_afi_to_ptr == True:
			afi = ".ip" + str(ipversion)
		else:
			afi = ""

		#print back PTR records (not soa record) to include in a zone file
		print(ip_address_ptr + "\tIN\tPTR\t" + short_hostname[0] + sep +  port_label_short + afi + split_hostname + ".")

