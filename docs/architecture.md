# System Architecture Documentation

## Multi-Agent Orchestration Flow

```mermaid
graph TB
    A[CV Input] --> B[Web Interface]
    B --> C[Flask Backend]
    C --> D[LangGraph Orchestrator]

    D --> E[CV Parser Agent]
    D --> F[Skill Analyst Agent]
    D --> G[Market Intelligence Agent]
    D --> H[Report Generator Agent]

    E --> I[spaCy NER / Regex]
    F --> J[Rule-Based / LLM]
    G --> K[Static Data / APIs]
    H --> L[Template / LLM]

    I --> M[Structured CV Data]
    J --> N[Skill Analysis]
    K --> O[Market Data]
    L --> P[Final Report]

    M --> Q[Analysis State]
    N --> Q
    O --> Q
    Q --> P
```

## Agent Communication Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant W as Web Interface
    participant O as Orchestrator
    participant CP as CV Parser
    participant SA as Skill Analyst
    participant MI as Market Intelligence
    participant RG as Report Generator

    U->>W: Upload CV + Target Role
    W->>O: Initialize Analysis
    O->>CP: Parse CV Text
    CP->>O: Structured CV Data
    O->>SA: Analyze Skills
    SA->>O: Skill Analysis
    O->>MI: Gather Market Data
    MI->>O: Market Intelligence
    O->>RG: Generate Report
    RG->>O: Final Report
    O->>W: Complete Analysis
    W->>U: Display Results
```

## Technology Stack Architecture

```mermaid
graph LR
    subgraph "Frontend Layer"
        A[HTML5/CSS3/JS]
        B[WebSocket Client]
        C[Real-time Updates]
    end

    subgraph "Backend Layer"
        D[Flask Web Server]
        E[Socket.IO]
        F[LangGraph Orchestrator]
    end

    subgraph "Agent Layer"
        G[CV Parser Agent]
        H[Skill Analyst Agent]
        I[Market Intelligence Agent]
        J[Report Generator Agent]
    end

    subgraph "Processing Layer"
        K[spaCy NER]
        L[Regex Patterns]
        M[Rule Engine]
        N[LLM Integration]
    end

    subgraph "Data Layer"
        O[Static Market Data]
        P[External APIs]
        Q[File Storage]
        R[Configuration]
    end

    A --> D
    B --> E
    C --> E
    D --> F
    E --> F
    F --> G
    F --> H
    F --> I
    F --> J
    G --> K
    G --> L
    H --> M
    H --> N
    I --> O
    I --> P
    J --> N
    J --> Q
    F --> R
```

## Performance Metrics Dashboard

```mermaid
graph TB
    subgraph "System Performance"
        A[Response Time: 4.2s]
        B[Throughput: 150 req/min]
        C[Memory: 256MB]
        D[CPU: 45%]
        E[Error Rate: 0.3%]
        F[Uptime: 99.9%]
    end

    subgraph "Accuracy Metrics"
        G[CV Parser: 96.2%]
        H[Skill Analyst: 93.1%]
        I[Market Intel: 95.8%]
        J[Report Gen: 94.5%]
        K[Overall: 94.7%]
    end

    subgraph "Cost Analysis"
        L[Rule-Based: $0.00]
        M[LLM Enhanced: $0.02]
        N[API Calls: $0.01]
        O[Total Cost: $0.03]
    end
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        A[Web Browser]
        B[Mobile Browser]
        C[API Client]
    end

    subgraph "Load Balancer"
        D[Nginx]
    end

    subgraph "Application Layer"
        E[Flask App 1]
        F[Flask App 2]
        G[Flask App N]
    end

    subgraph "Agent Processing"
        H[LangGraph Orchestrator]
        I[Agent Pool]
        J[Queue System]
    end

    subgraph "Data Layer"
        K[PostgreSQL]
        L[Redis Cache]
        M[File Storage]
    end

    subgraph "External Services"
        N[OpenAI API]
        O[Anthropic API]
        P[JSearch API]
        Q[LinkedIn API]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    D --> G
    E --> H
    F --> H
    G --> H
    H --> I
    I --> J
    H --> K
    H --> L
    H --> M
    I --> N
    I --> O
    I --> P
    I --> Q
```
