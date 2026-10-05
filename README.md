"# Nexus OMS - Order Management System

A microservices-based Order Management System that integrates Agent Core as a service.

## Architecture

Nexus OMS is designed as a modular system where the Agent Core from Project 1 operates as an independent microservice, communicating via REST/gRPC APIs.

### Core Components

1. **API Gateway** - Entry point for all client requests
2. **Order Service** - Handles order lifecycle management
3. **Agent Core Service** (Project 1) - Autonomous agent operations
4. **Database Layer** - Persistent storage for orders and state

### Technology Stack

- **Backend**: Node.js/Python
- **Communication**: REST, gRPC
- **Database**: PostgreSQL/MongoDB
- **Containerization**: Docker, Kubernetes

## Project Structure

```
nexus-oms/
├── services/
│   ├── api-gateway/
│   ├── order-service/
│   └── agent-core/      # Integrated from Project 1
├── shared/
│   ├── protocols/
│   └── utils/
├── deployments/
│   └── docker/
└── docs/
```

## Getting Started

1. Clone the repository
2. Install dependencies per service
3. Configure environment variables
4. Run with Docker Compose

## License

MIT" 
"# nexus-oms" 
