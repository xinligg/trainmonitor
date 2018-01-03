# -*- coding: utf-8 -*-
"""List of interfaces, generated from the Telepathy spec version 0.19.0

Copyright © 2005-2009 Collabora Limited
Copyright © 2005-2009 Nokia Corporation
Copyright © 2006 INdT


This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""
CONNECTION_MANAGER = 'org.freedesktop.Telepathy.ConnectionManager'
CONNECTION = 'org.freedesktop.Telepathy.Connection'
CONNECTION_FUTURE = 'org.freedesktop.Telepathy.Connection.FUTURE'
CONNECTION_INTERFACE_ALIASING = 'org.freedesktop.Telepathy.Connection.Interface.Aliasing'
CONNECTION_INTERFACE_AVATARS = 'org.freedesktop.Telepathy.Connection.Interface.Avatars'
CONNECTION_INTERFACE_BALANCE = 'org.freedesktop.Telepathy.Connection.Interface.Balance'
CONNECTION_INTERFACE_CAPABILITIES = 'org.freedesktop.Telepathy.Connection.Interface.Capabilities'
CONNECTION_INTERFACE_CONTACT_CAPABILITIES = 'org.freedesktop.Telepathy.Connection.Interface.ContactCapabilities'
CONNECTION_INTERFACE_CONTACT_INFO = 'org.freedesktop.Telepathy.Connection.Interface.ContactInfo.DRAFT'
CONNECTION_INTERFACE_CONTACTS = 'org.freedesktop.Telepathy.Connection.Interface.Contacts'
CONNECTION_INTERFACE_LOCATION = 'org.freedesktop.Telepathy.Connection.Interface.Location'
CONNECTION_INTERFACE_PRESENCE = 'org.freedesktop.Telepathy.Connection.Interface.Presence'
CONNECTION_INTERFACE_RENAMING = 'org.freedesktop.Telepathy.Connection.Interface.Renaming'
CONNECTION_INTERFACE_REQUESTS = 'org.freedesktop.Telepathy.Connection.Interface.Requests'
CONNECTION_INTERFACE_SIMPLE_PRESENCE = 'org.freedesktop.Telepathy.Connection.Interface.SimplePresence'
CHANNEL_BUNDLE = 'org.freedesktop.Telepathy.ChannelBundle.DRAFT'
CHANNEL = 'org.freedesktop.Telepathy.Channel'
CHANNEL_FUTURE = 'org.freedesktop.Telepathy.Channel.FUTURE'
CHANNEL_TYPE_CONTACT_LIST = 'org.freedesktop.Telepathy.Channel.Type.ContactList'
CHANNEL_TYPE_STREAMED_MEDIA = 'org.freedesktop.Telepathy.Channel.Type.StreamedMedia'
CHANNEL_TYPE_ROOM_LIST = 'org.freedesktop.Telepathy.Channel.Type.RoomList'
CHANNEL_TYPE_TEXT = 'org.freedesktop.Telepathy.Channel.Type.Text'
CHANNEL_TYPE_TUBES = 'org.freedesktop.Telepathy.Channel.Type.Tubes'
CHANNEL_TYPE_STREAM_TUBE = 'org.freedesktop.Telepathy.Channel.Type.StreamTube'
CHANNEL_TYPE_DBUS_TUBE = 'org.freedesktop.Telepathy.Channel.Type.DBusTube'
CHANNEL_TYPE_FILE_TRANSFER = 'org.freedesktop.Telepathy.Channel.Type.FileTransfer'
CHANNEL_TYPE_CONTACT_SEARCH = 'org.freedesktop.Telepathy.Channel.Type.ContactSearch.DRAFT2'
CHANNEL_TYPE_CALL = 'org.freedesktop.Telepathy.Channel.Type.Call.DRAFT'
CHANNEL_INTERFACE_CALL_STATE = 'org.freedesktop.Telepathy.Channel.Interface.CallState'
CHANNEL_INTERFACE_CHAT_STATE = 'org.freedesktop.Telepathy.Channel.Interface.ChatState'
CHANNEL_INTERFACE_CONFERENCE = 'org.freedesktop.Telepathy.Channel.Interface.Conference.DRAFT'
CHANNEL_INTERFACE_DESTROYABLE = 'org.freedesktop.Telepathy.Channel.Interface.Destroyable'
CHANNEL_INTERFACE_DTMF = 'org.freedesktop.Telepathy.Channel.Interface.DTMF'
CHANNEL_INTERFACE_GROUP = 'org.freedesktop.Telepathy.Channel.Interface.Group'
CHANNEL_INTERFACE_HOLD = 'org.freedesktop.Telepathy.Channel.Interface.Hold'
CHANNEL_INTERFACE_HTML = 'org.freedesktop.Telepathy.Channel.Interface.HTML.DRAFT'
CHANNEL_INTERFACE_PASSWORD = 'org.freedesktop.Telepathy.Channel.Interface.Password'
CHANNEL_INTERFACE_MEDIA_SIGNALLING = 'org.freedesktop.Telepathy.Channel.Interface.MediaSignalling'
CHANNEL_INTERFACE_MERGEABLE_CONFERENCE = 'org.freedesktop.Telepathy.Channel.Interface.MergeableConference.DRAFT'
CHANNEL_INTERFACE_MESSAGES = 'org.freedesktop.Telepathy.Channel.Interface.Messages'
CHANNEL_INTERFACE_SPLITTABLE = 'org.freedesktop.Telepathy.Channel.Interface.Splittable.DRAFT'
CHANNEL_INTERFACE_TUBE = 'org.freedesktop.Telepathy.Channel.Interface.Tube'
MEDIA_SESSION_HANDLER = 'org.freedesktop.Telepathy.Media.SessionHandler'
MEDIA_STREAM_HANDLER = 'org.freedesktop.Telepathy.Media.StreamHandler'
CALL_CONTENT = 'org.freedesktop.Telepathy.Call.Content.DRAFT'
CALL_CONTENT_INTERFACE_MEDIA = 'org.freedesktop.Telepathy.Call.Content.Interface.Media.DRAFT'
CALL_CONTENT_CODEC_OFFER = 'org.freedesktop.Telepathy.Call.Content.CodecOffer.DRAFT'
CALL_STREAM = 'org.freedesktop.Telepathy.Call.Stream.DRAFT'
CALL_STREAM_INTERFACE_MEDIA = 'org.freedesktop.Telepathy.Call.Stream.Interface.Media.DRAFT'
CALL_STREAM_ENDPOINT = 'org.freedesktop.Telepathy.Call.Stream.Endpoint.DRAFT'
DEBUG = 'org.freedesktop.Telepathy.Debug'
ACCOUNT_MANAGER = 'org.freedesktop.Telepathy.AccountManager'
ACCOUNT = 'org.freedesktop.Telepathy.Account'
ACCOUNT_INTERFACE_AVATAR = 'org.freedesktop.Telepathy.Account.Interface.Avatar'
CHANNEL_DISPATCHER = 'org.freedesktop.Telepathy.ChannelDispatcher'
CHANNEL_DISPATCHER_INTERFACE_OPERATION_LIST = 'org.freedesktop.Telepathy.ChannelDispatcher.Interface.OperationList'
CHANNEL_DISPATCH_OPERATION = 'org.freedesktop.Telepathy.ChannelDispatchOperation'
CHANNEL_REQUEST = 'org.freedesktop.Telepathy.ChannelRequest'
CLIENT = 'org.freedesktop.Telepathy.Client'
CLIENT_OBSERVER = 'org.freedesktop.Telepathy.Client.Observer'
CLIENT_APPROVER = 'org.freedesktop.Telepathy.Client.Approver'
CLIENT_HANDLER = 'org.freedesktop.Telepathy.Client.Handler'
CLIENT_HANDLER_FUTURE = 'org.freedesktop.Telepathy.Client.Handler.FUTURE'
CLIENT_INTERFACE_REQUESTS = 'org.freedesktop.Telepathy.Client.Interface.Requests'
CHANNEL_HANDLER = 'org.freedesktop.Telepathy.ChannelHandler'
PROPERTIES_INTERFACE = 'org.freedesktop.Telepathy.Properties'
