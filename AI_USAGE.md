# AI Usage

AI tools were used as development assistance during the LoanTrack assignment.

| Task | Tool | Accepted as-is | Changed and why |
|---|---|---|---|
| Initial project structure and architecture | ChatGPT | Partially | Reviewed and adapted the structure to match the assignment requirements. |
| Backend FastAPI implementation | ChatGPT | Partially | Tested the generated code locally and corrected database cursor usage. |
| Dockerfiles and Docker Compose | ChatGPT | Partially | Tested the images and adjusted configuration for non-root execution, health checks, and caching requirements. |
| Kubernetes manifests | ChatGPT | Partially | Tested every manifest on minikube and adjusted probes, resources, services, secrets, and persistent storage based on actual behavior. |
| README and evidence documentation | ChatGPT | Partially | Verified commands and outputs against the actual running environment before documenting them. |
| Troubleshooting | ChatGPT | No | Used actual command output and logs to identify and fix problems rather than assuming the generated configuration was correct. |

## Where AI was wrong or misleading

One generated backend implementation initially used `row_factory` incorrectly as an argument to the psycopg3 `execute()` call. When the `/loans` endpoint was tested, this caused the expected dictionary-style database rows to fail. I checked the psycopg3 cursor usage, changed the implementation to configure `row_factory=dict_row` on the cursor, and then verified the endpoint again.

The Kubernetes configuration also had to be tested against the actual minikube environment instead of being accepted blindly. I used `kubectl get`, `kubectl describe`, `kubectl logs`, `kubectl exec`, rollout commands, and application requests to verify that the generated configuration actually worked.
