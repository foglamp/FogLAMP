#ifndef _CONNECTION_MANAGER_H
#define _CONNECTION_MANAGER_H
/*
 * FogLAMP storage service.
 *
 * Copyright (c) 2017 OSisoft, LLC
 *
 * Released under the Apache 2.0 Licence
 *
 * Author: Mark Riddoch
 */

#include <plugin_api.h>
#include <list>
#include <mutex>

class Connection;

/**
 * Singleton class to manage SQLite3 connection pool
 */
class ConnectionManager {
	public:
		static ConnectionManager  *getInstance();
		void                      growPool(unsigned int);
		unsigned int              shrinkPool(unsigned int);
		Connection                *allocate();
		void                      release(Connection *);
		void			  shutdown();
		void			  setError(const char *, const char *, bool);
		void			  setReadingsGId(int readingsGId) {m_ReadingsGId = readingsGId;};
		int			      getReadingsGId()                {return m_ReadingsGId; };

		PLUGIN_ERROR		  *getError()
					  {
						return &lastError;
					  }

protected:
		ConnectionManager();

	private:
		static ConnectionManager     *instance;
		int                        m_ReadingsGId=1;


	protected:
		std::list<Connection *>      idle;
		std::list<Connection *>      inUse;
		std::mutex                   idleLock;
		std::mutex                   inUseLock;
		std::mutex                   errorLock;
		PLUGIN_ERROR		     lastError;
		bool			     m_trace;

};

#endif
