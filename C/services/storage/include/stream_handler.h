#ifndef _STREAM_HANDLER_H
#define _STREAM_HANDLER_H
/*
 * FogLAMP storage service.
 *
 * Copyright (c) 2019 Dianomic Systems Inc.
 *
 * Released under the Apache 2.0 Licence
 *
 * Author: Mark Riddoch
 */
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <sys/epoll.h>
#include <reading_stream.h>

#define MAX_EVENTS	40	// Number of epoll events in one epoll_wait call
#define RDS_BLOCK	50	// Number of readings to insert in each call to the storage plugin

class StreamHandler {
	public:
		StreamHandler();
		~StreamHandler();
		void			handler();
		uint32_t		createStream(uint32_t *token);
	private:
		class Stream {
			public:
					Stream();
					~Stream();
					uint32_t	create(int epollfd, uint32_t *token);
					void		handleEvent(int epollfd);
			private:
					void		setNonBlocking(int fd);
					size_t		available(int fd);
					void		queueInsert(unsigned int nReadings, bool commit);
					enum { Closed, Listen, AwaitingToken, Connected }
				       			m_status;
					int		m_socket;
					uint32_t	m_port;
					uint32_t	m_token;
					uint32_t	m_blockNo;
					enum { BlkHdr, RdHdr, RdBody }
				       			m_protocolState;
					uint32_t	m_readingNo;
					uint32_t	m_blockSize;
					size_t		m_readingSize;
					struct epoll_event
							m_event;
					ReadingStream	*m_readings[RDS_BLOCK+1];
		};
		std::thread		m_handlerThread;
		int			m_tokens;
		std::condition_variable	m_streamsCV;
		std::mutex		m_streamsMutex;
		std::vector<Stream *>	m_streams;
		bool			m_running;
		int			m_pollfd;
};
#endif
