#!/usr/bin/python

import os,sys

global MAX_CAPACITY
MAX_CAPACITY = ""
global layout
layout = {}

global target_start
target_start=""

global NUMBER
global START
global END
global CAPACITY
global TYPE
global BOOT
(NUMBER, START, END, CAPACITY, FILESYSTEM, TYPE, BOOT)=(0,1,2,3,4,5,6)

global FILESYSTEM_TYPE
FILESYSTEM_TYPE={"fat32":"b", "ntfs":"7"}

def print_readable_layout(device):
	cmd="parted %s print free" % device
	print(cmd)
	os.system(cmd)

def get_device_layout(device, data):
	global MAX_CAPACITY

	data.clear()
	f = os.popen("parted --machine %s print free" % device)
	lines = f.readlines()
	line=lines[1]
	MAX_CAPACITY = line.split(":")[1][0:-1]
	print "MAX_CAPACITY: %s" % MAX_CAPACITY
	for line in lines[2:]:
		line = line[:-1]
		line_list = line.split(":")
		if line_list[4] != "free;":
			key = "%s%s" % (device, line_list[0])
			data[key] = line_list
			print "%s %s" %(key, data[key])
	f.close()

def delete_partition(device, number, update_layout=False):
	global layout

	key = "%s%s" % (device, number)
	cmd = "parted -s %s rm %s" % (device, number)
	print cmd
	os.system(cmd)
	if update_layout:
		get_device_layout(device, layout)

def create_partition(device, type, start, end, update_layout=False):
	global layout

	cmd = "parted -s %s mkpart %s %s %s" % (device, type, start, end)
	print cmd
	os.system(cmd)
	if update_layout:
		get_device_layout(device, layout)



def set_partition_active(device, number):
	print "set_partition_active"
	fdisk_cmd="a\n%s\nw\n" % number
	print fdisk_cmd
	
	f=open("fdisk_cmd1", "w")
	f.write(fdisk_cmd)
	f.close()
	os.system("sleep 3")
	print ("sleep 3")
	os.system("fdisk %s < fdisk_cmd1" % device)
	print ("fdisk %s < fdisk_cmd1" % device)

def change_partition_type(device, number, type):
	if len(layout) == 1:
		fdisk_cmd="t\n%s\nw\n" % type
	else:
		fdisk_cmd="t\n%s\n%s\nw\n" % (number, type)
	print fdisk_cmd
	
	f=open("fdisk_cmd", "w")
	f.write(fdisk_cmd)
	f.close()
	print("fdisk %s < fdisk_cmd" % device)
	os.system("fdisk %s < fdisk_cmd" % device)

def format_partition_type(device_node, type):
	cmd="mkfs.ntfs --fast %s" % device_node
	os.system("sleep 3")
	print ("sleep 3")
	print cmd
	os.system(cmd)

def resize_partition(device, device_node, type, size):
	if type=="ntfs" or type=="":
		newsize=int(size.replace("GB",""))-1
		cmd="ntfsresize -f -s %dG %s" % (newsize, device_node)	
		print cmd
		os.system(cmd)
	elif type=="fat32":
		start=layout[device_node][START]
		if start[-2:-1] not in ["G", "M"]:
                        end_value="%s" % size[0][0:-2]
                else:
                        end_value=eval("%s + %s" % (start[0:-2], size[0:-2]) )
                end="%sGB" % end_value

		cmd="parted %s resize %s %s %s" % (device, layout[device_node][NUMBER], layout[device_node][START], end)
		print cmd
		os.system(cmd)

def format_loop(device):
	oldkeys=layout.keys()
	get_device_layout(device, layout)
	newkeys=layout.keys()
	for key in oldkeys:
		newkeys.remove(key)
	print "new partitions: %s" % newkeys
	for key in newkeys:
		if int(layout[key][NUMBER]) not in [1,2,3,4]:
			print "format %s" % key	
			change_partition_type(device, layout[key][NUMBER], FILESYSTEM_TYPE[ "ntfs" ])
			format_partition_type(key, "ntfs")

def split_primary_create_loop(device, orig_number):
	global target_start
	key = "%s%s" % (device, orig_number)
	print layout
	type=layout[key][FILESYSTEM]
	boot=layout[key][BOOT]
	shrink_size=size_list[0]
	resize_partition(device, key, type, shrink_size)

	delete_partition(device, orig_number, False)
	start=layout[key][START]
	count=1
	oldend=MAX_CAPACITY
	print "boot="+boot
	for new_size in size_list:
		if start[-2:-1] not in ["G", "M"]:
			end_value="%s" % size_list[0][0:-2]
		else:
			end_value=eval("%s + %s" % (start[0:-2], new_size[0:-2]) )
		end="%sGB" % end_value
		type=layout[key][FILESYSTEM]
		if type=="":
			type="ntfs" #ntfs
		print start, end
		if count == 1:
			oldend=layout[key][END]
			create_partition(device, "primary", target_start, end)
			change_partition_type(device, orig_number, FILESYSTEM_TYPE[ type ])
			if boot=="boot;":
				print "boot="+boot
				set_partition_active(device, layout[key][NUMBER])
			start=end
			count=2
		if count == 2:
			create_partition(device, "extend", start, oldend)
			count=3
		if count > 2:
			if count==len(size_list)+2:
				create_partition(device, "logical", start, oldend)
				break
			else:
				create_partition(device, "logical", start, end)
			count=count+1
		start=end

	format_loop(device)

def split_logical_create_loop(device, orig_number):
	key = "%s%s" % (device, orig_number)
	type=layout[key][FILESYSTEM]
	shrink_size=size_list[0]
	resize_partition(device, key, type, shrink_size)

	delete_partition(device, orig_number, False)
	start=layout[key][START]
	for new_size in size_list:
		end_value=eval("%s + %s" % (start[0:-2], new_size[0:-2]) )
		end="%sGB" % end_value
		type=layout[key][FILESYSTEM]
		if type=="":
			type="ntfs" #ntfs
		print start, end
		create_partition(device, "logical", start, end)
		change_partition_type(device, orig_number, FILESYSTEM_TYPE[ type ])
		start=end
	format_loop(device)

def go_ahead(device, orig_number, size_list):
	global layout

	print "Device %s Layout:" % device
	get_device_layout(device, layout)

	num=eval("%s" % orig_number)
	print num
	if num <=4:
		split_primary_create_loop(device, num)
	else:
		split_logical_create_loop(device, num)


if __name__== "__main__":
	global target_start
	device=sys.argv[1]
	orig_part_number=sys.argv[2]
	size_list=sys.argv[3].split(",")
	target_start=sys.argv[4]

	go_ahead(device, orig_part_number, size_list)

	print("parted %s print free" % device)
	os.system("parted %s print free" % device)

