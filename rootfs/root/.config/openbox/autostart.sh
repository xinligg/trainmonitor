# This shell script is run before Openbox launches.
# Environment variables set here are passed to the Openbox session.
export PATH=$PATH:/usr/games
export HOST_DIR="/host"

#/usr/bin/desktop-daemon >/dev/null 2>1
#lxpanel &
#/usr/bin/desktopview.sh &
#cairo-dock -o &
#fbpanel &
#x0vncserver PasswordFile=/root/.local/share/vnc_passwd &

#feh
#$HOME/.config/openbox/wallpaper.sh &
#feh --bg-scale $HOME/.wallpaper/wallpaper.bmp &
#feh --bg-scale /usr/share/starosdesktop/bg_1366.png &

#xcompmgr
#sleep 1
#xcompmgr &

#udev
#sleep 3
#/usr/sbin/acpid > /dev/null 2>1 &
#/sbin/udevd --daemon 
#/sbin/udevadm trigger 

#post-boot
#/usr/local/bin/post-boot.sh > /dev/null 2>1 &
$HOST_DIR/oem/scripts/post-boot.sh > /dev/null 2>1 &
