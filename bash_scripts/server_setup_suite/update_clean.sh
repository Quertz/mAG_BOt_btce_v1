#!/bin/bash

# Main logic
clear
echo "  Kontrola připojení k internetu..."
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
      echo "  Kontrola připojení k internetu selhala!"
      echo ""
      echo "  Tento skript vyžaduje funkční připojení k internetu."
      echo "  Prosím nakonfigurujte své připojení.."
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

apt-get update
apt-get -qy dist-upgrade
apt-get autoclean
# Install broken dependencies
apt-get -qfy install
dpkg --configure -a

OLDCONF=$(dpkg -l|grep "^rc"|awk '{print $2}')
YELLOW="\033[1;33m"
ENDCOLOR="\033[0m"
echo -e "$YELLOW""Čištění apt cache...""$ENDCOLOR"
aptitude clean -yf
echo -e "$YELLOW""Odstraňování starých konfiguračních souborů...""$ENDCOLOR"
aptitude purge -yf "$OLDCONF"
echo -e "$YELLOW""Odstraňuji staré kernely...""$ENDCOLOR"
aptitude purge -yf "$OLDKERNELS"
echo -e "$YELLOW""Vyprazdňuji všechny koše...""$ENDCOLOR"
rm -rf /home/*/.local/share/Trash/*/** &> /dev/null
rm -rf /home/*/tmp/*/** &> /dev/null
rm -rf /root/.local/share/Trash/*/** &> /dev/null
rm -rf /home/.Trash*/*/** &> /dev/null
rm -rf /*/**/.Trash-1000
rm -rf /home/"$USER"/tmp/* &> /dev/null
rm -rf /home/"$USER"/tmp/.* &> /dev/null
rm -rf /home/"$USER"/.cache* &> /dev/null
rm -rf /home/"$USER"/.config/**/Application*Cache/* &> /dev/null
rm -rf /**/tmp/* &> /dev/null
rm -rf /home/"$USER"/.backup/* &> /dev/null
rm -rf /home/"$USER"/.backup/.* &> /dev/null
echo -e "$YELLOW""Aktualizuji systém...""$ENDCOLOR"
apt-get update
apt-get -yfm autoclean
apt-get autoremove -yfm
aptitude purge ~c
dpkg --configure -a
echo -e "$YELLOW""Aktualizuji grub...""$ENDCOLOR"
update-grub
echo -e "$YELLOW""Skript skončil!""$ENDCOLOR"
touch /forcefsck
sleep 1s

exit 0