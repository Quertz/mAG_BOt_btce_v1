#!/bin/bash

if [ -d ~/tmp ]; then
  rm -r ~/tmp/**
else
  mkdir ~/tmp
fi


mkdir ~/tmp/bot_extract

cd ../..
cp -r ./ ~/tmp/bot_extract
cd ~/tmp/bot_extract
rm -rf ./.idea
rm -rf ./.git
rm -rf ./.gitignore
rm -rf ./testy.txt
rm -rf ./settings/keys.ini
rm -rf ./**/t1.py
rm -rf ./**/t2.py
rm -rf ./**/t3.py
rm -rf ./Aplication/tests.py
rm -rf ./Aplication/Backtesting
rm -rf ./Aplication/0_databases
rm -rf ./Aplication/0_temporary
rm -rf ./Aplication/__pycache__
rm -rf ./logs/applogs/*
rm -rf ./logs/backtestlogs/*
rm -rf ./logs/connlogs/*
rm -rf ./logs/tradelogs/*

echo "###########################################################################
# Nakonfigurujte možnosti, dle svého úvážení. Na velikosti písmen záleží. #
###########################################################################

# API klíče z Btc-e.
# Ujistěte se, že jste na serveru nastavili info a trade oprávnění.

[API]
key =
secret = " > ./settings/keys.ini

echo "V souboru ~/tmp máte vyextrahovaného bota."

exit 0