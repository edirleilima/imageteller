-- ===========================================================================
-- ImageTeller - database schema
--
-- Two tables:
--   story     one row per generated story (metadata + character/actor libs)
--   chapter   the ordered chapters belonging to a story
--
-- Tables are created parent-first (story before chapter) so the foreign key
-- resolves without disabling FK checks. Both use utf8mb4 with the portable
-- utf8mb4_unicode_ci collation (available on MySQL 5.7+/8.0 and MariaDB).
--
-- Import with:  mysql -u <user> -p < schema.sql
-- The database name below must match DB_DATABASE in your .env.
--
-- story.deleted state machine:  2 = unsaved draft · 0 = saved · 1 = deleted.
-- chapter.deleted:              0 = active · 1 = replaced/regenerated.
-- A story whose user_id is the empty string is publicly readable.
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS `imageteller`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE `imageteller`;

SET NAMES utf8mb4;

DROP TABLE IF EXISTS `chapter`;
DROP TABLE IF EXISTS `story`;

-- ---------------------------------------------------------------------------
-- story: one generated story per row.
-- ---------------------------------------------------------------------------
CREATE TABLE `story` (
  `id` int NOT NULL AUTO_INCREMENT,
  `title` varchar(1024) NOT NULL,
  `user_id` varchar(128) NOT NULL,
  `genre` varchar(128) DEFAULT NULL,
  `image_desc` text,
  `time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deleted` int DEFAULT '0',
  `characters` text,
  `actors` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- chapter: the chapters of a story, in insertion order.
-- ---------------------------------------------------------------------------
CREATE TABLE `chapter` (
  `id` int NOT NULL AUTO_INCREMENT,
  `story_id` int DEFAULT NULL,
  `title` varchar(2024) NOT NULL,
  `text` text NOT NULL,
  `alignment` enum('left','right','full') NOT NULL,
  `deleted` int NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `story_id` (`story_id`),
  CONSTRAINT `chapter_ibfk_1` FOREIGN KEY (`story_id`)
    REFERENCES `story` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
