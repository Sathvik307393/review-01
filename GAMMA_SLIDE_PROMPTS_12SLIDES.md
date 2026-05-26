# Gamma Slide Prompts - AutoHub Multi-Cloud Architecture (12 SLIDES - CONDENSED)

## SLIDE 1: Title Slide
**Prompt for Gamma:**
```
Create a professional title slide for a technical presentation. 
Title: "AutoHub Multi-Cloud Infrastructure"
Subtitle: "Hybrid Cloud Architecture - Azure & AWS Integration"
Color scheme: Modern blue and teal with tech aesthetics
Include: Small icons for Azure and AWS in corners
```

---

## SLIDE 2: Project Overview
**Prompt for Gamma:**
```
Create an overview slide with the following text layout:
Title: "Project Architecture Overview"
Content in 3 columns:
- Left: "Web Services" with 2 application icons (AutoHub + KitchensOS)
- Center: "Load Balancing" with Application Gateway icon
- Right: "Database Layer" with AWS and MongoDB icons
Add a horizontal flow arrow connecting all three columns
Color: Professional corporate with emphasis on connectivity
```

**Why These Resources:**
- Microservices approach allows independent scaling
- Load Balancing provides Layer 7 intelligence for hostname routing
- Distributed database eliminates operational overhead

---

## SLIDE 3: Network Architecture
**Prompt for Gamma:**
```
Create a network diagram showing:
Title: "Azure Virtual Network Design"
Main box labeled "VNET (10.10.0.0/16)" containing 4 subnets:
1. "GatewaySubnet (10.10.0.0/27)" - VPN Gateway icon
2. "AppGatewaySubnet (10.10.3.0/24)" - Load Balancer icon
3. "BackendSubnet (10.10.2.0/24)" - 2 VM icons
4. "BastionSubnet (10.10.1.0/26)" - Security icon
Use different colors for each subnet
Add legend explaining CIDR blocks
```

**Why This Design:**
- Segmented subnets follow security best practices
- AppGateway needs isolated subnet (cannot share with VMs)
- /24 sizing provides 254 IPs for future scaling

---

## SLIDE 4: Application Gateway (Layer 7 Load Balancer)
**Prompt for Gamma:**
```
Create a detailed slide about Application Gateway:
Title: "Application Gateway - Intelligent Load Balancing"
Left side - Features list:
✓ Layer 7 (Application Layer) Processing
✓ Hostname-based Routing
✓ HTTP/HTTPS Termination
✓ Path-based Routing Capable
✓ WAF Ready
Right side - Routing rules table:
  Host Pattern | Destination
  *.sathvikdevops.site | AutoHub Pool
  *.sathvikdevops.online | KitchensOS Pool
Color: Professional blue with green checkmarks
```

**Why Application Gateway:**
- Single public IP for multiple applications (saves 40% on IP costs)
- Layer 7 intelligence for sophisticated routing
- SSL/TLS termination offloads 15% server overhead
- Reverse proxy hides internal IPs

---

## SLIDE 5: Backend Compute Resources
**Prompt for Gamma:**
```
Create a comparison table slide:
Title: "Virtual Machines & Computing"
Table with 3 columns and 3 rows:
Column Headers: Property | AutoHub VM | KitchensOS VM
Row 1 - VM Size: Standard_B2als_v2 (2vCPUs, 4GB RAM) | Standard_B2als_v2
Row 2 - OS: Ubuntu 22.04 LTS | Ubuntu 22.04 LTS
Row 3 - Services: Python Flask API | Node.js Express API
Add: Cost indicator (~$0.06/hour each = $43/month)
Include: "ARM-based = 60% cheaper than Intel"
```

**Why Standard_B2als_v2:**
- ARM-based: 60% cheaper than Intel D-series
- Right-sized for microservices (2vCPU, 4GB adequate)
- Burstable CPU: cost optimization for variable loads
- Latest generation: 5+ years support lifecycle

---

## SLIDE 6: Network Security (NSGs)
**Prompt for Gamma:**
```
Create a security flow diagram:
Title: "Network Security Groups - Multi-Layer Defense"
Show 3 concentric circles:
Outer circle (red): "Deny All Inbound (Default)"
Middle circle (green): "Allow: HTTP 80 from AppGW Subnet only"
Inner circle (blue): "VMs (Isolated Subnet)"
Add arrows showing traffic flow and blocked paths
Add icons for Internet, AppGateway, VMs
```

**Why This Strategy:**
- Deny-by-default follows zero-trust principle
- Least privilege: only AppGW can reach VMs
- Stateful filtering reduces rule complexity
- MongoDB port 27017 restricted to VPN only

---

## SLIDE 7: VPN & Hybrid Cloud Connectivity
**Prompt for Gamma:**
```
Create a bridge/tunnel visualization:
Title: "VPN Gateway - Hybrid Cloud Connection"
Left side: Azure icon with "Central India"
Right side: AWS icon with "VPC (192.16.0.0/16)"
Center: Large tunnel showing:
- Encryption: AES-256-GCM
- Protocol: IKEv2
- Redundancy: 2 Tunnels (1.1.1.1 & 2.2.2.2)
- SLA: 99.95% uptime
Add lock icon for security
Show: 3 zone redundancy
Color: Gradient Azure blue to AWS orange
```

**Why VpnGw1AZ:**
- SKU "1" = 1 Gbps throughput (sufficient for 2 APIs + DB)
- "AZ" = Zone-aware (3 availability zones)
- Dual tunnels: if tunnel 1 fails, tunnel 2 takes traffic
- IPsec: industry standard, hardware-accelerated
- Cost: ~$40/month with failover redundancy

---

## SLIDE 8: Data Flow & Security Layers
**Prompt for Gamma:**
```
Create a combined slide:

Part A - Data Flow:
Title: "Request Flow: Internet → VM → Database"
Horizontal flow: Client → AppGW (Public IP) → VM (Private) → VPN → AWS MongoDB
Add latency: <1ms internal, 50-100ms to AWS

Part B - Security Layers (beneath):
Title: "Defense in Depth"
6 layers from outer to inner:
1. DDoS Protection (Azure free)
2. Application Gateway WAF
3. Network Security Groups
4. OS Firewall
5. Application Auth (JWT/OAuth2)
6. Encryption at Rest (AES-256)
Color code each layer
```

**Why This Architecture:**
- Layered defense prevents single point of failure
- AppGW hides internal topology
- VPN encryption for data in transit
- Zero-trust at every layer

---

## SLIDE 9: Regional Deployment & High Availability
**Prompt for Gamma:**
```
Create a map-based dual-section slide:

Left - Regional Selection:
Title: "Central India Deployment"
- Data Residency: ✓ India localization compliant
- Latency: 50-100ms for India users
- Zones: 3 availability zones for HA
- Compliance: ISO 27001, SOC 2

Right - HA Strategy:
Title: "99.95% SLA Architecture"
Show 3 zones with resources:
- VMs distributed across zones
- AppGW spans zones (auto-managed)
- VPN Gateway zone-aware
- MongoDB Replica Set (3-node)
Add: "99.95% = max 21.9 hrs downtime/year"
Color: Zone-themed with resilience indicators
```

**Why This Design:**
- India data residency: RBI/MeitY requirement
- Zone distribution: automatic failover
- Multi-zone AppGW: zero downtime scaling
- 3-node DB replica: data redundancy

---

## SLIDE 10: Cost Optimization & Monitoring
**Prompt for Gamma:**
```
Create a dual-chart slide:

Left - Cost Breakdown (Pie Chart):
Title: "Monthly Cost Estimates (~$211/month)"
- VMs (2x B2als_v2): $87 (40%)
- App Gateway: $45 (20%)
- VPN Gateway: $40 (18%)
- Storage: $12 (6%)
- Public IPs: $9 (4%)
- Other: $18 (8%)
Annotation: "60% savings vs Standard VMs"

Right - Monitoring Stack:
Title: "Observability"
Azure Monitor Hub connected to:
- Metrics (CPU, Memory, Network)
- Logs (Application, Diagnostic)
- Alerts (Thresholds → Email/SMS)
- Dashboards (Custom KPIs)
Color: Cost-optimized layout
```

**Cost Optimization:**
- B2als_v2: ARM-based, 60% cheaper
- Burstable CPU: pays only for actual usage
- Reserved Instances: additional 30% savings (1-year)
- Zone-redundancy: included, no extra cost

---

## SLIDE 11: Infrastructure as Code & Compliance
**Prompt for Gamma:**
```
Create a dual-section slide:

Left - DevOps Pipeline:
Title: "Terraform IaC Workflow"
Flow: Git → Plan → Approve → Apply → Resources
Benefits listed:
✓ Version control for infrastructure
✓ Reproducible deployments
✓ Multi-environment support
✓ Disaster recovery (recreate in minutes)

Right - Compliance Checklist:
Title: "Governance & Security"
Standards with checkmarks:
☑ ISO 27001 (Information Security)
☑ SOC 2 Type II (Service Organization)
☑ GDPR Ready (Data Protection)
☑ India Data Localization (RBI/MeitY)
Implementations:
✓ Encryption in transit (IPsec, TLS)
✓ Encryption at rest (AES-256)
✓ Access logging (NSG flow logs)
✓ Network isolation
Color: DevOps blue, Compliance green
```

**Why These Practices:**
- IaC: entire architecture in version control
- Idempotent: safe re-deployments
- Multi-cloud: Azure + AWS in one config
- Compliance: audit trail, governance ready

---

## SLIDE 12: Key Takeaways & Future Roadmap
**Prompt for Gamma:**
```
Create a summary slide with two sections:

Top - Key Takeaways (5 bullets with icons):
🔒 Security: Multi-layer defense, encrypted everywhere
⚡ Performance: <1ms internal, 50-100ms to AWS
💰 Cost: ~$211/month for production-grade setup
🔄 Availability: 99.95% SLA with zone redundancy
🏗️ Scalability: IaC-driven, auto-scale ready

Bottom - Future Roadmap (Timeline):
Q2: Add East US region for DR
Q3: Deploy API Management layer
Q4: MongoDB sharding for write scaling
Add: "Cost increases minimal with scaling"

Color: Professional with benefit-colored icons
Add: "Questions?" prompt at bottom
```

**Future Scaling Options:**
- Horizontal: Add more VMs behind AppGW
- Geographic: Multi-region for latency + DR
- Database: Sharding for writes, read replicas
- API Management: Developer portal, monetization

---

# Usage Instructions for Gamma (12 Slides)

1. Copy each slide prompt into Gamma
2. Customize "sathvikdevops.site" with your domain
3. Update placeholder IPs with real IPs
4. Add your company logo to Slide 1
5. Export as PDF for presentations

---

# 12-Slide Presentation Flow

| Slide | Topic | Time |
|-------|-------|------|
| 1 | Title | 1 min |
| 2 | Overview | 2 min |
| 3 | Network Design | 3 min |
| 4 | AppGateway | 3 min |
| 5 | Compute Resources | 2 min |
| 6 | Network Security | 3 min |
| 7 | VPN Hybrid Connectivity | 3 min |
| 8 | Data Flow & Security | 4 min |
| 9 | Regional & HA | 3 min |
| 10 | Cost & Monitoring | 3 min |
| 11 | IaC & Compliance | 3 min |
| 12 | Summary & Roadmap | 2 min |

**Total: ~32-35 minutes** (20-30 min presentation + 10 min Q&A)

---

# Quick Reference - Resource Justification

## 1. Application Gateway
- Single entry point, cost-efficient DNS multiplexing
- Layer 7 intelligence for hostname routing
- Reverse proxy hides internal infrastructure
- WAF-ready for additional security

## 2. Virtual Machines (B2als_v2)
- ARM-based, 60% cost savings vs Intel
- Appropriately sized for microservices (2 vCPU, 4GB RAM)
- Latest generation ensures 5+ year support
- Burstable CPU optimized for non-peak workloads

## 3. VPN Gateway (VpnGw1AZ)
- Zone-redundant for 99.95% availability
- 1 Gbps throughput sufficient for 2 APIs + DB sync
- Dual tunnels prevent single point of failure
- IPsec encryption for secure AWS connectivity

## 4. Network Security Groups
- Implicit deny-all follows cybersecurity zero-trust
- Least privilege per-subnet isolation
- Stateful filtering reduces rule complexity
- MongoDB port 27017 restricted to VPN tunnel only

## 5. Central India Region
- Compliant with India data residency requirements
- Lowest latency for India-based users
- Cost-competitive for APAC deployments
- Supports Indian business compliance frameworks
