#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
from pwd import getpwnam
from grp import getgrnam
from setuptools.command.install import install
from setuptools import setup
from subprocess import run

if not sys.platform.startswith("linux"):
    print("Wamp wamp, linux only")
    sys.exit(1)

if not os.getuid() == 0:
    print("You ain't root, you don't got the power!")
    sys.exit(1)

if not sys.version_info >= (3, 6):
    print("Must be run with Python 3.6+")
    sys.exit(1)


class PymoteInstall(install):

    def run(self):
        print("We are hijacking your usual install "
              "and doing it the way we want")
        current_dir_path = os.path.dirname(os.path.realpath(__file__))
        os.chdir(current_dir_path)

        print(" - Installing the service")
        with open("pymote_control.service") as f:
            data = f.read()
        with open("/lib/systemd/system/pymote_control.service", "w") as f:
            f.write(data.format(install_dir=current_dir_path))
        os.chown("/lib/systemd/system/pymote_control.service", 0, 0)

        print(" - Enabling the service")
        run("systemctl daemon-reload", shell=True)
        run("systemctl enable pymote_control.service", shell=True)

        print(" - Adding a system user 'pymote' ")
        run("useradd --system pymote", shell=True)
        run("groupadd pymote", shell=True)
        run("usermod -a -G pymote pymote", shell=True)
        uid = getpwnam('pymote').pw_uid
        gid = getgrnam('pymote').gr_gid
        os.chown(current_dir_path, uid, gid)
        os.setgid(gid)
        os.setuid(uid)

        print(" - Creating a new virtual env")
        major, minor, *_ = sys.version_info
        run(f"python{major}.{minor} -m venv .pymote_venv", shell=True)

        print(" - Installing the goods")
        run(".pymote_venv/bin/pip install --no-cache -r requirements.txt",
            shell=True)

        print("Setup complete!")

setup(
    name='pymote_control',
    version='1.0.0',
    cmdclass={'install': PymoteInstall}
)
