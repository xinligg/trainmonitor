#!/bin/sh

TARGET_DEVICE=$1

if [ "x$TARGET_DEVICE" = "x" -o ! -e $TARGET_DEVICE ]; then
	echo "Wrong TARGET_DEVICE $TARGET_DEVICE"
	exit 1
fi

dd if=/tmp/origMBR.dat of=${TARGET_DEVICE} bs=446 count=1 conv=notrunc
dd if=/tmp/origSector3.dat of=${TARGET_DEVICE} seek=3 bs=512 count=1 conv=notrunc
dd if=/tmp/origSector4.dat of=${TARGET_DEVICE} seek=4 bs=512 count=30 conv=notrunc

