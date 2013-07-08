Schemanizer REST API
====================

For every resource, common attributes are the following:
* list endpoint - allows retrieval of list of resources. Individual resource can be retrieved by appending primary key, for example, GET /api/v1/role/1/
* schema - retrieves info about the resource such as the supported fields, allowed HTTP methods, and allowed fields for filtering

Retrieving objects from a list endpoint will also include a meta object as shown from the output of Role list endpoint:
```
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

Meta fields:

limit - The current maximum number of objects return per call.
next - The URL for the next set of objects.
offset - The starting record number for the current set.
previous - The URL of the previous set of objects.
total_count - The number of objects of the current set.

HTTP status code should be checked for every API calls. In most cases when error occurs, the *error_message* field will be included in the content.


Role
----

List endpoint:
```
GET /api/v1/role/
```

Schema:
```
GET /api/v1/role/schema/
```


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

List endpoint:
```
GET /api/v1/user/
```

Schema:
```
GET /api/v1/user/schema/
```


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
            "github_login": null,
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
            "github_login": "test",
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
    "github_login": null,
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
    "github_login": null,
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
    "github_login": null,
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

List endpoint:
```
GET /api/v1/environment/
```

Schema:
```
GET /api/v1/environment/schema/
```


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

List endpoint:
```
GET /api/v1/server/
```

Schema:
```
GET /api/v1/server/schema/
```


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

List endpoint:
```
GET /api/v1/database_schema/
```

Schema:
```
GET /api/v1/database_schema/schema/
```


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

List endpoint:
```
GET /api/v1/schema_version/
```

Schema:
```
GET /api/v1/schema_version/schema/
```


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

List endpoint:
```
GET /api/v1/changeset/
```

Schema:
```
GET /api/v1/changeset/schema/
```


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
            "is_deleted": false,
            "repo_filename": "changesets/0703a01.yaml",
            "resource_uri": "/api/v1/changeset/4/",
            "review_status": "approved",
            "review_version": "/api/v1/schema_version/1/",
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
            "is_deleted": false,
            "resource_uri": "/api/v1/changeset/9/",
            "review_status": "needs",
            "review_version": "/api/v1/schema_version/1/",
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
    "is_deleted": false,
    "repo_filename": "",
    "resource_uri": "/api/v1/changeset/4/",
    "review_status": "approved",
    "review_version": "/api/v1/schema_version/1/",
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
        'review_version_id': 1
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
$ curl -H 'Content-Type: application/json' -X POST --data '{"changeset": {"database_schema_id": 1, "type": "DDL:Table:Create", "classification": "painless", "review_version_id": "1"}, "changeset_details": [{"type": "add", "description": "create a table", "apply_sql": "create table t1 (id int primary key auto_increment)", "revert_sql": "drop table t1"}]}' -u dev:dev http://localhost:8000/api/v1/changeset/submit/

{
    "after_version": null,
    "approved_at": null,
    "approved_by": null,
    "before_version": null,
    "classification": "painless",
    "created_at": "2013-05-10T00:21:41.454048",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 9,
    "is_deleted": false,
    "repo_filename": "",
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "needs",
    "review_version": "/api/v1/schema_version/1/",
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
    "is_deleted": false,
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "approved",
    "review_version": "/api/v1/schema_version/1/",
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
    "is_deleted": true,
    "repo_filename": "",
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "needs",
    "review_version": "/api/v1/schema_version/1/",
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
        'database_schema_id': 11,
        'type': 'DDL:Table:Drop',
        'classification': 'impacting',
        'review_version_id': 1
    },
    'changeset_details': [
        {
            'id': 8,
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
    'to_be_deleted_changeset_detail_ids': [11]
}
```
Note: changeset_details with no IDs will be inserted while those without IDs will be updated.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"changeset": {"database_schema_id": 11, "type": "DDL:Table:Drop", "classification": "impacting", "review_version_id": 1}, "changeset_details": [{"id": 8, "type": "add", "description": "ccreate a table", "apply_sql": "ccreate table t1...", "revert_sql": "ddrop table t1"}, {"type": "drop", "description": "drop a table", "apply_sql": "drop table t2", "revert_sql": "create table t2..."}], "to_be_deleted_changeset_detail_ids": [11]}' -u dba:dba http://localhost:8000/api/v1/changeset/update/9/

{
    "after_version": null,
    "approved_at": "2013-05-10T00:40:25",
    "approved_by": "/api/v1/user/2/",
    "before_version": null,
    "classification": "impacting",
    "created_at": "2013-05-10T00:21:41",
    "database_schema": "/api/v1/database_schema/5/",
    "id": 9,
    "is_deleted": false,
    "repo_filename": "",
    "resource_uri": "/api/v1/changeset/9/",
    "review_status": "needs",
    "review_version": "/api/v1/schema_version/1/",
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
    "task_id": "1e7cb249-a3af-4d6c-a6f0-c939525d2014"
}
```

### Changeset Review Status

API:
```
GET /api/v1/changeset/review_status/<task_id>/
```
task_id - Changeset review task ID

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset/review_status/f613e459-73f0-475b-a161-22b3bdede60f/

{
    "changeset_test_ids": [
        10
    ],
    "changeset_validation_ids": [
        11
    ],
    "review_results_url": "http://localhost:8000/changesetreviews/result/1/",
    "task_active": true,
    "message": {
        "message_type": "info",
        "message": "message"
    }
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
$ curl -H 'Content-Type: application/json' -X POST --data '{"changeset_id": 1, "server_id": 1}' -u dba:dba http://localhost:8000/api/v1/changeset/apply/

{
    "task_id": "1e7cb249-a3af-4d6c-a6f0-c939525d2014"
}

```


### Changeset Apply Status

API:
```
GET /api/v1/changeset/apply_status/<task_id>/
```
task_id - Changeset apply task ID.

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u dba:dba http://localhost:8000/api/v1/changeset/apply_status/4f04a70c-d60a-4761-9fe0-647e6eb7d381/

{
    "apply_results_url": "http://localhost:8000/changesetapplies/changeset-applies/?task_id=4f04a70c-d60a-4761-9fe0-647e6eb7d381",
    "changeset_detail_apply_ids": [15],
    "messages": [
        {
            "extra": null,
            "message": "ERROR <class 'utils.exceptions.Error'>: Schema version on host is unknown.",
            "message_type": "error"
        },
        {
            "extra": null,
            "message": "Changeset apply job completed.",
            "message_type": "info"
        }
    ]
}
```


Changeset Detail
----------------

List endpoint:
```
GET /api/v1/changeset_detail/
```

Schema:
```
GET /api/v1/changeset_detail/schema/
```


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
            "after_checksum": "a71b849f6fad54a3ee877187b7e8360e",
            "apply_sql": "create table t01 (id int primary key auto_increment) engine=InnoDB default charset=utf8",
            "apply_verification_sql": "",
            "before_checksum": "00000000000000000000000000000000",
            "changeset": "/api/v1/changeset/1/",
            "created_at": "2013-07-03T19:04:07",
            "description": "create table t01",
            "id": 1,
            "resource_uri": "/api/v1/changeset_detail/1/",
            "revert_sql": "drop table t01",
            "revert_verification_sql": "",
            "updated_at": "2013-07-04T20:47:11",
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
    "after_checksum": "a71b849f6fad54a3ee877187b7e8360e",
    "apply_sql": "create table t01 (id int primary key auto_increment) engine=InnoDB default charset=utf8",
    "apply_verification_sql": "",
    "before_checksum": "00000000000000000000000000000000",
    "changeset": "/api/v1/changeset/1/",
    "created_at": "2013-07-03T19:04:07",
    "description": "create table t01",
    "id": 1,
    "resource_uri": "/api/v1/changeset_detail/1/",
    "revert_sql": "drop table t01",
    "revert_verification_sql": "",
    "updated_at": "2013-07-04T20:47:11",
    "volumetric_values": ""
}
```

Test Type
---------

List endpoint:
```
GET /api/v1/test_type/
```

Schema:
```
GET /api/v1/test_type/schema/
```


Changeset Test
--------------

List endpoint:
```
GET /api/v1/changeset_test/
```

Schema:
```
GET /api/v1/changeset_test/schema/
```


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


Validation Type
---------------

List endpoint:
```
GET /api/v1/validation_type/
```

Schema:
```
GET /api/v1/validation_type/schema/
```


### Get Validation Types

API:
```
GET /api/v1/validation_type/
```


Changeset Validation
--------------------

List endpoint:
```
GET /api/v1/changeset_validation/
```

Schema:
```
GET /api/v1/changeset_validation/schema/
```


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

List endpoint:
```
GET /api/v1/changeset_detail_apply/
```

Schema:
```
GET /api/v1/changeset_detail_apply/schema/
```


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
