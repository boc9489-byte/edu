SET NAMES utf8mb4;

CREATE TABLE ask_table_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(128) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    domain VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    primary_key_name VARCHAR(128) NOT NULL,
    important_columns JSON NOT NULL,
    related_metrics JSON NOT NULL,
    tags JSON NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_ask_table_name (table_name),
    KEY idx_ask_table_domain (domain)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数表级语义元数据';

CREATE TABLE ask_column_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(128) NOT NULL,
    column_name VARCHAR(128) NOT NULL,
    display_name VARCHAR(128) NOT NULL,
    data_type VARCHAR(64) NOT NULL,
    role VARCHAR(32) NOT NULL,
    description TEXT NOT NULL,
    enum_values JSON NULL,
    related_metrics JSON NULL,
    source_hash VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_ask_column (table_name, column_name),
    KEY idx_ask_column_role (role),
    KEY idx_ask_column_table (table_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数字段级语义元数据';

CREATE TABLE ask_metric_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    metric_code VARCHAR(128) NOT NULL,
    metric_name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    main_table VARCHAR(128) NOT NULL,
    time_field VARCHAR(128) NOT NULL,
    aggregation TEXT NOT NULL,
    default_filter TEXT NOT NULL,
    supported_dimensions JSON NOT NULL,
    sql_template_key VARCHAR(128) NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_ask_metric_code (metric_code),
    KEY idx_ask_metric_table (main_table)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数指标元数据';

CREATE TABLE ask_dimension_info (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dimension_code VARCHAR(128) NOT NULL,
    dimension_name VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    table_name VARCHAR(128) NOT NULL,
    field_name VARCHAR(128) NOT NULL,
    groupable TINYINT NOT NULL DEFAULT 1,
    source_hash VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_ask_dimension_code (dimension_code),
    KEY idx_ask_dimension_field (table_name, field_name)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数维度元数据';

CREATE TABLE ask_column_metric (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    table_name VARCHAR(128) NOT NULL,
    column_name VARCHAR(128) NOT NULL,
    metric_code VARCHAR(128) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    created_at DATETIME NOT NULL,
    UNIQUE KEY uk_ask_column_metric (table_name, column_name, metric_code),
    KEY idx_ask_column_metric_metric (metric_code)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数字段指标关系';

CREATE TABLE ask_table_relation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    from_table VARCHAR(128) NOT NULL,
    from_column VARCHAR(128) NOT NULL,
    to_table VARCHAR(128) NOT NULL,
    to_column VARCHAR(128) NOT NULL,
    relation_type VARCHAR(32) NOT NULL,
    description TEXT NOT NULL,
    source_hash VARCHAR(64) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    UNIQUE KEY uk_ask_relation (from_table, from_column, to_table, to_column),
    KEY idx_ask_relation_from (from_table),
    KEY idx_ask_relation_to (to_table)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数表关系元数据';

CREATE TABLE ask_metadata_build_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    build_id VARCHAR(64) NOT NULL,
    target VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    rebuild_flag TINYINT NOT NULL DEFAULT 0,
    item_count INT NOT NULL DEFAULT 0,
    error_message TEXT NULL,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    UNIQUE KEY uk_ask_build_target (build_id, target),
    KEY idx_ask_build_status (status, started_at)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COMMENT = '问数元数据构建日志';
