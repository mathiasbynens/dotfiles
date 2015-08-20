#!/bin/bash

mail_data_dir="/Users/$USER/Library/Mail/V2/MailData"
killall -HUP Mail
BEFORE=`ls -lah $mail_data_dir | grep -E 'Envelope Index$' | awk '{ print $5 }'`
/usr/bin/sqlite3 $mail_data_dir/Envelope\ Index 'PRAGMA integrity_check';
/usr/bin/sqlite3 $mail_data_dir/Envelope\ Index vacuum;
AFTER=`ls -lah $mail_data_dir | grep -E 'Envelope Index$' | awk '{ print $5}'`
echo "before: $BEFORE"
echo "after:  $AFTER"
open -a "Mail.app"

/usr/bin/osascript -e 'tell application "Mail" to display dialog "Envelope Index before: " & "'$BEFORE'" & return & "Envelope Index after: " & "'$AFTER'"'
