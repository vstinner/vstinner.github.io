* OS X: force UTF-8
* FreeBSD, Solaris: use Python implementation of ASCII codec, libc functions
  are lying => "force ASCII"
* Bootstrap issue: PyUnicode_DecodeLocale() and PyUnicode_EncodeLocale() used
  until the Python codec is loaded.
* LC_CTYPE can be modified anytime: PyUnicode_DecodeLocale() != PyUnicode_DecodeFSDefault()
  if LC_CTYPE is modified after startup
* MBCS codec rewritten to handle error handlers
* MBCS mess with the Windows version
* CP_UTF7 special case
* add cp65011 Python codec: bad idea, but it was easier to implement it than
  to explain to uses that it's a bad idea :-)
* Code pages:

  - OEM: modifiable at runtime by SetConsoleCP()
  - ANSI: system-wide, but can be per thread
  - 932: Japanese -- mes with incremental decoders
  - 1252: European West, close to Latin1
  - 65000: UTF-7
  - 65001: UTF-8 -- error on surrogates since Windows Vista
