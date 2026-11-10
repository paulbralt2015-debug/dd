"""Effets côté lecteur définis par A/52 : downmix 5.1 -> stéréo (§7.8) et dialnorm (§7.6).
Colonnes PCM attendues pour 6 canaux : L R C LFE Ls Rs (convention de ac3/decoder.py)."""
import numpy as np

CMIX = (0.707, 0.595, 0.500, 0.595)   # cmixlev 00,01,10,11(réservé)
SMIX = (0.707, 0.500, 0.0, 0.500)     # surmixlev 00,01,10,11(réservé)


def downmix_stereo(pcm, meta, lfe=False):
    """Lo/Ro compatible : Lo = L + clev*C + slev*Ls, normalisé pour éviter l'écrêtage."""
    if pcm.shape[1] == 2:
        return pcm
    if pcm.shape[1] != 6:
        raise ValueError("downmix : 2 ou 6 canaux attendus")
    c = CMIX[getattr(meta, "cmixlev", 0) & 3]
    s = SMIX[getattr(meta, "surmixlev", 0) & 3]
    k = 1.0 / (1.0 + c + s + (0.707 if lfe else 0.0))
    L, R, C, F, Ls, Rs = (pcm[:, i] for i in range(6))
    lo = L + c * C + s * Ls + (0.707 * F if lfe else 0)
    ro = R + c * C + s * Rs + (0.707 * F if lfe else 0)
    return (np.stack([lo, ro], axis=1) * k).astype(np.float32)


def dialnorm_gain(meta):
    """Gain linéaire ramenant le niveau moyen du dialogue à -31 dBFS."""
    d = getattr(meta, "dialnorm", 31) or 31
    return 10 ** ((d - 31) / 20)
