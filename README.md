# ATSC A/52 (AC-3 / E-AC-3) Decoder & Player

Ce projet contient un analyseur et lecteur audio conforme à la norme **ATSC A/52:2018**.

## Compilation locale

```bash
mkdir build && cd build
cmake ..
make
./ac3_player input.ac3
```

## Compilation via GitHub Actions

Chaque push ou Pull Request déclenche la compilation automatique sous Linux, macOS et Windows.
