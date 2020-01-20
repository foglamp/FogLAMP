#include <gtest/gtest.h>
#include <reading_set.h>
#include <string.h>
#include <string>
#include <rapidjson/document.h>

using namespace std;
using namespace rapidjson;

const char *input = "{ \"count\" : 2, \"rows\" : [ "
	    "{ \"id\": 1, \"asset_code\": \"luxometer\", "
            "\"reading\": { \"lux\": 76204.524 }, "
            "\"user_ts\": \"2017-09-21 15:00:08.532958\", "
            "\"ts\": \"2017-09-22 14:47:18.872708\" }, "
	    "{ \"id\": 2, \"asset_code\": \"luxometer\", "
            "\"reading\": { \"lux\": 76834.361 }, "
            "\"user_ts\": \"2017-09-21 15:00:09.32958\", "
            "\"ts\": \"2017-09-22 14:48:18.72708\" }"
	    "] }";

const char *asset_notification = "{ \"readings\" : [ "
	    "{ \"id\": 1, \"asset_code\": \"luxometer\", "
            "\"reading\": { \"lux\": 76204.524 }, "
            "\"user_ts\": \"2017-09-21 15:00:08.532958\", "
            "\"ts\": \"2017-09-22 14:47:18.872708\" }, "
	    "{ \"id\": 2, \"asset_code\": \"luxometer\", "
            "\"reading\": { \"lux\": 76834.361 }, "
            "\"user_ts\": \"2017-09-21 15:00:09.32958\", "
            "\"ts\": \"2017-09-22 14:48:18.72708\" }"
	    "] }";
TEST(ReadingSet, Count)
{
	ReadingSet readingSet(input);
	ASSERT_EQ(2, readingSet.getCount());
}

TEST(ReadingSet, Index)
{
	ReadingSet readingSet(input);
	const Reading *reading = readingSet[0];
	string json = reading->toJSON();
	ASSERT_NE(json.find(string("\"asset_code\" : \"luxmeter\"")), 0);
	ASSERT_NE(json.find(string("\"reading\" : { \"lux\" : \"76204.524\" }")), 0);
	ASSERT_NE(json.find(string("\"user_ts\" : \"2017-09-22 14:47:18.872708\"")), 0);
}

TEST(ReadingSet, NotificationCount)
{
	ReadingSet readingSet(asset_notification);
	ASSERT_EQ(2, readingSet.getCount());
}

TEST(ReadingSet, NotificationIndex)
{
	ReadingSet readingSet(asset_notification);
	const Reading *reading = readingSet[0];
	string json = reading->toJSON();
	ASSERT_NE(json.find(string("\"asset_code\" : \"luxmeter\"")), 0);
	ASSERT_NE(json.find(string("\"reading\" : { \"lux\" : \"76204.524\" }")), 0);
	ASSERT_NE(json.find(string("\"readkey\" : ")), 0);
	ASSERT_NE(json.find(string("\"user_ts\" : \"2017-09-22 14:47:18.872708\"")), 0);
}
