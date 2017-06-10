#!/bin/bash
#set -xn
# Skript pro řízení přístupu k aplikaci
# na začátku běhu aplikace.

echo "
mAG_BOt se spouští.
Měním přístupová práva k aplikaci."

# Příprava složky
chmod -R 700 ./**
cd ..
chmod -R 700 ./**

# Odstranění starých složek.
rm -rf ./logs
rm -rf ./Aplication/__pycache__
rm -rf ./Aplication/**/__pycache__
rm -rf ./Aplication/0_databases
rm -rf ./Aplication/0_temporary

# Tvorba nových složek.
mkdir ./Aplication/0_databases
mkdir ./Aplication/0_temporary
mkdir ./logs
mkdir ./logs/applogs
mkdir ./logs/backtestlogs
mkdir ./logs/connlogs
mkdir ./logs/tradelogs

# Řízení práv k přístupu.
chmod -R 700 ./**
chmod -R 500 ./Aplication/*
chmod -R 700 ./Aplication/0_databases
chmod -R 700 ./Aplication/0_temporary
chmod -R 400 ./settings/*
chmod -R 500 ./bash_scripts/*

exit 0