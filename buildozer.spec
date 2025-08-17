
[app]
title = Lotto Recommender
package.name = lotto_recommender
package.domain = org.example
source.dir = .
source.include_exts = py,kv,txt,json,ttf,zip
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Permissions for Android storage
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# To access external storage for CSV exports (scoped storage on Android 10+ is handled by storage API)
android.api = 33
android.minapi = 24

[buildozer]
log_level = 2

[android]
# Use recipe cache if needed
# android.enable_androidx = True
