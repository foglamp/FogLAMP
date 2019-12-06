###############################################################################
################################### COMMANDS ##################################
###############################################################################
# Check RedHat || CentOS
$(eval PLATFORM_RH=$(shell (lsb_release -ds 2>/dev/null || cat /etc/*release 2>/dev/null | head -n1 || uname -om) | egrep '(Red Hat|CentOS)'))

# Log Platform RedHat || CentOS
$(if $(PLATFORM_RH), $(info Platform is $(PLATFORM_RH)))

# For RedHat || CentOS we need rh-python36
ifneq ("$(PLATFORM_RH)","")
	PIP_INSTALL_REQUIREMENTS := source scl_source enable rh-python36 && pip3 install -Ir
	PYTHON_BUILD_PACKAGE = source scl_source enable rh-python36 && python3 setup.py build -b ../$(PYTHON_BUILD_DIR)
	CMAKE := source scl_source enable rh-python36 && cmake
else
	PIP_INSTALL_REQUIREMENTS := pip3 install -Ir
	PYTHON_BUILD_PACKAGE = python3 setup.py build -b ../$(PYTHON_BUILD_DIR)
	CMAKE := cmake
endif

MKDIR_PATH := mkdir -p
CD := cd
LN := ln -sf
PIP_USER_FLAG = --user
USE_PIP_CACHE := no

RM_DIR := rm -r
RM_FILE := rm
MAKE_INSTALL = $(MAKE) install
CP            := cp
CP_DIR        := cp -r
SSL_NAME      := "foglamp"
AUTH_NAME     := "ca"
SSL_DAYS      := "365"

###############################################################################
################################### DIRS/FILES ################################
###############################################################################
# PARENT DIR
MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
CURRENT_DIR := $(dir $(MKFILE_PATH))

# C BUILD DIRS/FILES
CMAKE_FILE               := $(CURRENT_DIR)/CMakeLists.txt
CMAKE_BUILD_DIR          := cmake_build
CMAKE_GEN_MAKEFILE       := $(CURRENT_DIR)/$(CMAKE_BUILD_DIR)/Makefile
CMAKE_SERVICES_DIR       := $(CURRENT_DIR)/$(CMAKE_BUILD_DIR)/C/services
CMAKE_TASKS_DIR          := $(CURRENT_DIR)/$(CMAKE_BUILD_DIR)/C/tasks
CMAKE_STORAGE_BINARY     := $(CMAKE_SERVICES_DIR)/storage/foglamp.services.storage
CMAKE_SOUTH_BINARY       := $(CMAKE_SERVICES_DIR)/south/foglamp.services.south
CMAKE_NORTH_BINARY       := $(CMAKE_TASKS_DIR)/north/sending_process/sending_process
CMAKE_PLUGINS_DIR        := $(CURRENT_DIR)/$(CMAKE_BUILD_DIR)/C/plugins
DEV_SERVICES_DIR         := $(CURRENT_DIR)/services
DEV_TASKS_DIR            := $(CURRENT_DIR)/tasks
SYMLINK_PLUGINS_DIR      := $(CURRENT_DIR)/plugins
SYMLINK_STORAGE_BINARY   := $(DEV_SERVICES_DIR)/foglamp.services.storage
SYMLINK_SOUTH_BINARY     := $(DEV_SERVICES_DIR)/foglamp.services.south
SYMLINK_NORTH_BINARY     := $(DEV_TASKS_DIR)/sending_process
ASYNC_INGEST_PYMODULE    := $(CURRENT_DIR)/python/async_ingest.so*
FILTER_INGEST_PYMODULE    := $(CURRENT_DIR)/python/filter_ingest.so*

# PYTHON BUILD DIRS/FILES
PYTHON_SRC_DIR := python
PYTHON_BUILD_DIR := python_build_dir
PYTHON_LIB_DIR := $(PYTHON_BUILD_DIR)/lib
PYTHON_REQUIREMENTS_FILE := $(PYTHON_SRC_DIR)/requirements.txt
PYTHON_SETUP_FILE := $(PYTHON_SRC_DIR)/setup.py

# DATA AND ETC DIRS/FILES
DATA_SRC_DIR := data

# INSTALL DIRS
INSTALL_DIR=$(DESTDIR)/usr/local/foglamp
PYTHON_INSTALL_DIR=$(INSTALL_DIR)/python
SCRIPTS_INSTALL_DIR=$(INSTALL_DIR)/scripts
BIN_INSTALL_DIR=$(INSTALL_DIR)/bin
EXTRAS_INSTALL_DIR=$(INSTALL_DIR)/extras
SCRIPT_COMMON_INSTALL_DIR = $(SCRIPTS_INSTALL_DIR)/common
SCRIPT_PLUGINS_STORAGE_INSTALL_DIR = $(SCRIPTS_INSTALL_DIR)/plugins/storage
SCRIPT_SERVICES_INSTALL_DIR = $(SCRIPTS_INSTALL_DIR)/services
SCRIPT_TASKS_INSTALL_DIR = $(SCRIPTS_INSTALL_DIR)/tasks
FOGBENCH_PYTHON_INSTALL_DIR = $(EXTRAS_INSTALL_DIR)/python

# DB schema update
SQLITE_SCHEMA_UPDATE_SCRIPT_SRC := scripts/plugins/storage/sqlite/schema_update.sh
POSTGRES_SCHEMA_UPDATE_SCRIPT_SRC := scripts/plugins/storage/postgres/schema_update.sh
POSTGRES_SCHEMA_UPDATE_DIR := $(SCRIPTS_INSTALL_DIR)/plugins/storage/postgres
SQLITE_SCHEMA_UPDATE_DIR := $(SCRIPTS_INSTALL_DIR)/plugins/storage/sqlite

# SCRIPTS TO INSTALL IN BIN DIR
FOGBENCH_SCRIPT_SRC        := scripts/extras/fogbench
FOGLAMP_SCRIPT_SRC         := scripts/foglamp
FOGLAMP_UPDATE_SRC         := scripts/extras/foglamp_update
UPDATE_TASK_APT_SRC        := scripts/extras/update_task.apt
UPDATE_TASK_SNAPPY_SRC     := scripts/extras/update_task.snappy
SUDOERS_SRC                := scripts/extras/foglamp.sudoers
SUDOERS_SRC_RH             := scripts/extras/foglamp.sudoers_rh

# SCRIPTS TO INSTALL IN SCRIPTS DIR
COMMON_SCRIPTS_SRC          := scripts/common
POSTGRES_SCRIPT_SRC         := scripts/plugins/storage/postgres.sh
SQLITE_SCRIPT_SRC           := scripts/plugins/storage/sqlite.sh
SOUTH_SCRIPT_SRC            := scripts/services/south
SOUTH_C_SCRIPT_SRC          := scripts/services/south_c
STORAGE_SERVICE_SCRIPT_SRC  := scripts/services/storage
STORAGE_SCRIPT_SRC          := scripts/storage
NORTH_SCRIPT_SRC            := scripts/tasks/north
NORTH_C_SCRIPT_SRC          := scripts/tasks/north_c
NOTIFICATION_C_SCRIPT_SRC   := scripts/services/notification_c
PURGE_SCRIPT_SRC            := scripts/tasks/purge
STATISTICS_SCRIPT_SRC       := scripts/tasks/statistics
BACKUP_SRC                  := scripts/tasks/backup
RESTORE_SRC                 := scripts/tasks/restore
CHECK_CERTS_TASK_SCRIPT_SRC := scripts/tasks/check_certs
CERTIFICATES_SCRIPT_SRC     := scripts/certificates
AUTH_CERTIFICATES_SCRIPT_SRC := scripts/auth_certificates
PACKAGE_UPDATE_SCRIPT_SRC   := scripts/package

# Custom location of SQLite3 library
FOGLAMP_HAS_SQLITE3_PATH    := /tmp/foglamp-sqlite3-pkg/src

# EXTRA SCRIPTS
EXTRAS_SCRIPTS_SRC_DIR      := extras/scripts

# FOGBENCH
FOGBENCH_PYTHON_SRC_DIR     := extras/python/fogbench

# FogLAMP Version file
FOGLAMP_VERSION_FILE        := VERSION

###############################################################################
################################### OTHER VARS ################################
###############################################################################
# ETC
PACKAGE_NAME=FogLAMP

###############################################################################
############################ PRIMARY TARGETS ##################################
###############################################################################
# default
# compile any code that must be compiled
# generally prepare the development tree to allow for core to be run
default : apply_version \
	generate_selfcertificate \
	c_build $(SYMLINK_STORAGE_BINARY) $(SYMLINK_SOUTH_BINARY) $(SYMLINK_NORTH_BINARY) $(SYMLINK_PLUGINS_DIR) \
	python_build python_requirements_user

apply_version :
# VERSION : this file contains FogLAMP app version and FogLAMP DB schema revision
#
# Example:
# foglamp_version=1.2
# foglamp_schema=3
#
# Note: variable names are case insensitive, all spaces are removed
# Get variables and export FOGLAMP_VERSION and FOGLAMP_SCHEMA
	$(eval FOGLAMP_VERSION := $(shell cat $(FOGLAMP_VERSION_FILE) | tr -d ' ' | grep -i "FOGLAMP_VERSION=" | sed -e 's/\(.*\)=\(.*\)/\2/g'))
	$(eval FOGLAMP_SCHEMA := $(shell cat $(FOGLAMP_VERSION_FILE) | tr -d ' ' | grep -i "FOGLAMP_SCHEMA=" | sed -e 's/\(.*\)=\(.*\)/\2/g'))
	$(if $(FOGLAMP_VERSION),$(eval FOGLAMP_VERSION=$(FOGLAMP_VERSION)),$(error FOGLAMP_VERSION is not set, check VERSION file))
	$(if $(FOGLAMP_SCHEMA),$(eval FOGLAMP_SCHEMA=$(FOGLAMP_SCHEMA)),$(error FOGLAMP_SCHEMA is not set, check VERSION file))

# Print build or install message based on MAKECMDGOALS var
ifeq ($(MAKECMDGOALS),install)
	$(eval ACTION="Installing")
else
	$(eval ACTION="Building")
endif
	@echo "$(ACTION) $(PACKAGE_NAME) version $(FOGLAMP_VERSION), DB schema $(FOGLAMP_SCHEMA)"

# Use cache for python requirements depending on the value of USE_PIP_CACHE
ifeq ($(USE_PIP_CACHE), yes)
    $(eval NO_CACHE_DIR=)
else
    $(eval NO_CACHE_DIR= --no-cache-dir)
endif

# Check where this FogLAMP can be installed over an existing one:
schema_check : apply_version
###
# Call check_schema_update.sh (param 1 is installed FogLAMP VERSION file path, param2 is the new VERSION file path)
# and grab it's output
# Note: DATA_INSTALL_DIR is passed to the called script via export
###
	@$(eval SCHEMA_CHANGE_OUTPUT=$(shell export DATA_INSTALL_DIR=$(DATA_INSTALL_DIR); scripts/common/check_schema_update.sh "$(INSTALL_DIR)/${FOGLAMP_VERSION_FILE}" "${FOGLAMP_VERSION_FILE}"))

# Check for "error" "warning"
	@$(eval SCHEMA_CHANGE_ERROR=$(shell echo $(SCHEMA_CHANGE_OUTPUT) | grep -i error))
	@$(eval SCHEMA_CHANGE_WARNING=$(shell echo $(SCHEMA_CHANGE_OUTPUT) | grep -i warning))

# Abort, print warning or info message
	$(if $(SCHEMA_CHANGE_ERROR),$(error FogLAMP DB schema cannot be performed as pre-install task: $(SCHEMA_CHANGE_ERROR)),)
	$(if $(SCHEMA_CHANGE_WARNING),$(warning $(SCHEMA_CHANGE_WARNING)),$(info -- FogLAMP DB schema check OK: $(SCHEMA_CHANGE_OUTPUT)))

#
# install
# Creates a deployment structure in the default destination, /usr/local/foglamp
# Destination may be overridden by use of the DESTDIR=<location> directive
# This first does a make to build anything needed for the installation.
install : $(INSTALL_DIR) \
	generate_selfcertificate \
	schema_check \
	foglamp_version_file_install \
	c_install \
	python_install \
	python_requirements \
	scripts_install \
	bin_install \
	extras_install \
	data_install 

###############################################################################
############################ PRE-REQUISITE SCRIPTS ############################
###############################################################################
generate_selfcertificate:
	scripts/certificates $(SSL_NAME) $(SSL_DAYS)
	scripts/auth_certificates ca $(AUTH_NAME) $(SSL_DAYS)
	scripts/auth_certificates user user $(SSL_DAYS)
	scripts/auth_certificates user admin $(SSL_DAYS)

###############################################################################
############################ C BUILD/INSTALL TARGETS ##########################
###############################################################################
# run make execute makefiles producer by cmake
c_build : $(CMAKE_GEN_MAKEFILE)
	$(CD) $(CMAKE_BUILD_DIR) ; $(MAKE)
# Local copy of sqlite3 command line tool if needed
# Copy the cmd line tool into sqlite plugin dir
ifneq ("$(wildcard $(FOGLAMP_HAS_SQLITE3_PATH))","")
	$(info  SQLite3 package has been found in $(FOGLAMP_HAS_SQLITE3_PATH))
	$(CP) $(FOGLAMP_HAS_SQLITE3_PATH)/sqlite3 $(CMAKE_PLUGINS_DIR)/storage/sqlite/
endif

# run cmake to generate makefiles
# always rerun cmake because:
#   parent CMakeLists.txt may have changed
#   CMakeLists.txt files in subdirectories may have changed
$(CMAKE_GEN_MAKEFILE) : $(CMAKE_FILE) $(CMAKE_BUILD_DIR)
	$(CD) $(CMAKE_BUILD_DIR) ; $(CMAKE) $(CURRENT_DIR)

# create build dir
$(CMAKE_BUILD_DIR) :
	$(MKDIR_PATH) $@

# create symlink to storage binary
$(SYMLINK_STORAGE_BINARY) : $(DEV_SERVICES_DIR)
	$(LN) $(CMAKE_STORAGE_BINARY) $(SYMLINK_STORAGE_BINARY)

# create symlink to south binary
$(SYMLINK_SOUTH_BINARY) : $(DEV_SERVICES_DIR)
	$(LN) $(CMAKE_SOUTH_BINARY) $(SYMLINK_SOUTH_BINARY)

# create services dir
$(DEV_SERVICES_DIR) :
	$(MKDIR_PATH) $(DEV_SERVICES_DIR)

# create symlink to sending_process binary
$(SYMLINK_NORTH_BINARY) : $(DEV_TASKS_DIR)
	$(LN) $(CMAKE_NORTH_BINARY) $(SYMLINK_NORTH_BINARY)

# create tasks dir
$(DEV_TASKS_DIR) :
	$(MKDIR_PATH) $(DEV_TASKS_DIR)

# create symlink for plugins dir
$(SYMLINK_PLUGINS_DIR) :
	$(LN) $(CMAKE_PLUGINS_DIR) $(SYMLINK_PLUGINS_DIR)

# run make install on cmake based components
c_install : c_build
	$(CD) $(CMAKE_BUILD_DIR) ; $(MAKE_INSTALL)

###############################################################################
###################### PYTHON BUILD/INSTALL TARGETS ###########################
###############################################################################
# build python source
python_build : $(PYTHON_SETUP_FILE)
	$(CD) $(PYTHON_SRC_DIR) ; $(PYTHON_BUILD_PACKAGE) ; $(CD) $(CURRENT_DIR) ; $(CP) $(PYTHON_REQUIREMENTS_FILE) $(PYTHON_LIB_DIR)/.

# install python requirements without --user
python_requirements : $(PYTHON_REQUIREMENTS_FILE)
	$(PIP_INSTALL_REQUIREMENTS) $(PYTHON_REQUIREMENTS_FILE) $(NO_CACHE_DIR)

# install python requirements for user
python_requirements_user : $(PYTHON_REQUIREMENTS_FILE)
	$(PIP_INSTALL_REQUIREMENTS) $(PYTHON_REQUIREMENTS_FILE) $(PIP_USER_FLAG) $(NO_CACHE_DIR)

# create python install dir
$(PYTHON_INSTALL_DIR) :
	$(MKDIR_PATH) $@

# copy python package into install dir
python_install : python_build $(PYTHON_INSTALL_DIR)
	$(CP_DIR) $(PYTHON_LIB_DIR)/* $(PYTHON_INSTALL_DIR)

# copy FogLAMP version info file into install dir
foglamp_version_file_install :
	$(CP) $(FOGLAMP_VERSION_FILE) $(INSTALL_DIR)

###############################################################################
###################### SCRIPTS INSTALL TARGETS ################################
###############################################################################
# install scripts
scripts_install : $(SCRIPTS_INSTALL_DIR) \
	install_common_scripts \
	install_postgres_script \
	install_sqlite_script \
	install_south_script \
	install_south_c_script \
	install_storage_service_script \
	install_north_script \
	install_north_c_script \
	install_notification_c_script \
	install_purge_script \
	install_statistics_script \
	install_storage_script \
	install_backup_script \
	install_restore_script \
	install_check_certificates_script \
	install_certificates_script \
	install_auth_certificates_script \
	install_package_update_script

# create scripts install dir
$(SCRIPTS_INSTALL_DIR) :
	$(MKDIR_PATH) $@

install_common_scripts : $(SCRIPT_COMMON_INSTALL_DIR) $(COMMON_SCRIPTS_SRC)
	$(CP) $(COMMON_SCRIPTS_SRC)/*.sh $(SCRIPT_COMMON_INSTALL_DIR)
	$(CP) $(COMMON_SCRIPTS_SRC)/*.py $(SCRIPT_COMMON_INSTALL_DIR)

install_postgres_script : $(SCRIPT_PLUGINS_STORAGE_INSTALL_DIR) \
	$(POSTGRES_SCHEMA_UPDATE_DIR) $(POSTGRES_SCRIPT_SRC) $(POSTGRES_SCHEMA_UPDATE_SCRIPT_SRC)
	$(CP) $(POSTGRES_SCRIPT_SRC) $(SCRIPT_PLUGINS_STORAGE_INSTALL_DIR)
	$(CP) $(POSTGRES_SCHEMA_UPDATE_SCRIPT_SRC) $(POSTGRES_SCHEMA_UPDATE_DIR)
	$(CP_DIR) scripts/plugins/storage/postgres/upgrade $(POSTGRES_SCHEMA_UPDATE_DIR)
	$(CP_DIR) scripts/plugins/storage/postgres/downgrade $(POSTGRES_SCHEMA_UPDATE_DIR)

install_sqlite_script : $(SCRIPT_PLUGINS_STORAGE_INSTALL_DIR) \
	$(SQLITE_SCHEMA_UPDATE_DIR) $(SQLITE_SCRIPT_SRC) $(SQLITE_SCHEMA_UPDATE_SCRIPT_SRC)
	$(CP) $(SQLITE_SCRIPT_SRC) $(SCRIPT_PLUGINS_STORAGE_INSTALL_DIR)
	$(CP) $(SQLITE_SCHEMA_UPDATE_SCRIPT_SRC) $(SQLITE_SCHEMA_UPDATE_DIR)
	$(CP_DIR) scripts/plugins/storage/sqlite/upgrade $(SQLITE_SCHEMA_UPDATE_DIR)
	$(CP_DIR) scripts/plugins/storage/sqlite/downgrade $(SQLITE_SCHEMA_UPDATE_DIR)

install_south_script : $(SCRIPT_SERVICES_INSTALL_DIR) $(SOUTH_SCRIPT_SRC)
	$(CP) $(SOUTH_SCRIPT_SRC) $(SCRIPT_SERVICES_INSTALL_DIR)

install_south_c_script : $(SCRIPT_SERVICES_INSTALL_DIR) $(SOUTH_C_SCRIPT_SRC)
	$(CP) $(SOUTH_C_SCRIPT_SRC) $(SCRIPT_SERVICES_INSTALL_DIR)

install_storage_service_script : $(SCRIPT_SERVICES_INSTALL_DIR) $(STORAGE_SERVICE_SCRIPT_SRC)
	$(CP) $(STORAGE_SERVICE_SCRIPT_SRC) $(SCRIPT_SERVICES_INSTALL_DIR)

install_north_script : $(SCRIPT_TASKS_INSTALL_DIR) $(NORTH_SCRIPT_SRC)
	$(CP) $(NORTH_SCRIPT_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_north_c_script : $(SCRIPT_TASKS_INSTALL_DIR) $(NORTH_C_SCRIPT_SRC)
	$(CP) $(NORTH_C_SCRIPT_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_notification_c_script: $(SCRIPT_SERVICES_INSTALL_DIR) $(NOTIFICATION_C_SCRIPT_SRC)
	$(CP) $(NOTIFICATION_C_SCRIPT_SRC) $(SCRIPT_SERVICES_INSTALL_DIR)

install_purge_script : $(SCRIPT_TASKS_INSTALL_DIR) $(PURGE_SCRIPT_SRC)
	$(CP) $(PURGE_SCRIPT_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_statistics_script : $(SCRIPT_TASKS_INSTALL_DIR) $(STATISTICS_SCRIPT_SRC)
	$(CP) $(STATISTICS_SCRIPT_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_backup_script : $(SCRIPT_TASKS_INSTALL_DIR) $(BACKUP_SRC)
	$(CP) $(BACKUP_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_restore_script : $(SCRIPT_TASKS_INSTALL_DIR) $(RESTORE_SRC)
	$(CP) $(RESTORE_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_check_certificates_script : $(SCRIPT_TASKS_INSTALL_DIR) $(CHECK_CERTS_TASK_SCRIPT_SRC)
	$(CP) $(CHECK_CERTS_TASK_SCRIPT_SRC) $(SCRIPT_TASKS_INSTALL_DIR)

install_storage_script : $(SCRIPT_INSTALL_DIR) $(STORAGE_SCRIPT_SRC)
	$(CP) $(STORAGE_SCRIPT_SRC) $(SCRIPTS_INSTALL_DIR)

install_certificates_script : $(SCRIPT_INSTALL_DIR) $(CERTIFICATES_SCRIPT_SRC)
	$(CP) $(CERTIFICATES_SCRIPT_SRC) $(SCRIPTS_INSTALL_DIR)

install_auth_certificates_script : $(SCRIPT_INSTALL_DIR) $(AUTH_CERTIFICATES_SCRIPT_SRC)
	$(CP) $(AUTH_CERTIFICATES_SCRIPT_SRC) $(SCRIPTS_INSTALL_DIR)

install_package_update_script : $(SCRIPT_INSTALL_DIR) $(PACKAGE_UPDATE_SCRIPT_SRC)
	$(CP_DIR) $(PACKAGE_UPDATE_SCRIPT_SRC) $(SCRIPTS_INSTALL_DIR)
	chmod -R a-w $(SCRIPTS_INSTALL_DIR)/package
	chmod -R u+x $(SCRIPTS_INSTALL_DIR)/package

$(SCRIPT_COMMON_INSTALL_DIR) :
	$(MKDIR_PATH) $@

$(SCRIPT_PLUGINS_STORAGE_INSTALL_DIR) :
	$(MKDIR_PATH) $@

$(SCRIPT_SERVICES_INSTALL_DIR) :
	$(MKDIR_PATH) $@

$(SCRIPT_STORAGE_INSTALL_DIR) :
	$(MKDIR_PATH) $@

$(SCRIPT_TASKS_INSTALL_DIR) :
	$(MKDIR_PATH) $@

$(POSTGRES_SCHEMA_UPDATE_DIR) :
	$(MKDIR_PATH) $@
	$(MKDIR_PATH) $@/upgrade
	$(MKDIR_PATH) $@/downgrade

$(SQLITE_SCHEMA_UPDATE_DIR) :
	$(MKDIR_PATH) $@
	$(MKDIR_PATH) $@/upgrade
	$(MKDIR_PATH) $@/downgrade

###############################################################################
########################## BIN INSTALL TARGETS ################################
###############################################################################
# install bin
bin_install : $(BIN_INSTALL_DIR) $(FOGBENCH_SCRIPT_SRC) $(FOGLAMP_SCRIPT_SRC)
	$(CP) $(FOGBENCH_SCRIPT_SRC) $(BIN_INSTALL_DIR)
	$(CP) $(FOGLAMP_SCRIPT_SRC) $(BIN_INSTALL_DIR)
	$(CP) $(FOGLAMP_UPDATE_SRC) $(BIN_INSTALL_DIR)
	$(CP) $(UPDATE_TASK_APT_SRC) $(BIN_INSTALL_DIR)
	$(CP) $(UPDATE_TASK_SNAPPY_SRC) $(BIN_INSTALL_DIR)
ifneq ("$(PLATFORM_RH)","")
	$(CP) $(SUDOERS_SRC_RH) $(BIN_INSTALL_DIR)
else
	$(CP) $(SUDOERS_SRC) $(BIN_INSTALL_DIR)
endif

# create bin install dir
$(BIN_INSTALL_DIR) :
	$(MKDIR_PATH) $@

###############################################################################
####################### EXTRAS INSTALL TARGETS ################################
###############################################################################
# install bin
extras_install : $(EXTRAS_INSTALL_DIR) install_python_fogbench install_extras_scripts setuid_cmdutil

install_python_fogbench : $(FOGBENCH_PYTHON_INSTALL_DIR) $(FOGBENCH_PYTHON_SRC_DIR)
	$(CP_DIR) $(FOGBENCH_PYTHON_SRC_DIR) $(FOGBENCH_PYTHON_INSTALL_DIR)

$(FOGBENCH_PYTHON_INSTALL_DIR) :
	$(MKDIR_PATH) $@

install_extras_scripts : $(EXTRAS_INSTALL_DIR) $(EXTRAS_SCRIPTS_SRC_DIR)
	$(CP_DIR) $(EXTRAS_SCRIPTS_SRC_DIR) $(EXTRAS_INSTALL_DIR)

	sed -i "s|export FOGLAMP_ROOT=.*|export FOGLAMP_ROOT=\"$(INSTALL_DIR)\"|" $(EXTRAS_INSTALL_DIR)/scripts/setenv.sh
	sed -i "s|^FOGLAMP_ROOT=.*|FOGLAMP_ROOT=\"$(INSTALL_DIR)\"|" $(EXTRAS_INSTALL_DIR)/scripts/foglamp.service

# create extras install dir
$(EXTRAS_INSTALL_DIR) :
	$(MKDIR_PATH) $@

###############################################################################
####################### DATA INSTALL TARGETS ################################
###############################################################################
# install data
data_install : $(DATA_INSTALL_DIR) install_data

install_data : $(DATA_INSTALL_DIR) $(DATA_SRC_DIR)
	$(CP_DIR) $(DATA_SRC_DIR) $(INSTALL_DIR)

# data and etc directories, should be owned by the user running foglamp
# If install is executed with sudo and the sudo user is root, the data and etc
# directories must be set to be owned by the calling user.
ifdef SUDO_USER
ifeq ("$(USER)","root")

	chown -R ${SUDO_USER}:${SUDO_USER} $(DATA_SRC_DIR)
	chown -R ${SUDO_USER}:${SUDO_USER} $(INSTALL_DIR)/$(DATA_SRC_DIR)
endif
endif

# create extras install dir
#$(DATA_INSTALL_DIR) :
#	$(MKDIR_PATH) $@

# set setuid bit of cmdutil
setuid_cmdutil : c_install
	chmod u+s $(EXTRAS_INSTALL_DIR)/C/cmdutil


###############################################################################
######################## SUPPORTING BUILD/INSTALL TARGETS #####################
###############################################################################
# create install directory
$(INSTALL_DIR) :
	$(MKDIR_PATH) $@

###############################################################################
###############################################################################
###################### CLEAN/UNINSTALL TARGETS ################################
###############################################################################
# clean
clean :
	-$(RM_DIR) $(CMAKE_BUILD_DIR)
	-$(RM_DIR) $(PYTHON_BUILD_DIR)
	-$(RM_DIR) $(DEV_SERVICES_DIR)
	-$(RM) $(SYMLINK_PLUGINS_DIR)
	-$(RM) $(ASYNC_INGEST_PYMODULE)
	-$(RM) $(FILTER_INGEST_PYMODULE)
