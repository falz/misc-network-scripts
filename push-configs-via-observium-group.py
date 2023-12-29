#!/usr/bin/env python3
# falz 2018-12
#
# Push config snippets to devices defined in an Observium device group. This assumes you did something smart
# with the group, like have it all be a single OS.
#
# dependencies:
#	pip install argparse getpass2 napalm requests
#
# changelog:
# 
#	2018-11-29	first version. can log in to stuff, accepts cli args and talks to observium api. not much else.
#	2019-01-04	add pasteable wnrcs check in/out commands at end of run
#	2019-01-07	add inline password prompt as well as some friendlier lingo
#			remove hard coding of junos, tested on junos and ios + ios-xe
#	2019-01-15	speed tweaks for IOS. this arg is passed directly to netmiko
#	2020-03-20	convert to python3
#
# todo:
#	additional flag to further refine the group down using regexp or something
#	additional flag for debug info
#	fetch a url from http instead of having to be a local file
# use functions, lulz

###########################
# modules 
import argparse
import getpass
import json
import requests
import sys
from napalm import get_network_driver
#these are here to suppress crypto errors from paramiko <2.5.0 related to Juniper devices. Remove once Paramiko 2.5.0+ is available.
#       https://github.com/paramiko/paramiko/issues/1369
import warnings
warnings.filterwarnings(action='ignore',module='.*paramiko.*')

###########################
# config variables
password="<somepass>"
observium_url_prefix="https://observium.myorg.net/api/v0/devices/?group="
observium_url_suffix="&ignore=0&status=1&disabled=0"
request_timeout=5
device_timeout=300
split_hostname = ".myorg.net"
separator = "############################################################"

###########################
# functions

	

###########################
# cli arguments and help
parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', required=True, help='Config file. Full path to a text file or a plain text http url (hopefully)?')
parser.add_argument('-g', '--group', required=True, help='Group ID. Observium group ID under Devices->Group.')
parser.add_argument('-u', '--username', required=False, help='Username. Used for both Observium API call and device login. Defaults to shell username.')

args = vars(parser.parse_args()) 
configurl = args['config']
arggroup = args['group']
username = args['username']
if username  is None:
	username = getpass.getuser()

print("")
print("Password for username '" + username + "' required to connect to Observium API and to log in to devices.")
print("")
password = getpass.getpass()


###########################
# fetch device list from Observium API
try:
	device_url = observium_url_prefix + arggroup + observium_url_suffix
	#print(device_url)
	#print(username)
	#print(password)

	observium_devices = requests.get(device_url, auth=(username, password), timeout=request_timeout)
except requests.exceptions.RequestException as errormessage:
	print(errormessage)
	sys.exit(1)
#check http status code as 200
if observium_devices.status_code != 200:
	print("")
	print("Problem talking to Observium API, received HTTP status code " + str(observium_devices.status_code))
	print("Recheck password and double check if URL works: " + device_url)
	print("")
	sys.exit(1)

# Load JSON for each request
json_devices = observium_devices.json()
#print(json_devices)
devicecount=str(json_devices['count'])

print("Merging the contents of '" + configurl + "' into group " + arggroup + ", which contains " + devicecount + " devices..")
print("")

# create WNRCS commands to print at end
co_str = "co -l "
ci_str = "ci -u -m'" + wnrcs_message + "' "

devices_dictionary = {}
for device in json_devices['devices']:
	os		=	json_devices['devices'][device]['os']
	hostname	=	json_devices['devices'][device]['hostname']
	hostname_split	=	hostname.split(split_hostname)
	short_hostname	=	hostname_split[0]
	optional_args	=	{'fast_cli': False}

	# per ktbyers, this netmiko arg can speed things up. it fails on ios-xe however
	if os == "ios":
		optional_args={'fast_cli': True}

	# do some stuff to make observium OS types jive with what Napalm desires. See https://napalm.readthedocs.io/en/latest/support/
	if os == "iosxe":
		os = "ios"

	my_driver = get_network_driver(os)
	my_router = my_driver(hostname=short_hostname,username=username,password=password,timeout=device_timeout,optional_args=optional_args)
	my_router.open()

	if my_router.is_alive()['is_alive']:
		print("")
		print("Working on " + short_hostname + "..")
		#print(my_router.get_facts())

		my_router.load_merge_candidate(filename=configurl)
		diffs = my_router.compare_config()
		if diffs == "":
			print("No configuration changes required")
		else:
			print(diffs)
			yesno = input('\nApply changes to ' + short_hostname + '? [y/N] ').lower()
			#print(yesno)
			if (yesno == 'y') or (yesno == 'yes'):
				# do stuff
				print("Applying changes..")
				my_router.commit_config()


			else:
				print("Discarding changes..")
				my_router.discard_config()


	# Create a dictionary working on this stuff:
	devices_dictionary[json_devices['devices'][device]['hostname']] = json_devices['devices'][device]['os']

print("Complete!")
print("")
