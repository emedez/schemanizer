# Schemanizer CLI

The Schemanizer CLI is a tool which takes advantage of the Schemanizer API to allow users to perform Schemanizer functions without the need to visit the web application.

##Usage:

To start the CLI, use the command below. This will prompt for a password and will try to authenticate the username and password. If the authentication is successful, the CLI will be initialized.

    ./manage.py signin <username>

Sample Usage:

    ./manage.py signin admin
    Enter schemanizer password for user 'admin': <password_not_shown>
    # Successful Authentication
    Schemanizer(admin)> 

#### Schemanizer Commands

#### list_changesets - Show changesets needing review

Syntax:

    list_changesets

Sample Usage:

    Schemanizer(admin)> list_changesets
    Changesets That Need To Be Reviewed:
     ID             Type           Classification    Version Control   Submitted  
                                                           URL             By     
    =============================================================================
      4       DDL:Table:Create        painless                           admin  

#### create_changeset - Create a new changeset

Syntax:

    create_changeset

Sample Usage:

    Schemanizer(admin)> create_changeset
    Enter Schema ID: 1
    Type Choices:
        1 - DDL:Table:Create
    	2 - DDL:Table:Alter
    	3 - DDL:Table:Drop
    	4 - DDL:Code:Create
    	5 - DDL:Code:Alter
    	6 - DDL:Code:Drop
    	7 - DML:Insert
    	8 - DML:Insert:Select
    	9 - DML:Update
    	10 - DML:Delete
    Choose Type(enter corresponding number): 1
    Classification Choices:
    	1 - painless
    	2 - lowrisk
    	3 - dependency
    	4 - impacting
    Choose Classification(enter corresponding number): 1
    Enter Version Control URL: 
    Add Detail(Y/N): Y
    Type Choices:
    	1 - add
    	2 - drop
    	3 - change
    	4 - upd
    	5 - ins
    	6 - del
    Choose Type(enter corresponding number): 1
    Enter Description: Create t4
    Enter Apply SQL: create table t4 (id int primary key auto_increment)
    Enter Revert SQL: drop table t4
    Add Detail(Y/N): n
    Adding changeset successful

#### show_changeset - Show fields and details for a changeset

Syntax:

    show_changeset <id>

Sample Usage:

    Schemanizer(admin)> show_changeset 4
    Changeset #4
    
    ID: 4
    Schema: employees
    Submitted By: admin
    Review Status: approved
    Classification: painless
    
    Changeset Details:
    1.    ID: 4
    	Description: Create t4
    	Type: add
    	Apply SQL: create table t4 (id int primary key auto_increment)
    	Revert SQL: drop table t4

#### review_changeset - Run validations and tests for a changeset

Syntax:

    review_changeset <id>

Sample Usage:

    Schemanizer(admin)> review_changeset 4
    Enter Schema Version ID: 3
    Starting syntax validation...
    Sleeping for 60 second(s) to give time for EC2 instance to run.
    Sleeping for 60 second(s) to give time for EC2 instance to run.
    Sleeping for 60 second(s) to give time for EC2 instance to run.
    Sleeping for 60 second(s) to give time for MySQL server on EC2 instance to start.
    Sleeping for 60 second(s) to give time for MySQL server on EC2 instance to start.
    Sleeping for 60 second(s) to give time for MySQL server on EC2 instance to start.
    Connected to MySQL server on EC2 instance.
    Executing schema version DDL.
    Validating changeset detail...
    id: 4
    apply_sql:
    create table t4 (id int primary key auto_increment)
    Review thread ended.
    
    Validation Result Log:
    1. 
    
    Test Result Log:
    1. 
    
    *** Changeset check successful.

#### approve_changeset - Approve a changeset

Syntax:

    approve_changeset <id>
    
Sample Usage:

    Schemanizer(admin)> approve_changeset 4
    Approved Changeset Details:
    Changeset #4
    
    ID: 4
    Schema: employees
    Submitted By: admin
    Review Status: approved
    Classification: painless
    
    Changeset Details:
    1.    ID: 4
    	Description: Create t4
    	Type: add
    	Apply SQL: create table t4 (id int primary key auto_increment)
    	Revert SQL: drop table t4
    
    
    *** Changeset approval successful.

##### reject_changeset - Reject a changeset

Syntax:

    reject_changeset <id>

Sample Usage:

    Schemanizer(admin)> reject_changeset 4
    Approved Changeset Details:
    Changeset #4
    
    ID: 4
    Schema: employees
    Submitted By: admin
    Review Status: rejected
    Classification: painless
    
    Changeset Details:
    1.    ID: 4
        Description: Create t4
    	Type: add
    	Apply SQL: create table t4 (id int primary key auto_increment)
    	Revert SQL: drop table t4
    
    
    *** Changeset rejection successful.
    
#### apply_changeset - Apply a changeset

Syntax:

    apply_changeset <id>

Sample Usage:

    Schemanizer(admin)> apply_changeset 4
    Enter Server ID: 3
    Changeset apply thread started.
    Changeset apply thread started.
    create table t4 (id int primary key auto_increment)
    Changeset apply thread ended.
    Apply Changeset Result Log:
    1. 
    
    *** Changeset application successful.

