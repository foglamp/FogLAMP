#include <utility>

/*
 * FogLAMP OSI Soft OMF interface to PI Server.
 *
 * Copyright (c) 2018 Dianomic Systems
 *
 * Released under the Apache 2.0 Licence
 *
 * Author: Massimiliano Pinto
 */


#include <iostream>
#include <string>
#include <cstring>
#include <omf.h>
#include <logger.h>
#include <zlib.h>
#include <rapidjson/document.h>
#include "string_utils.h"
#include <plugin_api.h>

using namespace std;
using namespace rapidjson;

static bool isTypeSupported(DatapointValue& dataPoint);

// Structures to generate and assign the 1st level of AF hierarchy if the end point is PI Web API
const char *AF_HIERARCHY_1LEVEL_TYPE = QUOTE(
	[
		{
			"id": "_placeholder_typeid_",
			"version": "1.0.0.0",
			"type": "object",
			"classification": "static",
			"properties": {
				"Name": {
					"type": "string",
					"isindex": true
				}
			}
		}
	]
);

const char *AF_HIERARCHY_1LEVEL_STATIC = QUOTE(
	[
		{

			"typeid": "_placeholder_typeid_",
			"values": [
				{
				"Name": "_placeholder_"
				}
			]
		}
	]
);

const char *AF_HIERARCHY_1LEVEL_LINK = QUOTE(
	{
		"source": {
			"typeid": "_placeholder_src_type_",
			"index": "_placeholder_src_idx_"
		},
		"target": {
			"typeid": "_placeholder_tgt_type_",
			"index": "_placeholder_tgt_idx_"
		}
	}
);


/**
 * OMFData constructor
 */
OMFData::OMFData(const Reading& reading, const long typeId, const string& PIServerEndpoint,const string&  AFHierarchy1Level)
{
	string outData;
	string measurementId;

	measurementId = to_string(typeId) + "measurement_" + reading.getAssetName();

	// Add the 1st level of AFHierarchy as a prefix to the name in case of PI Web API
	if (PIServerEndpoint.compare("p") == 0)
	{
		measurementId = AFHierarchy1Level + "_" + measurementId;
	}

	// Convert reading data into the OMF JSON string
	outData.append("{\"containerid\": \"" + measurementId);
	outData.append("\", \"values\": [{");


	// Get reading data
	const vector<Datapoint*> data = reading.getReadingData();
	unsigned long skipDatapoints = 0;

	/**
	 * This loop creates:
	 * "dataName": {"type": "dataType"},
	 */
	for (vector<Datapoint*>::const_iterator it = data.begin(); it != data.end(); ++it)
	{
		if (!isTypeSupported((*it)->getData()))
		{
			skipDatapoints++;;	
			continue;
		}
		else
		{
			// Add datapoint Name
			outData.append("\"" + (*it)->getName() + "\": " + (*it)->getData().toString());
			outData.append(", ");
		}
	}

	// Append Z to getAssetDateTime(FMT_STANDARD)
	outData.append("\"Time\": \"" + reading.getAssetDateUserTime(Reading::FMT_STANDARD) + "Z" + "\"");

	outData.append("}]}");

	// Append all, some or no datapoins
	if (!skipDatapoints ||
	    skipDatapoints < data.size())
	{
		m_value.append(outData);
	}
}

/**
 * Return the (reference) JSON data in m_value
 */
const string& OMFData::OMFdataVal() const
{
	return m_value;
}

/**
 * OMF constructor
 */
OMF::OMF(HttpSender& sender,
	 const string& path,
	 const long id,
	 const string& token) :
	 m_path(path),
	 m_typeId(id),
	 m_producerToken(token),
	 m_sender(sender)
{
	m_lastError = false;
	m_changeTypeId = false;
	m_OMFDataTypes = NULL;
}

/**
 * OMF constructor with per asset data types
 */

OMF::OMF(HttpSender& sender,
	 const string& path,
	 map<string, OMFDataTypes>& types,
	 const string& token) :
	 m_path(path),
	 m_OMFDataTypes(&types),
	 m_producerToken(token),
	 m_sender(sender)
{
	// Get starting type-id sequence or set the default value
	auto it = (*m_OMFDataTypes).find(FAKE_ASSET_KEY);
	m_typeId = (it != (*m_OMFDataTypes).end()) ?
		   (*it).second.typeId :
		   TYPE_ID_DEFAULT;

	m_lastError = false;
	m_changeTypeId = false;
}

// Destructor
OMF::~OMF()
{
}

/**
 * Compress a string
 *
 * @param str			Input STL string that is to be compressed
 * @param compressionlevel	zlib/gzip Compression level
 * @return str			gzip compressed binary data
 */
std::string OMF::compress_string(const std::string& str,
                            int compressionlevel)
{
    const int windowBits = 15;
    const int GZIP_ENCODING = 16;

    z_stream zs;                        // z_stream is zlib's control structure
    memset(&zs, 0, sizeof(zs));

    if (deflateInit2(&zs, compressionlevel, Z_DEFLATED,
		 windowBits | GZIP_ENCODING, 8,
		 Z_DEFAULT_STRATEGY) != Z_OK)
        throw(std::runtime_error("deflateInit failed while compressing."));

    zs.next_in = (Bytef*)str.data();
    zs.avail_in = str.size();           // set the z_stream's input

    int ret;
    char outbuffer[32768];
    std::string outstring;

    // retrieve the compressed bytes blockwise
    do {
        zs.next_out = reinterpret_cast<Bytef*>(outbuffer);
        zs.avail_out = sizeof(outbuffer);

        ret = deflate(&zs, Z_FINISH);

        if (outstring.size() < zs.total_out) {
            // append the block to the output string
            outstring.append(outbuffer,
                             zs.total_out - outstring.size());
        }
    } while (ret == Z_OK);

    deflateEnd(&zs);

    if (ret != Z_STREAM_END) {          // an error occurred that was not EOF
        std::ostringstream oss;
        oss << "Exception during zlib compression: (" << ret << ") " << zs.msg;
        throw(std::runtime_error(oss.str()));
    }

    return outstring;
}

/**
 * Sends all the data type messages for a Reading data row
 *
 * @param row    The current Reading data row
 * @return       True is all data types have been sent (HTTP 2xx OK)
 *               False when first error occurs.
 */
bool OMF::sendDataTypes(const Reading& row)
{
	int res;
	m_changeTypeId = false;

	// Create header for Type
	vector<pair<string, string>> resType = OMF::createMessageHeader("Type");
	// Create data for Type message	
	string typeData = OMF::createTypeData(row);

	// If Datatyope in Reading row is not supported, just return true
	if (typeData.empty())
	{
		return true;
	}
	else
	{
		// TODO: ADD LOG
	}

	// Build an HTTPS POST with 'resType' headers
	// and 'typeData' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{
		res = m_sender.sendRequest("POST",
					   m_path,
					   resType,
					   typeData);
		if  ( ! (res >= 200 && res <= 299) )
		{
			Logger::getLogger()->error("Sending JSON dataType message 'Type' "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
						   res,
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   typeData.c_str() );
			return false;
		}
	}
	// Exception raised for HTTP 400 Bad Request
	catch (const BadRequest& e)
	{
		if (OMF::isDataTypeError(e.what()))
		{
			// Data type error: force type-id change
			m_changeTypeId = true;
		}
                Logger::getLogger()->warn("Sending JSON dataType message 'Type', "
					  "not blocking issue:  |%s| - message |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   (m_changeTypeId ? "Data Type " : "" ),
                                           e.what(),
                                           m_sender.getHostPort().c_str(),
                                           m_path.c_str(),
                                           typeData.c_str() );
		return false;
	}
	catch (const std::exception& e)
	{
                Logger::getLogger()->error("Sending JSON dataType message 'Type' "
					   "- generic error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
                                           e.what(),
                                           m_sender.getHostPort().c_str(),
                                           m_path.c_str(),
                                           typeData.c_str() );

		return false;
	}

	// Create header for Container
	vector<pair<string, string>> resContainer = OMF::createMessageHeader("Container");
	// Create data for Container message	
	string typeContainer = OMF::createContainerData(row);

	// Build an HTTPS POST with 'resContainer' headers
	// and 'typeContainer' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{
		res = m_sender.sendRequest("POST",
					   m_path,
					   resContainer,
					   typeContainer);
		if  ( ! (res >= 200 && res <= 299) )
		{
			Logger::getLogger()->error("Sending JSON dataType message 'Container' "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
						   res,
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   typeContainer.c_str() );
			return false;
		}
	}
	// Exception raised fof HTTP 400 Bad Request
	catch (const BadRequest& e)
	{
		if (OMF::isDataTypeError(e.what()))
		{
			// Data type error: force type-id change
			m_changeTypeId = true;
		}
		Logger::getLogger()->warn("Sending JSON dataType message 'Container' "
					   "not blocking issue: |%s| - message |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   (m_changeTypeId ? "Data Type " : "" ),
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   typeContainer.c_str() );
		return false;
	}
	catch (const std::exception& e)
	{
		Logger::getLogger()->error("Sending JSON dataType message 'Container' "
					   "- generic error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   typeContainer.c_str() );
		return false;
	}

	// Create header for Static data
	vector<pair<string, string>> resStaticData = OMF::createMessageHeader("Data");
	// Create data for Static Data message	
	string typeStaticData = OMF::createStaticData(row);

	// Build an HTTPS POST with 'resStaticData' headers
	// and 'typeStaticData' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{
		res = m_sender.sendRequest("POST",
					   m_path,
					   resStaticData,
					   typeStaticData);
		if  ( ! (res >= 200 && res <= 299) )
		{
			Logger::getLogger()->error("Sending JSON dataType message 'StaticData' "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
						   res,
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   typeStaticData.c_str() );
			return false;
		}
	}
	// Exception raised fof HTTP 400 Bad Request
	catch (const BadRequest& e)
	{
		if (OMF::isDataTypeError(e.what()))
		{
			// Data type error: force type-id change
			m_changeTypeId = true;
		}
		Logger::getLogger()->warn("Sending JSON dataType message 'StaticData'"
					   "not blocking issue: |%s| - message |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   (m_changeTypeId ? "Data Type " : "" ),
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   typeStaticData.c_str() );
		return false;
	}
	catch (const std::exception& e)
	{
		Logger::getLogger()->error("Sending JSON dataType message 'StaticData'"
					   "- generic error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   typeStaticData.c_str() );
		return false;
	}

	// Create header for Link data
	vector<pair<string, string>> resLinkData = OMF::createMessageHeader("Data");
	// Create data for Static Data message	
	string typeLinkData = OMF::createLinkData(row);

	// Build an HTTPS POST with 'resLinkData' headers
	// and 'typeLinkData' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{
		res = m_sender.sendRequest("POST",
					   m_path,
					   resLinkData,
					   typeLinkData);
		if  ( ! (res >= 200 && res <= 299) )
		{
			Logger::getLogger()->error("Sending JSON dataType message 'Data' (lynk) "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
						   res,
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   typeLinkData.c_str() );
			return false;
		}
		else
		{
			// All data types sent: success
			return true;
		}
	}
	// Exception raised fof HTTP 400 Bad Request
	catch (const BadRequest& e)
	{
		if (OMF::isDataTypeError(e.what()))
		{
			// Data type error: force type-id change
			m_changeTypeId = true;
		}
		Logger::getLogger()->warn("Sending JSON dataType message 'Data' (lynk) "
					   "not blocking issue: |%s| - message |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   (m_changeTypeId ? "Data Type " : "" ),
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   typeLinkData.c_str() );
		return false;
	}
	catch (const std::exception& e)
	{
		Logger::getLogger()->error("Sending JSON dataType message 'Data' (lynk) "
					   "- generic error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   typeLinkData.c_str() );
		return false;
	}
}

/**
 * AFHierarchy - send an OMF message
 *
 * @param msgType    message type : Type, Data
 * @param jsonData   OMF message to send

 */
bool OMF::AFHierarchySendMessage(const string& msgType, string& jsonData)
{
	bool success = true;
	int res = 0;
	string errorMessage;

	vector<pair<string, string>> resType = OMF::createMessageHeader(msgType);

	try
	{
		res = m_sender.sendRequest("POST", m_path, resType, jsonData);
		if  ( ! (res >= 200 && res <= 299) )
		{
			success = false;
		}
	}
	catch (const BadRequest& ex)
	{
		success = false;
		errorMessage = ex.what();
	}
	catch (const std::exception& ex)
	{
		success = false;
		errorMessage = ex.what();
	}

	if (! success)
	{
		if (res != 0)
			Logger::getLogger()->error("Sending JSON  Asset Framework hierarchy, "
						   "- HTTP code |%d| - error message |%s| - HostPort |%s| - path |%s| message type |%s| - OMF message |%s|",
						   res,
						   errorMessage.c_str(),
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   msgType.c_str(),
						   jsonData.c_str() );
		else
			Logger::getLogger()->error("Sending JSON  Asset Framework hierarchy, "
						   "- error message |%s| - HostPort |%s| - path |%s| message type |%s| - OMF message |%s|",
						   errorMessage.c_str(),
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   msgType.c_str(),
						   jsonData.c_str() );

	}

	return success;
}

/**
 * AFHierarchy - handles OMF types definition
 *
 */
bool OMF::sendAFHierarchyTypes()
{
	bool success;
	string jsonData;
	string tmpStr;

	jsonData = "";
	tmpStr = AF_HIERARCHY_1LEVEL_TYPE;
	StringReplace(tmpStr, "_placeholder_typeid_", m_AFHierarchy1Level + "_typeid");
	jsonData.append(tmpStr);

	success = AFHierarchySendMessage("Type", jsonData);

	return success;
}

/**
 *  AFHierarchy - handles OMF static data
 *
 */
bool OMF::sendAFHierarchyStatic()
{
	bool success;
	string jsonData;
	string tmpStr;

	jsonData = "";
	tmpStr = AF_HIERARCHY_1LEVEL_STATIC;
	StringReplace(tmpStr, "_placeholder_typeid_" , m_AFHierarchy1Level + "_typeid");
	StringReplace(tmpStr, "_placeholder_"        , m_AFHierarchy1Level);
	jsonData.append(tmpStr);

	success = AFHierarchySendMessage("Data", jsonData);

	return success;
}

/**
 * Add the 1st level of AF hierarchy if the end point is PI Web API
 * The hierarchy is created/recreated if an OMF type message is sent
 *
 */
bool OMF::sendAFHierarchy()
{
	bool success = true;

	if (m_PIServerEndpoint.compare("p") == 0)
	{
		success = sendAFHierarchyTypes();
		if (success)
		{
			success = sendAFHierarchyStatic();
		}

	}
	return success;
}

/**
 * Send all the readings to the PI Server
 *
 * @param readings            A vector of readings data pointers
 * @param skipSendDataTypes   Send datatypes only once (default is true)
 * @return                    != on success, 0 otherwise
 */
uint32_t OMF::sendToServer(const vector<Reading *>& readings,
			   bool compression, bool skipSentDataTypes)
{
	bool AFHierarchySent = false;

	std::map<string, Reading*> superSetDataPoints;

	// Create a superset of all found datapoints for each assetName
	// the superset[assetName] is then passed to routines which handle
	// creation of OMF data types
	OMF::setMapObjectTypes(readings, superSetDataPoints);

	/*
	 * Iterate over readings:
	 * - Send/cache Types
	 * - transform a reading to OMF format
	 * - add OMF data to new vector
	 */

	// Used for logging
	string json_not_compressed;

	bool pendingSeparator = false;
	ostringstream jsonData;
	jsonData << "[";

	// Fetch Reading* data
	for (vector<Reading *>::const_iterator elem = readings.begin();
						    elem != readings.end();
						    ++elem)
	{
		bool sendDataTypes;

		// Create the key for dataTypes sending once
		long typeId = OMF::getAssetTypeId((**elem).getAssetName());
		string key((**elem).getAssetName());

		sendDataTypes = (m_lastError == false && skipSentDataTypes == true) ?
				 // Send if not already sent
				 !OMF::getCreatedTypes(key) :
				 // Always send types
				 true;

		Reading* datatypeStructure = NULL;
		if (sendDataTypes)
		{
			// Get the supersetDataPoints for current assetName
			auto it = superSetDataPoints.find((**elem).getAssetName());
			if (it != superSetDataPoints.end())
			{
				datatypeStructure = (*it).second;
			}
		}

		// The AF hierarchy is created/recreated if an OMF type message is sent
		if (sendDataTypes and ! AFHierarchySent)
		{
			sendAFHierarchy();
			AFHierarchySent = true;
		}

		// Check first we have supersetDataPoints for the current reading
		if ((sendDataTypes && datatypeStructure == NULL) ||
		    // Handle the data types of the current reading
		    (sendDataTypes &&
		    // Send data type
		    !OMF::handleDataTypes(*datatypeStructure, skipSentDataTypes) &&
		    // Data type not sent: 
		    (!m_changeTypeId ||
		     // Increment type-id and re-send data types
		     !OMF::handleTypeErrors(*datatypeStructure))))
		{
			// Remove all assets supersetDataPoints
			OMF::unsetMapObjectTypes(superSetDataPoints);

			// Failure
			m_lastError = true;
			return 0;
		}

		// Add into JSON string the OMF transformed Reading data
		string outData = OMFData(**elem, typeId, m_PIServerEndpoint, m_AFHierarchy1Level ).OMFdataVal();
		if (!outData.empty())
		{
			jsonData << (pendingSeparator ? ", " : "") << outData;
			pendingSeparator = true;
		}
	}

	// Remove all assets supersetDataPoints
	OMF::unsetMapObjectTypes(superSetDataPoints);

	jsonData << "]";

	string json = jsonData.str();
	json_not_compressed = json;

	if (compression)
	{
		json = compress_string(json);
	}

	/**
	 * Types messages sent, now transform each reading to OMF format.
	 *
	 * After formatting the new vector of data can be sent
	 * with one message only
	 */

	// Create header for Readings data
	vector<pair<string, string>> readingData = OMF::createMessageHeader("Data");
	if (compression)
		readingData.push_back(pair<string, string>("compression", "gzip"));

	// Build an HTTPS POST with 'readingData headers
	// and 'allReadings' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{
		int res = m_sender.sendRequest("POST",
					       m_path,
					       readingData,
					       json);
		if  ( ! (res >= 200 && res <= 299) )
		{
			Logger::getLogger()->error("Sending JSON readings, "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
						   res,
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   json_not_compressed.c_str() );
			m_lastError = true;
			return 0;
		}
		// Reset error indicator
		m_lastError = false;

		// Return number of sent readings to the caller
		return readings.size();
	}
	// Exception raised fof HTTP 400 Bad Request
	catch (const BadRequest& e)
        {
		if (OMF::isDataTypeError(e.what()))
		{
			// Some assets have invalid or redefined data type
			// NOTE:
			//
			// 1- We consider this a NOT blocking issue.
			// 2- Type-id is not incremented
			// 3- Data Types cache is cleared: next sendData call
			//    will send data types again.
			Logger::getLogger()->warn("Sending JSON readings, "
						  "not blocking issue: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
						  e.what(),
						  m_sender.getHostPort().c_str(),
						  m_path.c_str(),
						  json_not_compressed.c_str() );

			// Extract assetName from error message
			string assetName = OMF::getAssetNameFromError(e.what());
			if (assetName.empty())
			{
				// Reset OMF types cache
				OMF::clearCreatedTypes();
				// Get maximum value among all per asset type-ids
				// if no data, just use current global type-id
				OMF::setTypeId();
				// Increment the new value of global type-id
				OMF::incrementTypeId();

				Logger::getLogger()->warn("Sending JSON readings, "
							  "not blocking issue: assetName not found in error message, "
							  " global 'type-id' has been set to %d "
							  "|%s| - HostPort |%s| - path |%s| - OMF message |%s|",
							  m_typeId,
							  e.what(),
							  m_sender.getHostPort().c_str(),
							  m_path.c_str(),
							  json_not_compressed.c_str());
			}
			else
			{
				// Increment type-id of assetName in in memory cache
				OMF::incrementAssetTypeId(assetName);
				// Remove data and keep type-id
				OMF::clearCreatedTypes(assetName);

				Logger::getLogger()->warn("Sending JSON readings, "
							  "not blocking issue: 'type-id' of assetName '%s' "
							  "has been set to %d "
							  "- HostPort |%s| - path |%s| - OMF message |%s|",
							  assetName.c_str(),
							  OMF::getAssetTypeId(assetName),
							  m_sender.getHostPort().c_str(),
							  m_path.c_str(),
							  json_not_compressed.c_str());
                        }

			// Reset error indicator
			m_lastError = false;

			// It returns size instead of 0 as the rows in the block should be skipped in case of an error
			// as it is considered a not blocking ones.
			return readings.size();
		}
		else
		{
			Logger::getLogger()->error("Sending JSON data error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
			                           e.what(),
			                           m_sender.getHostPort().c_str(),
			                           m_path.c_str(),
			                           json_not_compressed.c_str());
		}
		// Failure
		m_lastError = true;
		return 0;
	}
	catch (const std::exception& e)
	{
		Logger::getLogger()->error("Sending JSON data error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   json_not_compressed.c_str() );
		// Failure
		m_lastError = true;
		return 0;
	}
}

/**
 * Send all the readings to the PI Server
 *
 * @param readings            A vector of readings data
 * @param skipSendDataTypes   Send datatypes only once (default is true)
 * @return                    != on success, 0 otherwise
 */
uint32_t OMF::sendToServer(const vector<Reading>& readings,
			   bool skipSentDataTypes)
{
	/*
	 * Iterate over readings:
	 * - Send/cache Types
	 * - transform a reading to OMF format
	 * - add OMF data to new vector
	 */
	ostringstream jsonData;
	jsonData << "[";

	// Fetch Reading data
	for (vector<Reading>::const_iterator elem = readings.begin();
						    elem != readings.end();
						    ++elem)
	{
		bool sendDataTypes;

		// Create the key for dataTypes sending once
		long typeId = OMF::getAssetTypeId((*elem).getAssetName());
		string key((*elem).getAssetName());

		sendDataTypes = (m_lastError == false && skipSentDataTypes == true) ?
				 // Send if not already sent
				 !OMF::getCreatedTypes(key) :
				 // Always send types
				 true;

		// Handle the data types of the current reading
		if (sendDataTypes && !OMF::handleDataTypes(*elem, skipSentDataTypes))
		{
			// Failure
			m_lastError = true;
			return 0;
		}

		// Add into JSON string the OMF transformed Reading data
		jsonData << OMFData(*elem, typeId, m_PIServerEndpoint, m_AFHierarchy1Level).OMFdataVal() << (elem < (readings.end() -1 ) ? ", " : "");
	}

	jsonData << "]";

	// Build headers for Readings data
	vector<pair<string, string>> readingData = OMF::createMessageHeader("Data");

	// Build an HTTPS POST with 'readingData headers and 'allReadings' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{
		int res = m_sender.sendRequest("POST", m_path, readingData, jsonData.str());

		if  ( ! (res >= 200 && res <= 299) ) {
			Logger::getLogger()->error("Sending JSON readings data "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
				res,
				m_sender.getHostPort().c_str(),
				m_path.c_str(),
                                jsonData.str().c_str() );

			m_lastError = true;
			return 0;
		}
	}
	catch (const std::exception& e)
	{
		Logger::getLogger()->error("Sending JSON readings data "
					   "- generic error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   jsonData.str().c_str() );

		return false;
	}

	m_lastError = false;

	// Return number of sen t readings to the caller
	return readings.size();
}

/**
 * Send a single reading to the PI Server
 *
 * @param reading             A reading to send
 * @return                    != on success, 0 otherwise
 */
uint32_t OMF::sendToServer(const Reading& reading,
			   bool skipSentDataTypes)
{
	return OMF::sendToServer(&reading, skipSentDataTypes);
}

/**
 * Send a single reading pointer to the PI Server
 *
 * @param reading             A reading pointer to send
 * @return                    != on success, 0 otherwise
 */
uint32_t OMF::sendToServer(const Reading* reading,
			   bool skipSentDataTypes)
{
	ostringstream jsonData;
	jsonData << "[";

	if (!OMF::handleDataTypes(*reading, skipSentDataTypes))
	{
		// Failure
		return 0;
	}

	long typeId = OMF::getAssetTypeId((*reading).getAssetName());
	// Add into JSON string the OMF transformed Reading data
	jsonData << OMFData(*reading, typeId, m_PIServerEndpoint, m_AFHierarchy1Level).OMFdataVal();
	jsonData << "]";

	// Build headers for Readings data
	vector<pair<string, string>> readingData = OMF::createMessageHeader("Data");

	// Build an HTTPS POST with 'readingData headers and 'allReadings' JSON payload
	// Then get HTTPS POST ret code and return 0 to client on error
	try
	{

		int res = m_sender.sendRequest("POST", m_path, readingData, jsonData.str());

		if  ( ! (res >= 200 && res <= 299) )
		{
			Logger::getLogger()->error("Sending JSON readings data "
						   "- error: HTTP code |%d| - HostPort |%s| - path |%s| - OMF message |%s|",
						   res,
						   m_sender.getHostPort().c_str(),
						   m_path.c_str(),
						   jsonData.str().c_str() );

			return 0;
		}
	}
	catch (const std::exception& e)
	{
		Logger::getLogger()->error("Sending JSON readings data "
					   "- generic error: |%s| - HostPort |%s| - path |%s| - OMF message |%s|",
					   e.what(),
					   m_sender.getHostPort().c_str(),
					   m_path.c_str(),
					   jsonData.str().c_str() );

		return false;
	}

	// Return number of sent readings to the caller
	return 1;
}

/**
 * Creates a vector of HTTP header to be sent to Server
 *
 * @param type    The message type ('Type', 'Container', 'Data')
 * @return        A vector of HTTP Header string pairs
 */
const vector<pair<string, string>> OMF::createMessageHeader(const std::string& type) const
{
	vector<pair<string, string>> res;

	res.push_back(pair<string, string>("messagetype", type));
	res.push_back(pair<string, string>("producertoken", m_producerToken));
	res.push_back(pair<string, string>("omfversion", "1.0"));
	res.push_back(pair<string, string>("messageformat", "JSON"));
	res.push_back(pair<string, string>("action", "create"));

	return  res; 
}

/**
 * Creates the Type message for data type definition
 *
 * @param reading    A reading data
 * @return           Type JSON message as string
 */
const std::string OMF::createTypeData(const Reading& reading) const
{
	// Build the Type data message (JSON Array)

	// Add the Static data part

	string tData="[";

	tData.append("{ \"type\": \"object\", \"properties\": { ");
	for (auto it = m_staticData->cbegin(); it != m_staticData->cend(); ++it)
	{
		tData.append("\"");
		tData.append(it->first.c_str());
		tData.append("\": {\"type\": \"string\"},");
	}

	if (m_PIServerEndpoint.compare("c") == 0)
	{
		tData.append("\"Name\": { \"type\": \"string\", \"isindex\": true } }, "
					 "\"classification\": \"static\", \"id\": \"");
	}
	else if (m_PIServerEndpoint.compare("p") == 0)
	{
		tData.append("\"Name\": { \"type\": \"string\", \"isname\": true }, ");
		tData.append("\"AssetId\": { \"type\": \"string\", \"isindex\": true } ");
		tData.append(" }, \"classification\": \"static\", \"id\": \"");
	}

	// Add type_id + '_' + asset_name + '_typename_sensor'
	OMF::setAssetTypeTag(reading.getAssetName(),
			     "typename_sensor",
			     tData);

	tData.append("\" }, { \"type\": \"object\", \"properties\": {");


	// Add the Dynamic data part

	/* We add for ech reading
	 * the DataPoint name & type
	 * type is 'integer' for INT
	 * 'number' for FLOAT
	 * 'string' for STRING
	 */

	bool ret = true;
	const vector<Datapoint*> data = reading.getReadingData();

	/**
	 * This loop creates:
	 * "dataName": {"type": "dataType"},
	 */
	for (vector<Datapoint*>::const_iterator it = data.begin(); it != data.end(); ++it)
	{
		string omfType;
		if (!isTypeSupported( (*it)->getData()))
		{
			omfType = OMF_TYPE_UNSUPPORTED;
		}
		else
		{
	        	omfType = omfTypes[((*it)->getData()).getType()];
		}
		string format = OMF::getFormatType(omfType);
		if (format.compare(OMF_TYPE_UNSUPPORTED) == 0)
		{
			//TO DO: ADD LOG
			ret = false;
			continue;
		}
		// Add datapoint Name
		tData.append("\"" + (*it)->getName() + "\"");
		tData.append(": {\"type\": \"");
		// Add datapoint Type
		tData.append(omfType);

		// Applies a format if it is defined
		if (! format.empty() ) {

			tData.append("\", \"format\": \"");
			tData.append(format);
		}

		tData.append("\"}, ");
	}

	// Add time field
	tData.append("\"Time\": {\"type\": \"string\", \"isindex\": true, \"format\": \"date-time\"}}, "
"\"classification\": \"dynamic\", \"id\": \"");

	// Add type_id + '_' + asset_name + '__typename_measurement'
	OMF::setAssetTypeTag(reading.getAssetName(),
			     "typename_measurement",
			     tData);

	tData.append("\" }]");

	// Check we have to return empty data or not
	if (!ret && data.size() == 1)
	{
		// TODO: ADD LOGGING
		return string("");
	}
	else
	{
		// Return JSON string
		return tData;
	}
}

/**
 * Creates the Container message for data type definition
 *
 * @param reading    A reading data
 * @return           Type JSON message as string
 */
const std::string OMF::createContainerData(const Reading& reading) const
{
	string assetName = reading.getAssetName();

	string measurementId;

	// Build the Container data (JSON Array)
	string cData = "[{\"typeid\": \"";

	// Add type_id + '_' + asset_name + '__typename_measurement'
	OMF::setAssetTypeTag(assetName,
			     "typename_measurement",
			     cData);

	measurementId = to_string(OMF::getAssetTypeId(assetName)) + "measurement_" + assetName;

	// Add the 1st level of AFHierarchy as a prefix to the name in case of PI Web API
	if (m_PIServerEndpoint.compare("p") == 0)
	{
		measurementId = m_AFHierarchy1Level + "_" + measurementId;
	}

	cData.append("\", \"id\": \"" + measurementId);
	cData.append("\"}]");

	// Return JSON string
	return cData;
}

/**
 * Creates the Static Data message for data type definition
 *
 * Note: type is 'Data'
 *
 * @param reading    A reading data
 * @return           Type JSON message as string
 */
const std::string OMF::createStaticData(const Reading& reading) const
{
	// Build the Static data (JSON Array)
	string sData = "[";

	sData.append("{\"typeid\": \"");

	// Add type_id + '_' + asset_name + '_typename_sensor'
	OMF::setAssetTypeTag(reading.getAssetName(),
			     "typename_sensor",
			     sData);

	sData.append("\", \"values\": [{");
	for (auto it = m_staticData->cbegin(); it != m_staticData->cend(); ++it)
	{
		sData.append("\"");
		sData.append(it->first.c_str());
		sData.append("\": \"");
		sData.append(it->second.c_str());
		sData.append("\", ");
	}
	sData.append(" \"Name\": \"");

	// Add asset_name
	if (m_PIServerEndpoint.compare("c") == 0)
	{
		sData.append(reading.getAssetName());
	}
	else if (m_PIServerEndpoint.compare("p") == 0)
	{
		sData.append(reading.getAssetName());
		sData.append("\", \"AssetId\": \"");
		sData.append(m_AFHierarchy1Level + "_" + reading.getAssetName());
	}

	sData.append("\"}]}]");

	// Return JSON string
	return sData;
}

/**
 * Creates the Link Data message for data type definition
 *
 * Note: type is 'Data'
 *
 * @param reading    A reading data
 * @return           Type JSON message as string
 */
const std::string OMF::createLinkData(const Reading& reading) const
{
	string measurementId;
	string assetName = reading.getAssetName();
	// Build the Link data (JSON Array)

	string lData = "[{\"typeid\": \"__Link\", \"values\": [";

	// Handles the structure for the Connector Relay
	// not supported by PI Web API
	if (m_PIServerEndpoint.compare("c") == 0)
	{
		lData.append("{\"source\": {\"typeid\": \"");

		// Add type_id + '_' + asset_name + '__typename_sensor'
		OMF::setAssetTypeTag(assetName,
				     "typename_sensor",
				     lData);

		lData.append("\", \"index\": \"_ROOT\"},");
		lData.append("\"target\": {\"typeid\": \"");

		// Add type_id + '_' + asset_name + '__typename_sensor'
		OMF::setAssetTypeTag(assetName,
				     "typename_sensor",
				     lData);

		lData.append("\", \"index\": \"");

		// Add asset_name
		lData.append(assetName);

		lData.append("\"}},");
	}
	else if (m_PIServerEndpoint.compare("p") == 0)
	{
		// Link the asset to the 1st level of AF hierarchy if the end point is PI Web API

		string tmpStr = AF_HIERARCHY_1LEVEL_LINK;
		string targetTypeId;

		OMF::setAssetTypeTag(assetName, "typename_sensor", targetTypeId);

		StringReplace(tmpStr, "_placeholder_src_type_", m_AFHierarchy1Level + "_typeid");
		StringReplace(tmpStr, "_placeholder_src_idx_",  m_AFHierarchy1Level );
		StringReplace(tmpStr, "_placeholder_tgt_type_", targetTypeId);
		StringReplace(tmpStr, "_placeholder_tgt_idx_",  m_AFHierarchy1Level + "_" + assetName);

		lData.append(tmpStr);
		lData.append(",");
	}

	lData.append("{\"source\": {\"typeid\": \"");

	// Add type_id + '_' + asset_name + '__typename_sensor'
	OMF::setAssetTypeTag(assetName,
			     "typename_sensor",
			     lData);

	lData.append("\", \"index\": \"");

	if (m_PIServerEndpoint.compare("c") == 0)
	{
		// Add asset_name
		lData.append(assetName);
	}
	else if (m_PIServerEndpoint.compare("p") == 0)
	{
		lData.append(m_AFHierarchy1Level + "_" + assetName);
	}

	measurementId = to_string(OMF::getAssetTypeId(assetName)) + "measurement_" + assetName;

	// Add the 1st level of AFHierarchy as a prefix to the name in case of PI Web API
	if (m_PIServerEndpoint.compare("p") == 0)
	{
		measurementId = m_AFHierarchy1Level + "_" + measurementId;
	}

	lData.append("\"}, \"target\": {\"containerid\": \"" + measurementId);

	lData.append("\"}}]}]");

	// Return JSON string
	return lData;
}

/**
 * Set the tag ID_XYZ_typename_sensor|typename_measurement
 *
 * @param assetName    The assetName
 * @param tagName      The tagName to append
 * @param data         The string to append result tag
 */
void OMF::setAssetTypeTag(const string& assetName,
			  const string& tagName,
			  string& data) const
{

	string AssetTypeTag = to_string(this->getAssetTypeId(assetName)) +
		              "_" + assetName +
		              "_" + tagName;

	// Add the 1st level of AFHierarchy as a prefix to the name in case of PI Web API
	if (m_PIServerEndpoint.compare("p") == 0)
	{
		AssetTypeTag = m_AFHierarchy1Level + "_" + AssetTypeTag;
	}
	// Add type-id + '_' + asset_name + '_' + tagName'
	data.append(AssetTypeTag);
}

/**
 * Handles the OMF data types for the current Reading row
 * DataTypoes are created and sent only once per assetName + typeId
 * if skipSending is true
 *
 * @param row            The current Reading row with data
 * @param skipSending    Send once or always the data types
 * @return               True if data types have been sent or already sent.
 *                       False if the sending has failed.
 */ 
bool OMF::handleDataTypes(const Reading& row,
			  bool skipSending)
{
	// Create the key for dataTypes sending once
	const string key(skipSending ? (row.getAssetName()) : "");

	// Check whether to create and send Data Types
	bool sendTypes = (skipSending == true) ?
			  // Send if not already sent
			  !OMF::getCreatedTypes(key) :
			  // Always send types
			  true;

	// Handle the data types of the current reading
	if (sendTypes && !OMF::sendDataTypes(row))
	{
		// Failure
		return false;
	}

	// We have sent types, we might save this.
	if (skipSending && sendTypes)
	{
		// Save datatypes key
		OMF::setCreatedTypes(row);
	}

	// Success
	return true;
}

/**
 * Get from m_formatTypes map the key (OMF type + OMF format)
 *
 * @param key    The OMF type for which the format is requested
 * @return       The defined OMF format for the requested type
 *
 */
std::string OMF::getFormatType(const string &key) const
{
        string value;

        try
        {
                auto pos = m_formatTypes.find(key);
                value = pos->second;
        }
        catch (const std::exception& e)
        {
                Logger::getLogger()->error("Unable to find the OMF format for the type :" + key + ": - error: %s", e.what());
        }

        return value;
}

/**
 * Add the key (OMF type + OMF format) into a map
 *
 * @param key    The OMF type, key of the map
 * @param value  The OMF format to set for the specific OMF type
 *
 */
void OMF::setFormatType(const string &key, string &value)
{

	m_formatTypes[key] = value;
}

/**
 * Set which PIServer component should be used for the communication
 */
void OMF::setPIServerEndpoint(const string &PIServerEndpoint)
{
	m_PIServerEndpoint = PIServerEndpoint;
}

/**
 * Set the first level of hierarchy in Asset Framework in which the assets will be created, PI Web API only.
 */
void OMF::setAFHierarchy1Level(const string &AFHierarchy1Level)
{
	m_AFHierarchy1Level = AFHierarchy1Level;
}


/**
 * Set the list of errors considered not blocking in the communication
 * with the PI Server
 */
void OMF::setNotBlockingErrors(std::vector<std::string>& notBlockingErrors)
{

	m_notBlockingErrors = notBlockingErrors;
}


/**
 * Increment type-id
 */
void OMF::incrementTypeId()
{
	++m_typeId;
}

/**
 * Clear OMF types cache
 */
void OMF::clearCreatedTypes()
{
	if (m_OMFDataTypes)
	{
		m_OMFDataTypes->clear();
	}
}

/**
 * Check for invalid/redefinition data type error
 *
 * @param message       Server reply message for data type creation
 * @return              True for data type error, false otherwise
 */
bool OMF::isDataTypeError(const char* message)
{
	if (message)
	{
		string serverReply(message);

		for(string &item : m_notBlockingErrors) {

			if (serverReply.find(item) != std::string::npos)
			{
				return true;
			}
		}
	}
	return false;
}

/**
 * Send again Data Types of current readind data
 * with a new type-id
 *
 * NOTE: the m_typeId member variable value is incremented.
 *
 * @param reading       The current reading data
 * @return              True if data types with new-id
 *                      have been sent, false otherwise.
 */
bool OMF::handleTypeErrors(const Reading& reading)
{
	bool ret = true;
	string key = reading.getAssetName();

	// Reset change type-id indicator
	m_changeTypeId = false;

	// Increment per asset type-id in memory cache:
	// Note: if key is not found the global type-id is incremented
	OMF::incrementAssetTypeId(key);

	// Clear per asset data (but keep the type-id) if key found
	// or remove all data otherwise
	auto it = m_OMFDataTypes->find(key);
	if (it != m_OMFDataTypes->end())
	{
		// Clear teh OMF types cache per asset, keep type-id
		OMF::clearCreatedTypes(key);
	}
	else
	{
		// Remove all cached data, any asset
		OMF::clearCreatedTypes();
	}

	// Force re-send data types with a new type-id
	if (!OMF::handleDataTypes(reading,
				  false))
	{
		Logger::getLogger()->error("Failure re-sending JSON dataType messages "
					   "with new type-id=%d for asset %s",
					   OMF::getAssetTypeId(key),
					   key.c_str());
		// Failure
		m_lastError = true;
		ret = false;
	}

	return ret;
}

/**
 * Create a superset data map for each reading and found datapoints
 *
 * The output map is filled with a Reading object containing
 * all the datapoints found for each asset in the inoput reading set.
 * The datapoint have a fake value based on the datapoint type
 *  
 * @param    readings		Current input readings data
 * @param    dataSuperSet	Map to store all datapoints for an assetname
 */
void OMF::setMapObjectTypes(const vector<Reading*>& readings,
			    std::map<std::string, Reading*>& dataSuperSet) const
{
	// Temporary map for [asset][datapoint] = type
	std::map<string, map<string, string>> readingAllDataPoints;

	// Fetch ALL Reading pointers in the input vector
	// and create a map of [assetName][datapoint1 .. datapointN] = type
	for (vector<Reading *>::const_iterator elem = readings.begin();
						elem != readings.end();
						++elem)
	{
		// Get asset name
		string assetName = (**elem).getAssetName();
		// Get all datapoints
		const vector<Datapoint*> data = (**elem).getReadingData();
		// Iterate through datapoints
		for (vector<Datapoint*>::const_iterator it = data.begin();
							it != data.end();
							++it)
		{
			string omfType;
			if (!isTypeSupported((*it)->getData()))
			{
				omfType = OMF_TYPE_UNSUPPORTED;
			}
			else
			{
				omfType = omfTypes[((*it)->getData()).getType()];
			}
			string datapointName = (*it)->getName();

			auto itr = readingAllDataPoints.find(assetName);
			// Asset not found in the map
			if (itr == readingAllDataPoints.end())
			{
				// Set type of current datapoint for ssetName
				readingAllDataPoints[assetName][datapointName] = omfType;
			}
			else
			{
				// Asset found
				auto dpItr = (*itr).second.find(datapointName);
				// Datapoint not found
				if (dpItr == (*itr).second.end())
				{
					// Add datapointName/type to map with key assetName
					(*itr).second.emplace(datapointName, omfType);
				}
				else
				{
					if ((*dpItr).second.compare(omfType) != 0)
					{
						// Datapoint already set has changed type
						Logger::getLogger()->warn("Datapoint '" + datapointName + \
									  "' in asset '" + assetName + \
									  "' has changed type from '" + (*dpItr).second + \
									  " to " + omfType);
					}

					// Update datapointName/type to map with key assetName
					// 1- remove element
					(*itr).second.erase(dpItr);	
					// 2- Add new value
					readingAllDataPoints[assetName][datapointName] = omfType;
				}
			}
		}
	}

	// Loop now only the elements found in the per asset types map
	for (auto it = readingAllDataPoints.begin();
		  it != readingAllDataPoints.end();
		  ++it)
	{
		string assetName = (*it).first;
		vector<Datapoint *> values;
		// Set fake datapoints values
		for (auto dp = (*it).second.begin();
			  dp != (*it).second.end();
			  ++dp)
		{
			if ((*dp).second.compare(OMF_TYPE_FLOAT) == 0)
			{
				DatapointValue vDouble(0.1);
				values.push_back(new Datapoint((*dp).first, vDouble));
			}
			else if ((*dp).second.compare(OMF_TYPE_INTEGER) == 0)
			{
				DatapointValue vInt((long)1);
				values.push_back(new Datapoint((*dp).first, vInt));
			}
			else if ((*dp).second.compare(OMF_TYPE_STRING) == 0)
			{
				DatapointValue vString("v_str");
				values.push_back(new Datapoint((*dp).first, vString));
			}
			else if ((*dp).second.compare(OMF_TYPE_UNSUPPORTED) == 0)
			{
				std::vector<double> vData = {0};
				DatapointValue vArray(vData);
				values.push_back(new Datapoint((*dp).first, vArray));
			}
		}

		// Add the superset Reading data with fake values
		dataSuperSet.emplace(assetName, new Reading(assetName, values));
	}
}

/**
 * Cleanup the mapped object types for input data
 *
 * @param    dataSuperSet	The  mapped object to cleanup
 */
void OMF::unsetMapObjectTypes(std::map<std::string, Reading*>& dataSuperSet) const
{
	// Remove all assets supersetDataPoints
	for (auto m = dataSuperSet.begin();
		  m != dataSuperSet.end();
		  ++m)
	{
		(*m).second->removeAllDatapoints();
		delete (*m).second;
	}
	dataSuperSet.clear();
}
/**
 * Extract assetName from error message
 *
 * Currently handled cases
 * (1) $datasource + "." + $id + "_" + $assetName + "_typename_measurement" + ...
 * (2) $id + "measurement_" + $assetName
 *
 * @param    message		OMF error message (JSON)
 * @return   The found assetName if found, or empty string
 */
string OMF::getAssetNameFromError(const char* message)
{
	string assetName;
	Document error;

	error.Parse(message);

	if (!error.HasParseError() &&
	    error.HasMember("source") &&
	    error["source"].IsString())
	{
		string tmp = error["source"].GetString();

		// (1) $datasource + "." + $id + "_" + $assetName + "_typename_measurement" + ...
		size_t found = tmp.find("_typename_measurement");
		if (found != std::string::npos)
		{
			tmp = tmp.substr(0, found);
			found = tmp.find_first_of('.');
			if (found != std::string::npos &&
			    found < tmp.length())
			{
				tmp = tmp.substr(found + 1);
				found = tmp.find_first_of('_');
				if (found != std::string::npos &&
				    found < tmp.length())
				{
					assetName = assetName.substr(found + 1 );
				}
			}
		}
		else
		{
			// (2) $id + "measurement_" + $assetName
			found = tmp.find_first_of('_');
			if (found != std::string::npos &&
			    found < tmp.length())
			{
				assetName = tmp.substr(found + 1);
			}
		}
	}

	return assetName;
}

/**
 * Return the asset type-id
 *
 * @param assetName	The asset name
 * @return		The found type-id
 *			or the generic value
 */
long OMF::getAssetTypeId(const string& assetName) const
{
	long typeId;
	if (!m_OMFDataTypes)
	{
		// Use current value of m_typeId
		typeId = m_typeId;
	}
	else
	{
		auto it = m_OMFDataTypes->find(assetName);
		if (it != m_OMFDataTypes->end())
		{
			// Set the type-id of found element
			typeId = ((*it).second).typeId;
		}
		else
		{
			// Use current value of m_typeId
			typeId = m_typeId;
		}
	}
	return typeId;
}

/**
 * Increment the type-id for the given asset name
 *
 * If cached data pointer is NULL or asset name is not set
 * the global m_typeId is incremented.
 *
 * @param    assetName		The asset name
 *				which type-id sequence
 *				has to be incremented.
 */
void OMF::incrementAssetTypeId(const std::string& assetName)
{
	long typeId;
	if (!m_OMFDataTypes)
        {
                // Increment current value of m_typeId
		OMF::incrementTypeId();
        }
	else
	{
		auto it = m_OMFDataTypes->find(assetName);
		if (it != m_OMFDataTypes->end())
		{
			// Increment value of found type-id
			++((*it).second).typeId;
		}
		else
		{
                	// Increment current value of m_typeId
			OMF::incrementTypeId();
		}
	}
}

/**
 * Add the reading asset namekey into a map
 * That key is checked by getCreatedTypes in order
 * to send dataTypes only once
 *
 * @param row    The reading data row
 * @return       True, false if map pointer is NULL
 */
bool OMF::setCreatedTypes(const Reading& row)
{
	if (!m_OMFDataTypes)
	{
		return false;
	}

	string types;
	string key;

	if (m_PIServerEndpoint.compare("c") == 0)
	{
		key = row.getAssetName();
	}
	else if (m_PIServerEndpoint.compare("p") == 0)
	{
		key = m_AFHierarchy1Level + "_" + row.getAssetName();
	}


	long typeId = OMF::getAssetTypeId(key);
	const vector<Datapoint*> data = row.getReadingData();
	types.append("{");
	for (vector<Datapoint*>::const_iterator it = data.begin();
						(it != data.end() &&
						 isTypeSupported((*it)->getData()));
						++it)
	{
		if (it != data.begin())
		{
			types.append(", ");
		}

		string omfType;
		if (!isTypeSupported((*it)->getData()))
		{
			omfType = OMF_TYPE_UNSUPPORTED;
			continue;
		}
		else
		{
			omfType = omfTypes[((*it)->getData()).getType()];
		}

		string format = OMF::getFormatType(omfType);

		// Add datapoint Name
		types.append("\"" + (*it)->getName() + "\"");
		types.append(": {\"type\": \"");
		// Add datapoint Type
		types.append(omfType);

		// Applies a format if it is defined
		if (!format.empty())
		{
			types.append("\", \"format\": \"");
			types.append(format);
		}

		types.append("\"}");
	}
	types.append("}");

	if (m_OMFDataTypes->find(key) == m_OMFDataTypes->end())
	{
		// New entry
		OMFDataTypes newData;
		// Start from default as we don't have anything in the cache
		newData.typeId = m_typeId;
		newData.types = types;
		(*m_OMFDataTypes)[key] = newData;
	}
	else
	{
		// Just update dataTypes and keep the typeId
		(*m_OMFDataTypes)[key].types = types;
	}

	return true;
}

/**
 * Set a new value for global type-id
 *
 * new value is the maximum value of
 * type-id among all asset datatypes
 * or
 * the current value of m_typeId
 */
void OMF::setTypeId()
{
	long maxId = m_typeId;
	for (auto it = m_OMFDataTypes->begin();
		  it != m_OMFDataTypes->end();
		  ++it)
	{
		if ((*it).second.typeId > maxId)
		{
			maxId = (*it).second.typeId;
		}
	}
	m_typeId = maxId;
}

/**
 * Clear OMF types cache for given asset name
 * but keep the type-id
 */
void OMF::clearCreatedTypes(const string& key)
{
	if (m_OMFDataTypes)
	{
		auto it = m_OMFDataTypes->find(key);
		if (it != m_OMFDataTypes->end())
		{
			// Just clear data types
			(*it).second.types = "";
		}
	}
}

/**
 * Check the key (assetName) is set and not empty
 * in the per asset data types cache.
 *
 * @param key    The data type key (assetName) from the Reading row
 * @return       True is the key exists and data value is not empty:
 *		 this means the dataTypes were already sent
 *		 Found key with empty value means the data types
 *		 must be sent again with the new type-id.
 *               Return false if the key is not found or found but empty.
 */
bool OMF::getCreatedTypes(const string& key)
{
	bool ret;
	if (!m_OMFDataTypes)
	{
		ret = false;
	}
	else
	{
		auto it = m_OMFDataTypes->find(key);
		ret = (it != m_OMFDataTypes->end()) && !(*m_OMFDataTypes)[key].types.empty();
	}
	return ret;
}

/**
 * Check whether input Datapoint type is supported by OMF class
 *
 * @param    dataPoint		Input data
 * @return			True is fupported, false otherwise
 */ 

static bool isTypeSupported(DatapointValue& dataPoint)
{
	if (dataPoint.getType() == DatapointValue::DatapointTag::T_FLOAT_ARRAY ||
	    dataPoint.getType() == DatapointValue::DatapointTag::T_DP_DICT ||
	    dataPoint.getType() == DatapointValue::DatapointTag::T_DP_LIST)
	{
		return false;
	}
	else
	{
		return true;
	}
}
