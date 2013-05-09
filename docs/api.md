REST API
========


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
GET /api/v1/role/(role_id)/
```
<role_id> - Role ID/PK

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
            "auth_user": {
                "first_name": "",
                "last_login": "2013-05-08T18:36:37",
                "last_name": "",
                "resource_uri": "/api/v1/auth_user/1/",
                "username": "admin"
            },
            "created_at": "2013-04-03T17:02:34",
            "email": "admin@example.com",
            "id": 1,
            "name": "admin",
            "resource_uri": "/api/v1/user/1/",
            "role": {
                "created_at": "2013-04-01T04:02:25",
                "id": 1,
                "name": "admin",
                "resource_uri": "/api/v1/role/1/",
                "updated_at": "2013-04-01T04:02:25"
            },
            "updated_at": "2013-04-29T01:18:19"
        },
        {
            "auth_user": {
                "first_name": "",
                "last_login": "2013-05-03T00:04:56",
                "last_name": "",
                "resource_uri": "/api/v1/auth_user/2/",
                "username": "dba"
            },
            "created_at": "2013-04-29T19:11:10",
            "email": "dba@example.com",
            "id": 2,
            "name": "dba",
            "resource_uri": "/api/v1/user/2/",
            "role": {
                "created_at": "2013-04-01T04:02:31",
                "id": 2,
                "name": "dba",
                "resource_uri": "/api/v1/role/2/",
                "updated_at": "2013-04-01T04:02:31"
            },
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
<user_id> - User ID/PK

Sample usage and output:
```
$ curl -u admin:admin http://localhost:8000/api/v1/user/1/

{
    "auth_user": {
        "first_name": "",
        "last_login": "2013-05-08T18:36:37",
        "last_name": "",
        "resource_uri": "/api/v1/auth_user/1/",
        "username": "admin"
    },
    "created_at": "2013-04-03T17:02:34",
    "email": "admin@example.com",
    "id": 1,
    "name": "admin",
    "resource_uri": "/api/v1/user/1/",
    "role": {
        "created_at": "2013-04-01T04:02:25",
        "id": 1,
        "name": "admin",
        "resource_uri": "/api/v1/role/1/",
        "updated_at": "2013-04-01T04:02:25"
    },
    "updated_at": "2013-04-29T01:18:19"
}
```

### Create User

API:
```
POST /api/v1/user/create/
```
POST data should be JSON object in the form:
{
    "name": <name>,
    "email": <email>,
    "role_id": <role_id>,
    "password": <password>
}

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "dev2", "email": "dev2@example.com", "role_id": 3, "password": "dev"}' -u admin:admin http://localhost:8000/api/v1/user/create/

{
    "auth_user": {
        "first_name": "",
        "last_login": "2013-05-09T01:50:08.020853",
        "last_name": "",
        "resource_uri": "/api/v1/auth_user/8/",
        "username": "dev2"
    },
    "created_at": "2013-05-09T01:50:08.416342",
    "email": "dev2@example.com",
    "id": 8,
    "name": "dev2",
    "resource_uri": "/api/v1/user/7/",
    "role": {
        "created_at": "2013-04-01T04:02:36",
        "id": 3,
        "name": "developer",
        "resource_uri": "/api/v1/role/3/",
        "updated_at": "2013-04-01T04:02:36"
    },
    "updated_at": "2013-05-09T01:50:08.416651"
}
```

### Update User

API:
```
POST api/v1/user/update/<user_id>/
```
<user_id> - User ID/PK

POST data should be a JSON object in the form:
{
    "name": <name>,
    "email": <email>,
    "role_id": <role_id>
}

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "dev_2", "email": "dev_2@example.com", "role_id": 3}' -u admin:admin http://localhost:8000/api/v1/user/update/8/

{
    "auth_user": {
        "first_name": "",
        "last_login": "2013-05-09T01:56:18",
        "last_name": "",
        "resource_uri": "/api/v1/auth_user/9/",
        "username": "dev_2"
    },
    "created_at": "2013-05-09T01:56:18",
    "email": "dev_2@example.com",
    "id": 8,
    "name": "dev_2",
    "resource_uri": "/api/v1/user/8/",
    "role": {
        "created_at": "2013-04-01T04:02:36",
        "id": 3,
        "name": "developer",
        "resource_uri": "/api/v1/role/3/",
        "updated_at": "2013-04-01T04:02:36"
    },
    "updated_at": "2013-05-09T02:06:24.672610"
}
```

### Delete User

API:
```
POST /api/v1/user/delete/<user_id>/
```
<user_id> - User ID/PK

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
<user_id> - User ID/PK

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
<environment_id> - Environment ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X PUT --data '{"name": "env_6"}' -u admin:admin http://localhost:8000/api/v1/environment/7/
```

### Delete Environment

API:
```
DELETE /api/v1/environment/<environment_id>/
```
<environment_id> - Environment ID/PK

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
            "environment": {
                "created_at": "2013-04-27T00:24:40",
                "id": 1,
                "name": "dev",
                "resource_uri": "/api/v1/environment/1/",
                "updated_at": "2013-04-27T00:24:40"
            },
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
<server_id> - Server ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/server/1/

{
    "cached_size": null,
    "created_at": "2013-04-29T21:15:54",
    "environment": {
        "created_at": "2013-04-27T00:24:40",
        "id": 1,
        "name": "dev",
        "resource_uri": "/api/v1/environment/1/",
        "updated_at": "2013-04-27T00:24:40"
    },
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
{
    "name": <name>,
    "hostname": <hostname>,
    "port": <port>
}

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "localhost2", "hostname": "127.0.0.1"}' -u admin:admin http://localhost:8000/api/v1/server/
```

### Update Server

API:
```
PUT /api/v1/server/<server_id>/
```
<server_id> - Server ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X PUT --data '{"name": "localhost_2", "hostname": "localhost"}' -u admin:admin http://localhost:8000/api/v1/server/8/
```

### Delete Server

API:
```
DELETE /api/v1/server/<server_id>/
```
<server_id> - Server ID/PK

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
<database_schema_id> - Database Schema ID/PK

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
            "database_schema": {
                "created_at": "2013-04-30T23:20:15",
                "id": 5,
                "name": "test_schema_1",
                "resource_uri": "/api/v1/database_schema/5/",
                "updated_at": "2013-04-30T23:20:15"
            },
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
            "database_schema": {
                "created_at": "2013-05-09T21:49:20",
                "id": 6,
                "name": "pdbtest_db1",
                "resource_uri": "/api/v1/database_schema/6/",
                "updated_at": "2013-05-09T21:49:20"
            },
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
<schema_version_id> - Schema Version ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/schema_version/11/

{
    "checksum": "8f281fa8732078c9b4f6cea8c988c48b",
    "created_at": "2013-04-30T23:20:15",
    "database_schema": {
        "created_at": "2013-04-30T23:20:15",
        "id": 5,
        "name": "test_schema_1",
        "resource_uri": "/api/v1/database_schema/5/",
        "updated_at": "2013-04-30T23:20:15"
    },
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
{
    "server_id": <server_id>,
    "database_schema_name": <database_schema_name>
}

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"server_id": 1, "database_schema_name": "pdbtest_db1"}' -u admin:admin http://localhost:8000/api/v1/schema_version/save_schema_dump/

{
    "checksum": "f8c2431456e6847af3a6fab68e6b1e39",
    "created_at": "2013-05-09T21:49:20.892147",
    "database_schema": {
        "created_at": "2013-05-09T21:49:20.699588",
        "id": 6,
        "name": "pdbtest_db1",
        "resource_uri": "/api/v1/database_schema/6/",
        "updated_at": "2013-05-09T21:49:20.699933"
    },
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
            "after_version": {
                "checksum": "9c6c0612b81298ff8dbf86ae35ebc9d4",
                "created_at": "2013-05-03T00:19:19",
                "database_schema": {
                    "created_at": "2013-04-30T23:20:15",
                    "id": 5,
                    "name": "test_schema_1",
                    "resource_uri": "/api/v1/database_schema/5/",
                    "updated_at": "2013-04-30T23:20:15"
                },
                "ddl": "...",
                "id": 18,
                "resource_uri": "/api/v1/schema_version/18/",
                "updated_at": "2013-05-03T00:19:19"
            },
            "approved_at": "2013-05-03T00:19:29",
            "approved_by": {
                "auth_user": {
                    "first_name": "",
                    "last_login": "2013-05-03T00:04:56",
                    "last_name": "",
                    "resource_uri": "/api/v1/auth_user/2/",
                    "username": "dba"
                },
                "created_at": "2013-04-29T19:11:10",
                "email": "dba@example.com",
                "id": 2,
                "name": "dba",
                "resource_uri": "/api/v1/user/2/",
                "role": {
                    "created_at": "2013-04-01T04:02:31",
                    "id": 2,
                    "name": "dba",
                    "resource_uri": "/api/v1/role/2/",
                    "updated_at": "2013-04-01T04:02:31"
                },
                "updated_at": "2013-04-29T19:11:10"
            },
            "before_version": {
                "checksum": "8f281fa8732078c9b4f6cea8c988c48b",
                "created_at": "2013-05-01T00:47:27",
                "database_schema": {
                    "created_at": "2013-04-30T23:20:15",
                    "id": 5,
                    "name": "test_schema_1",
                    "resource_uri": "/api/v1/database_schema/5/",
                    "updated_at": "2013-04-30T23:20:15"
                },
                "ddl": "...",
                "id": 13,
                "resource_uri": "/api/v1/schema_version/13/",
                "updated_at": "2013-05-01T00:47:27"
            },
            "classification": "painless",
            "created_at": "2013-04-30T23:23:00",
            "database_schema": {
                "created_at": "2013-04-30T23:20:15",
                "id": 5,
                "name": "test_schema_1",
                "resource_uri": "/api/v1/database_schema/5/",
                "updated_at": "2013-04-30T23:20:15"
            },
            "id": 4,
            "is_deleted": 0,
            "resource_uri": "/api/v1/changeset/4/",
            "review_status": "approved",
            "reviewed_at": "2013-05-03T00:19:19",
            "reviewed_by": {
                "auth_user": {
                    "first_name": "",
                    "last_login": "2013-05-03T00:04:56",
                    "last_name": "",
                    "resource_uri": "/api/v1/auth_user/2/",
                    "username": "dba"
                },
                "created_at": "2013-04-29T19:11:10",
                "email": "dba@example.com",
                "id": 2,
                "name": "dba",
                "resource_uri": "/api/v1/user/2/",
                "role": {
                    "created_at": "2013-04-01T04:02:31",
                    "id": 2,
                    "name": "dba",
                    "resource_uri": "/api/v1/role/2/",
                    "updated_at": "2013-04-01T04:02:31"
                },
                "updated_at": "2013-04-29T19:11:10"
            },
            "submitted_at": "2013-04-30T23:23:00",
            "submitted_by": {
                "auth_user": {
                    "first_name": "",
                    "last_login": "2013-05-03T00:04:56",
                    "last_name": "",
                    "resource_uri": "/api/v1/auth_user/2/",
                    "username": "dba"
                },
                "created_at": "2013-04-29T19:11:10",
                "email": "dba@example.com",
                "id": 2,
                "name": "dba",
                "resource_uri": "/api/v1/user/2/",
                "role": {
                    "created_at": "2013-04-01T04:02:31",
                    "id": 2,
                    "name": "dba",
                    "resource_uri": "/api/v1/role/2/",
                    "updated_at": "2013-04-01T04:02:31"
                },
                "updated_at": "2013-04-29T19:11:10"
            },
            "type": "DDL:Table:Create",
            "updated_at": "2013-05-03T00:19:29",
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
<changset_id> - Changeset ID/PK

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -u admin:admin http://localhost:8000/api/v1/changeset/4/

{
    "after_version": {
        "checksum": "9c6c0612b81298ff8dbf86ae35ebc9d4",
        "created_at": "2013-05-03T00:19:19",
        "database_schema": {
            "created_at": "2013-04-30T23:20:15",
            "id": 5,
            "name": "test_schema_1",
            "resource_uri": "/api/v1/database_schema/5/",
            "updated_at": "2013-04-30T23:20:15"
        },
        "ddl": "...",
        "id": 18,
        "resource_uri": "/api/v1/schema_version/18/",
        "updated_at": "2013-05-03T00:19:19"
    },
    "approved_at": "2013-05-03T00:19:29",
    "approved_by": {
        "auth_user": {
            "first_name": "",
            "last_login": "2013-05-03T00:04:56",
            "last_name": "",
            "resource_uri": "/api/v1/auth_user/2/",
            "username": "dba"
        },
        "created_at": "2013-04-29T19:11:10",
        "email": "dba@example.com",
        "id": 2,
        "name": "dba",
        "resource_uri": "/api/v1/user/2/",
        "role": {
            "created_at": "2013-04-01T04:02:31",
            "id": 2,
            "name": "dba",
            "resource_uri": "/api/v1/role/2/",
            "updated_at": "2013-04-01T04:02:31"
        },
        "updated_at": "2013-04-29T19:11:10"
    },
    "before_version": {
        "checksum": "8f281fa8732078c9b4f6cea8c988c48b",
        "created_at": "2013-05-01T00:47:27",
        "database_schema": {
            "created_at": "2013-04-30T23:20:15",
            "id": 5,
            "name": "test_schema_1",
            "resource_uri": "/api/v1/database_schema/5/",
            "updated_at": "2013-04-30T23:20:15"
        },
        "ddl": "...",
        "id": 13,
        "resource_uri": "/api/v1/schema_version/13/",
        "updated_at": "2013-05-01T00:47:27"
    },
    "classification": "painless",
    "created_at": "2013-04-30T23:23:00",
    "database_schema": {
        "created_at": "2013-04-30T23:20:15",
        "id": 5,
        "name": "test_schema_1",
        "resource_uri": "/api/v1/database_schema/5/",
        "updated_at": "2013-04-30T23:20:15"
    },
    "id": 4,
    "is_deleted": 0,
    "resource_uri": "/api/v1/changeset/4/",
    "review_status": "approved",
    "reviewed_at": "2013-05-03T00:19:19",
    "reviewed_by": {
        "auth_user": {
            "first_name": "",
            "last_login": "2013-05-03T00:04:56",
            "last_name": "",
            "resource_uri": "/api/v1/auth_user/2/",
            "username": "dba"
        },
        "created_at": "2013-04-29T19:11:10",
        "email": "dba@example.com",
        "id": 2,
        "name": "dba",
        "resource_uri": "/api/v1/user/2/",
        "role": {
            "created_at": "2013-04-01T04:02:31",
            "id": 2,
            "name": "dba",
            "resource_uri": "/api/v1/role/2/",
            "updated_at": "2013-04-01T04:02:31"
        },
        "updated_at": "2013-04-29T19:11:10"
    },
    "submitted_at": "2013-04-30T23:23:00",
    "submitted_by": {
        "auth_user": {
            "first_name": "",
            "last_login": "2013-05-03T00:04:56",
            "last_name": "",
            "resource_uri": "/api/v1/auth_user/2/",
            "username": "dba"
        },
        "created_at": "2013-04-29T19:11:10",
        "email": "dba@example.com",
        "id": 2,
        "name": "dba",
        "resource_uri": "/api/v1/user/2/",
        "role": {
            "created_at": "2013-04-01T04:02:31",
            "id": 2,
            "name": "dba",
            "resource_uri": "/api/v1/role/2/",
            "updated_at": "2013-04-01T04:02:31"
        },
        "updated_at": "2013-04-29T19:11:10"
    },
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
{
    'changeset': {
        'database_schema': 1,
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

Get list of changesets that needs to be reviewed
------------------------------------------------
```
GET /api/v1/changeset/?review_status=needs
```

Reject changeset
----------------
```
POST /api/v1/changeset/reject/<changeset_id>/
```

Approve changeset
-----------------
```
POST /api/v1/changeset/approve/<changeset_id>/
```

Soft delete changeset
---------------------
```
POST /api/v1/changeset/soft-delete/<changeset_id>/
```

