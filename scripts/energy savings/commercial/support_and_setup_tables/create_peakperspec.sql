/*
Navicat PGSQL Data Transfer

Source Server         : DEER_Local
Source Server Version : 90405
Source Host           : localhost:5432
Source Database       : deer2020
Source Schema         : comairac

Target Server Type    : PGSQL
Target Server Version : 90405
File Encoding         : 65001

Date: 2018-08-23 13:31:00
*/


-- ----------------------------
-- Table structure for peakperspec
-- ----------------------------
SET search_path TO "MC_results_database";
DROP TABLE IF EXISTS "peakperspec";
CREATE TABLE "peakperspec" (
"BldgLoc" text COLLATE "default",
"PkDay" text COLLATE "default",
"PkHr" text COLLATE "default"
)
WITH (OIDS=FALSE)

;

-- ----------------------------
-- Records of peakperspec
-- Updated for CZ2022 weather data, 3/29/2021
-- ----------------------------
INSERT INTO "peakperspec" VALUES ('CZ01', '238', '0');
INSERT INTO "peakperspec" VALUES ('CZ02', '238', '0');
INSERT INTO "peakperspec" VALUES ('CZ03', '238', '0');
INSERT INTO "peakperspec" VALUES ('CZ04', '238', '0');
INSERT INTO "peakperspec" VALUES ('CZ05', '259', '0');
INSERT INTO "peakperspec" VALUES ('CZ06', '245', '0');
INSERT INTO "peakperspec" VALUES ('CZ07', '245', '0');
INSERT INTO "peakperspec" VALUES ('CZ08', '245', '0');
INSERT INTO "peakperspec" VALUES ('CZ09', '244', '0');
INSERT INTO "peakperspec" VALUES ('CZ10', '180', '0');
INSERT INTO "peakperspec" VALUES ('CZ11', '180', '0');
INSERT INTO "peakperspec" VALUES ('CZ12', '180', '0');
INSERT INTO "peakperspec" VALUES ('CZ13', '180', '0');
INSERT INTO "peakperspec" VALUES ('CZ14', '180', '0');
INSERT INTO "peakperspec" VALUES ('CZ15', '180', '0');
INSERT INTO "peakperspec" VALUES ('CZ16', '224', '0');

-- ----------------------------
-- Alter Sequences Owned By 
-- ----------------------------
