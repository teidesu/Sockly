DB_VERSIONS = {
    1: [
        'create table config (k text, v text)',
        'create unique index config_uindex on config (k)',
        'create table config_blobs (k text, v blob)',
        'create unique index config_blobs_uindex on config_blobs (k)'
    ]
}