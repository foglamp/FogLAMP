/*
 * FogLAMP storage service.
 *
 * Copyright (c) 2019 Dianomic Systems Inc
 *
 * Released under the Apache 2.0 Licence
 *
 * Author: Mark Riddoch
 */
#include <stream_handler.h>
#include <storage_api.h>
#include <reading_stream.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <fcntl.h>
#include <sys/epoll.h>
#include <sys/ioctl.h>
#include <chrono>
#include <unistd.h>
#include <errno.h>


using namespace std;

/**
 * C wrapper for the handler thread we use to handle the polling of
 * the stream ingestion protocol.
 *
 * @param handler	The SgtreamHanler instance that started this thread
 */
static void threadWrapper(void *handler)
{
	((StreamHandler *)handler)->handler();
}

/**
 * Constructor for the StreamHandler class
 */
StreamHandler::StreamHandler() : m_running(true)
{
	m_pollfd = epoll_create(1);
	m_handlerThread = thread(threadWrapper, this);
}


/**
 * Destructor for the StreamHandler. Close down the epoll
 * system and wait for the handler thread to terminate.
 */
StreamHandler::~StreamHandler()
{
	m_running = false;
	close(m_pollfd);
	m_handlerThread.join();
}

/**
 * The handler method for the stream handler. This is run in its own thread
 * and is responsible for using epoll to gather events on the descriptors and
 * to dispatch them to the individual streams
 */
void StreamHandler::handler()
{
	struct epoll_event events[MAX_EVENTS];
	while (m_running)
	{
		std::unique_lock<std::mutex> lock(m_streamsMutex);
		if (m_streams.size() == 0)
		{
			Logger::getLogger()->warn("Waiting for first stream to be created");
			m_streamsCV.wait_for(lock, chrono::milliseconds(500));
		}
		else
		{
			int nfds = epoll_wait(m_pollfd, events, MAX_EVENTS, 1);
			for (int i = 0; i < nfds; i++)
			{
				Stream *stream = (Stream *)events[i].data.ptr;
				stream->handleEvent(m_pollfd);
			}
		}
	}
}

/**
 * Create a new stream and add it to the epoll mechanism for the stream handler
 *
 * @param token		The single use connection token the client should send
 * @param The port on which this stream is listening
 */
uint32_t StreamHandler::createStream(uint32_t *token)
{
	Stream *stream = new Stream();
	uint32_t port = stream->create(m_pollfd, token);
	{
		std::unique_lock<std::mutex> lock(m_streamsMutex);
		m_streams.push_back(stream);
	}

	m_streamsCV.notify_all();

	return port;
}

/**
 * Create a stream object to deal with the stream protocol
 */
StreamHandler::Stream::Stream() : m_status(Closed)
{
}

/**
 * Destroy a stream
 */
StreamHandler::Stream::~Stream() 
{
}

/**
 * Create a new stream object. Add that stream to the epoll structure.
 * A listener socket is created and the port sent back to the caller. The client
 * will connect to this port and then send the token to verify they are the 
 * service that requested the stream to be connected.
 *
 * @param epollfd	The epoll descriptor
 * @param token		The single use token the client will send in the connect request
 */
uint32_t StreamHandler::Stream::create(int epollfd, uint32_t *token)
{
struct sockaddr_in	address;

	if ((m_socket = socket(AF_INET, SOCK_STREAM, 0)) < 0)
	{
		Logger::getLogger()->error("Failed to create socket: %s", sys_errlist[errno]);
		return 0;
	}
	address.sin_family = AF_INET;
	address.sin_addr.s_addr = INADDR_ANY;
	address.sin_port = 0;

	if (bind(m_socket, (struct sockaddr *)&address, sizeof(address)) < 0)
	{
		Logger::getLogger()->error("Failed to bind socket: %s", sys_errlist[errno]);
		return 0;
	}
	socklen_t len = sizeof(address);
	if (getsockname(m_socket, (struct sockaddr *)&address, &len) == -1)
		Logger::getLogger()->error("Failed to get socket name, %s", sys_errlist[errno]);
	m_port = ntohs(address.sin_port);
	Logger::getLogger()->info("Stream port bound to %d", m_port);
	setNonBlocking(m_socket);

	if (listen(m_socket, 3) < 0)
	{
		Logger::getLogger()->error("Failed to listen: %s", sys_errlist[errno]);
		return 0;
    	}
	m_status = Listen;

	srand(m_port + time(0));
	m_token = random() & 0xffffffff;
	*token = m_token;

	// Add to epoll set
	m_event.data.ptr = this;
	m_event.events = EPOLLIN | EPOLLRDHUP;
	if (epoll_ctl(epollfd, EPOLL_CTL_ADD, m_socket, &m_event) < 0)
	{
		Logger::getLogger()->error("Failed to add listening port %d to epoll fileset, %s", m_port, sys_errlist[errno]);
	}

	return m_port;
}

/**
 * Set the file descriptor to be non blocking
 *
 * @param fd	The file descripter to set non-blocking
 */
void StreamHandler::Stream::setNonBlocking(int fd)
{
	int flags;
	flags = fcntl(fd, F_GETFL, 0);
	flags |= O_NONBLOCK;
	fcntl(fd, F_SETFL, flags);
}

/**
 * Handle an epoll event. The precise handling will depend
 * on the state of the stream.
 *
 * @param epollfd	The epoll file descriptor
 */
void StreamHandler::Stream::handleEvent(int epollfd)
{
ssize_t n;

	if (m_status == Listen)
	{
		int conn_sock;
		struct sockaddr	addr;
		socklen_t	addrlen = sizeof(addr);
		if ((conn_sock = accept(m_socket,
                                          (struct sockaddr *)&addr, &addrlen)) == -1)
		{
			Logger::getLogger()->warn("Accept failed for streaming socket: %s", sys_errlist[errno]);
			return;
		}
		epoll_ctl(epollfd, EPOLL_CTL_DEL, m_socket, &m_event);
		close(m_socket);
		Logger::getLogger()->warn("Stream connection established");
		m_socket = conn_sock;
		m_status = AwaitingToken;
		setNonBlocking(m_socket);
		m_event.events = EPOLLIN | EPOLLRDHUP;
		m_event.data.ptr = this;
		epoll_ctl(epollfd, EPOLL_CTL_ADD, m_socket, &m_event);
	}
	else if (m_status == AwaitingToken)
	{
		RDSConnectHeader	hdr;
		if (available(m_socket) < sizeof(hdr))
		{
			return;
		}
		if ((n = read(m_socket, &hdr, sizeof(hdr))) != sizeof(hdr))
			Logger::getLogger()->warn("Short read of %d bytes: %s", n, sys_errlist[errno]);
		if (hdr.magic == RDS_CONNECTION_MAGIC && hdr.token == m_token)
		{
			m_status = Connected;
			m_blockNo = 0;
			m_readingNo = 0;
			m_protocolState = BlkHdr;
			Logger::getLogger()->warn("Token for streaming socket exchanged");
		}
		else
		{
			Logger::getLogger()->warn("Incorrect token for streaming socket");
			close(m_socket);
		}
	}
	else if (m_status == Connected)
	{
		while (1)
		{
			Logger::getLogger()->warn("Connected in protocol state %d, readingNo %d", m_protocolState, m_readingNo);
			if (m_protocolState == BlkHdr)
			{
				RDSBlockHeader blkHdr;
				if (available(m_socket) < sizeof(blkHdr))
				{
					Logger::getLogger()->warn("Not enough bytes for block header");
					return;
				}
				if ((n = read(m_socket, &blkHdr, sizeof(blkHdr))) != sizeof(blkHdr))
					Logger::getLogger()->warn("Short read of %d bytes: %s", n, sys_errlist[errno]);
				if (blkHdr.magic != RDS_BLOCK_MAGIC)
				{
					Logger::getLogger()->error("Expected block header, but incorrect header found");
					return;
				}
				if (blkHdr.blockNumber != m_blockNo)
				{
				}
				m_blockSize = blkHdr.count;
				m_protocolState = RdHdr;
			}
			else if (m_protocolState == RdHdr)
			{
				RDSReadingHeader rdhdr;
				if (available(m_socket) < sizeof(rdhdr))
				{
					Logger::getLogger()->warn("Not enough bytes for reading header");
					return;
				}
				if (read(m_socket, &rdhdr, sizeof(rdhdr)) != sizeof(rdhdr))
					Logger::getLogger()->warn("Not enough bytes for reading header");
				if (rdhdr.magic != RDS_READING_MAGIC)
				{
					Logger::getLogger()->error("Expected reading header, but incorrect header found");
					return;
				}
				Logger::getLogger()->warn("Reading Header: assetCodeLngth %d, payloadLength %d", rdhdr.assetLength, rdhdr.payloadLength);
				m_readingSize = sizeof(uint32_t) * 2 + sizeof(struct timeval)
					+ rdhdr.assetLength + rdhdr.payloadLength;
				Logger::getLogger()->warn("Reading Size: %d", m_readingSize);
				m_readings[m_readingNo % RDS_BLOCK] = (ReadingStream *)malloc(m_readingSize);
				m_readings[m_readingNo % RDS_BLOCK]->assetCodeLength = rdhdr.assetLength;
				m_readings[m_readingNo % RDS_BLOCK]->payloadLength = rdhdr.payloadLength;
				m_readingSize -= 2 * sizeof(uint32_t);
				m_protocolState = RdBody;
				close(m_socket);
			}
			else if (m_protocolState == RdBody)
			{
				if (available(m_socket) < m_readingSize)
				{
					Logger::getLogger()->warn("Not enough bytes for reading %d", m_readingSize);
					return;
				}
				if ((n = read(m_socket, &m_readings[m_readingNo % RDS_BLOCK]->userTs, m_readingSize)) != m_readingSize)
					Logger::getLogger()->warn("Short read of %d bytes: %s", n, sys_errlist[errno]);
				m_readingNo++;
				if ((m_readingNo % RDS_BLOCK) == 0)
				{
					queueInsert(RDS_BLOCK, false);
					for (int i = 0; i < RDS_BLOCK; i++)
						free(m_readings[i]);
				}
				else if (m_readingNo == m_blockSize)
				{
					queueInsert(m_readingNo % RDS_BLOCK, true);
					for (uint32_t i = 0; i < m_readingNo % RDS_BLOCK; i++)
						free(m_readings[i]);
				}
				m_protocolState = RdHdr;
			}
		}
	}
}

/**
 * Queue a block of readings to be inserted into the database. The readings
 * are available via the m_readings array.
 *
 * @param nReadings	The number of readings to insert
 * @param commit	Perform commit at end of this block
 */
void StreamHandler::Stream::queueInsert(unsigned int nReadings, bool commit)
{
	StorageApi *api = StorageApi::getInstance();
	// TODO write to the StorageAPI
	m_readings[nReadings] = NULL;
	api->readingStream(m_readings, commit);
}

/**
 * Return the number of bytes available to read on the
 * given file descriptor
 *
 * @param fd	The file descriptor to check
 */
size_t StreamHandler::Stream::available(int fd)
{
size_t	avail;

	if (ioctl(fd, FIONREAD, &avail) < 0)
	{
		Logger::getLogger()->warn("FIONREAD failed: %s", sys_errlist[errno]);
		return 0;
	}
	return avail;
}
