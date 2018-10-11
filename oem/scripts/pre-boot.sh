#!/bin/bash

echo pre-boot

vendor_id=`lspci -nm |grep 0300|awk '{print $3}'|tr -d \"`
device_id=`lspci -nm |grep 0300|awk '{print $4}'|tr -d \"`

ID=`echo $vendor_id:$device_id`

case $ID in 
	'10de:0a6c')
		echo "nm10 setting"
			;;
	'0300:1022')
		echo "old 3353 geode crash screen"
cat > /etc/X11/xorg.conf << EOF
Section "Device"
        Identifier      "Configured Video Device"
        Driver          "vesa"
EndSection

Section "Monitor"
        Identifier      "Configured Monitor"
EndSection

Section "Screen"
        Identifier      "Default Screen"
        Monitor         "Configured Monitor"
        Device          "Configured Video Device"
EndSection
EOF
			;;
	'0300:8086')
		echo "N455 setting"
cat > /etc/X11/xorg.conf << EOF
Section "Device"
        Identifier      "Configured Video Device"
        Driver          "vesa"
EndSection

Section "Monitor"
        Identifier      "Configured Monitor"
EndSection

Section "Screen"
        Identifier      "Default Screen"
        Monitor         "Configured Monitor"
        Device          "Configured Video Device"
EndSection
EOF

echo "blacklist i915" > /etc/modprobe.d/blacklist-graphicscard.conf
			;;

	'"1002"')
		echo "new setting"
			;;
	*)
		echo "geode setting"
cat > /etc/X11/xorg.conf << EOF
Section "Device"
        Identifier      "Configured Video Device"
        Driver          "geode"
EndSection

Section "Monitor"
        Identifier      "Configured Monitor"
EndSection

Section "Screen"
        Identifier      "Default Screen"
        Monitor         "Configured Monitor"
        Device          "Configured Video Device"
EndSection
EOF
			;;
esac

/sbin/udevd --daemon
/sbin/udevadm trigger
/sbin/udevadm settle

#End scripts
