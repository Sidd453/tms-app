-- ============================================================
--  TMS Database — PERFECT SCHEMA
--  Matches ALL frontend forms exactly
--  Run: mysql -u root -p1234 < init_db.sql
-- ============================================================

SET FOREIGN_KEY_CHECKS = 0;
CREATE DATABASE IF NOT EXISTS tms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE tms_db;

DROP TABLE IF EXISTS otp_tokens;
DROP TABLE IF EXISTS project_files;
DROP TABLE IF EXISTS tasks;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS project_managers;
DROP TABLE IF EXISTS team_leaders;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS departments;
DROP TABLE IF EXISTS roles_custom;
DROP TABLE IF EXISTS admin_profile;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. USERS
CREATE TABLE users (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    emp_id         VARCHAR(30)  UNIQUE NOT NULL,
    full_name      VARCHAR(100) NOT NULL,
    official_email VARCHAR(150) UNIQUE NOT NULL,
    personal_email VARCHAR(150),
    mobile         VARCHAR(20),
    password_hash  VARCHAR(512) NOT NULL,
    role           VARCHAR(30)  NOT NULL DEFAULT 'developer',
    department     VARCHAR(100),
    designation    VARCHAR(100),
    doj            DATE,
    work_location  VARCHAR(100),
    skills         TEXT,
    profile_pic    VARCHAR(255),
    status         VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. PROJECT MANAGERS
CREATE TABLE project_managers (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    emp_id          VARCHAR(30)  UNIQUE NOT NULL,
    full_name       VARCHAR(100) NOT NULL,
    official_email  VARCHAR(150) UNIQUE NOT NULL,
    personal_email  VARCHAR(150),
    mobile          VARCHAR(20),
    password_hash   VARCHAR(512),
    experience_yrs  TINYINT UNSIGNED DEFAULT 0,
    primary_domain  VARCHAR(100),
    initial_client  VARCHAR(150),
    status          VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. TEAM LEADERS (for PM dashboard TL management)
CREATE TABLE team_leaders (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    emp_id      VARCHAR(30) UNIQUE NOT NULL,
    full_name   VARCHAR(100) NOT NULL,
    email       VARCHAR(150),
    phone       VARCHAR(20),
    department  VARCHAR(100),
    experience  TINYINT UNSIGNED DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 4. DEPARTMENTS
CREATE TABLE departments (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    dept_name    VARCHAR(150) NOT NULL,
    hod_name     VARCHAR(100),
    description  TEXT,
    member_count SMALLINT UNSIGNED DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 5. ROLES CUSTOM
CREATE TABLE roles_custom (
    id           INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    role_name    VARCHAR(100) NOT NULL,
    access_level VARCHAR(50)  DEFAULT 'Read Only',
    description  TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 6. PROJECTS
CREATE TABLE projects (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_code     VARCHAR(50)  UNIQUE NOT NULL,
    project_name     VARCHAR(200) NOT NULL,
    client_name      VARCHAR(150),
    date_assigned    DATE,
    target_deadline  DATE,
    estimated_hours  VARCHAR(50),
    priority         VARCHAR(30)  DEFAULT 'Low',
    status           VARCHAR(30)  DEFAULT 'Planned',
    description      TEXT,
    progress         TINYINT UNSIGNED DEFAULT 0,
    assigned_pm_id   INT UNSIGNED NULL,
    created_by       INT UNSIGNED NULL,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_pm_id) REFERENCES project_managers(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by)     REFERENCES users(id)            ON DELETE SET NULL
) ENGINE=InnoDB;

-- 7. PROJECT FILES (unlimited attachments)
CREATE TABLE project_files (
    id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    project_id INT UNSIGNED NOT NULL,
    file_label VARCHAR(255) NOT NULL,
    file_path  VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 8. TASKS
CREATE TABLE tasks (
    id               INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    task_code        VARCHAR(30)  UNIQUE NOT NULL,
    task_name        VARCHAR(200) NOT NULL,
    project_id       INT UNSIGNED NULL,
    assigned_pm_id   INT UNSIGNED NULL,
    assigned_tl      VARCHAR(100),
    assigned_dev     VARCHAR(100),
    date_assigned    DATE,
    deadline         DATE,
    estimated_hours  VARCHAR(50),
    expertise_level  VARCHAR(100),
    department       VARCHAR(100),
    required_skills  VARCHAR(255),
    remark           TEXT,
    priority         VARCHAR(30)  DEFAULT 'Medium',
    status           VARCHAR(30)  DEFAULT 'Pending',
    progress         TINYINT UNSIGNED DEFAULT 0,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- 9. OTP TOKENS
CREATE TABLE otp_tokens (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    contact_value VARCHAR(150) NOT NULL,
    contact_type  VARCHAR(20)  NOT NULL DEFAULT 'email',
    otp_code      VARCHAR(10)  NOT NULL,
    purpose       VARCHAR(50)  DEFAULT 'forgot_password',
    expires_at    DATETIME     NOT NULL,
    is_used       TINYINT(1)   DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 10. ADMIN PROFILE
CREATE TABLE admin_profile (
    id             INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name      VARCHAR(100),
    official_email VARCHAR(150),
    mobile         VARCHAR(20),
    location       VARCHAR(100),
    profile_pic    VARCHAR(255),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- SEED DATA
-- ============================================================

INSERT INTO roles_custom (role_name, access_level, description) VALUES
('Super Admin',     'Full Access (Standard)', 'Full system access'),
('Project Manager', 'Full Access (Standard)', 'Manage projects and team'),
('Team Leader',     'Restricted Access',      'Lead development team'),
('Developer',       'Read Only',              'Build and deliver');

INSERT INTO departments (dept_name, hod_name, description, member_count) VALUES
('Development',  'Aditya Sharma', 'Core development team', 0),
('Design',       'Priya Mehta',   'UI/UX design team', 0),
('QA Testing',   'Rohit Joshi',   'Quality assurance', 0),
('DevOps',       'Nikhil Patil',  'Infrastructure & CI/CD', 0),
('Management',   'Purva Hande',   'Administration', 0);

-- Super Admin (password: Admin@123)
INSERT INTO users (emp_id, full_name, official_email, password_hash, role, status) VALUES
('EMP-SA-001', 'Purva Hande', 'purvaadmin@srujaninfotech.com', 'scrypt:32768:8:1$Qf22TPiafqDcWjFl$780670bd6262b84d59902dc8550f3ea0d67d11bed2c3439f54b1589a835a7b722f334bda3f4125860d1a8519e67e9604ed31f97648ed04599d81cde483e2148d', 'superadmin', 'active');

INSERT INTO admin_profile (id, full_name, official_email, mobile, location) VALUES
(1, 'Purva Hande', 'purvaadmin@srujaninfotech.com', '+91 77599 49543', 'Pune, Maharashtra');

SELECT 'TMS Database Ready!' AS status;