import pathlib
import threading

import sounddevice
import soundfile


class SoundPlayer:
    def __init__(self, file_path: pathlib.Path, looping: bool = False):
        self._playback_stop_event: threading.Event = threading.Event()
        self._playback_stop_event.set()
        self._file_path = file_path
        self._looping = looping

    def _play(self, file_path: pathlib.Path) -> None:
        def _work():
            self._playback_stop_event.clear()

            ended_normally = False

            def callback(out_data, frames, _time, _status):
                data = wf.buffer_read(frames, dtype='float32')
                if len(out_data) > len(data):
                    out_data[:len(data)] = data
                    out_data[len(data):] = b'\x00' * (len(out_data) - len(data))
                    raise sounddevice.CallbackStop
                else:
                    out_data[:] = data

            def finished_callback():
                nonlocal ended_normally

                self._playback_stop_event.set()
                ended_normally = True

            with soundfile.SoundFile(file_path) as wf:
                stream = sounddevice.RawOutputStream(samplerate=wf.samplerate,
                                                     channels=wf.channels,
                                                     callback=callback,
                                                     blocksize=1024,
                                                     finished_callback=finished_callback)

                with stream:
                    self._playback_stop_event.wait()
                    # Save result before the callback is called again
                    result = ended_normally
                    stream.stop()

            return result

        if self._looping:
            while _work():
                pass
        else:
            _work()

    def play(self):
        playback_thread = threading.Thread(target=self._play, args=(self._file_path,))
        playback_thread.start()

    def stop(self):
        if not self._playback_stop_event.is_set():
            self._playback_stop_event.set()
            return True

        return False

    def toggle(self) -> None:
        if not self.stop():
            self.play()
