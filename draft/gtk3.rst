   https://bodhi.fedoraproject.org/updates/FEDORA-2019-d67ec97b0b



             I'm not sure if the system accounted my vote after I
             added my second comment. Just I case, I vote again.
             vstinner - 2019-04-04 15:43:19.452036 (karma 0)
             More info in my original bug reports:    Firefox with
             Wayland crash on wl_abort() when selecting more than
             4000 characters in a <textarea>:
             https://bugzilla.mozilla.org/show_bug.cgi?id=1539773
             On Wayland, notify_surrounding_text() crash on
             wl_abort() if text is longer than 4000 bytes:
             https://gitlab.gnome.org/GNOME/gtk/issues/1783
             vstinner - 2019-04-04 15:40:52.225228 (karma 1)
             My test: run "MOZ_ENABLE_WAYLAND=1 firefox" (I have
             MOZ_ENABLE_WAYLAND=1 in /etc/environment), go to
             https://en.wikipedia.org/wiki/GTK : select all text &
             copy it, go to http://paste.alacon.org/ and paste the
             text in the textarea. Then select again the text =>
             Firefox exit immediately with gtk3-3.24.1-2.fc29.
             Using  gtk3-3.24.1-3.fc29, Firefox no longer crash.
             Good!
