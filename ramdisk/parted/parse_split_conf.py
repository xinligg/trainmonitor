#!/usr/bin/python

import os
import sys


config_file=sys.argv[1]
hardisk_prefix=sys.argv[2]

print config_file

f=open(config_file)
lines=f.readlines()
f.close()

line=lines[1][0:-1] #Disk=
l=line[5:].split(",")
(major,minor)=(l[0], l[1])
device="%s%c" % (hardisk_prefix, int(major)+97)

print device


line=lines[2][11:-1] #Partitions
size_list=",".join([ "%sGB" % v for v in line.split(",")] )

start=os.popen("parted -m %s unit B print | grep \"^%d:\" | tail -n 1 | awk -F: '{print $2}'" % (device, int(minor)))
start_string=start.readline()
cmd="./parted.py %s %d \"%s\" %s" % (device, int(minor), size_list, start_string)
print cmd

os.system(cmd)

