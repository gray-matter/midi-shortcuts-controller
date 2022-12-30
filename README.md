# Midi shortcuts controller

This was tested with:
* Ubuntu 22.04
* Pipewire with PulseAudio bindings
* Gnome Wayland
* Akai LPD8

## Requirements

* uinput
  * uinput must be loaded and enabled
  * `/dev/uinput` must be writable
* For lpd8
  * libasound2-dev
  * libjack-dev
* pulsectl must be available to control sound
* [Brotab](https://github.com/balta2ar/brotab) browsers extensions to orchestrate browsers
