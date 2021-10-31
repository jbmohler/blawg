FROM postgres:13

COPY pgschema.sql /blawg/pgschema.sql
COPY aacreate.sql /docker-entrypoint-initdb.d/aacreate.sql
COPY create_script.sh /docker-entrypoint-initdb.d/create_script.sh
