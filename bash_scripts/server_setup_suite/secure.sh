#!/bin/bash

echo "Skript pro zabezpečení se spouští. " &&

sleep 1s

# Tělo

connectioncontrol() {
  clear
  echo "  Kontroluji připojení k internetu..."
  sleep 1s
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

update() {
  apt-get update
  apt-get -qy dist-upgrade
  apt-get autoclean
  # Install broken dependencies
  apt-get -qfy install
  dpkg --configure -a
  }

install() {
  echo "Instaluji aplikace. "
  sleep 1s
  clear
  ##### Install software #####
  appsToInstall=(
  clamav clamav-daemon clamscan clamtk clamfs
  selinux selinux-utils selinux-basics gdebi
  setools setools-gui python-setools
  lsat harden harden-doc tiger policycoreutils cryptsetup
  sepol-utils debsecan rkhunter chkrootkit
  sssd-tools sanitizer sshguard systemsettings
  )
  for app in "${appsToInstall[@]}"
  do
      apt-get install -qy "$app"
  done
  freshclam
  }

firewallcheck() {
  echo "Kontrola a instalace firewalu." &&
  sleep 1s
  apt-get install -qy --install-suggests ufw
  ufw enable
  ufw status verbose &&
  sleep 3s &&
  clear
  ufw allow ssh
  ufw allow OpenSSH
  ufw allow 61245
  echo "
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  Pozor port pro přístup k serveru je nastven na: 61245
  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  "
  sleep 10s
  clear
  ufw allow 8374
  ufw allow 31200:31299/tcp
  ufw allow 32300:32399/udp
  clear
  #Re-check enable (required):
  ufw enable
  clear
  }

chrootkitcheck() {
  echo "Kontrola chrootkitu." &&
  sleep 1s &&
  chkrootkit -q
  rkhunter --update
  rkhunter --propupd
  rkhunter -q --check
  echo "# This file controls the state of SELinux on the system.
  # SELINUX= can take one of these three values:
  # enforcing - SELinux security policy is enforced.
  # permissive - SELinux prints warnings instead of enforcing.
  # disabled - No SELinux policy is loaded.
  SELINUX=enforcing
  # SELINUXTYPE= can take one of these two values:
  # default - equivalent to the old strict and targeted policies
  # mls     - Multi-Level Security (for military and educational use)
  # src     - Custom policy built from source
  SELINUXTYPE=default

  # SETLOCALDEFS= Check local definition changes
  SETLOCALDEFS=0" > /etc/selinux/config
  bash tiger
  tigercron
  hardening-check
  }

lynis() {
cd /usr/local
if [ -d /usr/local/lynis ]; then
  rm -rf ./lynis
fi
git clone https://github.com/CISOfy/lynis
cd lynis
bash lynis update release
bash lynis audit system -Q
cd ~
  }

# Run
connectioncontrol
update
install
update
firewallcheck
chrootkitcheck
lynis
# Audit

echo "Security skript je hotov." &&

exit 0