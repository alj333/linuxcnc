# Replacement CNC PC Setup

This is the handoff for building a replacement fanless PC for the 5th Axis
XYZBC machine. The goal is to reproduce the current operational setup, not to
install a generic LinuxCNC workstation.

Captured from the current controller on 2026-06-22.

## Target Baseline

Use these versions as the first target:

```text
OS: Debian GNU/Linux 12.13 (bookworm), amd64
base-files: 12.4+deb12u13
Kernel: 6.1.0-43-rt-amd64
Kernel package: linux-image-6.1.0-43-rt-amd64 6.1.162-1
Realtime mode: PREEMPT_RT
LinuxCNC repo branch to use: alj333/head-head-kinematics-rnd
Current local LinuxCNC baseline before this guide: acdb32c3a5
```

The Debian package repository may now offer a newer Bookworm RT kernel. Match
`6.1.162-1` first if possible. If a newer Bookworm RT kernel is used, run the
latency and no-motion smoke checks before connecting motion power.

## Path Contract

Several launchers and INI files use absolute paths. Keep these paths on the
new PC unless the configs are deliberately edited and retested:

```text
/home/cnc5/linuxcnc-dev
/home/cnc5/dev/venv
/home/cnc5/dev/qtpyvcp
/home/cnc5/dev/probe_basic
```

Create the OS user as `cnc5`. Give it sudo access.

## Git Repositories In Use

LinuxCNC:

```text
Primary fork: https://github.com/alj333/linuxcnc.git
Upstream: https://github.com/LinuxCNC/linuxcnc
Remote branch for this machine: head-head-kinematics-rnd
Old-PC local branch name: head-head-kinematics-rnd-pushable
```

Probe Basic:

```text
Configured repo on the old PC: https://github.com/kcjengr/probe_basic.git
Branch: main
Captured public commit: 5a76d5a4008b0ba4242c472fc0d1ee641eff7e5e
Old-PC state: ahead of origin/main with dirty launcher edits
```

QtPyVCP, required by Probe Basic:

```text
Primary fork with local display work: https://github.com/alj333/qtpyvcp.git
Upstream: https://github.com/kcjengr/qtpyvcp.git
Branch: main
Captured public commit: 17b7803c7b7e586713bd4afc0414e7eda447e934
Old-PC state: ahead of origin/main with dirty display/backplot edits
```

For a same-machine replacement, copy the full old-PC Probe Basic and QtPyVCP
working trees if possible. Re-cloning only the public commits will miss local
dirty edits unless those edits are committed or reapplied.

## Before Retiring The Old PC

The LinuxCNC repository alone is not the entire running system. Preserve these
items from the old PC:

```text
/home/cnc5/dev/qtpyvcp
/home/cnc5/dev/probe_basic
/home/cnc5/dev/venv
/usr/share/keyrings/linuxcnc-old.gpg
/usr/share/keyrings/linuxcnc.gpg
```

The current `/home/cnc5/dev/qtpyvcp` checkout has local/ahead display fixes and
dirty files. The current `/home/cnc5/dev/probe_basic` checkout is also ahead
and dirty. For an exact replacement, copy those whole source trees instead of
re-cloning upstream only.

Runtime state files are intentionally ignored by git. Copy these if current
offsets, parameter files, and Probe Basic UI state must follow the machine:

```text
configs/5th_axis_xyzbc_ssi_maintenance/*.var*
configs/5th_axis_xyzbc_ssi_probe_basic/*.var*
configs/5th_axis_xyzbc_ssi_probe_basic/linuxcnc.var*
configs/5th_axis_xyzbc_ssi_probe_basic/.vcp_persistent_data.pickle
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/*.var*
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/rs274ngc.var
configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/.vcp_persistent_data.pickle
```

The tracked tool table is:

```text
configs/5th_axis_xyzbc_ssi_probe_basic/tool.tbl
```

## OS Install

Install Debian 12 Bookworm amd64 with a graphical desktop. During install:

- Hostname can change, but this PC currently uses `cnc5`.
- Create user `cnc5`.
- Enable sudo for `cnc5`.
- Do not connect servo enable/motion power during software setup.

Recommended BIOS/firmware starting point:

- Disable suspend, hibernate, and wake/sleep automation.
- Disable CPU deep sleep/C-states if latency is poor.
- Prefer a fixed/performance CPU profile over aggressive power saving.
- Keep Secure Boot disabled unless the RT kernel and any out-of-tree modules
  are verified under Secure Boot.

## Apt Sources

Enable Debian `deb-src` entries because the LinuxCNC build dependency command
uses them. The current controller has this LinuxCNC package source:

```text
deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/linuxcnc-old.gpg] https://www.linuxcnc.org/ bookworm base 2.9-uspace 2.9-rt
deb-src [arch=amd64,arm64 signed-by=/usr/share/keyrings/linuxcnc-old.gpg] https://www.linuxcnc.org/ bookworm base 2.9-uspace 2.9-rt
```

If the key files were copied from the old PC, install them under
`/usr/share/keyrings/` before `apt update`.

Install the RT kernel and base tools:

```bash
sudo apt update
sudo apt install -y linux-image-rt-amd64 iptables git curl ca-certificates \
  build-essential dpkg-dev fakeroot devscripts python3-venv python3-pip \
  mesaflash network-manager
sudo reboot
```

After reboot, confirm the RT kernel:

```bash
uname -a
cat /etc/debian_version
```

Expected first target:

```text
Debian: 12.13
Kernel includes: PREEMPT_RT
Kernel package family: linux-image-rt-amd64
```

## Clone LinuxCNC

```bash
cd /home/cnc5
git clone -b head-head-kinematics-rnd https://github.com/alj333/linuxcnc.git linuxcnc-dev
cd /home/cnc5/linuxcnc-dev
git remote -v
git status --short --branch
```

The local branch name on the old PC is `head-head-kinematics-rnd-pushable`, but
it pushes to the remote branch `alj333/head-head-kinematics-rnd`. The new PC
should use the remote branch.

## Install Build Dependencies

From the LinuxCNC checkout:

```bash
cd /home/cnc5/linuxcnc-dev
sudo apt build-dep -y .
sudo apt install -y iptables mesa-utils python3-pyqt5 python3-pyqt5.qsci \
  python3-pyqt5.qtsvg python3-pyqt5.qtopengl python3-pyqt5.qtwebengine \
  python3-opencv python3-dbus python3-dbus.mainloop.pyqt5 python3-espeak \
  python3-numpy python3-cairo python3-gi-cairo python3-opengl \
  python3-configobj python3-serial python3-lxml python3-yaml python3-psutil \
  python3-scipy python3-pandas pyqt5-dev-tools gstreamer1.0-tools
```

`iptables` is required. This machine previously failed during `hm2_eth`
startup when `/usr/sbin/iptables` was missing.

## Restore Or Rebuild QtPyVCP And Probe Basic

Preferred exact replacement:

```bash
mkdir -p /home/cnc5/dev
# Copy these from the old PC, preserving ownership and git state:
# /home/cnc5/dev/qtpyvcp
# /home/cnc5/dev/probe_basic
# /home/cnc5/dev/venv
```

If the old trees cannot be copied, reconstruct the known public commits first,
then expect to reapply local display/launcher patches before calling the setup
complete:

```bash
mkdir -p /home/cnc5/dev
git clone https://github.com/kcjengr/qtpyvcp.git /home/cnc5/dev/qtpyvcp
git -C /home/cnc5/dev/qtpyvcp checkout 17b7803c7b7e586713bd4afc0414e7eda447e934

git clone https://github.com/kcjengr/probe_basic.git /home/cnc5/dev/probe_basic
git -C /home/cnc5/dev/probe_basic checkout 5a76d5a4008b0ba4242c472fc0d1ee641eff7e5e

python3 -m venv --system-site-packages /home/cnc5/dev/venv
source /home/cnc5/dev/venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e /home/cnc5/dev/qtpyvcp
python -m pip install -e /home/cnc5/dev/probe_basic
```

On the current controller, `pip freeze` reports editable installs for:

```text
qtpyvcp @ /home/cnc5/dev/qtpyvcp
probe_basic @ /home/cnc5/dev/probe_basic
```

## Build LinuxCNC Run-In-Place

```bash
cd /home/cnc5/linuxcnc-dev/src
./autogen.sh
./configure --with-realtime=uspace --disable-build-documentation
make -j"$(nproc)"
sudo make setuid
```

Verify basic commands:

```bash
cd /home/cnc5/linuxcnc-dev
source scripts/rip-environment
halrun -h
linuxcnc -h
```

## Mesa Ethernet Setup

The real machine config loads the Mesa 7i95 using:

```hal
loadrt hm2_eth board_ip="10.10.10.10"
```

Use a dedicated Ethernet port for Mesa. Give the PC side a static address in
the same subnet, with no gateway on that connection. Example:

```bash
nmcli device status
sudo nmcli con add type ethernet ifname <mesa-nic> con-name MESA \
  ipv4.method manual ipv4.addresses 10.10.10.1/24 ipv6.method disabled \
  connection.autoconnect yes
sudo nmcli con up MESA
ping -c 2 10.10.10.10
```

Replace `<mesa-nic>` with the actual Ethernet device on the new PC. Keep the
internet connection on a separate interface.

## Desktop Launchers

The primary TCPC Probe Basic launcher is:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/launch_xyzbc_ssi_tcpc_probe_basic.sh
```

The non-TCPC Probe Basic launcher is:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_probe_basic/launch_xyzbc_ssi_probe_basic.sh
```

The locked AXIS maintenance fallback is:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_maintenance/launch_xyzbc_ssi_maintenance.sh
```

Optional desktop entry:

```bash
cp /home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/'TCPC Trim Work.desktop' \
  /home/cnc5/Desktop/
chmod +x /home/cnc5/Desktop/'TCPC Trim Work.desktop'
```

## Software Verification Before Machine Power

Run these before connecting/energizing the machine:

```bash
cd /home/cnc5/linuxcnc-dev
git status --short --branch
uname -a
source scripts/rip-environment

cd /home/cnc5/linuxcnc-dev/tests/kinematics/head-head-tcpc-entry-exit
rm -f sim.var
/home/cnc5/linuxcnc-dev/scripts/rip-environment linuxcnc -r test.ini
```

Then launch the sim config and confirm the UI opens:

```bash
/home/cnc5/linuxcnc-dev/configs/sim/head_head_5axis/launch_probe_basic.sh
```

## First Hardware Launch

Initial real-machine launch should be done with drives disabled or with the
machine held in a state where unexpected motion cannot occur.

Checklist:

- Mesa ping to `10.10.10.10` passes.
- E-stop chain works.
- Servo/motion power is off for the first LinuxCNC start.
- Probe Basic opens without `hm2_eth` or `iptables` errors.
- TCPC status starts fail-safe as `TCPC OFF`.
- HAL shows B/C SSI channels valid before trusting rotary homing.

Start:

```bash
/home/cnc5/linuxcnc-dev/configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/launch_xyzbc_ssi_tcpc_probe_basic.sh
```

After LinuxCNC starts, verify no fresh error in the terminal or
`/tmp/linuxcnc.print.*`.

## Commissioning Checks

Do these in order, stopping on any unexpected result:

1. Home X/Y/Z/B/C with motion power available and feed override low.
2. Confirm B/C homing uses SSI absolute positions and does not redefine rotary
   zero at the current angle.
3. Run the no-motion B/C zero check when B/C are physically expected at zero:

   ```text
   nc_files/calibration/rotary_ssi_zero_verify.ngc
   ```

4. Confirm the active tool table values match the tracked
   `configs/5th_axis_xyzbc_ssi_probe_basic/tool.tbl`.
5. Run the TCPC production entry/exit smoke only after homing and tool state
   are understood:

   ```text
   nc_files/calibration/tcpc_production_entry_exit_smoke.ngc
   ```

6. Keep `G68.2` TWP production use disabled until the current TCPC/TWP notes in
   `configs/5th_axis_xyzbc_ssi_tcpc_probe_basic/README.md` say otherwise.

## Codex Handoff Prompt

Use this prompt on the new PC after installing Debian and Codex:

```text
Read /home/cnc5/linuxcnc-dev/docs/replacement-cnc-pc-setup.md and execute the
setup for the replacement CNC controller. Preserve the /home/cnc5 paths. Do not
energize motion power until the RT kernel, LinuxCNC build, QtPyVCP/Probe Basic
environment, Mesa Ethernet, and no-motion checks pass. Stop and report any
missing old-PC artifacts, dirty external QtPyVCP/Probe Basic patches, or
version mismatches before real machine motion.
```
