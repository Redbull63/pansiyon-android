[app]
title = Pansiyon Nobet
package.name = pansiyonnobet
package.domain = tr.meb.direkli
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,android
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
orientation = portrait
fullscreen = 0
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
