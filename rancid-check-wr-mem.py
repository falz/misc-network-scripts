#!/usr/bin/env python3
# script to check if 'wr mem' was done on routers in a rancid directory
# falz 2023-12
#
# todo
#   don't use rancid? coudl do live with
#      1.3.6.1.4.1.9.9.43.1.1.1 == ccmHistoryRunningLastChanged
#      1.3.6.1.4.1.9.9.43.1.1.2 == ccmHistoryRunningLastSaved
#      .1.3.6.1.4.1.9.9.43.1.1.1.0 = Timeticks: (1754069677) 203 days, 0:24:56.77
#      .1.3.6.1.4.1.9.9.43.1.1.2.0 = Timeticks: (2194003003) 253 days, 22:27:10.03
#
#   we only compare when both lines exist in config, we're not checking devices with only one

import csv
import os
from datetime import datetime


rancid_db = "/var/rancid/myorg/router.db"
rancid_dirs = [ '/var/rancid/myorg/configs/' ]
rancid_delimiter = ';'
cisco_models = [ 'ios', 'cisco']
changed_string = 'Last configuration change at'
saved_string = 'NVRAM config last updated at'
domain = ".myorg.net"

#! Last configuration change at 10:32:15 CST Wed Nov 8 2023 by falz
#! NVRAM config last updated at 11:09:26 CDT Wed Apr 19 2023

def check_configfile(myfile, hostname):
    issue = False
    mychanged = ""
    mysaved = ""
    for line in myfile.readlines():
        if changed_string in line:
            mychanged = line.strip()
        if saved_string in line:
            mysaved = line.strip()

    # we have both lines in file
    if mychanged and mysaved:
        changed_who = "UNKNOWN"
        saved_who = "UNKNOWN"

        # repeating code below, could make a function, but explicit for now

        #! Last configuration change at 10:32:15 CST Wed Nov 8 2023 by falz
        #! Last configuration change at 07:16:10 CDT Wed Nov 3 2021 by mdobrynina
        #! Last configuration change at 06:18:18 CDT Fri Jun 24 2022
        changed_list = mychanged.split(changed_string)
        if "by " in changed_list[1]:
            changed_by_list = changed_list[1].split("by ")
            changed_who = changed_by_list[1].strip()
            changed_date_str = changed_by_list[0].strip()            
        else: 
            changed_date_str = changed_list[1].strip()

        #! NVRAM config last updated at 11:09:26 CDT Wed Apr 19 2023
        #! NVRAM config last updated at 07:19:48 CDT Wed Nov 3 2021 by mdobrynina
        #! NVRAM config last updated at 08:50:13 CDT Tue Jun 28 2022 by ehammons
        saved_list = mysaved.split(saved_string)
        if "by " in saved_list[1]:
            saved_by_list = saved_list[1].split("by ")
            saved_who = saved_by_list[1].strip()
            saved_date_str = saved_by_list[0].strip()            
        else: 
            saved_date_str = saved_list[1].strip()


        changed_date_obj = date_convert(changed_date_str)
        saved_date_obj = date_convert(saved_date_str)

        if saved_date_obj < changed_date_obj:
            timediff = changed_date_obj - saved_date_obj
            timesince = now - changed_date_obj

            hostname_split = hostname.split(domain)
            print(hostname_split[0])
            print("\tSaved    ", saved_date_obj, "\t", saved_who, sep='')
            print("\tChanged: ", changed_date_obj, "\t", changed_who, " (", timediff, " after Saved)", sep='')
            print("\tWhen:    ", timesince, " ago", sep='') 
            print("\tBlame:   ", changed_who,  sep='')
            print("")
            issue = True
            
    return(issue)

def date_convert(date_str):
    # 08:50:13 CDT Tue Jun 28 2022
    datetime_object = datetime.strptime(date_str, '%H:%M:%S %Z %a %b %d %Y')
    #print(saved_datetime_object)
    return(datetime_object)

def check_devices(devices_list, rancid_dirs):
    issues = 0

    for dir in rancid_dirs:
        for hostname in devices_list:
            configfile = dir + hostname
            #print(configfile)
    
            try:
                with open(configfile, 'r') as myfile:
                    # check if timestamps in file, if so process it
                    file_contents = myfile.read()
                    if changed_string and saved_string in file_contents:
                        #print("True")
                        #print(configfile)
                        # cursor back to top of file
                        myfile.seek(0)
                        issue = check_configfile(myfile, hostname)
                        if issue:
                            issues = issues + 1

            except OSError:
                print("Could not open/read file:", configfile)
                #sys.exit()

    return(issues)


if __name__ == "__main__":
    devices_list = []
    with open(rancid_db, mode ='r') as myfile:
        mycsv = csv.reader(myfile, delimiter=rancid_delimiter)
        for row in mycsv:

            #dhcp-buildroom-1.myorg.net;cisco;down
            #r-abbotsfordsd.myorg.net;ios;up
            if len(row) == 3:
                hostname = row[0]
                model = row[1]
                updown = row[2]

                if updown == 'up' and model in cisco_models:
                    #print(hostname, model, updown)
                    devices_list.append(hostname)

    now = datetime.now().replace(microsecond=0)

    print(os.path.basename(__file__), ": Checking RANCID config files if `wr mem` needed")
    print("Checking", len(devices_list), "devices at", now)
    print("")
    issues = check_devices(devices_list, rancid_dirs)
    print(issues, "issues found")
