[app]
title = Yumiko
package.name = yumiko
package.domain = org.khiem
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas
version = 0.1
requirements = python3,kivy==2.3.0,requests,pillow,plyer,certifi
orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,READ_MEDIA_IMAGES
android.api = 31
android.minapi = 21
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
