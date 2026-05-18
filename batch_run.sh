#!/usr/bin/env bash
set -euo pipefail

mkdir -p results

(cd results && python3 ../single-image-process.py ../images/image-0001.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0002.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0003.png) &
(cd results && python3 ../single-image-process.py ../images/image-0004.png) &
wait

(cd results && python3 ../single-image-process.py ../images/image-0005.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0006.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0007.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0008.jpg) &
wait

(cd results && python3 ../single-image-process.py ../images/image-0009.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0010.jpg) &
(cd results && python3 ../single-image-process.py ../images/image-0011.jpg) &
wait
