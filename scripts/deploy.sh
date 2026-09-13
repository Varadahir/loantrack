#!/usr/bin/env bash
set -euo pipefail

echo "==> LoanTrack Kubernetes deployment"

if [ ! -f .env ]; then
  echo "ERROR: .env not found."
  echo "Create it first with: cp .env.example .env"
  exit 1
fi

echo "==> Checking minikube"
if ! minikube status >/dev/null 2>&1; then
  echo "Starting minikube..."
  minikube start --driver=docker
fi

echo "==> Building backend image inside minikube"
minikube image build -t loantrack-backend:v1 -f backend/Dockerfile .

echo "==> Building frontend image inside minikube"
minikube image build -t loantrack-frontend:v1 -f frontend/Dockerfile .

echo "==> Creating namespace"
kubectl apply -f k8s/namespace.yaml

echo "==> Creating Kubernetes Secret from local .env"
set -a
source .env
set +a

kubectl create secret generic loantrack-db-secret \
  -n loantrack \
  --from-literal=POSTGRES_DB="$POSTGRES_DB" \
  --from-literal=POSTGRES_USER="$POSTGRES_USER" \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=DB_USER="$DB_USER" \
  --from-literal=DB_PASSWORD="$DB_PASSWORD" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "==> Applying ConfigMap"
kubectl apply -f k8s/configmap.yaml

echo "==> Deploying PostgreSQL"
kubectl apply -f k8s/postgres.yaml

echo "==> Waiting for PostgreSQL"
kubectl rollout status statefulset/postgres -n loantrack --timeout=180s

echo "==> Deploying backend"
kubectl apply -f k8s/backend.yaml

echo "==> Waiting for backend"
kubectl rollout status deployment/backend -n loantrack --timeout=180s

echo "==> Deploying frontend"
kubectl apply -f k8s/frontend.yaml

echo "==> Waiting for frontend"
kubectl rollout status deployment/frontend -n loantrack --timeout=180s

echo ""
echo "==> Final Kubernetes status"
kubectl get pods -n loantrack
echo ""
kubectl get services -n loantrack

echo ""
echo "==> LoanTrack deployment completed successfully"
echo ""
echo "Application URL:"
minikube service frontend -n loantrack --url
echo ""
echo "Namespace: loantrack"

