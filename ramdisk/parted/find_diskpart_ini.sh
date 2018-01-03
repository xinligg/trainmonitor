#!/bin/sh

export LC_ALL=C

device_list=$(fdisk -l | grep "^/dev/" | awk '{print $1}')

for device in $device_list; do
	echo $device
	mount $device /mnt
	if [ $? -ne 0 ]; then
		ntfs-3g $device /mnt
		type=ntfs
	else
		type=fat32
	fi
	if [ $? -eq 0 ]; then
		if [ -f /mnt/diskpart.ini ]; then
			cp  /mnt/diskpart.ini /tmp/
			umount /mnt
			break
		else
			umount /mnt
			continue
		fi
	else
		umount /mnt
		continue
	fi
done

if [ -f /tmp/diskpart.ini ]; then
	dos2unix /tmp/diskpart.ini
	harddisk=$(echo $device | sed 's,\(/dev/[a-z][a-z]\).*,\1,')
	/root/parse_split_conf.py /tmp/diskpart.ini $harddisk
	if [ "x$type" = "xfat32"]; then
		mount $device /mnt
		mv /mnt/diskpart.ini /mnt/diskpart.ini.completed
		umount /mnt
	else 
		ntfs-3g $device /mnt
		mv /mnt/diskpart.ini /mnt/diskpart.ini.completed
		umount /mnt
	fi
	rm /tmp/diskpart.ini
else
	echo "I cannot find the diskpart.ini"
	exit 1
fi
