"""
Inspired by (copied :] from) TaylorSMarks's playsound:
https://github.com/TaylorSMarks/playsound
"""

import winsound

winsound.PlaySound()


class PlaySoundException(Exception):
    pass


def _playSoundWin(sound, block=True):
    from ctypes import c_buffer, windll
    from random import random
    from time import sleep
    from sys import getfilesystemencoding

    def winCommand(*command):
        buf = c_buffer(255)
        command = ' '.join(command).encode(getfilesystemencoding())
        errorCode = int(windll.winmm.mciSendStringA(command, buf, 254, 0))
        if errorCode:
            errorBuffer = c_buffer(255)
            windll.winmm.mciGetErrorStringA(errorCode, errorBuffer, 254)
            exceptionMessage = ('\n    Error ' + str(errorCode) + ' for command:'
                                                                  '\n        ' + command.decode() +
                                '\n    ' + errorBuffer.value.decode())
            raise PlaySoundException(exceptionMessage)
        return buf.value

    alias = 'playsound_' + str(random())
    winCommand('open "' + sound + '" alias', alias)
    winCommand('set', alias, 'time format milliseconds')
    durationInMS = winCommand('status', alias, 'length')
    winCommand('play', alias, 'from 0 to', durationInMS.decode())

    if block:
        sleep(float(durationInMS) / 1000.0)


def _playSoundOSX(sound, block=True):
    if '://' not in sound:
        if not sound.startswith('/'):
            from os import getcwd
            sound = getcwd() + '/' + sound
        sound = 'file://' + sound
    url = NSURL.URLWithString_(sound)
    nssound = NSSound.alloc().initWithContentsOfURL_byReference_(url, True)
    if not nssound:
        raise IOError('Unable to load sound named: ' + sound)
    nssound.play()


def _playSoundNix(sound, block=True):
    """Play a sound using GStreamer.
    Inspired by this:
    https://gstreamer.freedesktop.org/documentation/tutorials/playback/playbin-usage.html
    """
    if not block:
        raise NotImplementedError(
            "block=False cannot be used on this platform yet")

    # pathname2url escapes non-URL-safe characters
    import os
    try:
        from urllib.request import pathname2url
    except ImportError:
        # python 2
        from urllib import pathname2url

    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst

    Gst.init(None)

    playbin = Gst.ElementFactory.make('playbin', 'playbin')
    if sound.startswith(('http://', 'https://')):
        playbin.props.uri = sound
    else:
        playbin.props.uri = 'file://' + pathname2url(os.path.abspath(sound))

    set_result = playbin.set_state(Gst.State.PLAYING)
    if set_result != Gst.StateChangeReturn.ASYNC:
        raise PlaySoundException(
            "playbin.set_state returned " + repr(set_result))

    # FIXME: use some other bus method than poll() with block=False
    # https://lazka.github.io/pgi-docs/#Gst-1.0/classes/Bus.html
    bus = playbin.get_bus()
    bus.poll(Gst.MessageType.EOS, Gst.CLOCK_TIME_NONE)
    playbin.set_state(Gst.State.NULL)


from platform import system

system = system()

if system == 'Windows':
    playsound = _playSoundWin
elif system == 'Darwin':
    playsound = _playSoundOSX
else:
    playsound = _playSoundNix

del system

playsound('ihate.mp3', False)

screen = pygame.display.set_mode((300, 300))
pygame.init()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    pygame.display.flip()
    pygame.time.wait(10000)
    playsound('ihate.mp3', False)

pygame.quit()
