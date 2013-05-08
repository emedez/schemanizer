REST API
========

User
----

### List Users
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

### Create User
```
POST /api/v1/user/create/
```

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "dev2", "email": "dev2@example.com", "role": 3, "password": "dev"}' -u admin:admin http://localhost:8000/api/v1/user/create/

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

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "dev_2", "email": "dev_2@example.com", "role": 3}' -u admin:admin http://localhost:8000/api/v1/user/update/8/

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

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST -u admin:admin http://localhost:8000/api/v1/user/delete/8/

{}
```

Environment
-----------

### List Environments

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

### Create Environment

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X POST --data '{"name": "env6"}' -u admin:admin http://localhost:8000/api/v1/environment/
```

### Update Environment

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X PUT --data '{"name": "env_6"}' -u admin:admin http://localhost:8000/api/v1/environment/7/
```

### Delete Environment

Sample usage and output:
```
$ curl -H 'Content-Type: application/json' -X DELETE -u admin:admin http://localhost:8000/api/v1/environment/7/
```


Submit changeset
----------------
```
POST /api/v1/changeset/submit/
```

POST data should be a JSON string in the following form:
```
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
```

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

Get list of environments
------------------------
```
GET /api/v1/environment/
```
