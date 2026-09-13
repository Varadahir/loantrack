LoanTrack — Evidence

1. Test Environment

LoanTrack was developed and tested locally on Windows using Docker Desktop, Docker Compose, kubectl, minikube, and Python.

Kubernetes environment:

Kubernetes: v1.35.1

minikube: v1.38.1

Driver: Docker

All LoanTrack Kubernetes resources are deployed in the loantrack namespace.

2. Part B — Docker Evidence

B1. Docker Images

LoanTrack contains a separate Dockerfile for each application tier:

backend/Dockerfile

frontend/Dockerfile

PostgreSQL uses the official PostgreSQL image.

The backend uses a multi-stage Docker build. Dependencies are installed in the builder stage and only the installed dependencies and application files are copied into the final image.

Backend base image:

python:3.12-slim-bookworm

Frontend base image:

nginx:1.29-alpine

Both application containers run as a non-root user:

appuser

Commands used:

docker images loantrack-backend loantrack-frontend

docker compose ps

docker compose exec backend whoami

docker compose exec frontend whoami

The backend image was verified to be below the required 300 MB limit.

The containers were verified to run as the non-root user appuser.

B2. Docker Compose Services

Docker Compose runs all three application tiers:

Browser
|
| HTTP
v
Frontend / Nginx
|
| HTTP
v
Backend API
|
| PostgreSQL
v
PostgreSQL

All services use the user-defined Docker network:

loantrack

The backend connects to PostgreSQL using the Docker service name:

db:5432

The frontend communicates with the backend and never communicates directly with PostgreSQL.

Command:

docker compose ps

The following services were running successfully:

db

backend

frontend

PostgreSQL health was checked before the backend started.

B3. Backend Health Check

The backend provides:

GET /healthz

This endpoint checks whether the backend process is alive and does not depend on PostgreSQL.

Command:

Invoke-RestMethod http://localhost:8000/healthz

Output:

status service

ok     loantrack-api

The backend Docker image also contains a Docker HEALTHCHECK using /healthz.

B4. Database Readiness Check

The backend provides:

GET /readyz

This endpoint checks whether PostgreSQL is reachable.

Command:

Invoke-RestMethod http://localhost:8000/readyz

Output:

status database

ready  reachable

This confirms that the backend can reach PostgreSQL.

B5. Loan API

The backend provides:

GET /loans

POST /loans

Command:

Invoke-RestMethod http://localhost:8000/loans

The API successfully returned the seeded loan records.

Initial seed records:

1 | Aarav Sharma  | 250000.00 | Austin   | APPROVED
2 | Emma Wilson   | 375000.00 | Dallas   | PENDING
3 | Rahul Patel   | 180000.00 | Houston  | APPROVED
4 | Sophia Brown  | 425000.00 | Atlanta  | PENDING
5 | Daniel Thomas | 310000.00 | Phoenix  | CLOSED

B6. Frontend-to-Backend Connectivity

The frontend communicates with the backend over HTTP.

The browser sends requests to:

/api/loans

Nginx proxies these requests to:

backend:8000

The frontend contains no PostgreSQL driver, database connection string, or database credentials.

Command:

Invoke-RestMethod http://localhost:8080/api/loans

The frontend returned the same loan records provided by the backend.

Traffic flow:

Browser
|
| HTTP
v
Frontend
|
| HTTP /api/loans
v
Backend
|
| PostgreSQL
v
Database

B7. Docker Database Persistence

PostgreSQL uses the named Docker volume:

postgres_data

Persistence was tested using:

docker compose down

docker compose up -d

After restarting, the database records remained.

This confirmed that normal docker compose down does not remove the named PostgreSQL volume.

The reset behavior was also tested using:

docker compose down -v

docker compose up -d

The -v option removed the named PostgreSQL volume. After the volume was recreated, the database was initialized again using the migration and seed data.

The database returned to the original five seed rows.

B8. Docker UI Evidence

The LoanTrack application was successfully opened in the browser while running through Docker Compose.

The UI displays:

Loan records

Loan amount

Property city

Status

Add Loan form

Screenshot:

evidence/docker-ui.png

3. Part C — Database and Three-Tier Connectivity

C1. Database Schema

The database schema is stored in:

db/migrations/001_create_loans.sql

The migration creates the loans table.

Schema:

id              SERIAL PRIMARY KEY
borrower_name   TEXT NOT NULL
loan_amount     NUMERIC(14,2) NOT NULL
property_city   TEXT
status          TEXT NOT NULL DEFAULT 'PENDING'
created_at      TIMESTAMPTZ NOT NULL DEFAULT now()

The migration is applied automatically when the backend starts.

C2. Seed Data

Seed data is stored in:

db/seed/001_seed_loans.sql

The seed file contains five records:

1 | Aarav Sharma  | 250000.00 | Austin   | APPROVED
2 | Emma Wilson   | 375000.00 | Dallas   | PENDING
3 | Rahul Patel   | 180000.00 | Houston  | APPROVED
4 | Sophia Brown  | 425000.00 | Atlanta  | PENDING
5 | Daniel Thomas | 310000.00 | Phoenix  | CLOSED

C3. Connection Pooling

The backend uses psycopg-pool for PostgreSQL connection pooling.

The application uses a connection pool instead of creating a new database connection for every request.

C4. Database Startup

The backend contains database startup retry logic with backoff.

Successful backend startup logs:

Database connection successful on attempt 1.
Database migration applied successfully.
Database seed data inserted.
Application startup complete.

This confirms successful database connection, migration, and seed initialization.

C5. Health and Readiness Separation

The application separates process health from database readiness.

/healthz checks whether the backend process is alive and does not depend on PostgreSQL.

/readyz checks whether the backend can communicate with PostgreSQL.

This allows Kubernetes to distinguish between a running backend process and a backend that is ready to serve database-dependent requests.

C6. Add Loan Through UI and Verify in PostgreSQL

A new loan was added through the LoanTrack frontend UI.

Values entered:

Borrower Name: varad demo
Loan Amount: 275000
Property City: pune
Status: PENDING

Request flow:

Browser
|
v
Frontend
|
| POST /api/loans
v
Backend
|
| PostgreSQL
v
PostgreSQL

The frontend does not communicate directly with PostgreSQL.

The same record was then verified directly inside PostgreSQL.

Command:

kubectl exec -n loantrack postgres-0 -- psql -U loantrack -d loantrack -c "SELECT id, borrower_name, loan_amount, property_city, status FROM loans ORDER BY id;"

Output:

id | borrower_name | loan_amount | property_city |  status
----+---------------+-------------+---------------+----------
1 | Aarav Sharma  |   250000.00 | Austin        | APPROVED
2 | Emma Wilson   |   375000.00 | Dallas        | PENDING
3 | Rahul Patel   |   180000.00 | Houston       | APPROVED
4 | Sophia Brown  |   425000.00 | Atlanta       | PENDING
5 | Daniel Thomas |   310000.00 | Phoenix       | CLOSED
7 | varad demo    |   275000.00 | pune          | PENDING
(6 rows)

The varad demo record confirms that the loan submitted through the frontend was successfully processed by the backend and persisted in PostgreSQL.

The ID is 7 because PostgreSQL's SERIAL sequence does not automatically reuse the previously deleted ID 6.

4. Part D — Kubernetes / minikube Evidence

D1. Kubernetes Namespace

LoanTrack is deployed into the dedicated namespace:

loantrack

Command:

kubectl get namespace loantrack

Output:

NAME        STATUS
loantrack   Active

LoanTrack resources are isolated inside this namespace.

D2. Kubernetes Architecture

The Kubernetes architecture is:

                Kubernetes Cluster
                Namespace: loantrack

                       Browser
                          |
                          |
                     NodePort 30080
                          |
                          v
                +------------------+
                |    Frontend      |
                |   Deployment     |
                +--------+---------+
                         |
                         | HTTP
                         v
                +------------------+
                |     Backend      |
                |    Deployment    |
                |   3 replicas     |
                +--------+---------+
                         |
                         | TCP 5432
                         v
                +------------------+
                |   PostgreSQL     |
                |   StatefulSet    |
                +--------+---------+
                         |
                         v
                +------------------+
                | Persistent PVC   |
                +------------------+

D3. PostgreSQL StatefulSet

PostgreSQL was deployed as a StatefulSet.

A StatefulSet was selected because PostgreSQL is stateful and requires persistent storage.

Commands:

kubectl get statefulset -n loantrack

kubectl get pods -n loantrack -l app=postgres

kubectl get pvc -n loantrack

Verified state:

postgres StatefulSet: 1/1
postgres-0: 1/1 Running
PVC: Bound
Storage: 2Gi
Access Mode: ReadWriteOnce

D4. Backend Deployment

The backend runs as a Kubernetes Deployment.

Backend Service:

backend

Service type:

ClusterIP

Commands:

kubectl get deployment backend -n loantrack

kubectl get service backend -n loantrack

kubectl get pods -n loantrack -l app=backend

Verified state:

Backend Deployment: 3/3
Backend Service: ClusterIP

D5. Frontend Deployment

The frontend runs as a Kubernetes Deployment.

The frontend is exposed using a NodePort Service.

Commands:

kubectl get deployment frontend -n loantrack

kubectl get service frontend -n loantrack

kubectl get pods -n loantrack -l app=frontend

Verified state:

Frontend Deployment: 1/1
Frontend Pod: 1/1 Running
Frontend Service: NodePort
NodePort: 30080

The application was opened using:

minikube service frontend -n loantrack --url

The URL provided during testing was:

http://127.0.0.1:55506

The exact URL may change between minikube runs.

5. Kubernetes Configuration and Secrets

D6. ConfigMap

Non-sensitive configuration is stored in:

loantrack-config

The ConfigMap contains:

DB_HOST=postgres
DB_PORT=5432
DB_NAME=loantrack

Database passwords are not stored in the ConfigMap.

Command:

kubectl get configmap loantrack-config -n loantrack

D7. Kubernetes Secret

Database credentials are stored in:

loantrack-db-secret

The real Secret was created from the local .env values.

The Kubernetes manifests consume the credentials using secretKeyRef.

The repository contains:

k8s/secret.example.yaml

The example file contains dummy values only.

Command:

kubectl get secret loantrack-db-secret -n loantrack

Output:

NAME                   TYPE     DATA   AGE
loantrack-db-secret    Opaque   5      ...

Secret values were intentionally not displayed.

6. Kubernetes Health and Readiness Probes

Backend

Backend liveness probe:

/healthz

Backend readiness probe:

/readyz

The liveness probe checks whether the backend process is alive.

The readiness probe checks whether the backend can access PostgreSQL.

Frontend

Frontend liveness and readiness probes use:

/

The probes verify that the frontend HTTP server is responding.

7. Kubernetes DNS and Connectivity

The backend connects to PostgreSQL through the Kubernetes Service:

postgres

Fully qualified DNS name:

postgres.loantrack.svc.cluster.local

DNS Resolution

Command:

kubectl exec -n loantrack deploy/backend -- python -c "import socket; print(socket.gethostbyname_ex('postgres'))"

Output:

('postgres.loantrack.svc.cluster.local', [], ['10.97.105.93'])

This confirms that Kubernetes DNS successfully resolves the PostgreSQL Service.

TCP Connectivity

Command:

kubectl exec -n loantrack deploy/backend -- python -c "import socket; s=socket.create_connection(('postgres',5432),5); print('connected to postgres:5432'); s.close()"

Output:

connected to postgres:5432

This confirms that the backend pod can connect to PostgreSQL through the Kubernetes Service.

8. Part D4 — Scale Backend to 3 Replicas

The backend Deployment was scaled to three replicas.

Commands:

kubectl scale deployment/backend --replicas=3 -n loantrack

kubectl rollout status deployment/backend -n loantrack

kubectl get pods -n loantrack -l app=backend -o wide

Three backend pods were running.

Three pods observed during the scaling test were:

backend-6ff79dcb78-cd5jr
backend-6ff79dcb78-p5tt2
backend-6ff79dcb78-wgl5k

All three reached:

1/1 Running

Requests were repeatedly sent to the frontend API.

Command:

1..15 | ForEach-Object {
(Invoke-RestMethod "http://127.0.0.1:55506/api/loans").served_by
}

The requests were served by multiple backend pod names.

This demonstrates Kubernetes Service load balancing across the backend replicas.

9. Part D4 — Rolling Update to v2

A backend v2 image was created:

loantrack-backend

The /healthz endpoint was changed to include:

version: v2

Command:

kubectl set image deployment/backend backend=loantrack-backend -n loantrack

kubectl rollout status deployment/backend -n loantrack

The rollout completed successfully.

Verification:

kubectl exec -n loantrack deploy/backend -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/healthz').read().decode())"

Output:

{"status":"ok","service":"loantrack-api","version":"v2"}

User Experience During Rolling Update

The backend Deployment uses:

rollingUpdate:
maxUnavailable: 0
maxSurge: 1

maxUnavailable: 0 keeps existing backend capacity available during the update.

maxSurge: 1 allows Kubernetes to temporarily create one additional pod.

The readiness probe prevents traffic from being sent to a backend pod until it is ready.

Therefore, a user should continue receiving responses during the rollout.

10. Part D4 — Rollback

The backend v2 deployment was rolled back using:

kubectl rollout undo deployment/backend -n loantrack

kubectl rollout status deployment/backend -n loantrack

The backend was restored to the previous v1 image.

This demonstrates Kubernetes Deployment revision history and rollback.

11. Part D4 — Backend Pod Self-Healing

A backend pod was deliberately deleted.

Command:

kubectl delete pod backend-6ff79dcb78-llf9h -n loantrack

Kubernetes automatically created a replacement pod.

Replacement pod:

backend-6ff79dcb78-gc9jf

The replacement reached:

1/1 Running

This demonstrates Deployment self-healing.

12. Part D4 — PostgreSQL Pod Recovery and Persistence

The PostgreSQL pod was deliberately deleted.

Command:

kubectl delete pod postgres-0 -n loantrack

The StatefulSet recreated:

postgres-0

The PostgreSQL PVC remained bound.

Command:

kubectl get pvc -n loantrack

Verified state:

postgres-data-postgres-0
Status: Bound
Capacity: 2Gi
Access Mode: ReadWriteOnce

The database rows survived PostgreSQL pod deletion.

This confirms that PostgreSQL data is stored on persistent storage rather than only inside the container filesystem.

13. Final Kubernetes State

Command:

kubectl get all -n loantrack

Final state:

Pods:

backend-6ff79dcb78-gc9jf    1/1 Running
backend-6ff79dcb78-nx5m5    1/1 Running
backend-6ff79dcb78-zzbvd    1/1 Running
frontend-746d84cc76-qcmzd   1/1 Running
postgres-0                  1/1 Running

Services:

backend     ClusterIP   10.111.72.62   8000/TCP
frontend    NodePort    10.111.99.22   8080:30080/TCP
postgres    ClusterIP   10.97.105.93   5432/TCP

Deployments:

backend     3/3
frontend    1/1

StatefulSet:

postgres    1/1

14. Final Kubernetes Resources

Command:

kubectl get pvc,configmap,secret -n loantrack

Verified resources:

PVC:

postgres-data-postgres-0
Status: Bound
Capacity: 2Gi
Access Mode: ReadWriteOnce

ConfigMaps:

kube-root-ca.crt
loantrack-config

Secret:

loantrack-db-secret
Type: Opaque
Data: 5

Secret values were intentionally not displayed.

15. Kubernetes UI Evidence

The LoanTrack application was successfully opened through the Kubernetes NodePort.

The UI showed:

Loan records

varad demo loan

Loan amount

Property city

Status

Add Loan form

Screenshot:

evidence/kubernetes-ui.png

16. End-to-End Verification

Final traffic flow:

Browser
|
| HTTP
v
Frontend
|
| HTTP
v
Backend
|
| PostgreSQL
v
PostgreSQL
|
v
Persistent Storage

The frontend never communicates directly with PostgreSQL.

The backend is the application tier responsible for database communication.

17. E4 — Problems Faced

Issue 1 — psycopg3 Row Factory Error

Symptom

The backend initially had an error while returning database rows because the row_factory parameter was used incorrectly with the psycopg3 execute() operation.

The /loans endpoint did not correctly return the expected dictionary-style rows.

Diagnosis

The backend database query and psycopg3 cursor usage were inspected.

The database query itself was valid, but the cursor configuration was incorrect.

Root Cause

row_factory is configured at the cursor level in psycopg3 and should not be passed as an execute() keyword argument.

Fix

The cursor was changed to use:

with connection.cursor(row_factory=dict_row) as cursor:

The query was then executed normally:

rows = cursor.execute(...).fetchall()

The same correction was applied to the POST endpoint.

The backend was verified with:

python -m py_compile backend/app.py

The /loans endpoint then returned the expected loan records.

Git commit:

9f94808 fix: correct psycopg row factory usage

Issue 2 — Kubernetes Pod Startup Problem

Symptom

I reproduced a backend pod startup failure by temporarily setting the Deployment image to a nonexistent image tag.

Pod status:

backend-774bdd8f7c-5lzfc   0/1   ImagePullBackOff

Diagnosis

Commands run in order:

kubectl set image deployment/backend backend=loantrack-backend:not-found -n loantrack
kubectl get pods -n loantrack
kubectl describe pod backend-774bdd8f7c-5lzfc -n loantrack

Relevant output:

Image:          loantrack-backend:not-found
State:          Waiting
  Reason:       ErrImagePull
Ready:          False

Pod events showed:

Failed to pull image "loantrack-backend:not-found"
Error: ErrImagePull
Back-off pulling image "loantrack-backend:not-found"
Error: ImagePullBackOff

Root Cause

The Deployment referenced the image loantrack-backend:not-found, which did not exist in the minikube image store or an accessible registry. Kubernetes therefore could not pull the image.

Fix

I restored the Deployment to the valid locally built image:

kubectl set image deployment/backend backend=loantrack-backend:v1 -n loantrack
kubectl rollout status deployment/backend -n loantrack

Verification:

deployment "backend" successfully rolled out

The backend returned to a healthy Running state.

Issue 3 — Refused Connection / Service Routing Problem

Symptom

I reproduced a backend Service routing failure by temporarily changing the Service targetPort from 8000 to 8001.

The Service showed:

port:       8000
targetPort: 8001

The Service endpoints were published on port 8001:

backend   10.244.0.107:8001

A connection test from inside the Kubernetes cluster failed:

Connecting to backend:8000 through Kubernetes Service...
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ConnectionRefusedError: [Errno 111] Connection refused
pod "connection-test" deleted from loantrack namespace
pod loantrack/connection-test terminated (Error)

Diagnosis

Commands run in order:

kubectl patch service backend -n loantrack --type strategic --patch-file .\service-bad.yaml
kubectl get service backend -n loantrack -o yaml
kubectl get endpoints backend -n loantrack
kubectl run connection-test -n loantrack --rm -i --restart=Never --image=python:3.12-alpine -- python -c "import socket; print('Connecting to backend:8000 through Kubernetes Service...'); s=socket.socket(); s.settimeout(5); s.connect(('backend',8000)); print('CONNECTED'); s.close()"

Root Cause

The backend application listens on port 8000, but the Kubernetes Service was temporarily configured with targetPort: 8001.

The Service therefore forwarded traffic to a port where the backend was not listening, producing ConnectionRefusedError: [Errno 111] Connection refused.

Fix

I restored the Service to the correct target port:

kubectl patch service backend -n loantrack --type strategic --patch-file .\service-good.yaml
Remove-Item .\service-good.yaml -Force
kubectl get service backend -n loantrack
kubectl get endpoints backend -n loantrack

Verification showed:

backend   ClusterIP   10.111.72.62   <none>   8000/TCP
backend   10.244.0.107:8000

The Service was restored to the port on which the backend listens.

Issue 4 — Liveness Probe Killing a Healthy Container

Symptom

I reproduced a liveness-probe failure by temporarily changing the backend liveness endpoint from /healthz to /probe-test-failure.

The new backend pod initially started successfully:

backend-66f997dfc8-cwvk2   1/1   Running   0

After the liveness checks ran, the same container was restarted:

backend-66f997dfc8-cwvk2   1/1   Running   2 (12s ago)

Diagnosis

Commands run in order:

kubectl patch deployment backend -n loantrack --type strategic --patch-file .\probe-bad.yaml
kubectl rollout status deployment/backend -n loantrack --timeout=120s
kubectl get pods -n loantrack -l app=backend
Start-Sleep -Seconds 40
kubectl get pods -n loantrack -l app=backend
kubectl describe pod -n loantrack -l app=backend

Relevant output:

Restart Count: 2

Liveness: http-get http://:8000/probe-test-failure
delay=5s timeout=2s period=5s #success=1 #failure=3

Kubernetes events showed:

Warning  Unhealthy
Liveness probe failed: HTTP probe failed with statuscode: 404

Normal   Killing
Container backend failed liveness probe, will be restarted

Root Cause

The backend container itself was running, but the liveness probe was configured to call /probe-test-failure, which does not exist and therefore returned HTTP 404.

After three failed liveness checks, kubelet treated the container as unhealthy and restarted it.

Fix

I restored the original /healthz liveness probe:

kubectl patch deployment backend -n loantrack --type strategic --patch-file .\probe-good.yaml
Remove-Item .\probe-good.yaml -Force
kubectl rollout status deployment/backend -n loantrack --timeout=120s

Verification:

deployment "backend" successfully rolled out

The replacement backend pod reached:

1/1   Running

with the correct /healthz liveness probe restored.

18. Verification Summary

Verification

Status

Docker Compose three-tier application

PASS

Frontend to backend HTTP communication

PASS

Backend to PostgreSQL communication

PASS

PostgreSQL named volume

PASS

Database migration

PASS

Database seed data

PASS

Connection pooling

PASS

Backend /healthz

PASS

Backend /readyz

PASS

Kubernetes namespace

PASS

PostgreSQL StatefulSet

PASS

PostgreSQL persistent storage

PASS

Backend Deployment

PASS

Frontend Deployment

PASS

Backend ClusterIP

PASS

PostgreSQL ClusterIP

PASS

Frontend NodePort

PASS

Kubernetes ConfigMap

PASS

Kubernetes Secret

PASS

Kubernetes DNS resolution

PASS

Backend-to-PostgreSQL connectivity

PASS

Backend scaling to 3 replicas

PASS

Multiple backend pods serving requests

PASS

Backend v2 rolling update

PASS

Kubernetes rollback

PASS

Backend pod self-healing

PASS

PostgreSQL pod recovery

PASS

PostgreSQL data persistence

PASS

Final Kubernetes resource verification

PASS

19. Application URLs

Docker Compose frontend:

http://localhost:8080

Docker Compose backend:

http://localhost:8000

Kubernetes frontend:

minikube service frontend -n loantrack --url

The URL provided during testing was:

http://127.0.0.1:55506

The exact URL may change between minikube runs.

20. Security Verification

The following security requirements were verified:

.env is excluded using .gitignore.

Real database credentials are not committed to Git.

Kubernetes database credentials are stored in a Kubernetes Secret.

k8s/secret.example.yaml contains dummy values only.

Database passwords are not stored in the ConfigMap.

The frontend contains no PostgreSQL credentials.

The frontend does not connect directly to PostgreSQL.

PostgreSQL is exposed only through a ClusterIP Service inside Kubernetes.

Secret values were not included in this evidence document.

21. Conclusion

LoanTrack was successfully deployed and tested using Docker Compose and Kubernetes on a local minikube cluster.

The application was verified end-to-end from the browser through the frontend and backend to PostgreSQL.

Kubernetes operations including scaling, rolling update, rollback, backend pod replacement, PostgreSQL pod recovery, and persistent database storage were also verified.