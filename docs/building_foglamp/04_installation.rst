.. FogLAMP installation describes how to install FogLAMP

.. |br| raw:: html

   <br />

.. Images

.. Links

.. Links in new tabs

.. |build foglamp| raw:: html

   <a href="building_foglamp.html" target="_blank">here</a>

.. |snappy| raw:: html

   <a href="https://en.wikipedia.org/wiki/Snappy_(package_manager)" target="_blank">Snappy</a>

.. |snapcraft| raw:: html

   <a href="https://snapcraft.io" target="_blank">snapcraft.io</a>

.. |x86 Package| raw:: html

   <a href="https://s3.amazonaws.com/foglamp/snaps/x86_64/foglamp_1.0_amd64.snap" target="_blank">Snap for Intel x86_64 architecture</a>

.. |ARM Package| raw:: html

   <a href="https://s3.amazonaws.com/foglamp/snaps/armhf/foglamp_1.0_armhf.snap" target="_blank">Snap for ARM (armhf - ARM hard float) / Raspberry PI 2 & 3</a>

.. |Downloads page| raw:: html

   <a href="92_downloads.html" target="_blank">Downloads page</a>


.. =============================================


********************
FogLAMP Installation
********************

Installing FogLAMP using defaults is straightforward: depending on the usage, you may install a new version from source or from a pre-built package. In environments where the defaults do not fit, you will need to execute few more steps. This chapter describes the default installation of FogLAMP and the most common scenarios where administrators need to modify the default behavior.


Installing FogLAMP from a Build
===============================

Once you have built FogLAMP following the instructions presented |build foglamp|, you can execute the default installation with the ``make install`` command. By default, FogLAMP is installed from build in the root directory, under */usr/local/foglamp*. Since the root directory */* is a protected a system location, you will need superuser privileges to execute the command. Therefore, if you are not superuser, you should login as superuser or you should use the ``sudo`` command.

.. code-block:: console

  $ sudo make install
  mkdir -p /usr/local/foglamp
  Installing FogLAMP version 1.3.1, DB schema 2
  -- FogLAMP DB schema check OK: Info: /usr/local/foglamp is empty right now. Skipping DB schema check.
  cp VERSION /usr/local/foglamp
  cd cmake_build ; cmake /home/foglamp/FogLAMP/
  -- Boost version: 1.58.0
  -- Found the following Boost libraries:
  --   system
  --   thread
  --   chrono
  --   date_time
  --   atomic
  -- Found SQLite version 3.11.0: /usr/lib/x86_64-linux-gnu/libsqlite3.so
  -- Boost version: 1.58.0
  -- Found the following Boost libraries:
  --   system
  --   thread
  --   chrono
  --   date_time
  --   atomic
  -- Configuring done
  -- Generating done
  -- Build files have been written to: /home/foglamp/FogLAMP/cmake_build
  cd cmake_build ; make
  make[1]: Entering directory '/home/foglamp/FogLAMP/cmake_build'
  ...
  $

These are the main steps of the installation:

- Create the */usr/local/foglamp* directory, if it does not exist
- Build the code that has not been compiled and built yet
- Create all the necessary destination directories and copy the executables, scripts and configuration files
- Change the ownership of the *data* directory, if the install user is a superuser (we recommend to run FogLAMP as regular user, i.e. not as superuser).

FogLAMP is now present in */usr/local/foglamp* and ready to start. The start script is in the */usr/local/foglamp/bin* directory

.. code-block:: console

  $ cd /usr/local/foglamp/
  $ ls -l
  total 32
  drwxr-xr-x 2 root    root    4096 Apr 24 18:07 bin
  drwxr-xr-x 4 foglamp foglamp 4096 Apr 24 18:07 data
  drwxr-xr-x 4 root    root    4096 Apr 24 18:07 extras
  drwxr-xr-x 4 root    root    4096 Apr 24 18:07 plugins
  drwxr-xr-x 3 root    root    4096 Apr 24 18:07 python
  drwxr-xr-x 6 root    root    4096 Apr 24 18:07 scripts
  drwxr-xr-x 2 root    root    4096 Apr 24 18:07 services
  -rwxr-xr-x 1 root    root      37 Apr 24 18:07 VERSION
  $
  $ bin/foglamp
  Usage: foglamp {start|stop|status|reset|kill|help|version}
  $
  $ bin/foglamp help
  Usage: foglamp {start|stop|status|reset|kill|help|version}
  FogLAMP v1.3.1 admin script
  The script is used to start FogLAMP
  Arguments:
   start   - Start FogLAMP core (core will start other services).
   stop    - Stop all FogLAMP services and processes
   kill    - Kill all FogLAMP services and processes
   status  - Show the status for the FogLAMP services
   reset   - Restore FogLAMP factory settings
             WARNING! This command will destroy all your data!
   version - Print FogLAMP version
   help    - This text
  $
  $ bin/foglamp start
  Starting FogLAMP......
  FogLAMP started.
  $ 


Installing FogLAMP in a Different Destination Directory
-------------------------------------------------------

The destination directory for FogLAMP is the root directory */*.  You can change the destination by setting the *make* variable *DESTDIR*. For example, if you want to install FogLAMP in */opt* you should execute this command:

.. code-block:: console

  $ sudo make install DESTDIR=/opt
  mkdir -p /opt/usr/local/foglamp
  ...
  $ ls -l
  total 36
  drwxr-xr-x 9 root   root   4096 Dec 11 13:49 ./
  drwxr-xr-x 3 root   root   4096 Dec 11 13:49 ../
  drwxr-xr-x 2 root   root   4096 Dec 11 13:49 bin/
  drwxr-xr-x 3 ubuntu ubuntu 4096 Dec 11 13:49 data/
  drwxr-xr-x 3 root   root   4096 Dec 11 13:49 extras/
  drwxr-xr-x 3 root   root   4096 Dec 11 13:49 plugins/
  drwxr-xr-x 3 root   root   4096 Dec 11 13:49 python/
  drwxr-xr-x 6 root   root   4096 Dec 11 13:49 scripts/
  drwxr-xr-x 2 root   root   4096 Dec 11 13:49 services/
  $ 


Environment Variables
---------------------

In order to operate, FogLAMP requires two environment variables:

- **FOGLAMP_ROOT**: the root directory for FogLAMP. The default is */usr/local/foglamp*
- **FOGLAMP_DATA**: the data directory. The default is *$FOGLAMP_ROOT/data*, hence whichever value *FOGLAMP_ROOT* has plus the *data* sub-directory, or */usr/local/foglamp/data* in case *FOGLAMP_ROOT* is set as default value.

If you have installed FogLAMP in a non-default directory, you must at least set the new root directory before you start the platform. For example, supposing that the destination directory is */opt* and the package has been installed in */opt/usr/local/foglamp*, you should type:

.. code-block:: console

  $ export FOGLAMP_ROOT="/opt/usr/local/foglamp"
  $ cd /opt/usr/local/foglamp/
  $ bin/foglamp start
  Starting FogLAMP......
  FogLAMP started.
  $


The setenv.sh Script
--------------------

In the *extras/scripts* folder of the newly installed FogLAMP you can find the *setenv.sh* script. This script can be used to set the environment variables used by FogLAMP and update your PATH environment variable. |br|
You can call the script from your shell or you can add the same command to your *.profile* script:

.. code-block:: console

  $ cat /usr/local/foglamp/extras/scripts/setenv.sh
  #!/bin/sh

  ##--------------------------------------------------------------------
  ## Copyright (c) 2018 OSIsoft, LLC
  ##
  ## Licensed under the Apache License, Version 2.0 (the "License");
  ## you may not use this file except in compliance with the License.
  ## You may obtain a copy of the License at
  ##
  ##     http://www.apache.org/licenses/LICENSE-2.0
  ##
  ## Unless required by applicable law or agreed to in writing, software
  ## distributed under the License is distributed on an "AS IS" BASIS,
  ## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  ## See the License for the specific language governing permissions and
  ## limitations under the License.
  ##--------------------------------------------------------------------

  #
  # This script sets the user environment to facilitate the administration
  # of FogLAMP
  #
  # You can execute this script from shell, using for example this command:
  #
  # source /usr/local/foglamp/extras/scripts/setenv.sh
  #
  # or you can add the same command at the bottom of your profile script
  # {HOME}/.profile.
  #

  export FOGLAMP_ROOT="/usr/local/foglamp"
  export FOGLAMP_DATA="${FOGLAMP_ROOT}/data"

  export PATH="${FOGLAMP_ROOT}/bin:${PATH}"
  export LD_LIBRARY_PATH="${FOGLAMP_ROOT}/lib:${LD_LIBRARY_PATH}"

  $ source /usr/local/foglamp/extras/scripts/setenv.sh
  $


The foglamp.service Script
--------------------------

Another file available in the *extras/scripts* folder is the foglamp.service script. This script can be used to set FogLAMP as a Linux service. If you wish to do so, we recommend to install the FogLAMP package, but if you have a special build or for other reasons you prefer to work with FogLAMP built from source, this script will be quite helpful.

You can install FogLAMP as a service following these simple steps:

- After the ``make install`` command, copy *foglamp.service* with a simple name *foglamp* in the */etc/init.d* folder.
- Execute the command ``systemctl enable foglamp.service`` to enable FogLAMP as a service
- Execute the command ``systemctl start foglamp.service`` if you want to start FogLAMP

.. code-block:: console

  $ sudo cp /usr/local/foglamp/extras/scripts/foglamp.service /etc/init.d/foglamp
  $ sudo systemctl status foglamp.service
  ● foglamp.service
     Loaded: not-found (Reason: No such file or directory)
     Active: inactive (dead)
  $ sudo systemctl enable foglamp.service
  foglamp.service is not a native service, redirecting to systemd-sysv-install
  Executing /lib/systemd/systemd-sysv-install enable foglamp
  $ sudo systemctl status foglamp.service
  ● foglamp.service - LSB: FogLAMP
     Loaded: loaded (/etc/init.d/foglamp; bad; vendor preset: enabled)
     Active: inactive (dead)
       Docs: man:systemd-sysv-generator(8)
  $ sudo systemctl start foglamp.service
  $ sudo systemctl status foglamp.service
  ● foglamp.service - LSB: FogLAMP
     Loaded: loaded (/etc/init.d/foglamp; bad; vendor preset: enabled)
     Active: active (running) since Sun 2018-03-25 13:03:31 BST; 2min 8s ago
       Docs: man:systemd-sysv-generator(8)
    Process: 1661 ExecStart=/etc/init.d/foglamp start (code=exited, status=0/SUCCESS)
      Tasks: 14
     Memory: 79.5M
        CPU: 2.888s
     CGroup: /system.slice/foglamp.service
             ├─1759 python3 -m foglamp.services.core
             └─1764 /usr/local/foglamp/services/storage --address=0.0.0.0 --port=46309
  $

|br|


Installing the Debian Package
=============================

We have versions of FogLAMP available as Debian packages for you. Check the |Downloads page| to review which versions and platforms are available.


Obtaining and Installing the Debian Package
-------------------------------------------

Check the |Downloads page| to find the package to install.

Once you have downloaded the package, install it using the ``apt-get`` command. You can use ``apt-get`` to install a local Debian package and automatically retrieve all the necessary packages that are defined as pre-requisites for FogLAMP.  Note that you may need to install the package as superuser (or by using the ``sudo`` command) and move the package to the apt cache directory first (``/var/cache/apt/archives``).

For example, if you are installing FogLAMP on an Intel x86_64 machine, you can type this command to download the package:

.. code-block:: console

  $ wget https://s3.amazonaws.com/foglamp/debian/x86_64/foglamp-1.3.1-x86_64_ubuntu_16_04.deb
  --2018-04-24 18:22:08--  https://s3.amazonaws.com/foglamp/debian/x86_64/foglamp-1.3.1-x86_64_ubuntu_16_04.deb
  Resolving s3.amazonaws.com (s3.amazonaws.com)... 52.216.133.221
  Connecting to s3.amazonaws.com (s3.amazonaws.com)|52.216.133.221|:443... connected.
  HTTP request sent, awaiting response... 200 OK
  Length: 496094 (484K) [application/x-deb]
  Saving to: ‘foglamp-1.3.1-x86_64_ubuntu_16_04.deb’

  foglamp-1.3.1-x86_64_ubuntu_16_04.deb     100%[=============================================================>] 484.47K   521KB/s    in 0.9s
  2018-04-24 18:22:10 (521 KB/s) - ‘foglamp-1.3.1-x86_64_ubuntu_16_04.deb’ saved [496094/496094]
  $

We recommend to execute an *update-upgrade-update* of the system first, then you may copy the FogLAMP package in the *apt cache* directory and install it.


.. code-block:: console

  $ sudo apt update
  Hit:1 http://gb.archive.ubuntu.com/ubuntu xenial InRelease
  ...
  $ sudo apt upgrade
  ...
  $ sudo apt update
  ...
  $ sudo cp foglamp-1.3.1-x86_64_ubuntu_16_04.deb /var/cache/apt/archives/.
  ...
  $ sudo apt install /var/cache/apt/archives/foglamp-1.3.1-x86_64_ubuntu_16_04.deb
  Reading package lists... Done
  Building dependency tree
  Reading state information... Done
  Note, selecting 'foglamp' instead of '/var/cache/apt/archives/foglamp-1.3.1-x86_64_ubuntu_16_04.deb'
  The following packages were automatically installed and are no longer required:
  ...
  Unpacking foglamp (1.3.1) ...
  Setting up foglamp (1.3.1) ...
  Resolving data directory
  Data directory does not exist. Using new data directory
  Installing service script
  Generating certificate files
  Certificate files do not exist. Generating new certificate files.
  Creating a self signed SSL certificate ...
  Certificates created successfully, and placed in data/etc/certs
  Setting ownership of FogLAMP files
  Enabling FogLAMP service
  foglamp.service is not a native service, redirecting to systemd-sysv-install
  Executing /lib/systemd/systemd-sysv-install enable foglamp
  Starting FogLAMP service
  $ 

As you can see from the output, the installation automatically registers FogLAMP as a service, so it will come up at startup and it is already up and running when you complete the command.

Check the newly installed package:

.. code-block:: console

  $ sudo dpkg -l | grep foglamp
  ii  foglamp            1.3.1             amd64        FogLAMP, the open source platform for the Internet of Things
  $


You can also check the service currently running:

.. code-block:: console

  $ sudo systemctl status foglamp.service
  ● foglamp.service - LSB: FogLAMP
   Loaded: loaded (/etc/init.d/foglamp; bad; vendor preset: enabled)
   Active: active (running) since Thu 2018-05-10 03:48:20 BST; 1min 31s ago
     Docs: man:systemd-sysv-generator(8)
  Process: 1088 ExecStart=/etc/init.d/foglamp start (code=exited, status=0/SUCCESS)
    Tasks: 14
   Memory: 87.2M
      CPU: 2.603s
   CGroup: /system.slice/foglamp.service
           ├─1218 python3 -m foglamp.services.core
           └─1226 /usr/local/foglamp/services/storage --address=0.0.0.0 --port=44530

  ...
  $


Check if FogLAMP is up and running with the ``foglamp`` command:

.. code-block:: console

  $ /usr/local/foglamp/bin/foglamp status
  FogLAMP v1.3.1 running.
  FogLAMP Uptime:  162 seconds.
  FogLAMP records: 0 read, 0 sent, 0 purged.
  FogLAMP does not require authentication.
  === FogLAMP services:
  foglamp.services.core
  ...
  === FogLAMP tasks:
  ...
  $


Don't forget to add the *setenv.sh* available in the /usr/local/foglamp/extras/scripts* directory to your *.profile* user startup script if you want to have an easy access to the FogLAMP tools, and...


...Congratulations! This is all you need to do, now FogLAMP is ready to run.


Upgrading or Downgrading FogLAMP
--------------------------------

Upgrading or downgrading FogLAMP, starting from version 1.2, is as easy as installing it from scratch: simply follow the instructions in the previous section regarding the installation and the package will take care of the upgrade/downgrade path. The installation will not proceed if there is not a path to upgrade or downgrade from the currently installed version. You should still check the pre-requisites before you apply the upgrade. Clearly the old data will not be lost, there will be a schema upgrade/downgrade, if required.


Uninstalling the Debian Package
-------------------------------

Use the ``apt`` or the ``apt-get`` command to uninstall FogLAMP:

.. code-block:: console

  $ sudo apt remove foglamp
  Reading package lists... Done
  ...
  The following packages will be REMOVED
  foglamp
  0 to upgrade, 0 to newly install, 1 to remove and 2 not to upgrade.
  After this operation, 0 B of additional disk space will be used.
  Do you want to continue? [Y/n]
  (Reading database ... 211747 files and directories currently installed.)
  Removing foglamp (1.3.1) ...
  FogLAMP is currently running.
  Stop FogLAMP service.
  Kill FogLAMP.
  Remove python cache files.
  find: ‘/usr/local/foglamp/scripts/common/__pycache__’: No such file or directory
  Disable FogLAMP service.
  foglamp.service is not a native service, redirecting to systemd-sysv-install
  Executing /lib/systemd/systemd-sysv-install disable foglamp
  insserv: warning: current start runlevel(s) (empty) of script `foglamp' overrides LSB defaults (2 3 4 5).
  insserv: warning: current stop runlevel(s) (0 1 2 3 4 5 6) of script `foglamp' overrides LSB defaults (0 1 6).
  Remove FogLAMP service script
  Reset systemctl
  dpkg: warning: while removing foglamp, directory '/usr/local/foglamp' not empty so not removed
  $

The command also removes the service installed. |br| You may notice the warning in the last row of the command output: this is due to the fact that the data directory (``/usr/local/foglamp/data`` by default) has not been removed, in case an administrator might want to analyze or reuse the data.

|br|
