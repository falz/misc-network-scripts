# Info

Just some misc one off standalone scripts for things. Scripts are all standalone.

# Scripts
## observium-to-dns_ptr.py
Query observium API for IP addresses known. Will spit out a bind style PTR zone based on router interface names. We use this to import into our dns zones to have nice and accurate traceroutes.

Works for ipv4 and ipv6, has some config options but defaults to adding ip4 and ip6 to entries. Attempts to use standard shorthand names for interfaces. Works well with Cisco and Juniper interface names as-is, further configurable.

Sample output:

```
$ ./observium-to-dns_ptr.py -n 10.20.8.0/24
$TTL 14400
8.20.10.in-addr.arpa. 14400   IN      SOA     ns0.myorg.net. hostmaster.myorg.net. 2023122901 7200 1800 1209600 14400
8.20.10.in-addr.arpa. 14400   IN      NS      ns1.myorg.net.
8.20.10.in-addr.arpa. 14400   IN      NS      ns2.myorg.net.
10.8.20.10.in-addr.arpa.      IN      PTR     r-chippewatc-hub-ae3.ip4.myorg.net.
13.8.20.10.in-addr.arpa.      IN      PTR     r-mainfield-hub-ae1.ip4.myorg.net.
14.8.20.10.in-addr.arpa.      IN      PTR     r-franklin-hub-ae1.ip4.myorg.net.
17.8.20.10.in-addr.arpa.      IN      PTR     r-blackville-hub-ae0.ip4.myorg.net.
18.8.20.10.in-addr.arpa.      IN      PTR     r-springfield-hub-ae0.ip4.myorg.net.
21.8.20.10.in-addr.arpa.      IN      PTR     r-markville-isp-ae0.ip4.myorg.net.
22.8.20.10.in-addr.arpa.      IN      PTR     r-waterloo-hub-ae0.ip4.myorg.net.
29.8.20.10.in-addr.arpa.      IN      PTR     r-madison-hub-ae10.ip4.myorg.net.
<...>
```

## push-configs-via-observium-group.py
Take config from a local text file and push it to network devices using NAPALM. Uses observium group ID's to choose devices. Ie if you have a group for some specific vendor type (Juniper, Cisco) you'd give it proper config for that platform

Sample output:

```diff
$ ./push-configs-via-observium-group.py -g 36  -c policy-standards.txt

Password for username 'falz' required to connect to Observium API and to log in to devices.

Password:

Merging the contents of 'policy-standards.txt' into group 36, which contains 6 devices..


Working on r-qfx5100-lab..
[edit groups policy-standards policy-options]
+    community Action_Transit_Prepend1 members 65001:1000;
+    community Action_PeerPub_Prepend1 members 65002:1000;
+    community Action_PeerPriv_Prepend1 members 65003:1000;
+    community Action_Transit_Prepend2 members 65001:2000;

Apply changes to r-qfx5100-lab? [y/N]
Discarding changes..

Working on r-mx960-lab..
[edit groups policy-standards policy-options]
+    community Action_Transit_Prepend1 members 65001:1000;
+    community Action_PeerPub_Prepend1 members 65002:1000;
+    community Action_PeerPriv_Prepend1 members 65003:1000;
+    community Action_Transit_Prepend2 members 65001:2000;
;

Apply changes to r-mx960-lab? [y/N] 

```

## rancid-check-wr-mem.py
Will loop over files in one or more RANCID directories and compare timestamps to see if it was changed since writing to NVRAM.

Sample output:

```
$ /opt/scripts/rancid-check-wr-mem.py 

rancid-check-wr-mem.py : Checking RANCID config files if `wr mem` needed
Checking 474 devices at 2023-12-29 10:38:45.524396

r-applewood
        Blame:   UNKNOWN
        Changed: 2023-03-21 05:28:29     UNKNOWN
        Saved:   2023-01-05 07:39:19     falz

r-jamestown
        Blame:   bishop
        Changed: 2022-06-14 09:18:03     bishop
        Saved:   2021-11-15 06:10:36     falz

r-funkytown
        Blame:   newt
        Changed: 2021-06-09 09:26:02     newt
        Saved:   2020-11-20 07:52:44     ripley

r-rightville
        Blame:   newt
        Changed: 2023-07-20 10:13:56     newt
        Saved:   2023-06-05 06:52:30     UNKNOWN

r-stsville
        Blame:   ripley
        Changed: 2021-03-17 18:17:55     ripley
        Saved:   2021-03-17 18:15:41     ripley

r-victorville
        Blame:   hicks
        Changed: 2022-11-17 17:53:02     hicks
        Saved:   2022-11-17 17:44:47     ripley

```
