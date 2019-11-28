/*
 * FogLAMP storage service client
 *
 * Copyright (c) 2018 Dianomic Systems
 *
 * Released under the Apache 2.0 Licence
 *
 * Author: Mark Riddoch
 */
#include <storage_client.h>
#include <reading.h>
#include <reading_set.h>
#include <reading_stream.h>
#include <rapidjson/document.h>
#include <rapidjson/error/en.h>
#include <service_record.h>
#include <string>
#include <sstream>
#include <iostream>
#include <thread>
#include <map>
#include <string_utils.h>
#include <sys/uio.h>

#define INSTRUMENT	1

#if INSTRUMENT
#include <sys/time.h>
#endif

using namespace std;
using namespace rapidjson;
using HttpClient = SimpleWeb::Client<SimpleWeb::HTTP>;

// handles m_client_map access
std::mutex sto_mtx_client_map;

/**
 * Storage Client constructor
 */
StorageClient::StorageClient(const string& hostname, const unsigned short port) : m_streaming(false)
{
	m_host = hostname;
	m_pid = getpid();
	m_logger = Logger::getLogger();
	m_urlbase << hostname << ":" << port;
}

/**
 * Storage Client constructor
 * stores the provided HttpClient into the map
 */
StorageClient::StorageClient(HttpClient *client) : m_streaming(false)
{

	std::thread::id thread_id = std::this_thread::get_id();

	sto_mtx_client_map.lock();
	m_client_map[thread_id] = client;
	sto_mtx_client_map.unlock();
}


/**
 * Destructor for storage client
 */
StorageClient::~StorageClient()
{
	std::map<std::thread::id, HttpClient *>::iterator item;

	// Deletes all the HttpClient objects created in the map
	for (item  = m_client_map.begin() ; item  != m_client_map.end() ; ++item)
	{
		delete item->second;
	}
}

/**
 * Creates a HttpClient object for each thread
 * it stores/retrieves the reference to the HttpClient and the associated thread id in a map
 */
HttpClient *StorageClient::getHttpClient(void) {

	std::map<std::thread::id, HttpClient *>::iterator item;
	HttpClient *client;

	std::thread::id thread_id = std::this_thread::get_id();

	sto_mtx_client_map.lock();
	item = m_client_map.find(thread_id);

	if (item  == m_client_map.end() ) {

		// Adding a new HttpClient
		client = new HttpClient(m_urlbase.str());
		m_client_map[thread_id] = client;
		m_seqnum_map[thread_id].store(0);
		std::ostringstream ss;
		ss << std::this_thread::get_id();
	}
	else
	{
		client = item->second;
	}
	sto_mtx_client_map.unlock();

	return (client);
}

/**
 * Append a single reading
 */
bool StorageClient::readingAppend(Reading& reading)
{
	try {
		ostringstream convert;

		convert << "{ \"readings\" : [ ";
		convert << reading.toJSON();
		convert << " ] }";
		auto res = this->getHttpClient()->request("POST", "/storage/reading", convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			return true;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Append readings", res->status_code, resultPayload.str());
		return false;
	} catch (exception& ex) {
		m_logger->error("Failed to append reading: %s", ex.what());
	}
	return false;
}

/**
 * Append multiple readings
 *
 * TODO implement a mechanism to force streamed or non-streamed mode
 */
bool StorageClient::readingAppend(const vector<Reading *>& readings)
{
#if INSTRUMENT
	struct timeval	start, t1, t2;
#endif
	if (m_streaming)
	{
		return streamReadings(readings);
	}
	// See if we should switch to stream mode
	struct timeval tmFirst, tmLast, dur;
	readings[0]->getUserTimestamp(&tmFirst);
	readings[readings.size()-1]->getUserTimestamp(&tmLast);
	timersub(&tmLast, &tmFirst, &dur);
	double timeSpan = dur.tv_sec + ((double)dur.tv_usec / 1000000);
	double rate = (double)readings.size() / timeSpan;
	if (rate > STREAM_THRESHOLD)
	{
		m_logger->info("Reading rate %.1f readings per second above threshold, attmempting to switch to stream mode", rate);
		if (openStream())
		{
			m_logger->info("Successfully switch to stream mode for readings");
			return streamReadings(readings);
		}
		m_logger->warn("Failed to switch to streaming mode");
	}
	static HttpClient *httpClient = this->getHttpClient(); // to initialize m_seqnum_map[thread_id] for this thread
	try {
		std::thread::id thread_id = std::this_thread::get_id();
		ostringstream ss;
		sto_mtx_client_map.lock();
		m_seqnum_map[thread_id].fetch_add(1);
		ss << m_pid << "#" << thread_id << "_" << m_seqnum_map[thread_id].load();
		sto_mtx_client_map.unlock();

		SimpleWeb::CaseInsensitiveMultimap headers = {{"SeqNum", ss.str()}};

#if INSTRUMENT
		gettimeofday(&start, NULL);
#endif
		ostringstream convert;
		convert << "{ \"readings\" : [ ";
		for (vector<Reading *>::const_iterator it = readings.cbegin();
						 it != readings.cend(); ++it)
		{
			if (it != readings.cbegin())
			{
				convert << ", ";
			}
			convert << (*it)->toJSON();
		}
		convert << " ] }";
#if INSTRUMENT
		gettimeofday(&t1, NULL);
#endif
		auto res = this->getHttpClient()->request("POST", "/storage/reading", convert.str(), headers);
#if INSTRUMENT
		gettimeofday(&t2, NULL);
#endif
		if (res->status_code.compare("200 OK") == 0)
		{
#if INSTRUMENT
			struct timeval tm;
			timersub(&t1, &start, &tm);
			double buildTime, requestTime;
			buildTime = tm.tv_sec + ((double)tm.tv_usec / 1000000);
			timersub(&t2, &t1, &tm);
			requestTime = tm.tv_sec + ((double)tm.tv_usec / 1000000);
			m_logger->info("Appended %d readings in %.3f seconds. Took %.3f seconds to build request", readings.size(), requestTime, buildTime);
			m_logger->info("%.1f Readings per second, request building %.2f%% of time", readings.size() / (buildTime + requestTime),
					(buildTime * 100) / (requestTime + buildTime));
			m_logger->info("Request block size %dK", strlen(convert.str().c_str())/1024);
#endif
			return true;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Append readings", res->status_code, resultPayload.str());
		return false;
	} catch (exception& ex) {
		m_logger->error("Failed to append readings: %s", ex.what());
	}
	return false;
}

/**
 * Perform a generic query against the readings data
 *
 * @param query		The query to execute
 * @return ResultSet	The result of the query
 */
ResultSet *StorageClient::readingQuery(const Query& query)
{
	try {
		ostringstream convert;

		convert << query.toJSON();
		auto res = this->getHttpClient()->request("PUT", "/storage/reading/query", convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			ResultSet *result = new ResultSet(resultPayload.str().c_str());
			return result;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Query readings", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to query readings: %s", ex.what());
		throw;
	} catch (exception* ex) {
		m_logger->error("Failed to query readings: %s", ex->what());
		delete ex;
		throw exception();
	}
	return 0;
}

/**
 * Retrieve a set of readings for sending on the northbound
 * interface of FogLAMP
 *
 * @param readingId	The ID of the reading which should be the first one to send
 * @param count		Maximum number if readings to return
 * @return ReadingSet	The set of readings
 */
ReadingSet *StorageClient::readingFetch(const unsigned long readingId, const unsigned long count)
{
	try {

		char url[256];
		snprintf(url, sizeof(url), "/storage/reading?id=%ld&count=%ld",
				readingId, count);

		auto res = this->getHttpClient()->request("GET", url);
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			ReadingSet *result = new ReadingSet(resultPayload.str().c_str());
			return result;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Fetch readings", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to fetch readings: %s", ex.what());
		throw;
	} catch (exception* ex) {
		m_logger->error("Failed to fetch readings: %s", ex->what());
		delete ex;
		throw exception();
	}
	return 0;
}

/**
 * Purge the readings by age
 *
 * @param age	Number of hours old a reading has to be to be considered for purging
 * @param sent	The ID of the last reading that was sent
 * @param purgeUnsent	Flag to control if unsent readings should be purged
 * @return PurgeResult	Data on the readings hat were purged
 */
PurgeResult StorageClient::readingPurgeByAge(unsigned long age, unsigned long sent, bool purgeUnsent)
{
	try {
		char url[256];
		snprintf(url, sizeof(url), "/storage/reading/purge?age=%ld&sent=%ld&flags=%s",
				age, sent, purgeUnsent ? "purge" : "retain");
		auto res = this->getHttpClient()->request("PUT", url);
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		if (res->status_code.compare("200 OK") == 0)
		{
			return PurgeResult(resultPayload.str());
		}
		handleUnexpectedResponse("Purge by age", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to purge readings: %s", ex.what());
		throw;
	} catch (exception* ex) {
		m_logger->error("Failed to purge readings: %s", ex->what());
		delete ex;
		throw exception();
	}
	return PurgeResult();
}

/**
 * Purge the readings by size
 *
 * @param size		Desired maximum size of readings table
 * @param sent	The ID of the last reading that was sent
 * @param purgeUnsent	Flag to control if unsent readings should be purged
 * @return PurgeResult	Data on the readings hat were purged
 */
PurgeResult StorageClient::readingPurgeBySize(unsigned long size, unsigned long sent, bool purgeUnsent)
{
	try {
		char url[256];
		snprintf(url, sizeof(url), "/storage/reading/purge?size=%ld&sent=%ld&flags=%s",
				size, sent, purgeUnsent ? "purge" : "retain");
		auto res = this->getHttpClient()->request("PUT", url);
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			return PurgeResult(resultPayload.str());
		}
	} catch (exception& ex) {
		m_logger->error("Failed to fetch readings: %s", ex.what());
		throw;
	} catch (exception* ex) {
		m_logger->error("Failed to fetch readings: %s", ex->what());
		delete ex;
		throw exception();
	}
	return PurgeResult();
}

/**
 * Query a table
 *
 * @param tablename	The name of the table to query
 * @param query		The query payload
 * @return ResultSet*	The resultset of the query
 */
ResultSet *StorageClient::queryTable(const std::string& tableName, const Query& query)
{
	try {
		ostringstream convert;

		convert << query.toJSON();
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s/query", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str());
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		if (res->status_code.compare("200 OK") == 0)
		{
			ResultSet *result = new ResultSet(resultPayload.str().c_str());
			return result;
		}
		handleUnexpectedResponse("Query table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to query table %s: %s", tableName.c_str(), ex.what());
		throw;
	} catch (exception* ex) {
		m_logger->error("Failed to query table %s: %s", tableName.c_str(), ex->what());
		delete ex;
		throw exception();
	}
	return 0;
}

/**
 * Query a table and return a ReadingSet pointer
 *
 * @param tablename	The name of the table to query
 * @param query		The query payload
 * @return ReadingSet*	The resultset of the query as
 *			ReadingSet class pointer
 */
ReadingSet* StorageClient::queryTableToReadings(const std::string& tableName,
						const Query& query)
{
	try {
		ostringstream convert;

		convert << query.toJSON();
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s/query", tableName.c_str());

		auto res = this->getHttpClient()->request("PUT", url, convert.str());
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();

		if (res->status_code.compare("200 OK") == 0)
		{
			ReadingSet* result = new ReadingSet(resultPayload.str().c_str());
			return result;
		}
		handleUnexpectedResponse("Query table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to query table %s: %s", tableName.c_str(), ex.what());
		throw;
	} catch (exception* ex) {
		m_logger->error("Failed to query table %s: %s", tableName.c_str(), ex->what());
		delete ex;
		throw exception();
	}
	return 0;
}

/**
 * Insert data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param values	The values to insert into the table
 * @return int		The number of rows inserted
 */
int StorageClient::insertTable(const string& tableName, const InsertValues& values)
{
	try {
		ostringstream convert;

		convert << values.toJSON();
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("POST", url, convert.str());
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		if (res->status_code.compare("200 OK") == 0 || res->status_code.compare("201 Created") == 0)
		{
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("POST result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of insertTable. %s. Document is %s",
						GetParseError_En(doc.GetParseError()),
						resultPayload.str().c_str());
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to append table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		handleUnexpectedResponse("Insert table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to insert into table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return 0;
}

/**
 * Update data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param values	The values to insert into the table
 * @param where		The conditions to match the updated rows
 * @return int		The number of rows updated
 */
int StorageClient::updateTable(const string& tableName, const InsertValues& values, const Where& where)
{
	static HttpClient *httpClient = this->getHttpClient(); // to initialize m_seqnum_map[thread_id] for this thread
	try {
		std::thread::id thread_id = std::this_thread::get_id();
		ostringstream ss;
		sto_mtx_client_map.lock();
		m_seqnum_map[thread_id].fetch_add(1);
		ss << m_pid << "#" << thread_id << "_" << m_seqnum_map[thread_id].load();
		sto_mtx_client_map.unlock();

		SimpleWeb::CaseInsensitiveMultimap headers = {{"SeqNum", ss.str()}};

		ostringstream convert;

		convert << "{ \"updates\" : [ ";
		convert << "{ \"where\" : ";
		convert << where.toJSON();
		convert << ", \"values\" : ";
		convert << values.toJSON();
		convert << " }";
		convert << " ] }";
		
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str(), headers);
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of updateTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to update table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Update table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to update table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}

/**
 * Update data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param values	The expressions to update into the table
 * @param where		The conditions to match the updated rows
 * @return int		The number of rows updated
 */
int StorageClient::updateTable(const string& tableName, const ExpressionValues& values, const Where& where)
{
	static HttpClient *httpClient = this->getHttpClient(); // to initialize m_seqnum_map[thread_id] for this thread
	try {
		std::thread::id thread_id = std::this_thread::get_id();
		ostringstream ss;
		sto_mtx_client_map.lock();
		m_seqnum_map[thread_id].fetch_add(1);
		ss << m_pid << "#" << thread_id << "_" << m_seqnum_map[thread_id].load();
		sto_mtx_client_map.unlock();

		SimpleWeb::CaseInsensitiveMultimap headers = {{"SeqNum", ss.str()}};
		
		ostringstream convert;

		convert << "{ \"updates\" : [ ";
		convert << "{ \"where\" : ";
		convert << where.toJSON();
		convert << ", \"expressions\" : ";
		convert << values.toJSON();
		convert << " }";
		convert << " ] }";
		
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str(), headers);
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of updateTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to update table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Update table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to update table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}

/**
 * Update data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param updates	The expressions and condition pairs to update in the table
 * @return int		The number of rows updated
 */
int StorageClient::updateTable(const string& tableName, vector<pair<ExpressionValues *, Where *>>& updates)
{
	static HttpClient *httpClient = this->getHttpClient(); // to initialize m_seqnum_map[thread_id] for this thread
	try {
		std::thread::id thread_id = std::this_thread::get_id();
		ostringstream ss;
		sto_mtx_client_map.lock();
		m_seqnum_map[thread_id].fetch_add(1);
		ss << m_pid << "#" << thread_id << "_" << m_seqnum_map[thread_id].load();
		sto_mtx_client_map.unlock();

		SimpleWeb::CaseInsensitiveMultimap headers = {{"SeqNum", ss.str()}};
		
		ostringstream convert;
		convert << "{ \"updates\" : [ ";
		for (vector<pair<ExpressionValues *, Where *>>::const_iterator it = updates.cbegin();
						 it != updates.cend(); ++it)
		{
			if (it != updates.cbegin())
			{
				convert << ", ";
			}
			convert << "{ \"where\" : ";
			convert << it->second->toJSON();
			convert << ", \"expressions\" : ";
			convert << it->first->toJSON();
			convert << " }";
		}
		convert << " ] }";
		
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str(), headers);
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of updateTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to update table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Update table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to update table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}


/**
 * Update data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param values	The values to insert into the table
 * @param expressions	The expression to update inthe table
 * @param where		The conditions to match the updated rows
 * @return int		The number of rows updated
 */
int StorageClient::updateTable(const string& tableName, const InsertValues& values, const ExpressionValues& expressions, const Where& where)
{
	try {
		ostringstream convert;

		convert << "{ \"updates\" : [ ";
		convert << "{ \"where\" : ";
		convert << where.toJSON();
		convert << ", \"values\" : ";
		convert << values.toJSON();
		convert << ", \"expressions\" : ";
		convert << expressions.toJSON();
		convert << " }";
		convert << " ] }";
		
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of updateTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to update table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Update table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to update table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}

/**
 * Update data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param json		The values to insert into the table
 * @param where		The conditions to match the updated rows
 * @return int		The number of rows updated
 */
int StorageClient::updateTable(const string& tableName, const JSONProperties& values, const Where& where)
{
	try {
		ostringstream convert;

		convert << "{ \"updates\" : [ ";
		convert << "{ \"where\" : ";
		convert << where.toJSON();
		convert << ", ";
		convert << values.toJSON();
		convert << " }";
		convert << " ] }";
		
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of updateTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to update table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Update table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to update table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}

/**
 * Update data into an arbitrary table
 *
 * @param tableName	The name of the table into which data will be added
 * @param values	The values to insert into the table
 * @param jsonProp	The JSON Properties to update
 * @param where		The conditions to match the updated rows
 * @return int		The number of rows updated
 */
int StorageClient::updateTable(const string& tableName, const InsertValues& values, const JSONProperties& jsonProp, const Where& where)
{
	try {
		ostringstream convert;

		convert << "{ \"updates\" : [ ";
		convert << "{ \"where\" : ";
		convert << where.toJSON();
		convert << ", \"values\" : ";
		convert << values.toJSON();
		convert << ", ";
		convert << jsonProp.toJSON();
		convert << " }";
		convert << " ] }";
		
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("PUT", url, convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of updateTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to update table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Update table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to update table %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}

/**
 * Delete from a table
 *
 * @param tablename	The name of the table to delete from
 * @param query		The query payload to match rows to delete
 * @return int	The number of rows deleted
 */
int StorageClient::deleteTable(const std::string& tableName, const Query& query)
{
	try {
		ostringstream convert;

		convert << query.toJSON();
		char url[128];
		snprintf(url, sizeof(url), "/storage/table/%s", tableName.c_str());
		auto res = this->getHttpClient()->request("DELETE", url, convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("PUT result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of deleteTable. %s",
						GetParseError_En(doc.GetParseError()));
				return -1;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to delete table data: %s",
					doc["message"].GetString());
				return -1;
			}
			return doc["rows_affected"].GetInt();
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Delete from table", res->status_code, resultPayload.str());
	} catch (exception& ex) {
		m_logger->error("Failed to delete table data %s: %s", tableName.c_str(), ex.what());
		throw;
	}
	return -1;
}

/**
 * Standard logging method for all interactions
 *
 * @param operation	The operation beign undertaken
 * @param responseCode	The HTTP response code
 * @param payload	The payload in the response message
 */
void StorageClient::handleUnexpectedResponse(const char *operation,
			const string& responseCode,  const string& payload)
{
Document doc;

	doc.Parse(payload.c_str());
	if (!doc.HasParseError())
	{
		if (doc.HasMember("message"))
		{
			m_logger->info("%s completed with result %s", operation, 
							responseCode.c_str());
			m_logger->error("%s: %s", operation,
				doc["message"].GetString());
		}
	}
	else
	{
		m_logger->error("%s completed with result %s", operation, responseCode.c_str());
	}
}

/**
 * Register interest for a Reading asset name
 *
 * @param assetName	The asset name to register
 *			for readings data notification
 * @param callbackUrl	The callback URL to send readings data.
 * @return		True on success, false otherwise.
 */
bool StorageClient::registerAssetNotification(const string& assetName,
					      const string& callbackUrl)
{
	try
	{
		ostringstream convert;

		convert << "{ \"url\" : \"";
		convert << callbackUrl;
		convert << "\" }";
		auto res = this->getHttpClient()->request("POST",
							  "/storage/reading/interest/" + urlEncode(assetName),
							  convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			return true;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Register asset",
					 res->status_code,
					 resultPayload.str());

		return false;
	} catch (exception& ex)
	{
		m_logger->error("Failed to register asset '%s': %s",
				assetName.c_str(),
				ex.what());
	}
	return false;
}

/**
 * Unregister interest for a Reading asset name
 *
 * @param assetName	The asset name to unregister
 *			for readings data notification
 * @param callbackUrl	The callback URL provided in registration.
 * @return		True on success, false otherwise.
 */
bool StorageClient::unregisterAssetNotification(const string& assetName,
						const string& callbackUrl)
{
	try
	{
		ostringstream convert;

		convert << "{ \"url\" : \"";
		convert << callbackUrl;
		convert << "\" }";
		auto res = this->getHttpClient()->request("DELETE",
							  "/storage/reading/interest/" + urlEncode(assetName),
							  convert.str());
		if (res->status_code.compare("200 OK") == 0)
		{
			return true;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Unregister asset",
					 res->status_code,
					 resultPayload.str());

		return false;
	} catch (exception& ex)
	{
		m_logger->error("Failed to unregister asset '%s': %s",
				assetName.c_str(),
				ex.what());
	}
	return false;
}

bool StorageClient::openStream()
{
	try {
		auto res = this->getHttpClient()->request("POST", "/storage/reading/stream");
		m_logger->info("POST /storage/reading/stream returned: %s", res->status_code.c_str());
		if (res->status_code.compare("200 OK") == 0)
		{
			ostringstream resultPayload;
			resultPayload << res->content.rdbuf();
			Document doc;
			doc.Parse(resultPayload.str().c_str());
			if (doc.HasParseError())
			{
				m_logger->info("POST result %s.", res->status_code.c_str());
				m_logger->error("Failed to parse result of createStream. %s. Document is %s",
						GetParseError_En(doc.GetParseError()),
						resultPayload.str().c_str());
				return false;
			}
			else if (doc.HasMember("message"))
			{
				m_logger->error("Failed to switch to stream mode: %s",
					doc["message"].GetString());
				return false;
			}
			int port, token;
			if ((!doc.HasMember("port")) || (!doc.HasMember("token")))
			{
				m_logger->error("Missing items in stream creation response");
				return false;
			}
		       	port = doc["port"].GetInt();
			token = doc["token"].GetInt();
			if ((m_stream = socket(AF_INET, SOCK_STREAM, 0)) == -1)
        		{
				m_logger->error("Unable to create socket");
				return false;
			}
			struct sockaddr_in serv_addr;
			hostent *server;
			if ((server = gethostbyname(m_host.c_str())) == NULL)
			{
				m_logger->error("Unable to resolve hostname for reading stream: %s", m_host.c_str());
				return false;
			}
			bzero((char *) &serv_addr, sizeof(serv_addr));
			serv_addr.sin_family = AF_INET;
			bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);
			serv_addr.sin_port = htons(port);
			if (connect(m_stream, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0)
			{
				Logger::getLogger()->warn("Unable to connect to storage streaming server: %s, %d", m_host.c_str(), port);
				return false;
			}
			RDSConnectHeader conhdr;
			conhdr.magic = RDS_CONNECTION_MAGIC;
			conhdr.token = token;
			write(m_stream, &conhdr, sizeof(conhdr));
			m_streaming = true;
			m_logger->info("Storage stream succesfully created");
			return true;
		}
		ostringstream resultPayload;
		resultPayload << res->content.rdbuf();
		handleUnexpectedResponse("Create reading stream", res->status_code, resultPayload.str());
		return false;
	} catch (exception& ex) {
		m_logger->error("Failed to create reading stream: %s", ex.what());
	}
	m_logger->error("Fallen through!");
	return false;
}

/**
 * Stream a set of readings to the storage service.
 *
 * TODO Deal with acknowledgements, add error checking/recovery
 *
 * @param readings	The readings to stream
 * @return bool		True if the readings have been sent
 */
bool StorageClient::streamReadings(const std::vector<Reading *> & readings)
{
RDSBlockHeader   	blkhdr;
RDSReadingHeader 	rdhdrs[STREAM_BLK_SIZE];
struct { const void *iov_base; size_t iov_len;} iovs[STREAM_BLK_SIZE * 3];
string			payloads[STREAM_BLK_SIZE];

	if (!m_streaming)
	{
		return false;
	}
	blkhdr.magic = RDS_BLOCK_MAGIC;
	blkhdr.blockNumber = m_readingBlock++;
	blkhdr.count = readings.size();
	write(m_stream, &blkhdr, sizeof(blkhdr));
	for (int i = 0; i < readings.size(); i++)
	{
		int offset = i % STREAM_BLK_SIZE;
		rdhdrs[offset].magic = RDS_READING_MAGIC;
		rdhdrs[offset].readingNo = i;
		rdhdrs[offset].assetLength = readings[i]->getAssetName().length() + 1;
		payloads[offset] = readings[i]->getDatapointsJSON();
		rdhdrs[offset].payloadLength = payloads[offset].length() + 1;
		iovs[offset * 3].iov_base = &rdhdrs[offset];
		iovs[offset * 3].iov_len = sizeof(RDSReadingHeader);
		iovs[(offset * 3) + 1].iov_base = readings[i]->getAssetName().c_str();
		iovs[(offset * 3) + 1].iov_len = rdhdrs[offset].assetLength;
		iovs[(offset * 3) + 2].iov_base = payloads[offset].c_str();
		iovs[(offset * 3) + 2].iov_len = rdhdrs[offset].payloadLength;
		if (offset == STREAM_BLK_SIZE - 1)
		{
			writev(m_stream, (const iovec *)iovs, STREAM_BLK_SIZE * 3);
		}
	}
	if (readings.size() % STREAM_BLK_SIZE)
	{
		writev(m_stream, (const iovec *)iovs, (readings.size() % STREAM_BLK_SIZE) * 3);
	}
	return true;
}
