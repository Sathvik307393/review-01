# Azure Multi-Cloud Traffic Flow Architecture

## Overview
This document explains the complete traffic flow from Internet → Application Gateway → VMs → Database → AWS, with all visible and hidden Azure components.

---

## 1. ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────┐
│                          INTERNET (WWW)                             │
│  Port 80 (HTTP) Traffic to *.sathvikdevops.site & *.sathvikdevops. │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ↓ DNS Resolution + Public IP
         ┌───────────────────────────────────┐
         │  Azure Public IP (pip-app-gateway)│
         │  Static IP for Application Gateway │
         │  (This is the Internet-facing IP) │
         └────────────────┬──────────────────┘
                          │
                          ↓ Port 80 Traffic
    ┌─────────────────────────────────────────────────────────────┐
    │         AZURE VIRTUAL NETWORK (10.10.0.0/16)              │
    │                                                             │
    │  ┌──────────────────────────────────────────────────────┐  │
    │  │    AppGatewaySubnet (10.10.3.0/24)                  │  │
    │  │  ┌────────────────────────────────────────────────┐ │  │
    │  │  │  Application Gateway (ALB/L7 Load Balancer)  │ │  │
    │  │  │  - Terminates port 80 connections            │ │  │
    │  │  │  - Routes based on hostname (wildcard DNS)   │ │  │
    │  │  │  - Sends traffic to backend pools            │ │  │
    │  │  │  - Rules: *.sathvikdevops.site → autohub-pool │ │  │
    │  │  │  - Rules: *.sathvikdevops.online → kitchenos  │ │  │
    │  │  └────────────────────────────────────────────────┘ │  │
    │  └──────────────────────┬───────────────────────────────┘  │
    │                         │                                   │
    │                         │ Private traffic (10.10.2.x)       │
    │              ┌──────────┴──────────┐                        │
    │              ↓                     ↓                        │
    │  ┌──────────────────────┐ ┌──────────────────────┐          │
    │  │ BackendSubnet        │ │ BackendSubnet        │          │
    │  │ (10.10.2.0/24)       │ │ (10.10.2.0/24)       │          │
    │  │                      │ │                      │          │
    │  │ ┌──────────────────┐ │ │ ┌──────────────────┐ │          │
    │  │ │ VM: autohub      │ │ │ │ VM: kitchenos    │ │          │
    │  │ │ (nic-autohub)    │ │ │ │ (nic-kitchenos)  │ │          │
    │  │ │ Private IP:      │ │ │ │ Private IP:      │ │          │
    │  │ │ 10.10.2.x        │ │ │ │ 10.10.2.y        │ │          │
    │  │ │ Port 80 Listening│ │ │ │ Port 80 Listening│ │          │
    │  │ │                  │ │ │ │                  │ │          │
    │  │ │ NSG: allow HTTP  │ │ │ │ NSG: allow HTTP  │ │          │
    │  │ │ from AppGW subnet │ │ │ │ from AppGW subnet │ │          │
    │  │ └──────────────────┘ │ │ └──────────────────┘ │          │
    │  └──────────┬───────────┘ └────────┬─────────────┘          │
    │             │                      │                        │
    │             └──────────┬───────────┘                        │
    │                        ↓                                    │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │  GatewaySubnet (10.10.0.0/27)                       │   │
    │  │  ┌───────────────────────────────────────────────┐  │   │
    │  │  │  VPN Gateway (vgw-azure-to-aws)              │  │   │
    │  │  │  - Type: RouteBased VPN                       │  │   │
    │  │  │  - SKU: VpnGw1AZ (supports Zone redundancy)   │  │   │
    │  │  │  - Encrypted tunnel to AWS VPN endpoints      │  │   │
    │  │  │  - Local Network Gateway: AWS tunnel IPs      │  │   │
    │  │  │  - Connection type: IPsec/IKEv2               │  │   │
    │  │  └───────────────────────────────────────────────┘  │   │
    │  └────────────────┬──────────────────────────────────┘   │
    │                   │                                       │
    │                   ↓ Encrypted VPN Tunnel (IPsec)          │
    │           Port 500/4500 (IKE/ESP)                        │
    └───────────────────┼──────────────────────────────────────┘
                        │
         ┌──────────────┴───────────────┐
         ↓                              ↓
┌─────────────────────────┐  ┌─────────────────────────┐
│  AWS VPN Tunnel 1       │  │  AWS VPN Tunnel 2       │
│  IP: 1.1.1.1            │  │  IP: 2.2.2.2            │
│  PSK: shared_key_1      │  │  PSK: shared_key_2      │
└──────────┬──────────────┘  └──────────┬──────────────┘
           │                            │
           └────────────┬───────────────┘
                        ↓
         ┌──────────────────────────────┐
         │    AWS VPC (192.16.0.0/16)   │
         │                              │
         │  ┌────────────────────────┐  │
         │  │  MongoDB/Database      │  │
         │  │  (or other backend DB) │  │
         │  │  Port 27017            │  │
         │  └────────────────────────┘  │
         └──────────────────────────────┘
```

---

## 2. COMPONENT BREAKDOWN

### **VISIBLE/EXPLICIT COMPONENTS (Created by Terraform)**

#### Layer 1: Perimeter
- **Public IP (pip-app-gateway)**: Static public IPv4 address owned by Azure
  - Route from ISP → Azure data center
  - Associated with Application Gateway
  - Publicly resolvable via DNS

#### Layer 2: Gateway Tier
- **Application Gateway (ALB)**
  - Layer 7 load balancer (understands HTTP/HTTPS)
  - Terminates client connections
  - **Hostname-based routing**: 
    - `*.sathvikdevops.site` → `autohub-pool` (autohub VM)
    - `*.sathvikdevops.online` → `kitchenos-pool` (kitchenos VM)
  - Health probes check backend health
  - WAF-capable (Web Application Firewall)
  - Session affinity: Disabled (stateless)

#### Layer 3: Compute Tier
- **Virtual Machine 1 (vm-autohub-backend)**
  - Size: Standard_B2als_v2 (2vCPUs, 4GB RAM)
  - NIC: nic-autohub (Private IP: 10.10.2.x)
  - OS: Ubuntu 22.04 LTS
  - Port 80 Listening (HTTP service)
  - Application: AutoHub Python service

- **Virtual Machine 2 (vm-kitchenos-backend)**
  - Size: Standard_B2als_v2 (2vCPUs, 4GB RAM)
  - NIC: nic-kitchenos (Private IP: 10.10.2.y)
  - OS: Ubuntu 22.04 LTS
  - Port 80 Listening (HTTP service)
  - Application: KitchensOS Node.js service

#### Layer 4: Connectivity (VPN)
- **VPN Gateway (vgw-azure-to-aws)**
  - SKU: VpnGw1AZ (1 Gbps, Zone-redundant capable)
  - Type: RouteBased (dynamic routing via BGP/UDR)
  - Encryption: IPsec with IKEv2
  - High availability via zone distribution

- **Local Network Gateway 1 & 2**
  - Represent AWS VPN endpoints (1.1.1.1, 2.2.2.2)
  - Store AWS tunnel public IPs
  - Reference AWS network CIDR (192.16.0.0/16)

- **VPN Connections (Tunnel 1 & 2)**
  - IPsec encrypted tunnels
  - PSK (pre-shared keys) for authentication
  - Redundancy: 2 tunnels for failover

---

### **HIDDEN/IMPLICIT COMPONENTS (Automatically Created by Azure)**

These are automatically provisioned when you create the above resources:

#### 1. **Network Interface Cards (NICs)**
- Azure automatically attaches NICs to VMs
- Each NIC has a private IP from subnet CIDR
- VLAN/Virtual ethernet bridge binding

#### 2. **Route Tables & System Routes**
- Default routes for each subnet:
  - VNet local routes (10.10.0.0/16 → Local)
  - 0.0.0.0/0 → Internet (via NAT)
- User-defined routes (UDRs):
  - 192.16.0.0/16 (AWS CIDR) → VPN Gateway

#### 3. **Network Address Translation (NAT)**
- **Outbound NAT**: VMs send traffic destined for internet
  - Destination: Internet (not in VNet)
  - Action: Azure NAT translates VM private IP → Public IP
  - VM doesn't have public IP; Azure handles NAT

#### 4. **Azure's Internal Switch/Hypervisor Networking**
- Virtual switch (Hyper-V vSwitch) connects VMs
- MAC address translation
- Frame forwarding at hypervisor level

#### 5. **Network Security Fabric**
- **Stateful Firewall** (implicit in NSG):
  - Tracks established connections
  - Return traffic automatically allowed
  - Connection state table maintained

#### 6. **DNS Name Resolution**
- **Private DNS** for internal names (azure internal)
- **Public DNS** for Internet names (handled by registrar)

#### 7. **Subnet Local Services**
- DHCP server (assigns private IPs)
- ARP resolver (maps IPs to MAC addresses)
- IGMP multicast group manager

#### 8. **Availability Set / Implicit Load Balancing**
- Azure Fabric handles:
  - VM placement across fault domains
  - Health monitoring
  - Automatic failover

#### 9. **Storage Account (for VM OS Disks)**
- Automatically created managed disks
- Block blob storage in backend
- Replication (LRS/GRS)

#### 10. **Azure Monitor / Diagnostic Extensions**
- Activity logs
- Network watchers (implicit packet capture)
- Metrics aggregation

---

## 3. DETAILED TRAFFIC FLOW (Step-by-Step)

### **Inbound Flow: Internet → VMs**

```
STEP 1: DNS Resolution
┌──────────────────────────────────────────┐
│ User: curl https://api.sathvikdevops.site│
│ Browser resolves DNS                      │
│ Returns: 40.X.X.X (Public IP)            │
└──────────────────┬───────────────────────┘
                   ↓
STEP 2: TCP Handshake
┌────────────────────────────────────────────────┐
│ Client IP: 203.0.113.50:54321 (ISP assigned)  │
│ Server IP: 40.X.X.X (Azure Public IP):80      │
│ TCP SYN → Application Gateway                  │
└────────────────┬───────────────────────────────┘
                 ↓
STEP 3: App Gateway Accepts Connection
┌────────────────────────────────────────────────────────────┐
│ App Gateway Frontend:                                      │
│   - Terminates TCP 3-way handshake                        │
│   - Listens on 40.X.X.X:80                               │
│   - Creates new TCP session with backend                  │
│   - Connection state tracked in session table             │
└────────────────┬─────────────────────────────────────────┘
                 ↓
STEP 4: Hostname Parsing
┌────────────────────────────────────────────────────────────┐
│ HTTP Request:                                              │
│   GET /api/bookings HTTP/1.1                              │
│   Host: api.sathvikdevops.site                            │
│                                                            │
│ App Gateway extracts hostname: api.sathvikdevops.site     │
│ Matches rule: *.sathvikdevops.site → autohub-pool        │
└────────────────┬─────────────────────────────────────────┘
                 ↓
STEP 5: Backend Selection
┌────────────────────────────────────────────────────────────┐
│ Backend Pool: autohub-pool                                 │
│ Members: [10.10.2.10 (vm-autohub-backend)]               │
│                                                            │
│ Health probe status: Healthy ✓                            │
│ (Periodic HTTP GET on port 80)                            │
│                                                            │
│ App Gateway selects VM (only 1 member in pool)           │
└────────────────┬─────────────────────────────────────────┘
                 ↓
STEP 6: Private Network Routing
┌─────────────────────────────────────────────────────────┐
│ Packet forwarding within Azure VNet:                    │
│                                                         │
│ Source: 40.X.X.X:EPHEMERAL (App Gateway private IP)   │
│ Dest: 10.10.2.10:80 (autohub VM)                      │
│                                                         │
│ Route Table lookup:                                     │
│   10.10.2.0/24 in BackendSubnet → Local delivery      │
│                                                         │
│ ARP Resolution:                                         │
│   ARP broadcast on BackendSubnet                       │
│   10.10.2.10's MAC address discovered                  │
│   Frame forwarded to NIC's MAC                         │
└─────────────────┬──────────────────────────────────────┘
                  ↓
STEP 7: NSG Ingress Rules Evaluation
┌──────────────────────────────────────────────────────────────┐
│ Network Security Group (nsg-backend) applied to NIC:        │
│                                                              │
│ Inbound Rules (evaluated top-to-bottom):                    │
│   Priority 100: Allow TCP port 80                           │
│     From: 10.10.3.0/24 (AppGatewaySubnet) ✓ MATCH!        │
│     Action: ALLOW                                           │
│     → Traffic passes NSG                                    │
│                                                              │
│ Note: Priority 900 (deny-all-inbound) comes AFTER, so       │
│       doesn't apply if earlier rule matches                 │
└──────────────────┬───────────────────────────────────────┘
                   ↓
STEP 8: VM Receives Packet
┌──────────────────────────────────────────────────────────┐
│ VM's network stack receives packet:                       │
│   - NIC passes to kernel network stack                   │
│   - TCP stack reassembles segments                       │
│   - Port 80 socket accepts connection                    │
│   - HTTP server (nginx/Python Flask) receives request   │
│                                                          │
│ HTTP Request processed:                                  │
│   GET /api/bookings → Connect to local MongoDB          │
│   Port 27017 → Outbound traffic to AWS VPN tunnel       │
└──────────────────┬───────────────────────────────────────┘
```

---

### **Outbound Flow: VMs → AWS Database**

```
STEP 9: VM Initiates Database Query
┌────────────────────────────────────────────────┐
│ Python/Node.js Application on VM:              │
│   client = MongoClient("192.16.x.x:27017")    │
│   (AWS MongoDB private IP in VPC)              │
│                                                │
│ TCP SYN packet created:                        │
│   Source: 10.10.2.10:EPHEMERAL (VM)           │
│   Dest: 192.16.x.x:27017 (AWS MongoDB)        │
└────────────────┬───────────────────────────────┘
                 ↓
STEP 10: Local Route Table Lookup
┌─────────────────────────────────────────────────────┐
│ VM's route table (inherited from subnet):            │
│                                                      │
│ Destination: 192.16.x.x (AWS CIDR)                 │
│ Matching Route: 192.16.0.0/16 → vgw-azure-to-aws  │
│                                                      │
│ Decision: Send packet to VPN Gateway                │
│ Next Hop: VPN Gateway (10.10.0.X)                  │
└────────────────┬────────────────────────────────────┘
                 ↓
STEP 11: NSG Outbound Rules Evaluation
┌───────────────────────────────────────────────────────────┐
│ NSG Outbound Rules:                                       │
│                                                           │
│ Priority 100: Allow TCP 27017 to 192.16.0.0/16          │
│   (allow-mongo-out-to-aws rule)                          │
│   Source: 10.10.2.10 (VM)                               │
│   Dest: 192.16.0.0/16 (AWS VPC CIDR)                    │
│   Port: 27017 (MongoDB)                                  │
│   → MATCH! Action: ALLOW                                │
│                                                           │
│ Traffic passes NSG egress                                │
└───────────────┬──────────────────────────────────────────┘
                │
STEP 12: VPN Tunnel Routing
┌─────────────────────────────────────────────────────────┐
│ VPN Gateway receives packet (192.16.x.x destination):   │
│                                                         │
│ IPsec Processing:                                       │
│   - Packet encapsulation:                               │
│     Original: IPv4(192.16.x.x) + MongoDB data          │
│     Encapsulated: IPv4(1.1.1.1) +                       │
│                   IPsec Header + Encrypted Original +   │
│                   ICV (Integrity Check Value)           │
│                                                         │
│   - Encryption: AES-256-GCM (or negotiated)            │
│   - HMAC: SHA256 (or negotiated)                        │
│   - Tunnel: Azure Public IP (X.X.X.X) →                │
│             AWS Tunnel 1 (1.1.1.1)                      │
└────────────────┬──────────────────────────────────────┘
                 ↓
STEP 13: Internet Transit
┌──────────────────────────────────────────────────────┐
│ Encrypted packet travels via Internet:               │
│   Source IP: X.X.X.X (Azure VPN Gateway Public IP)  │
│   Dest IP: 1.1.1.1 (AWS VPN Endpoint)               │
│   Protocol: UDP 500 (IKE) or 4500 (ESP)             │
│                                                      │
│ ISP routing, BGP advertisements, etc.               │
│ (Standard Internet packet delivery)                 │
└──────────────┬───────────────────────────────────────┘
               ↓
STEP 14: AWS VPN Endpoint Decryption
┌─────────────────────────────────────────────────────┐
│ AWS VPN receives encrypted packet:                  │
│                                                     │
│ IPsec Decryption:                                   │
│   - Extract encrypted payload                       │
│   - Verify ICV (integrity)                          │
│   - Decrypt using shared PSK                        │
│   - Extract original packet: IPv4(192.16.x.x)      │
│                                                     │
│ AWS routing: 192.16.x.x is in local VPC            │
│   → Forward to MongoDB instance                     │
└──────────────┬──────────────────────────────────────┘
               ↓
STEP 15: AWS Database Processing
┌────────────────────────────────────────────┐
│ MongoDB Replica Set receives connection:   │
│   - Port 27017 listening                   │
│   - Authenticates connection               │
│   - Processes query                        │
│   - Returns result set                     │
└────────────────┬───────────────────────────┘
```

---

### **Return Flow: AWS Database → VM → Internet**

```
STEP 16: AWS Returns Response
┌───────────────────────────────────────────────┐
│ MongoDB Response:                             │
│   - Query results serialized (BSON)           │
│   - TCP payload sent back                     │
│   - Source: 192.16.x.x:27017 (AWS MongoDB)  │
│   - Dest: 10.10.2.10:EPHEMERAL (Azure VM)   │
└────────────────┬──────────────────────────────┘
                 ↓
STEP 17: AWS VPN Encryption & Tunnel
┌──────────────────────────────────────────────────┐
│ AWS VPN encrypts return traffic:                 │
│   - Same IPsec encryption (reverse direction)    │
│   - IPsec header + encryption                    │
│   - Source: 1.1.1.1 (AWS tunnel)                │
│   - Dest: X.X.X.X (Azure VPN Gateway)          │
│   - Sent over UDP 4500 (ESP protocol)           │
└──────────────┬───────────────────────────────────┘
               ↓
STEP 18: Azure VPN Decryption
┌─────────────────────────────────────────────┐
│ Azure VPN Gateway decrypts:                 │
│   - Receives encrypted packet               │
│   - Validates PSK                           │
│   - Decrypts payload                        │
│   - Extract original: 192.16.x.x → 10.10.2.10 │
└──────────────┬────────────────────────────┘
               ↓
STEP 19: VM Receives Data
┌────────────────────────────────────────────────┐
│ VM's TCP socket receives MongoDB response:     │
│   - Network stack reassembles segments        │
│   - Application layer receives result         │
│   - HTTP handler processes (JSON conversion)  │
└────────────────┬───────────────────────────────┘
                 ↓
STEP 20: VM Sends HTTP Response to App Gateway
┌──────────────────────────────────────────────────┐
│ VM Application sends HTTP response:              │
│   HTTP/1.1 200 OK                               │
│   Content-Type: application/json                 │
│   [JSON booking data]                            │
│                                                  │
│ TCP packet:                                      │
│   Source: 10.10.2.10:80                         │
│   Dest: 10.10.3.X:EPHEMERAL (App Gateway)      │
│                                                  │
│ NSG Outbound: Allowed by default                │
│ (Destination is VNet local: 10.10.3.0/24)      │
└──────────────┬───────────────────────────────────┘
               ↓
STEP 21: App Gateway Receives Response
┌────────────────────────────────────────────────┐
│ Application Gateway:                            │
│   - Receives HTTP 200 response                  │
│   - Matches to original client connection       │
│   - Modifies headers if needed (optional)      │
│   - Buffers response                           │
│   - Session state updated                      │
└────────────────┬───────────────────────────────┘
                 ↓
STEP 22: Send to Internet Client
┌────────────────────────────────────────────────┐
│ App Gateway sends HTTP response:                │
│   Source: 40.X.X.X:80 (Azure Public IP)       │
│   Dest: 203.0.113.50:54321 (Client ISP IP)    │
│                                                │
│ Azure's NAT reverses the translation:          │
│   Original VM private IP → Public IP           │
│                                                │
│ Response travels via Internet to client        │
│ Client browser renders JSON/HTML response      │
└────────────────────────────────────────────────┘
```

---

## 4. KEY TECHNICAL CONCEPTS

### **Network Address Translation (NAT)**
- **Implicit in App Gateway**: Rewrites source IP
  - External client (203.0.113.50) → App Gateway → VM (10.10.2.10)
  - VM doesn't see external client IP directly
- **Outbound NAT for internet**: VMs don't have public IPs
  - VM initiates connection to 8.8.8.8 (Google DNS)
  - Azure translates private IP to temporary public IP
  - Response returned to public IP, re-translated to private IP

### **Stateful Firewall (NSG)**
- **Connection Tracking**:
  - Inbound HTTP (port 80) → tracked as "Established"
  - Return traffic on same connection → automatically allowed
  - No need to explicitly allow "Outbound" for response
- **5-Tuple Tracking**: (Protocol, Source IP, Dest IP, Source Port, Dest Port)

### **IPsec VPN Encryption**
- **IKEv2 Negotiation** (Phase 1):
  - Peers authenticate using PSK (pre-shared key)
  - Negotiate encryption algorithm (AES-256)
  - Negotiate HMAC (SHA256)
  - Establish secure channel for Phase 2
  
- **IPsec SA Establishment** (Phase 2):
  - Create Security Associations (SAs) for data traffic
  - Inbound SA: for Azure → AWS direction
  - Outbound SA: for AWS → Azure direction
  
- **Data Encryption**:
  - Each packet encrypted with SA parameters
  - ICV (Integrity Check Value) prevents tampering
  - ESP (Encapsulating Security Payload) header added
  - Sequence numbers prevent replay attacks

### **Layer 7 Load Balancing (App Gateway)**
- **Host-based Routing**: Inspects HTTP Host header
- **Path-based Routing**: Could route `/api/*` vs `/web/*` to different backends
- **Cookie-based Affinity**: Sticky sessions (disabled in our config)
- **Health Probes**: Periodic HTTP GET to verify backend health

### **Azure's Virtual Switch**
- All VMs in same subnet → connected via virtual switch
- MAC address learning
- VLAN tagging (implicit)
- Multicast/broadcast domain

---

## 5. TRAFFIC FLOW SUMMARY TABLE

| Direction | Source IP | Dest IP | Port | Protocol | Component | NSG Rule |
|-----------|-----------|---------|------|----------|-----------|----------|
| 1. Inbound | 203.0.113.50 | 40.X.X.X | 80 | TCP | Public Internet | N/A |
| 2. Inbound | 40.X.X.X | 10.10.2.10 | 80 | TCP | App Gateway → VM | allow_http_from_gateway |
| 3. Outbound | 10.10.2.10 | 192.16.x.x | 27017 | TCP | VM → VPN | allow_mongo_out_to_aws |
| 4. Outbound | X.X.X.X | 1.1.1.1 | 500/4500 | UDP | VPN → Internet | N/A (implicit route) |
| 5. Return | 1.1.1.1 | X.X.X.X | 500/4500 | UDP | Internet → VPN | N/A (implicit route) |
| 6. Return | 192.16.x.x | 10.10.2.10 | 27017 | TCP | AWS → VM (encrypted) | Stateful (return traffic) |
| 7. Return | 10.10.2.10 | 40.X.X.X | 80 | TCP | VM → App Gateway | Default allow outbound |
| 8. Return | 40.X.X.X | 203.0.113.50 | 80 | TCP | App Gateway → Client | N/A (Internet) |

---

## 6. SECURITY LAYERS

1. **Layer 1 - Perimeter**: App Gateway only exposes HTTP (port 80)
   - Other ports not accessible from internet
   - WAF capabilities available (not deployed)

2. **Layer 2 - NSG Ingress**: Only App Gateway subnet can send HTTP to backend
   - 10.10.3.0/24 → port 80 allowed
   - All other inbound denied (deny-all-inbound priority 900)

3. **Layer 3 - NSG Egress**: Only MongoDB (port 27017) allowed to AWS
   - 192.16.0.0/16 destination allowed
   - Other destinations blocked

4. **Layer 4 - VPN Encryption**: MongoDB traffic encrypted end-to-end
   - IPsec tunnel between Azure and AWS
   - Man-in-the-middle attacks prevented

5. **Layer 5 - Application**: Each service (autohub, kitchenos) runs isolated processes
   - Database credentials managed separately
   - SQL injection prevention at app level

---

## 7. FAILOVER & REDUNDANCY

### **App Gateway Redundancy**
- **Capacity = 1**: Single instance (could scale to 2+)
- Multi-zone available but not deployed
- Health probes every 30s detect unhealthy backends

### **VPN Gateway Redundancy**
- **SKU: VpnGw1AZ**: Zone-redundant capable
- **2 Tunnels**: Tunnel 1 (1.1.1.1) + Tunnel 2 (2.2.2.2)
- AWS side: Also has redundant endpoints
- If tunnel 1 fails → traffic reroutes to tunnel 2

### **Database (AWS)**
- Assumed MongoDB Replica Set (not in Azure terraform)
- If primary node fails → secondary takes over
- Azure can continue querying replica set

---

## 8. PERFORMANCE CHARACTERISTICS

| Component | Latency | Bandwidth | Notes |
|-----------|---------|-----------|-------|
| App Gateway (local) | <1ms | Unlimited | Layer 7 inspection may add 5-10ms |
| VM ↔ AWS (VPN) | 50-150ms | 1-10 Gbps | Depends on internet path, VPN SKU limits |
| Azure-AWS VPN (IPsec) | Minimal | Variable | Encryption/decryption CPU overhead ~5% |
| MongoDB Query | Variable | Variable | Depends on data size, AWS database performance |

---

## 9. IMPLICIT COMPONENTS NOT EXPLICITLY DEFINED

1. **System Network Interfaces**: Every subnet has reserved IP addresses
   - .0: Network address
   - .1: Azure gateway (internal router)
   - .2-X: Available IPs
   - .255: Broadcast address

2. **Azure Monitor Agents**: (optional, not deployed here)
   - Performance metrics
   - Network traffic logs
   - Diagnostics

3. **Backup/Snapshot Service**: (if enabled)
   - Managed disk snapshots
   - Point-in-time recovery

4. **Azure Update Management**: Patches OS/packages

---

## 10. DEPLOYMENT CHECKLIST

```
✓ VNet created with address space 10.10.0.0/16
✓ 4 Subnets created:
  - GatewaySubnet (10.10.0.0/27) for VPN
  - AzureBastionSubnet (10.10.1.0/26) for management
  - BackendSubnet (10.10.2.0/24) for VMs
  - AppGatewaySubnet (10.10.3.0/24) for load balancer
  
✓ VMs deployed:
  - vm-autohub-backend (AutoHub service)
  - vm-kitchenos-backend (KitchensOS service)
  
✓ Application Gateway configured:
  - Frontend: 40.X.X.X:80
  - Backends: 2 pools (autohub, kitchenos)
  - Rules: hostname-based routing
  
✓ VPN Gateway configured:
  - 2 tunnels to AWS (redundancy)
  - IPsec encryption
  
✓ NSG Rules:
  - Ingress: HTTP from App Gateway subnet
  - Egress: MongoDB to AWS CIDR
  - Default Deny All (implicit)
  
✓ Route Tables (implicit):
  - Local routes: 10.10.0.0/16 → Local
  - AWS routes: 192.16.0.0/16 → VPN Gateway
  - Internet: 0.0.0.0/0 → NAT
```

---

## CONCLUSION

Traffic flows through multiple layers of security, load balancing, and encryption:
1. **Internet → App Gateway**: Public entry point
2. **App Gateway → VMs**: Private routing with NSG filtering
3. **VMs → AWS**: IPsec-encrypted VPN tunnel
4. **Database ↔ VM**: Secure, encrypted communication
5. **VM → Client**: Return path via App Gateway

This architecture provides **security in depth**, **high availability** through redundancy, and **encryption** for sensitive data in transit.
