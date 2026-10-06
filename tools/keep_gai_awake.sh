#!/usr/bin/env bash
set -e
mkdir -p /etc/systemd/logind.conf.d
cat >/etc/systemd/logind.conf.d/90-gai-awake.conf <<'EOF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
HandleSuspendKey=ignore
HandleHibernateKey=ignore
IdleAction=ignore
EOF
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
if command -v gsettings >/dev/null 2>&1; then
  su -s /bin/bash -c 'gsettings set org.gnome.desktop.session idle-delay 0' "${SUDO_USER:-root}" 2>/dev/null || true
  su -s /bin/bash -c 'gsettings set org.gnome.desktop.screensaver lock-enabled false' "${SUDO_USER:-root}" 2>/dev/null || true
  su -s /bin/bash -c 'gsettings set org.gnome.desktop.screensaver idle-activation-enabled false' "${SUDO_USER:-root}" 2>/dev/null || true
fi
systemctl daemon-reload
systemctl restart systemd-logind
echo "G.A.I. keep-awake policy installed."
