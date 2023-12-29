# Info

Just some misc one off standalone scripts for things. Scripts are all standalone.

# Scripts
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
