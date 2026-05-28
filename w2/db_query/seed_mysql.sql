-- =============================================================================
-- db_query 演示库：职工与组织常用信息（MySQL 8.0+ / MariaDB 10.5+）
-- 使用示例：
--   mysql -h 127.0.0.1 -P 3306 -u root -p yourdb < w2/db_query/seed_mysql.sql
-- 或在 mysql 客户端内：SOURCE /path/to/w2/db_query/seed_mysql.sql;
-- 说明：会 DROP 同名表后重建；请勿在生产库直接执行。
-- 列名 year_month / status 含 MySQL 保留字 YEAR、STATUS，DDL 中须用反引号。
-- =============================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

START TRANSACTION;

-- -----------------------------------------------------------------------------
-- 结构：部门 → 职工 → 联系方式 / 教育经历 / 月度薪酬摘要（可分表查询）
-- -----------------------------------------------------------------------------

DROP TABLE IF EXISTS employee_salary_snapshots;
DROP TABLE IF EXISTS employee_education;
DROP TABLE IF EXISTS employee_contacts;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(32) NOT NULL UNIQUE COMMENT '部门编码',
    name            VARCHAR(128) NOT NULL,
    location        VARCHAR(256) COMMENT '办公地点',
    manager_name    VARCHAR(64),
    created_at      DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='组织机构 / 部门';

CREATE TABLE employees (
    id                  INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_no         VARCHAR(32) NOT NULL UNIQUE COMMENT '工号',
    full_name           VARCHAR(64) NOT NULL,
    gender              VARCHAR(8) NOT NULL COMMENT '男 / 女 / 其他',
    birth_date          DATE NOT NULL,
    hire_date           DATE NOT NULL,
    leave_date          DATE,
    department_id       INT NOT NULL,
    job_title           VARCHAR(64) NOT NULL,
    employment_type     VARCHAR(16) NOT NULL DEFAULT '正式'
        COMMENT '正式 / 试用 / 外包 / 实习',
    `status`            VARCHAR(16) NOT NULL DEFAULT '在职'
        COMMENT '在职 / 休假 / 离职',
    id_card_masked      VARCHAR(32) COMMENT '证件号脱敏展示',
    mobile              VARCHAR(32),
    email               VARCHAR(128),
    remark              TEXT,
    updated_at          DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    CONSTRAINT chk_employees_gender
        CHECK (gender IN ('男', '女', '其他')),
    CONSTRAINT chk_employees_employment_type
        CHECK (employment_type IN ('正式', '试用', '外包', '实习')),
    CONSTRAINT chk_employees_status
        CHECK (`status` IN ('在职', '休假', '离职')),
    CONSTRAINT fk_employees_department
        FOREIGN KEY (department_id) REFERENCES departments (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='职工主档';

CREATE INDEX idx_employees_dept ON employees (department_id);
CREATE INDEX idx_employees_status ON employees (`status`);

CREATE TABLE employee_contacts (
    id                      INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_id             INT NOT NULL,
    registered_address      VARCHAR(512),
    current_city            VARCHAR(64),
    emergency_contact_name  VARCHAR(64),
    emergency_contact_phone VARCHAR(32),
    emergency_relation      VARCHAR(32),
    CONSTRAINT fk_contacts_employee
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='联系与紧急联系人';

CREATE TABLE employee_education (
    id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    degree          VARCHAR(32) NOT NULL,
    school          VARCHAR(128) NOT NULL,
    major           VARCHAR(128),
    graduation_year SMALLINT,
    is_highest      TINYINT(1) NOT NULL DEFAULT 1 COMMENT '1=最高学历',
    CONSTRAINT fk_education_employee
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='教育经历（支持多条，标记最高学历）';

CREATE TABLE employee_salary_snapshots (
    id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    employee_id     INT NOT NULL,
    `year_month`    VARCHAR(7) NOT NULL COMMENT 'YYYY-MM',
    base_salary     DECIMAL(12, 2) NOT NULL,
    allowance       DECIMAL(12, 2) NOT NULL DEFAULT 0,
    currency        VARCHAR(8) NOT NULL DEFAULT 'CNY',
    CONSTRAINT uk_salary_employee_month UNIQUE (employee_id, `year_month`),
    CONSTRAINT chk_salary_year_month
        CHECK (`year_month` REGEXP '^[0-9]{4}-[0-9]{2}$'),
    CONSTRAINT fk_salary_employee
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='月度薪酬快照（演示用，非真实发薪系统）';

-- -----------------------------------------------------------------------------
-- 数据
-- -----------------------------------------------------------------------------

INSERT INTO departments (code, name, location, manager_name) VALUES
    ('HQ', '总部', '上海市浦东新区', '张敏'),
    ('RD', '研发中心', '杭州市余杭区', '李强'),
    ('OPS', '运营中心', '深圳市南山区', '王芳'),
    ('FIN', '财务部', '上海市浦东新区', '赵磊');

INSERT INTO employees (
    employee_no, full_name, gender, birth_date, hire_date, leave_date,
    department_id, job_title, employment_type, `status`,
    id_card_masked, mobile, email, remark
) VALUES
    ('E2023001', '陈思远', '男', '1990-05-12', '2023-03-01', NULL,
     (SELECT id FROM departments WHERE code = 'RD'), '高级工程师', '正式', '在职',
     '310***********1234', '13800138001', 'chen.siyuan@example.com', '后端方向'),
    ('E2022008', '刘婉清', '女', '1995-11-03', '2022-07-15', NULL,
     (SELECT id FROM departments WHERE code = 'OPS'), '运营主管', '正式', '在职',
     '440***********5678', '13800138002', 'liu.wanqing@example.com', NULL),
    ('E2021015', '周博文', '男', '1988-02-28', '2021-01-10', NULL,
     (SELECT id FROM departments WHERE code = 'HQ'), '产品经理', '正式', '在职',
     '110***********9012', '13800138003', 'zhou.bowen@example.com', NULL),
    ('E2024012', '孙悦', '女', '1999-08-20', '2024-02-01', NULL,
     (SELECT id FROM departments WHERE code = 'FIN'), '会计', '试用', '在职',
     '330***********3456', '13800138004', 'sun.yue@example.com', NULL),
    ('E2019055', '韩磊', '男', '1985-12-01', '2019-06-01', '2024-12-31',
     (SELECT id FROM departments WHERE code = 'RD'), '架构师', '正式', '离职',
     '320***********7890', '13800138005', 'han.lei@example.com', '已交接完毕');

INSERT INTO employee_contacts (
    employee_id, registered_address, current_city,
    emergency_contact_name, emergency_contact_phone, emergency_relation
) VALUES
    ((SELECT id FROM employees WHERE employee_no = 'E2023001'),
     '上海市浦东新区张江路 100 号', '上海',
     '陈建国', '13900001111', '父亲'),
    ((SELECT id FROM employees WHERE employee_no = 'E2022008'),
     '浙江省杭州市西湖区文三路 88 号', '杭州',
     '刘梅', '13900002222', '母亲'),
    ((SELECT id FROM employees WHERE employee_no = 'E2021015'),
     '北京市朝阳区望京街 1 号', '上海',
     '周晓华', '13900003333', '配偶'),
    ((SELECT id FROM employees WHERE employee_no = 'E2024012'),
     '浙江省杭州市滨江区江南大道 200 号', '杭州',
     '孙建国', '13900004444', '父亲'),
    ((SELECT id FROM employees WHERE employee_no = 'E2019055'),
     '江苏省南京市鼓楼区中山路 50 号', '南京',
     '韩雪', '13900005555', '配偶');

INSERT INTO employee_education (
    employee_id, degree, school, major, graduation_year, is_highest
) VALUES
    ((SELECT id FROM employees WHERE employee_no = 'E2023001'),
     '硕士', '上海交通大学', '计算机科学与技术', 2016, 1),
    ((SELECT id FROM employees WHERE employee_no = 'E2023001'),
     '学士', '南京大学', '软件工程', 2013, 0),
    ((SELECT id FROM employees WHERE employee_no = 'E2022008'),
     '学士', '浙江大学', '市场营销', 2017, 1),
    ((SELECT id FROM employees WHERE employee_no = 'E2021015'),
     '硕士', '复旦大学', '工商管理', 2012, 1),
    ((SELECT id FROM employees WHERE employee_no = 'E2024012'),
     '学士', '浙江财经大学', '会计学', 2021, 1),
    ((SELECT id FROM employees WHERE employee_no = 'E2019055'),
     '硕士', '清华大学', '计算机科学与技术', 2010, 1);

INSERT INTO employee_salary_snapshots (employee_id, `year_month`, base_salary, allowance, currency) VALUES
    ((SELECT id FROM employees WHERE employee_no = 'E2023001'), '2026-01', 28000.00, 3500.00, 'CNY'),
    ((SELECT id FROM employees WHERE employee_no = 'E2022008'), '2026-01', 22000.00, 2000.00, 'CNY'),
    ((SELECT id FROM employees WHERE employee_no = 'E2021015'), '2026-01', 32000.00, 4000.00, 'CNY'),
    ((SELECT id FROM employees WHERE employee_no = 'E2024012'), '2026-01', 9000.00, 500.00, 'CNY'),
    ((SELECT id FROM employees WHERE employee_no = 'E2019055'), '2024-12', 45000.00, 6000.00, 'CNY');

COMMIT;

SET FOREIGN_KEY_CHECKS = 1;
