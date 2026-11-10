"""Lecteur vidéo avec décodage Dolby Digital (AC-3) par ac3/decoder.py.
Vidéo : OpenCV (muet). Audio : AC3Decoder -> effets A/52 -> sounddevice. Horloge maître = audio.
Usage : python -m player.player film.mp4 [--mode stereo|5.1] [--dialnorm]"""
import argparse, os, queue, sys, threading, time
import cv2, numpy as np, sounddevice as sd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from ac3.decoder import AC3Decoder
from player.demux import load
from player.effects import downmix_stereo, dialnorm_gain


class AudioOut:
    def __init__(self, ch, rate):
        self.q, self.buf, self.played, self.ch = queue.Queue(maxsize=48), None, 0, ch
        self.stream = sd.OutputStream(samplerate=rate, channels=ch, dtype="float32", callback=self.cb)

    def cb(self, out, n, t, st):
        got = 0
        while got < n:
            if self.buf is None or len(self.buf) == 0:
                try:
                    self.buf = self.q.get_nowait()
                except queue.Empty:
                    break
            take = self.buf[:n - got]
            out[got:got + len(take)] = take
            self.buf = self.buf[len(take):]; got += len(take)
        out[got:] = 0
        self.played += got


def decode_thread(frames, a, mode, use_dn):
    dec = AC3Decoder()
    for fr in frames:
        pcm, meta = dec.decode(fr)
        if use_dn:
            pcm = pcm * dialnorm_gain(meta)
        if mode == "stereo":
            pcm = downmix_stereo(pcm, meta)
        elif pcm.shape[1] != a.ch:
            raise SystemExit(f"Flux à {pcm.shape[1]} canaux, sortie à {a.ch} : utilise --mode stereo")
        a.q.put(np.clip(pcm, -1, 1).astype(np.float32))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("--mode", choices=["stereo", "5.1"], default="stereo")
    ap.add_argument("--dialnorm", action="store_true")
    o = ap.parse_args()
    frames, rate = load(o.file)
    a = AudioOut(2 if o.mode == "stereo" else 6, rate)
    threading.Thread(target=decode_thread, args=(frames, a, o.mode, o.dialnorm), daemon=True).start()
    cap = cv2.VideoCapture(o.file) if not o.file.lower().endswith(".ac3") else None
    fps = (cap.get(cv2.CAP_PROP_FPS) or 25) if cap else 25
    while a.q.qsize() < 8:
        time.sleep(0.01)
    a.stream.start(); i = 0
    while a.stream.active:
        clock = a.played / rate
        if cap is None:
            time.sleep(0.05); continue
        ok, img = cap.read()
        if not ok:
            break
        t = i / fps; i += 1
        if clock - t > 0.1:           # en retard : on saute l'affichage
            continue
        while t > a.played / rate and a.stream.active:
            time.sleep(0.002)
        cv2.imshow("lecteur AC-3", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    a.stream.stop(); cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
