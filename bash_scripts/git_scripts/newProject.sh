#!/bin/bash

# Skript je třeba umístit v kořenové složce projektu !

# Nejprve inicializujeme funkce:
init () {
git init

if [ ! -d ./Documents/ ]
then
    mkdir ./Documents/
fi

touch ./Documents/README.md
touch ./Documents/TODO.md
touch ./Documents/PREMISE.md
echo "Přidávám soubory: *.py *.sh *.ini TODO a README"
git add *.py
git add *.sh
git add *.ini
git add TODO.md
git add README.md
git add PREMISE.md
git add .placeholder
git commit -m 'initial project version'
}

gitignore () {
echo "
*.db
*.log
logs/**/*.log
.idea
.DS_Store
*.pyc
*.swp
*-journal
/**/0_databases/
/**/0_temporary/
/**/skripty/
" > .gitignore

echo "
.*.db
*.log
logs/**/*.log
.idea
.DS_Store
*.pyc
*.swp
*-journal
/**/0_databases/
/**/0_temporary/
/**/skripty/
" >> .git/info/exclude
}


# Pohyb po složce:
ROOTDIR="`pwd`"
PROJECTNAME=`basename "$ROOTDIR"`
GITNAME="$PROJECTNAME.git"

# Inicializujeme projekt:
init && gitignore && cd ..

# Extrakce
git clone --bare $PROJECTNAME $GITNAME

# Nahrání na ssh server:
scp -r -P 61245 $GITNAME jan@217.198.117.90:~/git_repos/$GITNAME || echo "

Nemůžu se připojit ke vzdálenému repozitáři ssh.

"
sleep 2s
rm -rf $GITNAME

# Návrat do ROOTDIR a remote add:
cd $ROOTDIR
git remote add origin ssh://jan@217.198.117.90:61245/home/jan/git_repos/$GITNAME

notify-send "Inicializace projektu ukončena. Nyní se smažu." || echo "

Inicializace projektu ukončena. Nyní se smažu.

"

sleep 2s

rm -f ./newProject.sh &

exit 0