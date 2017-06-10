#!/bin/bash
#set -xn
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

connectioncontrol() {
  clear
  echo "  Kontroluji připojení k internetu..."
  sleep 2s
  echo ""
  # Check the connection by downloading a file from ftp.debian.org. No disk space used.
  if ! wget -O - http://ftp.debian.org/debian/README &> /dev/null
  then
    until [ "$CONT" != "" ]; do
      echo ""
      if ! wget -O - http://ftp.debian.org/debian/README &> /dev/null
      then
        clear
        echo "  Nemáte funkční připojení k internetu!"
        echo ""
        echo "  Tento skript vyžaduje funkční připojení k internetu."
        echo "  Prosím nastavte své připojení."
        clear
        echo "Skript byl přerušen."
        sleep 3s
        exit 0
      else
        CONT="pass"
      fi
    done
  fi
  clear
  echo "  Test připojení k internetu prošel..."
  sleep 2s
  }

update () {
apt-get update
apt-get -qy dist-upgrade
apt-get autoclean
# Install broken dependencies
apt-get -qfy install
dpkg --configure -a
}

dependencies () {

##### Install Python software #####
appsToInstall=(
python3-numpy cython3 cython3-dbg libxml2-dev libxslt1-dev
libevent-dev python3-distlib python3-dev locales
)
for app in "${appsToInstall[@]}"
do
    apt-get install -qy -install--suggests "$app"
done

##### Install software #####
appsToInstall=(
python3-pip python3-distlib gcc python3-dev build-essential cmake
autoconf automake pkg-config libtool libzip-dev libxml2-dev
libsigc++-2.0-dev libglade2-dev libgtkmm-2.4-dev libglu1-mesa-dev
libgl1-mesa-glx mesa-common-dev libmysqlclient-dev locales
libmysqlcppconn-dev uuid-dev liblua5.1-dev libpixman-1-dev
libpcre3-dev libgnome2-dev python-dev libgnome-keyring-dev
libgtk2.0-dev libpango1.0-dev libcairo2-dev python-dev libboost-dev
libctemplate-dev mysql-client python-pysqlite2 libsqlite3-dev iodbc
libiodbc2 libiodbc2-dev libtinyxml-dev python3-scipy
htop wget openssh-server openssh-client git clamav screen
)
for app in "${appsToInstall[@]}"
do
    apt-get install -yqf "$app"
done
}

systalib () {
# Install base ta-lib systemwide (sudo)
if [ -d /usr/local/lib ]
then
    cd /usr/local/lib
else
    if [ -d /usr/lib ]
    then
        cd /usr/lib
    fi
fi
rm -rf ./ta-lib*
sleep 1s
wget http://freefr.dl.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz || wget http://softlayer-ams.dl.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz && tar -xvzf *.tar.gz && rm -rf *.tar.gz
sleep 1s
cd ta-lib
./configure --prefix=/usr
make
make install
sleep 1s
pip3 install TA-Lib
}


############################### Body:



clear
sleep 1s
echo "

        Začínám aktualizovat a instalovat závislosti...


        "

connectioncontrol

update

clear

dependencies

clear

update

sleep 1s

echo "

        Stahuji Syswide Talib a instaluji local Talib...


        "

systalib

clear

sleep 1s

echo "

        Hotovo...


        "

sleep 1s

apt-get install console-data
apt-get install console-setup
apt-get install console-locales
apt-get install keyboard-configuration


sleep 2s

clear

echo "


Nyní budeme konfigurovat system wide locales.

Nastavíme kódování UTF-8 unicode pro celý systém.

Je důležité toto dělat opatrně.!

Jako výchozí kódování nastavte en.US_UTF8
a jako sekundární nastavte cs.CZ-UTF8 !!!
Neprohodit !!!


"

sleep 5s

dpkg-reconfigure locales

sleep 2s

source ~/.bashrc

screen bash secure.sh

exit 0