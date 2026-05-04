--Table: global_settings
create table global_settings (
    id BIGSERIAL primary key,
    paused BOOLEAN not null default false,
    paused_start_time DOUBLE PRECISION not null default 0,
    paused_end_time DOUBLE PRECISION not null default 0,
    task JSONB default null,
    progress JSONB default null,
    report JSONB default null
);
insert into global_settings (id)
values (1);
--
--
-- 
-- white_list
create table white_list (
    id BIGSERIAL primary key,
    account_name VARCHAR(255) not null,
    mail VARCHAR(255) not null,
    presentation_name VARCHAR(255) not null,
    role VARCHAR(16) not null default 'admin'
);
create unique index idx_wl_account_name on white_list (account_name);
create index idx_wl_mail on white_list (mail);

--
--
--
--Table: fixity_task
create table fixity_task (
    id BIGSERIAL primary key,
    fixity_type INT not null default 0,
    fixity_filter JSONB default null,
    annotation VARCHAR(255) default null,
    creator BIGINT not null,
    creation_time DOUBLE PRECISION not null default 0,
    actual_start_time DOUBLE PRECISION not null default 0,
    actual_end_time DOUBLE PRECISION not null default 0,
    state INT not null default 0
);
create index task_state on fixity_task (state);

--
--
-- 
-- Table:  fixity_report
create table fixity_report (
    id BIGSERIAL primary key,
    archived_time DOUBLE PRECISION not null default 0,
    task JSONB default null,
    progress JSONB default null,
    report JSONB default null
);
create index fixityreport_archived_time on fixity_report (archived_time);
--
--
-- 
-- Table: blob_event_queue
create table blob_event_queue (
    id BIGSERIAL primary key,
    creation_time DOUBLE PRECISION not null default 0,
    event_id VARCHAR(64) not null,
    blob_url VARCHAR(1024) not null,
    received_time DOUBLE PRECISION not null default 0,
    finished_time DOUBLE PRECISION default null,
    file_check_state INT default 10,
    file_check_desc VARCHAR(4000),
    file_check_sum VARCHAR(255),
    blob_name VARCHAR(255),
    blob_size BIGINT,
    file_check_state_confirmed BOOLEAN default false
);
create unique index blobeventqueue_event_id on blob_event_queue (event_id);
create index blobeventqueue_file_check_state on blob_event_queue (file_check_state);

--
--
-- 
-- Table:  blob_event_results
create table blob_event_results (
    id BIGSERIAL primary key,
    checked_time DOUBLE PRECISION not null default 0,
    file_check_state INT default 10,
    file_check_desc VARCHAR(4000),
    file_check_sum VARCHAR(255),
    blob_name VARCHAR(255),
    blob_size BIGINT
);
create index blobeventresults_file_check_state on blob_event_results (file_check_state);
create index blobeventresults_blob_name on blob_event_results (blob_name);


--
--
-- 
-- Table:  permanent_index
create table permanent_index (
    id BIGINT not null,
    file_size BIGINT,
    version BIGINT,
    status BIGINT,
    stored_entity_id VARCHAR(255),
    check_sum_type VARCHAR(255),
    storage_id BIGINT,
    update_date TIMESTAMP,
    storage_entity_type VARCHAR(8),
    index_location VARCHAR(255),
    check_sum VARCHAR(255),
    update_check_sum SMALLINT,
    phys_check_sum VARCHAR(255),
    phys_check_sum_type VARCHAR(255),
    xsd_versions VARCHAR(50),
    created_by VARCHAR(255),
    title VARCHAR(4000),
    ie_pi_id BIGINT default null,
    pir_file_check_state INT not null default 10,
    pir_file_check_desc VARCHAR(4000) default null,
    pir_file_checksum VARCHAR(255) default null,
    pir_mets_check_state INT not null default 10,
    pir_mets_check_desc VARCHAR(4000) default null,
    pir_mets_checksum VARCHAR(255) default null,
    pir_mets_file_not_in_db JSONB default null,
    constraint permanent_index_pk_01 primary key (id)
);
create index permanentindex_storageentity on permanent_index (storage_entity_type);
create index permanentindex_s_e_id on permanent_index (stored_entity_id);
create index permanentindex_version on permanent_index (version);
create index permanentindex_index_location on permanent_index (index_location);
create index permanentindex_pir_file_check_state on permanent_index (pir_file_check_state);
create index permanentindex_pir_mets_check_state on permanent_index (pir_mets_check_state);

--
--
--
-- 
-- Table:  permanent_index_bau
create table permanent_index_bau (
    id BIGINT not null,
    file_size BIGINT,
    version BIGINT,
    status BIGINT,
    stored_entity_id VARCHAR(255),
    check_sum_type VARCHAR(255),
    storage_id BIGINT,
    update_date TIMESTAMP,
    storage_entity_type VARCHAR(8),
    index_location VARCHAR(255),
    check_sum VARCHAR(255),
    update_check_sum SMALLINT,
    phys_check_sum VARCHAR(255),
    phys_check_sum_type VARCHAR(255),
    xsd_versions VARCHAR(50),
    created_by VARCHAR(255),
    title VARCHAR(4000),
    ie_pi_id BIGINT default null,
    pir_file_check_state INT not null default 10,
    pir_file_check_desc VARCHAR(4000) default null,
    pir_file_checksum VARCHAR(255) default null,
    pir_mets_check_state INT not null default 10,
    pir_mets_check_desc VARCHAR(4000) default null,
    pir_mets_checksum VARCHAR(255) default null,
    pir_mets_file_not_in_db JSONB default null,
    constraint permanent_index_bau_pk_01 primary key (id)
);
create index permanentindexbau_storageentity on permanent_index_bau (storage_entity_type);
create index permanentindexbau_s_e_id on permanent_index_bau (stored_entity_id);
create index permanentindexbau_version on permanent_index_bau (version);
create index permanentindexbau_index_location on permanent_index_bau (index_location);
create index permanentindexbau_pir_file_check_state on permanent_index_bau (pir_file_check_state);
create index permanentindexbau_pir_mets_check_state on permanent_index_bau (pir_mets_check_state);
--
--
-- 
-- Table: storage_parameter
create table storage_parameter (
    id BIGINT not null,
    value VARCHAR(4000),
    key VARCHAR(50),
    storage_id BIGINT,
    constraint storage_parameter_pk_01 primary key (id)
);
-- Index on the Foreign Key column (corresponds to STORAGE_ID_IDX)
create index storage_id_idx on storage_parameter (storage_id);
--
--
--
-- Table: durable_transaction
create table durable_transaction (
    id BIGSERIAL primary key,
    trans_id VARCHAR(64) not null,
    job_type INT not null default 0,
    req_blob_url VARCHAR(1024) default null,
    transaction  JSONB default null,
    creation_time DOUBLE PRECISION not null default 0,
    state INT not null default 0
);
create unique index durabletransaction_trans_id on durable_transaction (trans_id);
create index durabletransaction_state on durable_transaction (state);
