#!/bin/bash

/usr/bin/xmodmap ~/.Xmodmap

# set mouse acceleration and threshold (pointer is too fast with new Xvesa build)
#/usr/bin/xset m 1.5/1 4

# for aufs to merge opt-get plugin
mount -t tmpfs none /opt

# generate menu
# /usr/local/bin/update-menus

# start system bus
mkdir -p /var/run/dbus
mkdir -p /var/run/network
#mkdir -p /var/run/nscd
chown messagebus:messagebus /var/run/dbus
dbus-launch --config-file=/etc/dbus-1/system.conf

# mount all partitions
for i in `fdisk -l | grep "^/dev" | grep -v Extended | grep -v "Win95 Ext'd" | cut -d' ' -f1`; do
	mkdir -p /media/`basename $i`;
	mount $i /media/`basename $i`;
done

# install opt file if exist 
if [ ! "$(cat /proc/cmdline | grep opt=no )" ]; then
	find /mnt -maxdepth 4 -name *.opt -exec opt-get {} \;
fi

# start hotplug script
xhost +
#/bin/cp /sbin/hotplug-x /sbin/hotplug

sleep 0.5
#hald --daemon=yes
/usr/lib/upower/upowerd &
/usr/lib/udisks/udisks-daemon &
sleep 0.5
#for create pulseaudio device
mkdir -p /tmp/.pulse
mkdir -p /root/.pulse
mount -o bind /tmp/.pulse /root/.pulse
pulseaudio --start
#NetworkManager
/usr/sbin/wicd -foe &
sleep 0.5
wpa_supplicant -u -s &
#nscd
sleep 0.5
#nm-applet --sm-disable &
wicd-gtk &
ifconfig lo up &
sleep 0.5
gnome-volume-control-applet &
/usr/bin/aset &
sleep 0.5
ibus-daemon --xim &
sleep 0.5
gnome-power-manager &

#ln -sf /usr/local/bin/anti_virus /opt/anti_virus
#ln -sf /usr/local/bin/data_rescue /opt/data_rescue
#ln -sf /usr/local/bin/wsysrt /opt/wsysrt
ln -sf /mnt/Data/apps/sc25/opt/wsysrt /opt/wsysrt

# mount all partitions
mkdir -p /WINDOWS
x=0
dri=(C D E F G H I J K L M N O P Q R S T U V W X Y Z)
for i in `fdisk -l | grep "^/dev" | grep -v Extended | grep -v "Win95 Ext'd" | cut -d' ' -f1`; do
#	mkdir -p /media/${dri[$x]};
#	mount $i /media/${dri[$x]};
#	mkdir -p /WINDOWS/${dri[$x]};
#	mount $i /WINDOWS/${dri[$x]};
	if [ ! -e /WINDOWS/${dri[$x]} ]; then
		ln -s /media/`basename $i` /WINDOWS/${dri[$x]}
	fi
	let x++;
done

#for wsysrt
mk_bootdiskini
task_manager.py
#End scripts
