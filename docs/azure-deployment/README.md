# Azure Deployment Guide

This guide describes a practical Azure deployment for the Open French API Explorer: a Streamlit application that reads public data.gouv.fr and ADEME/Data Fair APIs.

## Recommended architecture

Start with Azure Container Apps. It runs the existing Python application as a container, handles HTTPS ingress, and does not require VM administration. The deployment architecture is shown in [architecture.md](architecture.md).

### Azure resources

| Resource | Purpose | Initial configuration |
| --- | --- | --- |
| Azure Container Apps environment | Hosting boundary for the app | Consumption workload profile; add VNet integration if private networking is required |
| Azure Container App | Runs Streamlit | External HTTPS ingress for a public app, or internal ingress for private access; listen on port `8501` |
| Azure Container Registry (ACR) | Stores deployable container images | Private registry; grant the Container App managed identity image-pull permission |
| Log Analytics workspace | Stores container and platform logs | Connect the Container Apps environment and retain logs according to organizational policy |
| Azure Monitor | Alerts and operational dashboards | Alert on repeated restarts, failed revisions, high resource use, and HTTP failures |
| Microsoft Entra ID | User authentication | Protect the app when it is not intended for anonymous public use |

No database is required for the initial deployment. The app fetches records on demand and streams browser downloads. Add Azure Blob Storage only if ingestion results need to be persisted centrally or shared between app instances.

## Application container requirements

The repository includes a `Dockerfile` used by the GitHub Actions workflow. The image:

- Use a supported Python runtime compatible with `pyproject.toml`.
- Install the project and its runtime dependencies.
- Run Streamlit with `--server.address=0.0.0.0` and `--server.port=8501`.
- Configure a health probe against Streamlit's `/_stcore/health` endpoint.
- Run as a non-root user where practical.
- Avoid bundling local virtual environments, caches, downloaded datasets, or credentials.

Use a small initial allocation, for example 0.5 vCPU and 1 GiB memory, and adjust after observing actual resource usage. This is a starting point, not a capacity guarantee. Large results held in memory can increase application memory requirements.

## Network design

### Public, authenticated deployment

For the simplest hosted app, use Container Apps external ingress with HTTPS. Protect user access with Microsoft Entra ID using an available Container Apps authentication integration or a trusted identity-aware proxy. Consider Azure Front Door or Application Gateway with Web Application Firewall when organizational policy requires centralized TLS, custom domains, or edge filtering.

### Private deployment

Use internal Container Apps ingress and VNet integration when access should be limited to corporate networks. Users then need connectivity through a VPN, ExpressRoute, or a connected private network. A private deployment will not be reachable through a general public URL.

### Outbound API access

The app must make outbound HTTPS requests to the configured public APIs, including `www.data.gouv.fr` and the selected Data Fair host such as `data.ademe.fr`. Allow DNS and TCP port 443. Avoid a fixed host allowlist that prevents legitimate custom Data Fair instances from working.

The explorer accepts a custom Data Fair URL. Before making the app available to untrusted users, restrict this field to approved public API hosts and prevent access to private, loopback, link-local, and cloud metadata destinations. This avoids turning a public app into a proxy for requests to unintended services. If outbound traffic must be centrally inspected or controlled, use VNet integration with NAT Gateway or Azure Firewall and define explicit egress rules.

Upstream API limits still apply. The UI limits the number of records requested, but production settings should be conservative and respect each provider's published rate limits. For scheduled or very large ingestion jobs, use a separate background worker or Azure Container Apps Job instead of holding a long request open in the interactive UI.

## CI/CD with GitHub Actions

Recommended flow:

1. On pull requests, install dependencies and run `pytest`.
2. On merges to `main`, build the Docker image.
3. Authenticate GitHub Actions to Azure using OpenID Connect (OIDC) federation.
4. Push an immutable image tag, such as the Git commit SHA, to ACR.
5. Deploy that image to the Container App and wait for the new revision to become healthy.
6. Run a small post-deployment health check; retain the previous revision for rollback.

Use a dedicated Entra application/service principal for GitHub federation, scoped to only the required resource group and deployment actions. Do not store an Azure client secret in GitHub when OIDC federation is available. The Container App should use a managed identity for ACR pulls and any future Azure resource access.

### GitHub and Azure configuration

The workflow is in `.github/workflows/azure-deploy.yml`. It runs tests and validates the Docker image build on pull requests. A push to `main` builds and pushes an image tagged with the commit SHA, updates the Container App, and waits for its new revision to be provisioned. Manual runs are permitted only from `main`.

Before enabling deployment, configure:

- An Azure subscription and resource group.
- ACR and the Container Apps environment/app.
- A GitHub OIDC federated credential scoped to this repository and deployment branch or GitHub environment.
- GitHub Actions variables, at repository or `production` environment scope:

	| Variable | Value |
	| --- | --- |
	| `AZURE_CLIENT_ID` | Client/application ID of the Entra identity federated to GitHub |
	| `AZURE_TENANT_ID` | Entra tenant ID |
	| `AZURE_SUBSCRIPTION_ID` | Target Azure subscription ID |
	| `AZURE_RESOURCE_GROUP` | Resource group containing the Container App |
	| `AZURE_CONTAINER_APP` | Existing Container App name |
	| `AZURE_CONTAINER_REGISTRY` | ACR resource name only, without `.azurecr.io` |
- A GitHub Environment named `production`, since the deploy job targets that environment. Add required reviewers if production approvals are needed.
- A federated credential whose subject matches `repo:<owner>/<repository>:environment:production` and whose audience is `api://AzureADTokenExchange`.
- Azure role assignments for the federated deployment identity: `AcrPush` on the registry and the permissions needed to update the Container App, scoped to only the required resources where possible.
- A user-assigned or system-assigned managed identity on the Container App with `AcrPull` on the registry, configured as the app's registry authentication identity.
- An existing Container App configured with ingress on port `8501`, the desired authentication and network policy, and a startup/readiness probe for `/_stcore/health`.

There are currently no application API keys in the project. If a future source requires credentials, store them in Azure Key Vault or a protected Container App secret, not in source control or image layers.

## Environments and release safety

For a small first deployment, one Container App can be enough. For a production release process, create separate development/staging and production apps or environments. Deploy to staging first, verify health and a small API fetch, then promote the same immutable image to production. Keep production ingress, authentication, and allowed API hosts explicit.

Container Apps revisions provide a rollback path. Configure a deployment to retain the last known-good revision, and document who can shift traffic back if a health check fails.

## Cost and operations

Container Apps consumption billing is a reasonable starting model for intermittent usage. Costs depend on active replicas, CPU/memory, logs retained, registry storage, networking, and any edge or firewall services. NAT Gateway, Azure Firewall, Front Door, Application Gateway, Log Analytics ingestion, and always-on replicas can materially change cost. Confirm current regional pricing and organizational requirements before provisioning.

Monitor:

- Container restarts and failed revisions.
- CPU and memory usage, especially during record fetches.
- Application exceptions and upstream HTTP errors/timeouts.
- API response latency and rate-limit responses.
- Log Analytics ingestion and retention costs.

## Deployment readiness checklist

- [ ] Add and test a production `Dockerfile`.
- [ ] Select public authenticated or private ingress.
- [ ] Restrict custom Data Fair URLs to approved destinations before public exposure.
- [ ] Create ACR and the Container Apps environment/app.
- [ ] Configure managed identity for image pulls.
- [ ] Configure GitHub OIDC federation and least-privilege role assignments.
- [ ] Add PR test and main-branch build/deploy workflows.
- [ ] Add health checks, logging, and operational alerts.
- [ ] Test a small fetch against each intended upstream API.
- [ ] Confirm licensing, rate limits, privacy requirements, and retention needs for every dataset.
