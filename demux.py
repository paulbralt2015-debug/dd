"""Extraction des trames AC-3 d'un MP4/MOV (sample entry 'ac-3') ou d'un .ac3 brut."""
import mmap, struct
from ac3.decoder import frame_size

CONTAINERS = (b"moov", b"trak", b"mdia", b"minf", b"stbl")


def _boxes(b, start, end):
    p = start
    while p + 8 <= end:
        size, typ = struct.unpack(">I4s", b[p:p + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", b[p + 8:p + 16])[0]; hdr = 16
        elif size == 0:
            size = end - p
        yield typ, p + hdr, p + size
        p += size


def _find_ac3_track(b, start, end, found=None):
    """Descend récursivement ; renvoie un dict de boîtes stbl d'une piste AC-3."""
    for typ, s, e in _boxes(b, start, end):
        if typ == b"trak":
            t = {}
            _walk(b, s, e, t)
            if t.get("fmt") == b"ac-3":
                return t
        elif typ == b"moov":
            r = _find_ac3_track(b, s, e)
            if r:
                return r
    return None


def _walk(b, start, end, t):
    for typ, s, e in _boxes(b, start, end):
        if typ in CONTAINERS:
            _walk(b, s, e, t)
        elif typ == b"stsd":
            t["fmt"] = b[s + 12:s + 16]
            t["rate"] = struct.unpack(">I", b[s + 8 + 24:s + 8 + 28])[0] >> 16
        elif typ in (b"stsz", b"stsc", b"stco", b"co64"):
            t[typ] = (s, e)


def mp4_frames(path):
    """Renvoie (liste de trames bytes, fréquence d'échantillonnage)."""
    with open(path, "rb") as f:
        b = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        t = _find_ac3_track(b, 0, len(b))
        if not t:
            raise ValueError("Aucune piste AC-3 ('ac-3') dans ce MP4")
        s, _ = t[b"stsz"]
        fixed, count = struct.unpack(">II", b[s + 4:s + 12])
        sizes = [fixed] * count if fixed else list(struct.unpack(f">{count}I", b[s + 12:s + 12 + 4 * count]))
        s, _ = t[b"stsc"]
        n = struct.unpack(">I", b[s + 4:s + 8])[0]
        stsc = [struct.unpack(">3I", b[s + 8 + 12 * i:s + 20 + 12 * i]) for i in range(n)]
        key, fmt, w = (b"stco", ">I", 4) if b"stco" in t else (b"co64", ">Q", 8)
        s, _ = t[key]
        n = struct.unpack(">I", b[s + 4:s + 8])[0]
        chunks = [struct.unpack(fmt, b[s + 8 + w * i:s + 8 + w * (i + 1)])[0] for i in range(n)]
        frames, si = [], 0
        for ci, off in enumerate(chunks, 1):
            spc = [x[1] for x in stsc if x[0] <= ci][-1]
            for _ in range(spc):
                if si >= len(sizes):
                    break
                frames.append(bytes(b[off:off + sizes[si]])); off += sizes[si]; si += 1
        return frames, t["rate"] or 48000


def raw_ac3_frames(path):
    data = open(path, "rb").read()
    frames, pos = [], 0
    while pos < len(data):
        n = frame_size(data, pos)
        if not n:
            raise ValueError(f"Synchronisation perdue à l'octet {pos}")
        frames.append(data[pos:pos + n]); pos += n
    return frames, 48000


def load(path):
    return raw_ac3_frames(path) if path.lower().endswith(".ac3") else mp4_frames(path)
