-- MySQL dump 10.13  Distrib 5.5.31, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: cdt
-- ------------------------------------------------------
-- Server version	5.5.31-0ubuntu0.12.04.1-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `changeset_actions`
--

DROP TABLE IF EXISTS `changeset_actions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_actions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_id` int(11) DEFAULT NULL,
  `type` enum('created','changed','deleted','review started','reviewed','validations passed','validations failed','tests passed','tests failed','approved','rejected','applied') DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_actions`
--

LOCK TABLES `changeset_actions` WRITE;
/*!40000 ALTER TABLE `changeset_actions` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_actions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changeset_applies`
--

DROP TABLE IF EXISTS `changeset_applies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_applies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_id` int(11) DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  `applied_at` datetime DEFAULT NULL,
  `applied_by` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_applies`
--

LOCK TABLES `changeset_applies` WRITE;
/*!40000 ALTER TABLE `changeset_applies` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_applies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changeset_detail_applies`
--

DROP TABLE IF EXISTS `changeset_detail_applies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_detail_applies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_detail_id` int(11) DEFAULT NULL,
  `environment_id` int(11) DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  `results_log` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_detail_applies`
--

LOCK TABLES `changeset_detail_applies` WRITE;
/*!40000 ALTER TABLE `changeset_detail_applies` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_detail_applies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changeset_detail_table_map`
--

DROP TABLE IF EXISTS `changeset_detail_table_map`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_detail_table_map` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_detail_id` int(11) DEFAULT NULL,
  `database_table_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_detail_table_map`
--

LOCK TABLES `changeset_detail_table_map` WRITE;
/*!40000 ALTER TABLE `changeset_detail_table_map` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_detail_table_map` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changeset_details`
--

DROP TABLE IF EXISTS `changeset_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_id` int(11) DEFAULT NULL,
  `description` text,
  `apply_sql` text,
  `revert_sql` text,
  `before_checksum` varchar(255) DEFAULT NULL,
  `after_checksum` varchar(255) DEFAULT NULL,
  `apply_verification_sql` text,
  `volumetric_values` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_details`
--

LOCK TABLES `changeset_details` WRITE;
/*!40000 ALTER TABLE `changeset_details` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changeset_tests`
--

DROP TABLE IF EXISTS `changeset_tests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_tests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_detail_id` int(11) DEFAULT NULL,
  `test_type_id` int(11) DEFAULT NULL,
  `environment_id` int(11) DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  `started_at` datetime DEFAULT NULL,
  `ended_at` datetime DEFAULT NULL,
  `results_log` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_tests`
--

LOCK TABLES `changeset_tests` WRITE;
/*!40000 ALTER TABLE `changeset_tests` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_tests` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changeset_validations`
--

DROP TABLE IF EXISTS `changeset_validations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changeset_validations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `changeset_id` int(11) DEFAULT NULL,
  `validation_type_id` int(11) DEFAULT NULL,
  `timestamp` timestamp NULL DEFAULT NULL,
  `result` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changeset_validations`
--

LOCK TABLES `changeset_validations` WRITE;
/*!40000 ALTER TABLE `changeset_validations` DISABLE KEYS */;
/*!40000 ALTER TABLE `changeset_validations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `changesets`
--

DROP TABLE IF EXISTS `changesets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `changesets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `type` enum('DDL:Table:Create','DDL:Table:Alter','DDL:Table:Drop','DDL:Code:Create','DDL:Code:Alter','DDL:Code:Drop','DML:Insert','DML:Insert:Select','DML:Update','DML:Delete') DEFAULT NULL,
  `classification` enum('painless','lowrisk','dependency','impacting') DEFAULT NULL,
  `version_control_url` varchar(255) DEFAULT NULL,
  `review_status` enum('needs','in_progress','rejected','approved') DEFAULT NULL,
  `reviewed_by` int(11) DEFAULT NULL,
  `approved_by` int(11) DEFAULT NULL,
  `submitted_at` datetime DEFAULT NULL,
  `reviewed_at` datetime DEFAULT NULL,
  `approved_at` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `submitted_by` int(11) DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT NULL,
  `database_schema_id` int(11) DEFAULT NULL,
  `before_version` int(11) DEFAULT NULL,
  `after_version` int(11) DEFAULT NULL,
  `repo_filename` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `changesets`
--

LOCK TABLES `changesets` WRITE;
/*!40000 ALTER TABLE `changesets` DISABLE KEYS */;
/*!40000 ALTER TABLE `changesets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clusters`
--

DROP TABLE IF EXISTS `clusters`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `clusters` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clusters`
--

LOCK TABLES `clusters` WRITE;
/*!40000 ALTER TABLE `clusters` DISABLE KEYS */;
/*!40000 ALTER TABLE `clusters` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `collector_runs`
--

DROP TABLE IF EXISTS `collector_runs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `collector_runs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `collector` varchar(25) DEFAULT NULL,
  `last_run` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `collector` (`collector`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `collector_runs`
--

LOCK TABLES `collector_runs` WRITE;
/*!40000 ALTER TABLE `collector_runs` DISABLE KEYS */;
/*!40000 ALTER TABLE `collector_runs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `database_schemas`
--

DROP TABLE IF EXISTS `database_schemas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `database_schemas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `database_schemas`
--

LOCK TABLES `database_schemas` WRITE;
/*!40000 ALTER TABLE `database_schemas` DISABLE KEYS */;
/*!40000 ALTER TABLE `database_schemas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `database_tables`
--

DROP TABLE IF EXISTS `database_tables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `database_tables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `schema_id` int(11) DEFAULT NULL,
  `cached_size` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `database_tables`
--

LOCK TABLES `database_tables` WRITE;
/*!40000 ALTER TABLE `database_tables` DISABLE KEYS */;
/*!40000 ALTER TABLE `database_tables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `environments`
--

DROP TABLE IF EXISTS `environments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `environments` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `update_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `environments`
--

LOCK TABLES `environments` WRITE;
/*!40000 ALTER TABLE `environments` DISABLE KEYS */;
/*!40000 ALTER TABLE `environments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `explain_results`
--

DROP TABLE IF EXISTS `explain_results`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `explain_results` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `explained_statement_id` int(11) DEFAULT NULL,
  `select_id` int(11) DEFAULT NULL,
  `select_type` text,
  `table` text,
  `type` text,
  `possible_keys` text,
  `key` text,
  `key_len` int(11) DEFAULT NULL,
  `ref` text,
  `rows` int(11) DEFAULT NULL,
  `extra` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `explain_results`
--

LOCK TABLES `explain_results` WRITE;
/*!40000 ALTER TABLE `explain_results` DISABLE KEYS */;
/*!40000 ALTER TABLE `explain_results` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `explained_statements`
--

DROP TABLE IF EXISTS `explained_statements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `explained_statements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dt` datetime DEFAULT NULL,
  `statement` text,
  `hostname` text,
  `canonicalized_statement` text,
  `canonicalized_statement_hash` int(11) DEFAULT NULL,
  `canonicalized_statement_hostname_hash` int(11) DEFAULT NULL,
  `db` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `explained_statements`
--

LOCK TABLES `explained_statements` WRITE;
/*!40000 ALTER TABLE `explained_statements` DISABLE KEYS */;
/*!40000 ALTER TABLE `explained_statements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'admin','2013-04-01 04:02:25','2013-04-01 04:02:25'),(2,'dba','2013-04-01 04:02:31','2013-04-01 04:02:31'),(3,'developer','2013-04-01 04:02:36','2013-04-01 04:02:36');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_migrations`
--

DROP TABLE IF EXISTS `schema_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_migrations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `version` varchar(255) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `version` (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_migrations`
--

LOCK TABLES `schema_migrations` WRITE;
/*!40000 ALTER TABLE `schema_migrations` DISABLE KEYS */;
/*!40000 ALTER TABLE `schema_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_version_history`
--

DROP TABLE IF EXISTS `schema_version_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_version_history` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `environment_id` int(11) DEFAULT NULL,
  `cluster_id` int(11) DEFAULT NULL,
  `server_id` int(11) DEFAULT NULL,
  `schema_id` int(11) DEFAULT NULL,
  `schema_version_id` int(11) DEFAULT NULL,
  `date_applied` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_version_history`
--

LOCK TABLES `schema_version_history` WRITE;
/*!40000 ALTER TABLE `schema_version_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `schema_version_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_versions`
--

DROP TABLE IF EXISTS `schema_versions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `schema_versions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `database_schema_id` int(11) DEFAULT NULL,
  `ddl` text,
  `checksum` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_versions`
--

LOCK TABLES `schema_versions` WRITE;
/*!40000 ALTER TABLE `schema_versions` DISABLE KEYS */;
/*!40000 ALTER TABLE `schema_versions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `server_schemas`
--

DROP TABLE IF EXISTS `server_schemas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `server_schemas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(64) NOT NULL,
  `server_id` int(11) DEFAULT NULL,
  `cached_size` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `server_schemas`
--

LOCK TABLES `server_schemas` WRITE;
/*!40000 ALTER TABLE `server_schemas` DISABLE KEYS */;
/*!40000 ALTER TABLE `server_schemas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servers`
--

DROP TABLE IF EXISTS `servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `servers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `hostname` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `environment_id` int(11) DEFAULT NULL,
  `port` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servers`
--

LOCK TABLES `servers` WRITE;
/*!40000 ALTER TABLE `servers` DISABLE KEYS */;
/*!40000 ALTER TABLE `servers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `snapshots`
--

DROP TABLE IF EXISTS `snapshots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `snapshots` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `txn` int(11) DEFAULT NULL,
  `collector_run_id` int(11) DEFAULT NULL,
  `statistic_id` int(11) DEFAULT NULL,
  `parent_txn` int(11) DEFAULT NULL,
  `run_time` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `snapshots`
--

LOCK TABLES `snapshots` WRITE;
/*!40000 ALTER TABLE `snapshots` DISABLE KEYS */;
/*!40000 ALTER TABLE `snapshots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `statements`
--

DROP TABLE IF EXISTS `statements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `statements` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dt` datetime DEFAULT NULL,
  `statement` text,
  `server_id` int(11) DEFAULT NULL,
  `canonicalized_statement` text,
  `canonicalized_statement_hash` int(11) DEFAULT NULL,
  `canonicalized_statement_hostname_hash` int(11) DEFAULT NULL,
  `query_time` double DEFAULT NULL,
  `lock_time` double DEFAULT NULL,
  `rows_sent` int(11) DEFAULT NULL,
  `rows_examined` int(11) DEFAULT NULL,
  `rows_affected` int(11) DEFAULT NULL,
  `rows_read` int(11) DEFAULT NULL,
  `bytes_sent` int(11) DEFAULT NULL,
  `tmp_tables` int(11) DEFAULT NULL,
  `tmp_disk_tables` int(11) DEFAULT NULL,
  `tmp_table_sizes` int(11) DEFAULT NULL,
  `sequence_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `hostname` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `statements`
--

LOCK TABLES `statements` WRITE;
/*!40000 ALTER TABLE `statements` DISABLE KEYS */;
/*!40000 ALTER TABLE `statements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `table_definitions`
--

DROP TABLE IF EXISTS `table_definitions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `table_definitions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server` varchar(100) DEFAULT NULL,
  `database_name` varchar(64) DEFAULT NULL,
  `table_name` varchar(64) DEFAULT NULL,
  `create_syntax` text,
  `run_time` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `table_definitions`
--

LOCK TABLES `table_definitions` WRITE;
/*!40000 ALTER TABLE `table_definitions` DISABLE KEYS */;
/*!40000 ALTER TABLE `table_definitions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `table_users`
--

DROP TABLE IF EXISTS `table_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `table_users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `permtype` int(11) DEFAULT NULL,
  `server` varchar(255) DEFAULT NULL,
  `Host` varchar(255) DEFAULT NULL,
  `Db` varchar(255) DEFAULT NULL,
  `User` varchar(255) DEFAULT NULL,
  `Table_name` varchar(255) DEFAULT NULL,
  `Password` varchar(255) DEFAULT NULL,
  `Column_name` varchar(255) DEFAULT NULL,
  `Routine_name` varchar(255) DEFAULT NULL,
  `Routine_type` varchar(255) DEFAULT NULL,
  `Grantor` varchar(255) DEFAULT NULL,
  `Create_priv` varchar(1) DEFAULT NULL,
  `Drop_priv` varchar(1) DEFAULT NULL,
  `Grant_priv` varchar(1) DEFAULT NULL,
  `References_priv` varchar(1) DEFAULT NULL,
  `Event_priv` varchar(1) DEFAULT NULL,
  `Alter_priv` varchar(1) DEFAULT NULL,
  `Delete_priv` varchar(1) DEFAULT NULL,
  `Index_priv` varchar(1) DEFAULT NULL,
  `Insert_priv` varchar(1) DEFAULT NULL,
  `Select_priv` varchar(1) DEFAULT NULL,
  `Update_priv` varchar(1) DEFAULT NULL,
  `Create_tmp_table_priv` varchar(1) DEFAULT NULL,
  `Lock_tables_priv` varchar(1) DEFAULT NULL,
  `Trigger_priv` varchar(1) DEFAULT NULL,
  `Create_view_priv` varchar(1) DEFAULT NULL,
  `Show_view_priv` varchar(1) DEFAULT NULL,
  `Alter_routine_priv` varchar(1) DEFAULT NULL,
  `Create_routine_priv` varchar(1) DEFAULT NULL,
  `Execute_priv` varchar(1) DEFAULT NULL,
  `File_priv` varchar(1) DEFAULT NULL,
  `Create_user_priv` varchar(1) DEFAULT NULL,
  `Process_priv` varchar(1) DEFAULT NULL,
  `Reload_priv` varchar(1) DEFAULT NULL,
  `Repl_client_priv` varchar(1) DEFAULT NULL,
  `Repl_slave_priv` varchar(1) DEFAULT NULL,
  `Show_db_priv` varchar(1) DEFAULT NULL,
  `Shutdown_priv` varchar(1) DEFAULT NULL,
  `Super_priv` varchar(1) DEFAULT NULL,
  `ssl_type` varchar(20) DEFAULT NULL,
  `ssl_cipher` blob,
  `x509_issuer` blob,
  `x509_subject` blob,
  `max_questions` int(11) DEFAULT NULL,
  `max_updates` int(11) DEFAULT NULL,
  `max_connections` int(11) DEFAULT NULL,
  `max_user_connections` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `run_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `table_users`
--

LOCK TABLES `table_users` WRITE;
/*!40000 ALTER TABLE `table_users` DISABLE KEYS */;
/*!40000 ALTER TABLE `table_users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `table_views`
--

DROP TABLE IF EXISTS `table_views`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `table_views` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server` varchar(100) DEFAULT NULL,
  `database_name` varchar(64) DEFAULT NULL,
  `table_name` varchar(64) DEFAULT NULL,
  `create_syntax` text,
  `run_time` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `table_views`
--

LOCK TABLES `table_views` WRITE;
/*!40000 ALTER TABLE `table_views` DISABLE KEYS */;
/*!40000 ALTER TABLE `table_views` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `table_volumes`
--

DROP TABLE IF EXISTS `table_volumes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `table_volumes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `server` varchar(100) DEFAULT NULL,
  `database_name` varchar(64) DEFAULT NULL,
  `table_name` varchar(64) DEFAULT NULL,
  `data_length` bigint(20) DEFAULT NULL,
  `index_length` bigint(20) DEFAULT NULL,
  `data_free` bigint(20) DEFAULT NULL,
  `run_time` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `table_volumes`
--

LOCK TABLES `table_volumes` WRITE;
/*!40000 ALTER TABLE `table_volumes` DISABLE KEYS */;
/*!40000 ALTER TABLE `table_volumes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `test_types`
--

DROP TABLE IF EXISTS `test_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `test_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `test_types`
--

LOCK TABLES `test_types` WRITE;
/*!40000 ALTER TABLE `test_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `test_types` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  `auth_user_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `validation_types`
--

DROP TABLE IF EXISTS `validation_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `validation_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `description` text,
  `validation_commands` text,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `validation_types`
--

LOCK TABLES `validation_types` WRITE;
/*!40000 ALTER TABLE `validation_types` DISABLE KEYS */;
/*!40000 ALTER TABLE `validation_types` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2013-06-10 21:04:29
