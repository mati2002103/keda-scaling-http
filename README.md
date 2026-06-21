# KEDA + RabbitMQ + Celery POC (minikube)

Dwa warianty scalera (stosuj **tylko jeden** na raz — oba targetują ten sam
deployment). Wszystkie komponenty używają wspólnego Secret `rabbitmq-credentials`
(użytkownik `poc` / `poc`):

| Komponent | Klucz w Secrecie | Port |
|-----------|------------------|------|
| worker, producer | `amqp-url` | 5672 |
| KEDA HTTP | `http-url-fqdn` | 15672 |
| KEDA AMQP | `amqp-url-fqdn` | 5672 |

| Plik | Protokół | Co liczy KEDA |
|------|----------|---------------|
| `03-scaledobject-http.yaml` | HTTP `:15672` | `ready + unacked` (`excludeUnacknowledged: false`) |
| `optional/03-scaledobject-amqp.yaml` | AMQP `:5672` | tylko `ready` |

## Prereqs

- `minikube start`
- `kubectl`, `helm`, `docker`

## Wdrożenie od zera

### 1. Obraz

```bash
eval $(minikube docker-env)
docker build -t celery-poc:local .
```

### 2. KEDA

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace --version 2.20.1
kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=120s
```

### 3. Workload

```bash
kubectl create namespace keda-poc
kubectl apply -f 00-credentials.yaml
kubectl apply -f 01-rabbitmq.yaml
kubectl wait --for=condition=available --timeout=120s deploy/rabbitmq -n keda-poc

# pierwszy raz lub po zmianie queue args — usuń starą kolejkę celery
kubectl exec -n keda-poc deploy/rabbitmq -- rabbitmqctl delete_queue celery --if-unused || true

kubectl apply -f 02-worker.yaml

# HTTP (ready + unacked) — zalecany do długich zadań
kubectl apply -f 03-scaledobject-http.yaml

# ALBO AMQP (tylko ready) — do porównania
# kubectl delete scaledobject celery-worker-scaler-http -n keda-poc
# kubectl apply -f optional/03-scaledobject-amqp.yaml
```

### 4. Test

```bash
# kolejka
watch -n2 "kubectl exec -n keda-poc deploy/rabbitmq -- rabbitmqctl list_queues name messages_ready messages_unacknowledged 2>/dev/null | grep -E 'name|celery[^@]'"

# pody + HPA
watch -n2 'kubectl get pods,hpa -n keda-poc'

# zadania
kubectl apply -f 04-producer-job.yaml
```

### Przełączanie scalera

```bash
kubectl delete scaledobject celery-worker-scaler-amqp -n keda-poc --ignore-not-found
kubectl apply -f 03-scaledobject-http.yaml   # lub optional/03-scaledobject-amqp.yaml
```

## Zachowanie HTTP vs AMQP

**HTTP** (`excludeUnacknowledged: false`):
- `ready=0`, `unacked=16` → KEDA widzi **16** → trzyma 4 pody
- Scale-down dopiero gdy zadania się skończą i zrobią ACK

**AMQP**:
- `ready=0`, `unacked=16` → KEDA widzi **0** → scale-down po `cooldownPeriod`

## Teardown

```bash
kubectl delete namespace keda-poc
helm uninstall keda -n keda
```
