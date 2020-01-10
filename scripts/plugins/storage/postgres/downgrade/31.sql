--
-- ADD  the column: read_key   uuid
--

ALTER TABLE readings DROP CONSTRAINT readings_pkey;

CREATE TABLE foglamp.new_readings (
    id         bigint                      NOT NULL DEFAULT nextval('foglamp.readings_id_seq'::regclass),
    asset_code character varying(50)       NOT NULL,                      -- The provided asset code. Not necessarily located in the
                                                                        -- assets table.
    read_key   uuid                        UNIQUE,                        -- An optional unique key used to avoid double-loading.
    reading    jsonb                       NOT NULL DEFAULT '{}'::jsonb,  -- The json object received
    user_ts    timestamp(6) with time zone NOT NULL DEFAULT now(),        -- The user timestamp extracted by the received message
    ts         timestamp(6) with time zone NOT NULL DEFAULT now(),
    CONSTRAINT readings_pkey PRIMARY KEY (id) );


INSERT INTO new_readings
SELECT
    id,
    asset_code,
    -- UUID Generation
    uuid_in(md5(random()::text || clock_timestamp()::text)::cstring),
    reading,
    user_ts,
    ts
FROM readings;

DROP INDEX fki_readings_fk1;
DROP INDEX readings_ix2;
DROP INDEX readings_ix3;

DROP TABLE readings;

ALTER TABLE new_readings rename to readings;

CREATE INDEX fki_readings_fk1
    ON foglamp.readings USING btree (asset_code, user_ts desc);

CREATE INDEX readings_ix2
    ON foglamp.readings USING btree (asset_code);

CREATE INDEX readings_ix3
    ON foglamp.readings USING btree (user_ts);
