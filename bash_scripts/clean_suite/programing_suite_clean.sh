#!/bin/bash
# Standartní, lehké vyčištění složek bota.

cd ../..
rm -rf ./Aplication/0_databases/**
rm -rf ./Aplication/0_temporary/**
rm -rf ./**/t1.py
rm -rf ./**/t2.py
rm -rf ./**/__pycache__
rm -rf ./logs/applogs/*
rm -rf ./logs/backtestlogs/*
rm -rf ./logs/connlogs/*
rm -rf ./logs/tradelogs/*

exit 0