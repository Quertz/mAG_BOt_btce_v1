#!/bin/bash

# Pohyb po složce:
BASEDIR="`pwd`"
cd ..
ROOTDIR="`pwd`"
PROJECTNAME=`basename "$ROOTDIR"`
cd ..
# Nejdříve ze serveru odstraníme starší verze:
ssh -p 61245 jan@217.198.117.90 'rm -r /home/jan/git_repos_tests/$PROJECTNAME/*'
# Nyní naklonujeme novou verzi:
scp -r -P 61245 ./$PROJECTNAME jan@217.198.117.90:~/git_repos_tests/$PROJECTNAME

exit 0