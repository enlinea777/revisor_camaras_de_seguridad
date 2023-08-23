#!/bin/bash
contador=1

for archivo in *.mp4; do
    nuevo_nombre="$contador.mp4"
    mv "$archivo" "$nuevo_nombre"
    contador=$((contador + 1))
done

# unir los mp4 en uno
# ffmpeg -f concat -safe 0 -i <(for f in *.mp4; do echo "file '$PWD/$f'"; done) -c copy output.mp4
