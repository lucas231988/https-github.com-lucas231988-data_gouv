# Azure Deployment Architecture

```mermaid
flowchart LR
    User[User / browser]
    GH[GitHub Actions<br/>tests, build, deploy]
    ACR[Azure Container Registry]
    subgraph Azure[Azure subscription]
        subgraph ACA[Container Apps environment]
            App[Container App<br/>Streamlit :8501]
        end
        Logs[Log Analytics<br/>and Azure Monitor]
        Identity[Managed identity]
        Auth[Microsoft Entra ID<br/>authentication]
        Egress[NAT Gateway / Azure Firewall<br/>optional controlled egress]
    end
    APIs[data.gouv.fr and<br/>ADEME / Data Fair APIs]

    User -->|HTTPS ingress| Auth
    Auth -->|Authorized HTTPS| App
    GH -->|OIDC federation| Azure
    GH -->|Push immutable image| ACR
    ACR -->|Image pull permission| Identity
    Identity --> App
    App -->|HTTPS outbound| Egress
    Egress --> APIs
    App -->|Container and app logs| Logs
```

For a private-only deployment, use internal ingress and private network connectivity from user devices. For a public deployment, keep HTTPS ingress protected by authentication and apply approved-host restrictions to custom API URLs.
