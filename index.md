## Welcome to the ChatBot home page

This is a simple bot for the recording and sending of messages in a discord server to an email address.


### Recording

These commands will assist in recording and sending logs of a room's
messages. They will also clean a room

* record_start

record_start is used to signal the bot to start recording

`$record_start`

* record_send

record_send is used to stop recording and send to one or more email addresses. The room will then be cleared of non-pinned messages

`$record_send test@test.com`

`$record_send test@test.com, bob@test.com`

* room_clean is used to erase the whole room

You may send the room's contents to an email address

`$room_clean`

`$room_clean test@test.com`
