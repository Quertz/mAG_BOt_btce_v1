#!/bin/bash
#set -xn
# Skript pro řízení přístupu k aplikaci
# na konci běhu aplikace.

echo "
mAG_BOt se vypíná.
Navracím standartní přístupová práva k aplikaci.."

# Návrat práv k přístupu a vyčištění složky.
cd ..
chmod -R 700 ./**
rm -rf ./Aplication/__pycache__
rm -rf ./Aplication/**/__pycache__
rm -rf ./Aplication/0_temporary/tradespermissions.per
rm -rf ./Aplication/0_temporary/currentticker.txt
chmod -R 700 ./**

exit 0