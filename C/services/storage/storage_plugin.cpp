/*
 * FogLAMP storage service.
 *
 * Copyright (c) 2017 OSisoft, LLC
 *
 * Released under the Apache 2.0 Licence
 *
 * Author: Mark Riddoch
 */
#include <storage_plugin.h>
#include <chrono>

#define START_TIME std::chrono::high_resolution_clock::time_point t1 = std::chrono::high_resolution_clock::now();
#define END_TIME std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now(); \
				 auto usecs = std::chrono::duration_cast<std::chrono::microseconds>( t2 - t1 ).count();
#define PRINT_TIME(msg) std::chrono::high_resolution_clock::time_point t2 = std::chrono::high_resolution_clock::now(); \
				 auto usecs = std::chrono::duration_cast<std::chrono::microseconds>( t2 - t1 ).count(); \
				 Logger::getLogger()->info("%s:%d: " msg " took %lld usecs", __FUNCTION__, __LINE__, usecs);


using namespace std;

/**
 * Constructor for the class that wraps the storage plugin
 *
 * Create a set of function points that resolve to the loaded plugin and
 * enclose in the class.
 *
 * TODO Add support for multiple plugins
 */
StoragePlugin::StoragePlugin(PLUGIN_HANDLE handle) : Plugin(handle)
{
	// Call the init method of the plugin
	PLUGIN_HANDLE (*pluginInit)() = (PLUGIN_HANDLE (*)())
					manager->resolveSymbol(handle, "plugin_init");
	instance = (*pluginInit)();


	// Setup the function pointers to the plugin
  	commonInsertPtr = (int (*)(PLUGIN_HANDLE, const char*, const char*))
				manager->resolveSymbol(handle, "plugin_common_insert");
	commonRetrievePtr = (char * (*)(PLUGIN_HANDLE, const char*, const char*))
				manager->resolveSymbol(handle, "plugin_common_retrieve");
	commonUpdatePtr = (int (*)(PLUGIN_HANDLE, const char*, const char*))
				manager->resolveSymbol(handle, "plugin_common_update");
	commonDeletePtr = (int (*)(PLUGIN_HANDLE, const char*, const char*))
				manager->resolveSymbol(handle, "plugin_common_delete");
	readingsAppendPtr = (int (*)(PLUGIN_HANDLE, const char *))
				manager->resolveSymbol(handle, "plugin_reading_append");
	readingsFetchPtr = (char * (*)(PLUGIN_HANDLE, unsigned long id, unsigned int blksize))
				manager->resolveSymbol(handle, "plugin_reading_fetch");
	readingsRetrievePtr = (char * (*)(PLUGIN_HANDLE, const char *))
				manager->resolveSymbol(handle, "plugin_reading_retrieve");
	readingsPurgePtr = (char * (*)(PLUGIN_HANDLE, unsigned long age, unsigned int flags, unsigned long sent))
				manager->resolveSymbol(handle, "plugin_reading_purge");
	releasePtr = (void (*)(PLUGIN_HANDLE, const char *))
				manager->resolveSymbol(handle, "plugin_release");
	lastErrorPtr = (PLUGIN_ERROR * (*)(PLUGIN_HANDLE))
				manager->resolveSymbol(handle, "plugin_last_error");
}

/**
 * Call the insert method in the plugin
 */
int StoragePlugin::commonInsert(const string& table, const string& payload)
{
	START_TIME;
	int rv = this->commonInsertPtr(instance, table.c_str(), payload.c_str());
	END_TIME;
	//Logger::getLogger()->info("%s:%d: commonInsert for %d row(s) in %s table done in %lld usecs", __FUNCTION__, __LINE__, rv, table.c_str(), usecs);
	//Logger::getLogger()->info("%s:%d: commonInsert payload=%s", __FUNCTION__, __LINE__, payload.c_str());
	return rv;
}

/**
 * Call the retrieve method in the plugin
 */
char *StoragePlugin::commonRetrieve(const string& table, const string& payload)
{
	START_TIME;
	char *rv = this->commonRetrievePtr(instance, table.c_str(), payload.c_str());
	END_TIME;
	//Logger::getLogger()->info("%s:%d: commonRetrieve for %s table done in %lld usecs", __FUNCTION__, __LINE__, table.c_str(), usecs);
	return rv;
}

/**
 * Call the update method in the plugin
 */
int StoragePlugin::commonUpdate(const string& table, const string& payload)
{
	START_TIME;
	int rv = this->commonUpdatePtr(instance, table.c_str(), payload.c_str());
	END_TIME;
	//Logger::getLogger()->info("%s:%d: commonUpdate for %d row(s) in %s table done in %lld usecs", __FUNCTION__, __LINE__, rv, table.c_str(), usecs);
	//Logger::getLogger()->info("%s:%d: commonUpdate payload=%s", __FUNCTION__, __LINE__, payload.c_str());
	return rv;
}

/**
 * Call the delete method in the plugin
 */
int StoragePlugin::commonDelete(const string& table, const string& payload)
{
	return this->commonDeletePtr(instance, table.c_str(), payload.c_str());
}

/**
 * Call the readings append method in the plugin
 */
int StoragePlugin::readingsAppend(const string& payload)
{
	START_TIME;
	int rv = this->readingsAppendPtr(instance, payload.c_str());
	END_TIME;
	Logger::getLogger()->info("%s:%d: %d rows added in %lld usecs", __FUNCTION__, __LINE__, rv, usecs);
	return rv;
}

/**
 * Call the readings fetch method in the plugin
 */
char * StoragePlugin::readingsFetch(unsigned long id, unsigned int blksize)
{
	return this->readingsFetchPtr(instance, id, blksize);
}

/**
 * Call the readings retrieve method in the plugin
 */
char *StoragePlugin::readingsRetrieve(const string& payload)
{
	return this->readingsRetrievePtr(instance, payload.c_str());
}

/**
 * Call the readings purge method in the plugin
 */
char *StoragePlugin::readingsPurge(unsigned long age, unsigned int flags, unsigned long sent)
{
	return this->readingsPurgePtr(instance, age, flags, sent);
}

/**
 * Release a result from a retrieve
 */
void StoragePlugin::release(const char *results)
{
	this->releasePtr(instance, results);
}

/**
 * Get the last error from the plugin
 */
PLUGIN_ERROR *StoragePlugin::lastError()
{
	return this->lastErrorPtr(instance);
}
