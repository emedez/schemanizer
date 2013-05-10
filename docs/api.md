Schemanizer REST API Introduction
=================================

The following are the resources supported by the API:
```
{
    "auth_user": {
        "list_endpoint": "/api/v1/auth_user/",
        "schema": "/api/v1/auth_user/schema/"
    },
    "changeset": {
        "list_endpoint": "/api/v1/changeset/",
        "schema": "/api/v1/changeset/schema/"
    },
    "changeset_detail": {
        "list_endpoint": "/api/v1/changeset_detail/",
        "schema": "/api/v1/changeset_detail/schema/"
    },
    "changeset_detail_apply": {
        "list_endpoint": "/api/v1/changeset_detail_apply/",
        "schema": "/api/v1/changeset_detail_apply/schema/"
    },
    "changeset_test": {
        "list_endpoint: "/api/v1/changeset_test/",
        "schema": "/api/v1/changeset_detail/schema/"
    },
    "changeset_validation": {
        "list_endpoint: "/api/v1/changeset_validation/",
        "schema": "/api/v1/changeset_validation/schema/"
    },
    "database_schema": {
        "list_endpoint": "/api/v1/database_schema/",
        "schema": "/api/v1/database_schema/schema/"
    },
    "environment": {
        "list_endpoint": "/api/v1/environment/",
        "schema": "/api/v1/environment/schema/"
    },
    "role": {
        "list_endpoint": "/api/v1/role/",
        "schema": "/api/v1/role/schema/"
    },
    "schema_version": {
        "list_endpoint": "/api/v1/schema_version/",
        "schema": "/api/v1/schema_version/schema/"
    },
    "server": {
        "list_endpoint": "/api/v1/server/",
        "schema": "/api/v1/server/schema/"
    },
    "user": {
        "list_endpoint": "/api/v1/user/",
        "schema": "/api/v1/user/schema/"
    }
}
```

The above JSON object is the output of browsing:
```
http://<domain>:<port>/api/v1/?format=json
```
The list_endpoint field is the url for listing resource objects.
The schema field is the the url for retrieving info about the resouce object, such as fields, allowed HTTP methods, and allowed fields for filtering.


Schemanizer REST API
====================

This section describes the individual API. Sample usage and outputs are provided.
HTTP status code should be checked for every API calls. In most cases when error occurs, the *error_message* field will be included in the content.


Role
----

### Get Roles

API:
```
GET /api/v1/role/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/role/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 3
    },
    "objects": [
        {
            "created_at": "2013-04-01T04:02:25",
            "id": 1,
            "name": "admin",
            "resource_uri": "/api/v1/role/1/",
            "updated_at": "2013-04-01T04:02:25"
        },
        {
            "created_at": "2013-04-01T04:02:31",
            "id": 2,
            "name": "dba",
            "resource_uri": "/api/v1/role/2/",
            "updated_at": "2013-04-01T04:02:31"
        },
        {
            "created_at": "2013-04-01T04:02:36",
            "id": 3,
            "name": "developer",
            "resource_uri": "/api/v1/role/3/",
            "updated_at": "2013-04-01T04:02:36"
        }
    ]
}
```

### Get Role

API:
```
GET /api/v1/role/<role_id>/
```
role_id - Role ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/role/1/

{
    "created_at": "2013-04-01T04:02:25",
    "id": 1,
    "name": "admin",
    "resource_uri": "/api/v1/role/1/",
    "updated_at": "2013-04-01T04:02:25"
}
```


User
----

### Get Users

API:
```
GET /api/v1/user/
```

Sample usage and output:
```
$ curl -u admin:admin http://localhost:8000/api/v1/user/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 2
    },
    "objects": [
        {
            "auth_user": "/api/v1/auth_user/1/",
            "created_at": "2013-04-03T17:02:34",
            "email": "admin@example.com",
            "id": 1,
            "name": "admin",
            "resource_uri": "/api/v1/user/1/",
            "role": "/api/v1/role/1/",
            "updated_at": "2013-04-29T01:18:19"
        },
        {
            "auth_user": "/api/v1/auth_user/2/",
            "created_at": "2013-04-29T19:11:10",
            "email": "dba@example.com",
            "id": 2,
            "name": "dba",
            "resource_uri": "/api/v1/user/2/",
            "role": "/api/v1/role/2/",
            "updated_at": "2013-04-29T19:11:10"
        }
    ]
}
```

### Get User

API:
```
GET /api/v1/user/<user_id>/
```
user_id - User ID/PK

Sample usage and output:
```
$ curl -u admin:admin http://localhost:8000/api/v1/user/1/

{
    "auth_user": "/api/v1/auth_user/1/",
    "created_at": "2013-04-03T17:02:34",
    "email": "admin@example.com",
    "id": 1,
    "name": "admin",
    "resource_uri": "/api/v1/user/1/",
    "role": "/api/v1/role/1/",
    "updated_at": "2013-04-29T01:18:19"
}
```

### Create User

API:
```
POST /api/v1/user/create/
```
POST data should be JSON object in the form:
```
{
    "name": <name>,
    "email": <email>,
    "role_id": <role_id>,
    "password": <password>
}
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "dev2", "email": "dev2@example.com", "role_id": 3, "password": "dev"}' -u admin:admin http://localhost:8000/api/v1/user/create/

{
    "auth_user": "/api/v1/auth_user/8/",
    "created_at": "2013-05-09T01:50:08.416342",
    "email": "dev2@example.com",
    "id": 8,
    "name": "dev2",
    "resource_uri": "/api/v1/user/7/",
    "role": "/api/v1/role/3/",
    "updated_at": "2013-05-09T01:50:08.416651"
}
```

### Update User

API:
```
POST api/v1/user/update/<user_id>/
```
user_id - User ID/PK

POST data should be a JSON object in the form:
```
{
    "name": <name>,
    "email": <email>,
    "role_id": <role_id>
}
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "dev_2", "email": "dev_2@example.com", "role_id": 3}' -u admin:admin http://localhost:8000/api/v1/user/update/8/

{
    "auth_user": "/api/v1/auth_user/9/",
    "created_at": "2013-05-09T01:56:18",
    "email": "dev_2@example.com",
    "id": 8,
    "name": "dev_2",
    "resource_uri": "/api/v1/user/8/",
    "role": "/api/v1/role/3/",
    "updated_at": "2013-05-09T02:06:24.672610"
}
```

### Delete User

API:
```
POST /api/v1/user/delete/<user_id>/
```
user_id - User ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST -u admin:admin http://localhost:8000/api/v1/user/delete/8/

{}
```


Environment
-----------

### Get Environments

API:
```
GET /api/v1/environment/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/environment/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 3
    },
    "objects": [
        {
            "created_at": "2013-04-27T00:24:40",
            "id": 1,
            "name": "dev",
            "resource_uri": "/api/v1/environment/1/",
            "updated_at": "2013-04-27T00:24:40"
        },
        {
            "created_at": "2013-04-27T00:24:48",
            "id": 2,
            "name": "test",
            "resource_uri": "/api/v1/environment/2/",
            "updated_at": "2013-04-27T00:24:48"
        },
        {
            "created_at": "2013-04-27T00:24:53",
            "id": 3,
            "name": "prod",
            "resource_uri": "/api/v1/environment/3/",
            "updated_at": "2013-04-27T00:24:53"
        }
    ]
}
```

### Get Environment

API:
```
GET /api/v1/environment/<user_id>/
```
user_id - User ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/environment/1/

{
    "created_at": "2013-04-27T00:24:40",
    "id": 1,
    "name": "dev",
    "resource_uri": "/api/v1/environment/1/",
    "updated_at": "2013-04-27T00:24:40"
}
```

### Create Environment

API:
```
POST /api/v1/environment/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "env6"}' -u admin:admin http://localhost:8000/api/v1/environment/
```

### Update Environment

API:
```
PUT /api/v1/environment/<environment_id>/
```
environment_id - Environment ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X PUT --data '{"name": "env_6"}' -u admin:admin http://localhost:8000/api/v1/environment/7/
```

### Delete Environment

API:
```
DELETE /api/v1/environment/<environment_id>/
```
environment_id - Environment ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X DELETE -u admin:admin http://localhost:8000/api/v1/environment/7/
```

Server
------

### Get Servers

API:
```
GET /api/v1/server/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/server/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "cached_size": null,
            "created_at": "2013-04-29T21:15:54",
            "environment": "/api/v1/environment/1/",
            "hostname": "localhost",
            "id": 1,
            "name": "localhost",
            "port": null,
            "resource_uri": "/api/v1/server/1/",
            "updated_at": "2013-04-29T21:15:54"
        }
    ]
}
```

### Get Server

API:
```
GET /api/v1/server/<server_id>/
```
server_id - Server ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/server/1/

{
    "cached_size": null,
    "created_at": "2013-04-29T21:15:54",
    "environment": "/api/v1/environment/1/",
    "hostname": "localhost",
    "id": 1,
    "name": "localhost",
    "port": null,
    "resource_uri": "/api/v1/server/1/",
    "updated_at": "2013-04-29T21:15:54"
}
```

### Create Server

API:
```
POST /api/v1/server/
```

POST data should be a JSON object in the form:
```
{
    "name": <name>,
    "hostname": <hostname>,
    "port": <port>
}
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "localhost2", "hostname": "127.0.0.1"}' -u admin:admin http://localhost:8000/api/v1/server/
```

### Update Server

API:
```
PUT /api/v1/server/<server_id>/
```
server_id - Server ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X PUT --data '{"name": "localhost_2", "hostname": "localhost"}' -u admin:admin http://localhost:8000/api/v1/server/8/
```

### Delete Server

API:
```
DELETE /api/v1/server/<server_id>/
```
server_id - Server ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X DELETE -u admin:admin http://localhost:8000/api/v1/server/8/
```

Database Schema
---------------

### Get Database Schemas

API:
```
GET /api/v1/database_schema/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/database_schema/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "created_at": "2013-04-30T23:20:15",
            "id": 5,
            "name": "test_schema_1",
            "resource_uri": "/api/v1/database_schema/5/",
            "updated_at": "2013-04-30T23:20:15"
        }
    ]
}
```

### Get Database Schema

API:
```
GET /api/v1/database_schema/<database_schema_id>/
```
database_schema_id - Database Schema ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/database_schema/5/

{
    "created_at": "2013-04-30T23:20:15",
    "id": 5,
    "name": "test_schema_1",
    "resource_uri": "/api/v1/database_schema/5/",
    "updated_at": "2013-04-30T23:20:15"
}
```


Schema Version
--------------

### Get Schema Versions

API:
```
GET /api/v1/schema_version/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/schema_version/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "checksum": "8f281fa8732078c9b4f6cea8c988c48b",
            "created_at": "2013-04-30T23:20:15",
            "database_schema": "/api/v1/database_schema/5/",
            "ddl": "...",
            "id": 11,
            "resource_uri": "/api/v1/schema_version/11/",
            "updated_at": "2013-04-30T23:20:15"
        }
    ]
}
```

Sample filter usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/schema_version/?database_schema__id=6

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "checksum": "f8c2431456e6847af3a6fab68e6b1e39",
            "created_at": "2013-05-09T21:49:20",
            "database_schema": "/api/v1/database_schema/6/",
            "ddl": "...",
            "id": 20,
            "resource_uri": "/api/v1/schema_version/20/",
            "updated_at": "2013-05-09T21:49:20"
        }
    ]
}
```

### Get Schema Version

API:
```
GET /api/v1/schema_version/<schema_version_id>/
```
schema_version_id - Schema Version ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/schema_version/11/

{
    "checksum": "8f281fa8732078c9b4f6cea8c988c48b",
    "created_at": "2013-04-30T23:20:15",
    "database_schema": "/api/v1/database_schema/5/",
    "ddl": "...",
    "id": 11,
    "resource_uri": "/api/v1/schema_version/11/",
    "updated_at": "2013-04-30T23:20:15"
}
```


### Save Schema Dump

API:
```
POST /api/v1/schema_version/save_schema_dump/
```

POST data should be a JSON object in the form:
```
{
    "server_id": <server_id>,
    "database_schema_name": <database_schema_name>
}
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"server_id": 1, "database_schema_name": "pdbtest_db1"}' -u admin:admin http://localhost:8000/api/v1/schema_version/save_schema_dump/

{
    "checksum": "f8c2431456e6847af3a6fab68e6b1e39",
    "created_at": "2013-05-09T21:49:20.892147",
    "database_schema": "/api/v1/database_schema/6/",
    "ddl": "...",
    "id": 20,
    "resource_uri": "/api/v1/schema_version/20/",
    "updated_at": "2013-05-09T21:49:20.892291"
}
```

Changeset
---------

### Get Changesets

API:
```
GET /api/v1/changeset/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "after_version": "/api/v1/schema_version/18/",
            "approved_at": "2013-05-03T00:19:29",
            "approved_by": "/api/v1/user/2/",
            "before_version": "/api/v1/schema_version/13/",
            "classification": "painless",
            "created_at": "2013-04-30T23:23:00",
            "database_schema": "/api/v1/database_schema/5/",
            "id": 4,
            "is_deleted": 0,
            "resource_uri": "/api/v1/changeset/4/",
            "review_status": "approved",
            "reviewed_at": "2013-05-03T00:19:19",
            "reviewed_by": "/api/v1/user/2/",
            "submitted_at": "2013-04-30T23:23:00",
            "submitted_by": "/api/v1/user/2/",
            "type": "DDL:Table:Create",
            "updated_at": "2013-05-03T00:19:29",
            "version_control_url": ""
        }
    ]
}
```

### Get Changesets That Needs To Be Reviewed

API:
```
GET /api/v1/changeset/?review_status=needs
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset/?review_status=needs

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "after_version": null,
            "approved_at": null,
            "approved_by": null,
            "before_version": null,
            "classification": "painless",
            "created_at": "2013-05-10T00:21:41",
            "database_schema": "/api/v1/database_schema/5/",
            "id": 9,
            "is_deleted": 0,
            "resource_uri": "/api/v1/changeset/9/",
            "review_status": "needs",
            "reviewed_at": null,
            "reviewed_by": null,
            "submitted_at": "2013-05-10T00:21:41",
            "submitted_by": "/api/v1/user/3/",
            "type": "DDL:Table:Create",
            "updated_at": "2013-05-10T00:21:41",
            "version_control_url": ""
        }
    ]
}
```


### Get Changeset

API:
```
GET /api/v1/changeset/<changset_id>/
```
changset_id - Changeset ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset/4/

{
    "after_version": "/api/v1/schema_version/18/",
    "approved_at": "2013-05-03T00:19:29",
    "approved_by": "/api/v1/user/2/",
    "before_version": "/api/v1/schema_version/13/",
    "classification": "painless",
    "created_at": "2013-04-30T23:23:00",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 4,
    "is_deleted": 0,
    "resource_uri": "/api/v1/changeset/4/",
    "review_status": "approved",
    "reviewed_at": "2013-05-03T00:19:19",
    "reviewed_by": "/api/v1/user/2/",
    "submitted_at": "2013-04-30T23:23:00",
    "submitted_by": "/api/v1/user/2/",
    "type": "DDL:Table:Create",
    "updated_at": "2013-05-03T00:19:29",
    "version_control_url": ""
}
```


### Submit Changeset

API:
```
POST /api/v1/changeset/submit/
```

POST data should be a JSON string in the following form:
```
{
    'changeset': {
        'database_schema_id': 1,
        'type': 'DDL:Table:Create',
        'classification': 'painless',
        'version_control_url': ''
    },
    'changeset_details': [
        {
            'type': 'add',
            'description': 'create a table',
            'apply_sql': 'create table t1 (id int primary key auto_increment)',
            'revert_sql': 'drop table t1'
        }
    ]
}
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"changeset": {"database_schema_id": 1, "type": "DDL:Table:Create", "classification": "painless", "version_control_url": ""}, "changeset_details": [{"type": "add", "description": "create a table", "apply_sql": "create table t1 (id int primary key auto_increment)", "revert_sql": "drop table t1"}]}' -u dev:dev http://localhost:8000/api/v1/changeset/submit/

{
    "after_version": null,
    "approved_at": null,
    "approved_by": null,
    "before_version": null,
    "classification": "painless",
    "created_at": "2013-05-10T00:21:41.454048",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 9,
    "is_deleted": 0,
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "needs",
    "reviewed_at": null,
    "reviewed_by": null,
    "submitted_at": "2013-05-10T00:21:41.452454",
    "submitted_by": "/api/v1/user/3/",
    "type": "DDL:Table:Create",
    "updated_at": "2013-05-10T00:21:41.454188",
    "version_control_url": ""
}
```


### Reject changeset

API:
```
POST /api/v1/changeset/reject/<changeset_id>/
```
changeset_id - Changeset ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST -u dba:dba http://localhost:8000/api/v1/changeset/reject/9/

{
    "after_version": null,
    "approved_at": "2013-05-10T00:35:16.485194",
    "approved_by": "/api/v1/user/2/",
    "before_version": null,
    "classification": "painless",
    "created_at": "2013-05-10T00:21:41",
    "database_schema": {
        "created_at": "2013-04-30T23:20:15",
        "id": 5,
        "name": "test_schema_1",
        "resource_uri": "/api/v1/database_schema/5/",
        "updated_at": "2013-04-30T23:20:15"
    },
    "id": 9,
    "is_deleted": 0,
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "rejected",
    "reviewed_at": null,
    "reviewed_by": null,
    "submitted_at": "2013-05-10T00:21:41",
    "submitted_by": "/api/v1/user/3/",
    "type": "DDL:Table:Create",
    "updated_at": "2013-05-10T00:35:16.520062",
    "version_control_url": ""
}
```

### Approve Changeset

API:
```
POST /api/v1/changeset/approve/<changeset_id>/
```
changeset_id - Changeset ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST -u dba:dba http://localhost:8000/api/v1/changeset/approve/9/

{
    "after_version": null,
    "approved_at": "2013-05-10T00:40:25.307858",
    "approved_by": "/api/v1/user/2/",
    "before_version": null,
    "classification": "painless",
    "created_at": "2013-05-10T00:21:41",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 9,
    "is_deleted": 0,
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "approved",
    "reviewed_at": null,
    "reviewed_by": null,
    "submitted_at": "2013-05-10T00:21:41",
    "submitted_by": "/api/v1/user/3/",
    "type": "DDL:Table:Create",
    "updated_at": "2013-05-10T00:40:25.367167",
    "version_control_url": ""
}
```

### Soft Delete Changeset

API:
```
POST /api/v1/changeset/soft_delete/<changeset_id>/
```
changeset_id - Changeset ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST -u dba:dba http://localhost:8000/api/v1/changeset/soft_delete/9/

{
    "after_version": null,
    "approved_at": "2013-05-10T00:40:25",
    "approved_by": "/api/v1/user/2/",
    "before_version": null,
    "classification": "painless",
    "created_at": "2013-05-10T00:21:41",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 9,
    "is_deleted": 1,
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "needs",
    "reviewed_at": null,
    "reviewed_by": null,
    "submitted_at": "2013-05-10T00:21:41",
    "submitted_by": "/api/v1/user/3/",
    "type": "DDL:Table:Create",
    "updated_at": "2013-05-10T00:48:12.179797",
    "version_control_url": ""
}
```

### Update Changeset

API:
```
POST /api/v1/changeset/update/<changeset_id>/
```
changeset_id - Changeset ID/PK

POST data should be a JSON object in the form:
```
{
    'changeset': {
        'database_schema_id': 5,
        'type': 'DDL:Table:Drop',
        'classification': 'impacting',
        'version_control_url': 'https://'
    },
    'changeset_details': [
        {
            'id': 10,
            'type': 'add',
            'description': 'ccreate a table',
            'apply_sql': 'ccreate table t1...',
            'revert_sql': 'ddrop table t1'
        },
        {
            'type': 'drop',
            'description': 'drop a table',
            'apply_sql': 'drop table t2',
            'revert_sql': 'create table t2...'
        }
    ],
    'to_be_deleted_changeset_detail_ids': [11, 12]
}
```
Note: changeset_details with no IDs will be inserted while those without IDs will be updated.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"changeset": {"database_schema_id": 5, "type": "DDL:Table:Drop", "classification": "impacting", "version_control_url": "https://"}, "changeset_details": [{"id": 10, "type": "add", "description": "ccreate a table", "apply_sql": "ccreate table t1...", "revert_sql": "ddrop table t1"}, {"type": "drop", "description": "drop a table", "apply_sql": "drop table t2", "revert_sql": "create table t2..."}], "to_be_deleted_changeset_detail_ids": [11, 12]}' -u dba:dba http://localhost:8000/api/v1/changeset/update/9/

{
    "after_version": null,
    "approved_at": "2013-05-10T00:40:25",
    "approved_by": "/api/v1/user/2/",
    "before_version": null,
    "classification": "impacting",
    "created_at": "2013-05-10T00:21:41",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 9,
    "is_deleted": 0,
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "needs",
    "reviewed_at": null,
    "reviewed_by": null,
    "submitted_at": "2013-05-10T00:21:41",
    "submitted_by": "/api/v1/user/3/",
    "type": "DDL:Table:Drop",
    "updated_at": "2013-05-10T01:24:14.981568",
    "version_control_url": "https://"
}
```


### Review Changeset

API:
```
POST /api/v1/changeset/review/<changeset_id>/
```
changeset_id - Changeset ID/PK

POST data should be a JSON object in the form:
```
{
    "schema_version_id": <schema_version_id>
}
```

Use the Changeset Review Status API to check the status/result of changeset review.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"schema_version_id": 11}' -u dba:dba http://localhost:8000/api/v1/changeset/review/11/

{
    "request_id": "69c6d6be71ac7c4bf908b4d7f986d4004dabbd97",
    "thread_started": true
}
```

### Changeset Review Status

API:
```
GET /api/v1/changeset/review_status/<request_id>/
```
request_id - ID of the request that started the review thread.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset/review_status/69c6d6be71ac7c4bf908b4d7f986d4004dabbd97/

{
    {
    "thread_changeset_test_ids": [
        27
    ],
    "thread_changeset_validation_ids": [
        23
    ],
    "thread_errors": [],
    "thread_is_alive": false,
    "thread_messages": [
        [
            "info",
            "Review thread ended."
        ]
    ],
    "thread_review_results_url": "http://localhost:8000/schemanizer/changeset/view-review-results/11/?changeset_validation_ids=23&changeset_test_ids=27"
}
```


### Apply Changeset

API:
```
POST /api/v1/changeset/apply/
```

POST data should be a JSON object in the form:
```
{
    "changeset_id": <changeset_id>
    "server_id": <server_id>
}
```

Use the Changeset Apply Status API to check the status/result of changeset apply.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"changeset_id": 11, "server_id": 1}' -u dba:dba http://localhost:8000/api/v1/changeset/apply/

{
    "request_id": "ae54b91bc38d0256a48c95b18b7103b06a83313a",
    "thread_started": true
}
```


### Changeset Apply Status

API:
```
GET /api/v1/changeset/apply_status/<request_id>/
```
request_id - ID of the request that started the apply thread.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset/apply_status/ae54b91bc38d0256a48c95b18b7103b06a83313a/

{
    "thread_changeset_detail_apply_ids": [
        15
    ],
    "thread_is_alive": false,
    "thread_messages": [
        [
            "info",
            "Changeset apply thread started."
        ],
        [
            "info",
            "create table t3 (\r\n  id int primary key auto_increment\r\n)"
        ],
        [
            "info",
            "Changeset apply thread ended."
        ]
    ]
}
```


Changeset Detail
----------------

### Get Changeset Details

API:
```
GET /api/v1/changeset_detail/?changeset__id=<changeset_id>
```
changeset_id - Changeset ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset_detail/?changeset__id=9

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 2
    },
    "objects": [
        {
            "after_checksum": "",
            "apply_sql": "ccreate table t1...",
            "before_checksum": "",
            "changeset": "/api/v1/changeset/9/",
            "count_sql": "",
            "created_at": "2013-05-10T00:21:41",
            "description": "ccreate a table",
            "id": 10,
            "resource_uri": "/api/v1/changeset_detail/10/",
            "revert_sql": "ddrop table t1",
            "type": "add",
            "updated_at": "2013-05-10T01:24:15",
            "volumetric_values": ""
        },
        {
            "after_checksum": "",
            "apply_sql": "drop table t2",
            "before_checksum": "",
            "changeset": "/api/v1/changeset/9/",
            "count_sql": "",
            "created_at": "2013-05-10T01:24:15",
            "description": "drop a table",
            "id": 13,
            "resource_uri": "/api/v1/changeset_detail/13/",
            "revert_sql": "create table t2...",
            "type": "drop",
            "updated_at": "2013-05-10T01:24:15",
            "volumetric_values": ""
        }
    ]
}
```

### Get Changeset Detail

API:
```
GET /api/v1/changeset_detail/<changeset_detail_id>/
```
changeset_detail_id - Changeset Detail ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset_detail/10/

{
    "after_checksum": "",
    "apply_sql": "ccreate table t1...",
    "before_checksum": "",
    "changeset": "/api/v1/changeset/9/",
    "count_sql": "",
    "created_at": "2013-05-10T00:21:41",
    "description": "ccreate a table",
    "id": 10,
    "resource_uri": "/api/v1/changeset_detail/10/",
    "revert_sql": "ddrop table t1",
    "type": "add",
    "updated_at": "2013-05-10T01:24:15",
    "volumetric_values": ""
}
```


Changeset Test
--------------

### Get Changeset Tests

API:
```
GET /api/v1/changeset_test/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset_test/

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "changeset_detail": "/api/v1/changeset_detail/15/",
            "created_at": "2013-05-10T23:25:00",
            "ended_at": "2013-05-10T23:25:00",
            "id": 27,
            "resource_uri": "/api/v1/changeset_test/27/",
            "results_log": "",
            "started_at": "2013-05-10T23:25:00",
            "updated_at": "2013-05-10T23:25:00"
        }
    ]
}
```

### Get Changeset Test

API:
```
GET /api/v1/changeset_test/<changeset_test_id>/
```
changeset_test_id = Changeset Test ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset_test/27/

{
    "changeset_detail": "/api/v1/changeset_detail/15/",
    "created_at": "2013-05-10T23:25:00",
    "ended_at": "2013-05-10T23:25:00",
    "id": 27,
    "resource_uri": "/api/v1/changeset_test/27/",
    "results_log": "",
    "started_at": "2013-05-10T23:25:00",
    "updated_at": "2013-05-10T23:25:00"
}
```


Changeset Validation
--------------------

### Get Changeset Validations

API:
```
GET /api/v1/changeset_validation/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset_validation/?changeset__id=11

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "changeset": "/api/v1/changeset/11/",
            "created_at": "2013-05-10T23:25:00",
            "id": 23,
            "resource_uri": "/api/v1/changeset_validation/23/",
            "result": "",
            "timestamp": "2013-05-10T15:25:00",
            "updated_at": "2013-05-10T23:25:00"
        }
    ]
}
```


### Get Changeset Validation

API:
```
GET /api/v1/changeset_validation/<changeset_validation_id>/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset_validation/23/

{
    "changeset": "/api/v1/changeset/11/",
    "created_at": "2013-05-10T23:25:00",
    "id": 23,
    "resource_uri": "/api/v1/changeset_validation/23/",
    "result": "",
    "timestamp": "2013-05-10T15:25:00",
    "updated_at": "2013-05-10T23:25:00"
}
```


Changeset Detail Apply
----------------------

### Get Changeset Detail Applies

API:
```
GET /api/v1/changeset_detail_apply/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset_detail_apply/?changeset_detail__changeset__id=11

{
    "meta": {
        "limit": 20,
        "next": null,
        "offset": 0,
        "previous": null,
        "total_count": 1
    },
    "objects": [
        {
            "changeset_detail": "/api/v1/changeset_detail/15/",
            "created_at": "2013-05-11T01:11:42",
            "environment": "/api/v1/environment/1/",
            "id": 15,
            "resource_uri": "/api/v1/changeset_detail_apply/15/",
            "results_log": "",
            "server": "/api/v1/server/1/",
            "updated_at": "2013-05-11T01:11:42"
        }
    ]
}
```

### Get Changeset Detail Apply

API:
```
GET /api/v1/changeset_detail_apply/<changeset_detail_apply_id>/
```
changeset_detail_apply_id = Changeset Detail Apply ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset_detail_apply/15/

{
    "changeset_detail": "/api/v1/changeset_detail/15/",
    "created_at": "2013-05-11T01:11:42",
    "environment": "/api/v1/environment/1/",
    "id": 15,
    "resource_uri": "/api/v1/changeset_detail_apply/15/",
    "results_log": "",
    "server": "/api/v1/server/1/",
    "updated_at": "2013-05-11T01:11:42"
}
```