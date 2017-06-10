#!/bin/bash

# Main logic
echo "Clamscan startuje." &
cd /
clamscan --remove=yes -r /
echo "Clamscan hotov." &

exit 0