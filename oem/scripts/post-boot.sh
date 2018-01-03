#!/bin/bash
HOST_DIR="/host"

feh --bg-scale $HOST_DIR/oem/wallpaper/wallpaper.png &

#xcompmgr &
#xterm &
#/usr/sbin/acpid &
#acpid &

#/usr/bin/xmodmap ~/.Xmodmap

# set mouse acceleration and threshold (pointer is too fast with new Xvesa build)
#/usr/bin/xset m 1.5/1 4

#depmod
modprobe advcan
#CAN_MAJOR=`awk '$2=="advcan" {print $1}' /proc/devices`
#mknod /dev/can0 c $CAN_MAJOR 0
#mknod /dev/can1 c $CAN_MAJOR 1
chmod 666 /dev/can0
chmod 666 /dev/can1

cd /opt/advcan
./cansetup ./PCM3680.conf

xset -dpms

# for aufs to merge opt-get plugin
#mkdir /opt
#mount -t tmpfs none /opt
ln -s $HOST_DIR/apps/* /opt

#zenity --info test &
cd /opt/Project
./hmi_sh &

# generate menu
# /usr/local/bin/update-menus

$HOST_DIR/oem/scripts/acc
#/sbin/udevd --daemon
#/sbin/udevadm trigger
#/sbin/udevadm settle

# start system bus
mkdir -p /var/run/dbus
mkdir -p /var/run/network
#mkdir -p /var/run/nscd
chown messagebus:messagebus /var/run/dbus
dbus-launch --config-file=/etc/dbus-1/system.conf 

# mount all partitions
#for i in `fdisk -l | grep "^/dev" | grep -v Extended | grep -v "W95 Ext'd" | cut -d' ' -f1`; do
#	mkdir -p /media/`basename $i`;
#	mount $i /media/`basename $i`;
#done

# install opt file if exist 
if [ ! "$(cat /proc/cmdline | grep opt=no )" ]; then
	find $HOST_DIR -maxdepth 2 -name *.opt -exec opt-get {} \;
fi
#cp $HOST_DIR/oem/lib/* /usr/lib/


# start hotplug script
#xhost +
#/bin/cp /sbin/hotplug-x /sbin/hotplug

#sleep 0.5
##hald --daemon=yes
/usr/lib/upower/upowerd &
/usr/lib/udisks/udisks-daemon &
#sleep 0.5
#for create pulseaudio device
#mkdir -p /tmp/.pulse
#mkdir -p /root/.pulse
#mount -o bind /tmp/.pulse /root/.pulse
pulseaudio --start
#NetworkManager
#/usr/sbin/wicd -foe &
#sleep 0.5
#wpa_supplicant -u -s &
##nscd
#sleep 0.5
#nm-applet --sm-disable &
#wicd-gtk &
ifconfig lo up &
#sleep 0.5
gnome-volume-control-applet &
/usr/bin/aset &
#sleep 0.5
#ibus-daemon --xim &
#scim -d
#sleep 0.5
#gnome-power-manager &

$HOST_DIR/oem/scripts/desktop.sh &

# mount all partitions

#$HOST_DIR/oem/scripts/mount_windows_partitions

#End scripts
