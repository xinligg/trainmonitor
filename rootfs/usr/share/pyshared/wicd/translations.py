#!/usr/bin/env python
# -* coding: utf-8 -*-

""" translations -- module for handling the translation strings for wicd. """
#
#   Copyright (C) 2007 - 2009 Adam Blackburn
#   Copyright (C) 2007 - 2009 Dan O'Reilly
#   Copyright (C) 2009        Andrew Psaltis
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License Version 2 as
#   published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import locale
import os
import wpath
import gettext


def get_gettext():
    """ Set up gettext for translations. """
    # Borrowed from an excellent post on how to do this at
    # http://www.learningpython.com/2006/12/03/translating-your-pythonpygtk-application/
    local_path = wpath.translations
    langs = []
    osLanguage = os.environ.get('LANGUAGE', None)
    if osLanguage:
        langs += osLanguage.split(":")
    osLanguage = None
    osLanguage = os.environ.get('LC_MESSAGES', None)
    if osLanguage:
        langs += osLanguage.split(":")
    try:
        # This avoids a bug: locale.getdefaultlocale() prefers
        # LC_CTYPE over LANG/LANGUAGE
        lc, encoding = locale.getdefaultlocale(envvars=('LC_MESSAGES', 
                                                        'LC_ALL', 'LANG', 
                                                        'LANGUAGE'))
    except ValueError, e:
        print str(e)
        print "Default locale unavailable, falling back to en_US"
    if (lc):
        langs += [lc]
    langs += ["en_US"]
    lang = gettext.translation('wicd', local_path, languages=langs, 
                               fallback=True)
    _ = lang.gettext
    return _

# Generated automatically on Thu, 14 Jan 2010 18:49:22 CST
_ = get_gettext()
language = {}
language['resetting_ip_address'] = _('''Resetting IP address...''')
language['prefs_help'] = _('''Preferences dialog''')
language['no_dhcp_offers'] = _('''Connection Failed: No DHCP offers received.''')
language['more_help'] = _('''For more detailed help, consult the wicd-curses(8) man page.''')
language['bad_pass'] = _('''Connection Failed: Bad password''')
language['cannot_start_daemon'] = _('''Unable to connect to wicd daemon DBus interface. This typically means there was a problem starting the daemon. Check the wicd log for more information.''')
language['verifying_association'] = _('''Verifying access point association...''')
language['wired_always_on'] = _('''Always show wired interface''')
language['could_not_connect'] = _('''Could not connect to wicd's D-Bus interface. Check the wicd log for error messages.''')
language['path_to_pac_file'] = _('''Path to PAC File''')
language['always_switch_to_wired'] = _('''Always switch to wired connection when available''')
language['disconn_help'] = _('''Disconnect from all networks''')
language['wired_networks'] = _('''Wired Networks''')
language['backend_alert'] = _('''Changes to your backend won't occur until the daemon is restarted.''')
language['about_help'] = _('''Stop a network connection in progress''')
language['connecting'] = _('''Connecting''')
language['pre_disconnect_script'] = _('''Run pre-disconnect script''')
language['cannot_edit_scripts_1'] = _('''To avoid various complications, wicd-curses does not support directly editing the scripts directly.  However, you can edit them manually.  First, (as root)", open the "$A" config file, and look for the section labeled by the $B in question.  In this case, this is:''')
language['cannot_edit_scripts_3'] = _('''You can also configure the wireless networks by looking for the "[<ESSID>]" field in the config file.''')
language['cannot_edit_scripts_2'] = _('''Once there, you can adjust (or add) the "beforescript", "afterscript", and "disconnectscript" variables as needed, to change the preconnect, postconnect, and disconnect scripts respectively.  Note that you will be specifying the full path to the scripts - not the actual script contents.  You will need to add/edit the script contents separately.  Refer to the wicd manual page for more information.''')
language['scripts_need_pass'] = _('''You must enter your password to configure scripts''')
language['dns_domain'] = _('''DNS domain''')
language['aborted'] = _('''Connection Cancelled''')
language['scanning_stand_by'] = _('''Scanning networks... stand by...''')
language['password'] = _('''Password''')
language['no_daemon_tooltip'] = _('''Wicd daemon unreachable''')
language['use_static_dns'] = _('''Use Static DNS''')
language['setting_broadcast_address'] = _('''Setting broadcast address...''')
language['choose_wired_profile'] = _('''Select or create a wired profile to connect with''')
language['make_wired_profile'] = _('''To connect to a wired network, you must create a network profile.  To create a network profile, type a name that describes this network, and press Add.''')
language['esc_to_cancel'] = _('''Press ESC to cancel''')
language['scanning'] = _('''Scanning''')
language['flushing_routing_table'] = _('''Flushing the routing table...''')
language['brought_to_you'] = _('''Brought to you by:''')
language['refresh_help'] = _('''Refresh network list''')
language['select_hidden_essid'] = _('''Select Hidden Network ESSID''')
language['ext_programs'] = _('''External Programs''')
language['connect'] = _('''Connect''')
language['help_help'] = _('''Display this help dialog''')
language['use_global_dns'] = _('''Use global DNS servers''')
language['enable_encryption'] = _('''This network requires encryption to be enabled.''')
language['use_last_used_profile'] = _('''Use last used profile on wired autoconnect''')
language['preferences'] = _('''Preferences''')
language['dhcp_failed'] = _('''Connection Failed: Unable to Get IP Address''')
language['setting_static_ip'] = _('''Setting static IP addresses...''')
language['connecting_to_daemon'] = _('''Connecting to daemon...''')
language['automatic_connect'] = _('''Automatically connect to this network''')
language['add_new_wired_profile'] = _('''Add a new wired profile''')
language['dhcp_client'] = _('''DHCP Client''')
language['display_type_dialog'] = _('''Use dBm to measure signal strength''')
language['global_settings'] = _('''Use these settings for all networks sharing this essid''')
language['config_help'] = _('''Configure Selected Network''')
language['use_debug_mode'] = _('''Enable debug mode''')
language['removing_old_connection'] = _('''Removing old connection...''')
language['no_sudo_prog'] = _('''Could not find a graphical sudo program.  The script editor could not be launched.  You'll have to edit scripts directly your configuration file.''')
language['wireless_networks'] = _('''Wireless Networks''')
language['configuring_wired'] = _('''Configuring preferences for wired profile "$A"''')
language['no_wireless_networks_found'] = _('''No wireless networks found.''')
language['madwifi_for_adhoc'] = _('''Check if using madwifi/atheros drivers''')
language['properties'] = _('''Properties''')
language['setting_encryption_info'] = _('''Setting encryption info''')
language['about'] = _('''About Wicd''')
language['ok'] = _('''OK''')
language['adhoc_help'] = _('''Set up Ad-hoc network''')
language['scripts_help'] = _('''Select scripts''')
language['invalid_address'] = _('''Invalid address in $A entry.''')
language['configuring_interface'] = _('''Configuring wireless interface...''')
language['generating_psk'] = _('''Generating PSK...''')
language['validating_authentication'] = _('''Validating authentication...''')
language['essid'] = _('''ESSID''')
language['anonymous_identity'] = _('''Anonymous Identity''')
language['wireless_interface'] = _('''Wireless Interface''')
language['hidden_network'] = _('''Hidden Network''')
language['key'] = _('''Key''')
language['wicd_curses'] = _('''Wicd Curses Interface''')
language['debugging'] = _('''Debugging''')
language['use_encryption'] = _('''Use Encryption''')
language['wpa_supplicant'] = _('''WPA Supplicant''')
language['global_dns_servers'] = _('''Global DNS servers''')
language['not_connected'] = _('''Not connected''')
language['done'] = _('''Done connecting...''')
language['cannot_connect_to_daemon'] = _('''Can't connect to the daemon, trying to start it automatically...''')
language['cancel'] = _('''Cancel''')
language['case_sensitive'] = _('''All controls are case sensitive''')
language['gateway'] = _('''Gateway''')
language['backend'] = _('''Backend''')
language['dbus_fail'] = _('''DBus failure! This is most likely caused by the wicd daemon stopping while wicd-curses is running. Please restart the daemon, and then restart wicd-curses.''')
language['terminated'] = _('''Terminated by user''')
language['wired_detect'] = _('''Wired Link Detection''')
language['add_new_profile'] = _('''Add a new profile''')
language['use_ics'] = _('''Activate Internet Connection Sharing''')
language['create_adhoc_network'] = _('''Create an Ad-Hoc Network''')
language['interface_up'] = _('''Putting interface up...''')
language['global_dns_not_enabled'] = _('''Global DNS has not been enabled in general preferences.''')
language['dns'] = _('''DNS''')
language['advanced_settings'] = _('''Advanced Settings''')
language['username'] = _('''Username''')
language['wicd_auto_config'] = _('''Automatic (recommended)''')
language['wired_network_found'] = _('''Wired connection detected''')
language['netmask'] = _('''Netmask''')
language['select_a_network'] = _('''Choose from the networks below:''')
language['connect_help'] = _('''Connect to selected network''')
language['no_delete_last_profile'] = _('''wicd-curses does not support deleting the last wired profile.  Try renaming it ('F2')''')
language['gen_settings'] = _('''General Settings''')
language['connected_to_wireless'] = _('''Connected to $A at $B (IP: $C)''')
language['exception'] = _('''EXCEPTION! Please report this to the maintainer and file a bug report with the backtrace below:''')
language['configuring_wireless'] = _('''Configuring preferences for wireless network "$A" ($B)''')
language['generating_wpa_config'] = _('''Generating WPA configuration file...''')
language['search_domain'] = _('''Search domain''')
language['encrypt_info_missing'] = _('''Required encryption information is missing.''')
language['running_dhcp'] = _('''Obtaining IP address...''')
language['lost_dbus'] = _('''The wicd daemon has shut down. The UI will not function properly until it is restarted.''')
language['wired_network_instructions'] = _('''To connect to a wired network, you must create a network profile. To create a network profile, type a name that describes this network, and press Add.''')
language['setting_static_dns'] = _('''Setting static DNS servers...''')
language['auto_reconnect'] = _('''Automatically reconnect on connection loss''')
language['use_wep_encryption'] = _('''Use Encryption (WEP only)''')
language['wired_autoconnect_settings'] = _('''Wired Autoconnect Settings''')
language['before_script'] = _('''Run script before connect''')
language['always_use_wext'] = _('''You should almost always use wext as the WPA supplicant driver''')
language['network_interfaces'] = _('''Network Interfaces''')
language['use_default_profile'] = _('''Use default profile on wired autoconnect''')
language['scan'] = _('''Scan''')
language['ip'] = _('''IP''')
language['connected_to_wired'] = _('''Connected to wired network (IP: $A)''')
language['wpa_supplicant_driver'] = _('''WPA Supplicant Driver''')
language['access_cards'] = _('''Wicd needs to access your computer's network cards.''')
language['killswitch_enabled'] = _('''Wireless Kill Switch Enabled''')
language['hidden_network_essid'] = _('''Hidden Network ESSID''')
language['secured'] = _('''Secured''')
language['interface_down'] = _('''Putting interface down...''')
language['authentication'] = _('''Authentication''')
language['after_script'] = _('''Run script after connect''')
language['show_wired_list'] = _('''Prompt for profile on wired autoconnect''')
language['channel'] = _('''Channel''')
language['unsecured'] = _('''Unsecured''')
language['rename_wired_profile'] = _('''Rename wired profile''')
language['daemon_unavailable'] = _('''The wicd daemon is unavailable, so your request cannot be completed''')
language['stop_showing_chooser'] = _('''Stop Showing Autoconnect pop-up temporarily''')
language['scan_help'] = _('''Scan for hidden networks''')
language['use_static_ip'] = _('''Use Static IPs''')
language['raw_screen_arg'] = _('''use urwid's raw screen controller''')
language['route_flush'] = _('''Route Table Flushing''')
language['scripts'] = _('''Scripts''')
language['identity'] = _('''Identity''')
language['automatic_reconnection'] = _('''Automatic Reconnection''')
language['wired_interface'] = _('''Wired Interface''')
language['press_to_quit'] = _('''Press F8 or Q to quit.''')
language['default_wired'] = _('''Use as default profile (overwrites any previous default)''')
language['wired_network'] = _('''Wired Network''')
language['dns_server'] = _('''DNS server''')
language['notifications'] = _('''Notifications''')
language['display_notifications'] = _('''Display notifications about connection status''')
language['connection_established'] = _('''Connection established''')
language['disconnected'] = _('''Disconnected''')
language['establishing_connection'] = _('''Establishing connection...''')
language['association_failed'] = _('''Connection failed: Could not contact the wireless access point.''')
language['access_denied'] = _('''Unable to contact the Wicd daemon due to an access denied error from DBus. Please check that your user is in the $A group.''')
language['disconnecting_active'] = _('''Disconnecting active connections...''')
language['access_denied_wc'] = _('''ERROR: wicd-curses was denied access to the wicd daemon: please check that your user is in the "$A" group.''')
language['post_disconnect_script'] = _('''Run post-disconnect script''')
language['resume_script'] = _('''Resume script''')
language['suspend_script'] = _('''Suspend script''')
language['invalid_ip_address'] = _('''Invalid IP address entered.''')
language['verify_ap_dialog'] = _('''Ping static gateways after connecting to verify association''')
language['conn_info_wireless'] = _('''$A
$B
$C
$D
$E KB/s
$F KB/s''')
language['conn_info_wired'] = _('''$A
$B KB/s
$C KB/s''')
language['conn_info_wireless_labels'] = _('''Wireless
SSID:
Speed:
IP:
Strength:
RX:
TX:''')
language['conn_info_wired_labels'] = _('''Wired
IP:
RX:
TX:''')
