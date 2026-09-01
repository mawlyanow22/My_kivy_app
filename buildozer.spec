[app]

# (str) Title of your application
title = Expense Notes

# (str) Package name
package.name = expensenotes

# (str) Package domain (used for the Android package name)
package.domain = org.alihan

# (str) Source code directory
source.dir = .

# (str) Main entry point
source.main = main.py

# (str) Application version
version = 1.0

# (list) Python modules to include
requirements = python3,kivy,kivymd

# (str) Supported orientation (portrait or landscape)
orientation = portrait

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (list) Android permissions
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (str) Android API target
android.api = 35

# (str) Android minimum API
android.minapi = 23

# (str) Android NDK version
android.ndk = 27c

# (str) Android architecture(s)
android.arch = arm64-v8a, armeabi-v7a

# (bool) Fullscreen
fullscreen = 0

# (str) Presplash image
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon
# icon.filename = %(source.dir)s/data/icon.png

# (list) File extensions to include
source.include_exts = py,json,png,jpg,jpeg,kv,atlas

# (list) File patterns to exclude
source.exclude_exts = spec,pyc,pyo

# (bool) Keep app's storage local to the app
android.private_storage = True

# (str) Android application theme
android.add_src =

# (bool) Enable AndroidX
android.enable_androidx = True

# (bool) Enable Android app bundle
android.arch = arm64-v8a, armeabi-v7a

# (str) Log level
log_level = 2


[buildozer]

# (str) Log level
log_level = 2

# (str) Warn if buildozer is run as root
warn_on_root = 1
