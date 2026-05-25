# AutoHub & KitchenOS Hybrid Multi-Cloud Platform

This repository contains the decoupled microservice architectures for two independent applications deployed across a hybrid **Azure** and **AWS** cloud environment:

1. **AutoHub (Python)** — Car fleet inventory and rental booking management system.
2. **KitchenOS (Node.js)** — Indian vegetarian recipe library and pantry tracking system.

---

## Architecture Overview

```mermaid
graph TD
    User([User Browser]) -->|HTTP Port 80| AppGateway[Azure Application Gateway]
    
    subgraph Azure VNet (10.10.0.0/16)
        subgraph Gateway Subnet (10.10.0.0/27)
            AzureVPNGW[Azure VPN Gateway]
        end
        
        subgraph Bastion Subnet (10.10.1.0/26)
            AzureBastion[Azure Bastion Host]
        end
        
        subgraph Backend Subnet (10.10.2.0/24)
            VM_Autohub[vm-autohub-backend<br/>Python Microservices<br/>Nginx Front & Backend]
            VM_KitchenOS[vm-kitchenos-backend<br/>Node.js Microservices<br/>Nginx Front & Backend]
        end
    end
    
    subgraph AWS VPC (192.16.0.0/16)
        subgraph AWS Gateway Components
            AWS_VGW[Virtual Private Gateway]
            AWS_CGW[Customer Gateway]
        end
        
        subgraph Private Database Subnet (192.16.0.0/24)
            Mongo_Autohub[(autohub_mongo VM<br/>192.16.0.101)]
            Mongo_KitchenOS[(kitchenos_mongo VM<br/>192.16.0.244)]
        end
    end

    AppGateway -->|HTTP Port 80| VM_Autohub
    AppGateway -->|HTTP Port 80| VM_KitchenOS
    
    AzureVPNGW <===>|IPsec Site-to-Site VPN Tunnels 1 & 2| AWS_VGW
    
    VM_Autohub -->|Private TCP 27017| Mongo_Autohub
    VM_KitchenOS -->|Private TCP 27017| Mongo_KitchenOS
```

### Network & DNS Address Mappings

| Application | Domain Namespace | AWS MongoDB Private IP | Local Port | Production Backend VM Port |
| :--- | :--- | :--- | :--- | :--- |
| **AutoHub** | `*.sathvikdevops.site` | `192.16.0.101` | `5000` | `80` (Proxies to `5001-5009`) |
| **KitchenOS** | `*.sathvikdevops.online` | `192.16.0.244` | `3000` | `80` (Proxies to `3001-3006`) |

---

## 1. Local Development Setup

To run both platforms locally on your machine (using local file-based JSON databases as a fallback):

### Running AutoHub (Python)
1. Navigate to the Python directory:
   ```bash
   cd autohub_python
   ```
2. Install dependencies:
   ```bash
   pip install pymongo
   ```
3. Run the central orchestrator:
   ```bash
   python run_all.py
   ```
4. Access the dashboard: `http://localhost:5000`

### Running KitchenOS (Node.js)
1. Navigate to the Node.js directory:
   ```bash
   cd kitchenos_nodejs
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the central orchestrator:
   ```bash
   npm start
   ```
4. Access the dashboard: `http://localhost:3000`

---

## 2. Production Provisioning & Setup Guide

Follow this step-by-step guide to configure the hybrid infrastructure across Azure and AWS.

### Phase 1: Azure Resource Group & VNet Setup
1. Log in to the **Azure Portal**.
2. Search for **Resource Groups** and create a resource group:
   * **Name**: `rg-multicloud-prod`.
   * **Region**: Choose your target region (e.g., `East US`).
3. Search for **Virtual Networks** and click **Create**:
   * **Resource Group**: `rg-multicloud-prod`.
   * **Name**: `vnet-azure-prod`.
   * **IP Addresses Tab**:
     * Change IPv4 Address Space to: `10.10.0.0/16`.
     * Click **Add Subnet** (Bastion):
       * **Name**: `AzureBastionSubnet` *(Must use this exact name).*
       * **Range**: `10.10.1.0/26`.
     * Click **Add Subnet** (Backend Application Subnet):
       * **Name**: `BackendSubnet`.
       * **Range**: `10.10.2.0/24`.
     * Click **Add Subnet** (VPN Gateway Subnet):
       * **Name**: `GatewaySubnet` *(Must use this exact name).*
       * **Range**: `10.10.0.0/27`.
4. Click **Review + Create**, then **Create**.

---

### Phase 2: AWS VPC & Private Subnet Setup
1. Log in to the **AWS VPC Console** and click **Create VPC**.
2. **Resources to create**: Select **VPC only**.
3. **Name Tag**: `vpc-aws-prod`.
4. **IPv4 CIDR Block**: `192.16.0.0/16`.
5. Click **Create VPC**.
6. Select **Subnets** in the left menu -> click **Create Subnet**:
   * **VPC**: Select `vpc-aws-prod`.
   * **Subnet Name**: `PrivateDatabaseSubnet`.
   * **IPv4 CIDR Block**: `192.16.0.0/24`.
7. Click **Create Subnet**.

---

### Phase 3: AWS MongoDB Instances Setup
1. Go to the **Amazon EC2 Console** -> **Instances** -> click **Launch Instances**.
2. Provision **Instance 1 (AutoHub Database)**:
   * **Name**: `autohub_mongo`.
   * **AMI**: `Ubuntu Server 22.04 LTS`.
   * **Subnet**: Select `PrivateDatabaseSubnet` (`192.16.0.0/24`).
   * **Auto-assign Public IP**: **Disable**.
   * **Private IP**: Hardcode/assign `192.16.0.101`.
3. Provision **Instance 2 (KitchenOS Database)**:
   * **Name**: `kitchenos_mongo`.
   * **AMI**: `Ubuntu Server 22.04 LTS`.
   * **Subnet**: Select `PrivateDatabaseSubnet` (`192.16.0.0/24`).
   * **Auto-assign Public IP**: **Disable**.
   * **Private IP**: Hardcode/assign `192.16.0.244`.
4. Create and attach a Security Group named `sg-mongodb-prod` to **both** EC2 instances with these inbound rules:
   * **Rule 1**: Port: `27017` (TCP) | Source: `10.10.0.0/16` (Azure VNet CIDR)
   * **Rule 2**: Port: `22` (TCP) | Source: `192.16.0.0/16` (AWS VPC Private Space)
5. SSH into both EC2 instances and install/configure MongoDB 7.0:
   ```bash
   sudo apt install -y gnupg curl
   curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
   echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
   sudo apt update
   sudo apt install -y mongodb-org
   sudo systemctl enable --now mongod
   ```
6. Open `/etc/mongod.conf` (`sudo nano /etc/mongod.conf`) and configure:
   * **Bind IP**: Set `bindIp` to `0.0.0.0`
7. Connect to the shell (`mongosh`) and initialize the root and application credentials:
   ```javascript
   use admin
   db.createUser({ user: "admin", pwd: "SecureAdminPassword", roles: [ { role: "userAdminAnyDatabase", db: "admin" }, "readWriteAnyDatabase" ] })
   
   // Run on Instance 1 (AutoHub)
   use autohub
   db.createUser({ user: "autohub_user", pwd: "AutoHubPassword", roles: [ { role: "readWrite", db: "autohub" } ] })
   
   // Run on Instance 2 (KitchenOS)
   use kitchenos
   db.createUser({ user: "kitchenos_user", pwd: "KitchenOSPassword", roles: [ { role: "readWrite", db: "kitchenos" } ] })
   ```
8. Enable auth in `/etc/mongod.conf`:
   ```yaml
   security:
     authorization: "enabled"
   ```
9. Restart the service: `sudo systemctl restart mongod`.

---

### Phase 4: Azure & AWS IPsec VPN Setup

#### 1. Deploy the Azure VPN Gateway
1. Go to the Azure Portal -> **Virtual Network Gateways** -> click **Create**.
2. Set **Name**: `vgw-azure-to-aws` | **Gateway Type**: `VPN` | **VPN Type**: `Route-based` | **SKU**: `VpnGw1` | **Virtual Network**: `vnet-azure-prod`.
3. Set **Public IP address**: Select **Create new** -> Name: `pip-azure-vpn-gw`.
4. Click **Create** (takes 20–45 mins). Once deployed, copy its **Public IP Address** from the overview page.

#### 2. Configure AWS VPN Gateway & Tunnel Connection
1. In the AWS VPC Console, select **Customer Gateways** -> **Create Customer Gateway**:
   * **Name**: `cgw-to-azure` | **IP Address**: Paste the **Azure VPN Gateway Public IP**.
2. Select **Virtual Private Gateways** -> **Create Virtual Private Gateway**:
   * **Name**: `vgw-aws-to-azure`.
   * Attach it to your VPC: Select it -> click **Actions** -> **Attach to VPC** -> Select `vpc-aws-prod`.
3. Select **Site-to-Site VPN Connections** -> **Create VPN Connection**:
   * **Name**: `vpn-aws-azure`.
   * **Target Gateway**: `Virtual Private Gateway` -> Select `vgw-aws-to-azure`.
   * **Customer Gateway**: `Existing` -> Select `cgw-to-azure`.
   * **Routing**: `Static` | **Static IP Prefixes**: Enter Azure VNet range `10.10.0.0/16`.
4. Click **Create**. Once `Available`, select the connection -> click **Download Configuration** (select **Generic**).
5. Open the configuration file and record:
   * **Tunnel 1 IPsec Tunnel Outer IP Address** (e.g. `3.95.36.91`) and its **Pre-Shared Key**.
   * **Tunnel 2 IPsec Tunnel Outer IP Address** and its **Pre-Shared Key**.

#### 3. Complete Azure Local Gateway & Connection Bindings
1. In the Azure Portal, search **Local network gateways** -> click **Create**:
   * **Name**: `lng-aws-tunnel-1` | **IP Address**: Enter **Tunnel 1 Outer IP** | **Address space**: `192.16.0.0/16`.
2. Click **Create** again:
   * **Name**: `lng-aws-tunnel-2` | **IP Address**: Enter **Tunnel 2 Outer IP** | **Address space**: `192.16.0.0/16`.
3. Open your Azure VPN Gateway (`vgw-azure-to-aws`) -> **Connections** -> click **+ Add**:
   * **Connection 1**: Name: `conn-to-aws-t1` | Connection type: `Site-to-site (IPsec)` | Local Gateway: `lng-aws-tunnel-1` | Shared Key: Paste **Tunnel 1 Pre-Shared Key**.
   * **Connection 2**: Name: `conn-to-aws-t2` | Connection type: `Site-to-site (IPsec)` | Local Gateway: `lng-aws-tunnel-2` | Shared Key: Paste **Tunnel 2 Pre-Shared Key**.

#### 4. Enable AWS Route Table Propagation
1. Go to AWS VPC Console -> **Route Tables** -> Select the route table for `PrivateDatabaseSubnet`.
2. Go to **Route Propagation** -> click **Edit route propagation**.
3. Check **Enable** next to your Virtual Private Gateway (`vgw-aws-to-azure`) and click **Save**.

---

### Phase 5: Azure Backend VMs & Bastion Setup
1. In the Azure Portal, search for **Virtual Machines** -> click **Create** -> **Virtual machine**.
2. **VM 1 (AutoHub Python)**: Name: `vm-autohub-backend` | Subnet: `BackendSubnet` | Public IP: **None** | Image: `Ubuntu Server 22.04 LTS`.
3. **VM 2 (KitchenOS Node.js)**: Name: `vm-kitchenos-backend` | Subnet: `BackendSubnet` | Public IP: **None** | Image: `Ubuntu Server 22.04 LTS`.
4. **Deploy Bastion**:
   * Search for **Bastion** -> click **Create**.
   * **Virtual network**: `vnet-azure-prod` | **Subnet**: `AzureBastionSubnet` | **Public IP**: Create a new Standard SKU IP (`pip-bastion`).
   * *SSH into both backend VMs securely via Bastion using your private SSH key.*

---

### Phase 6: Subnet Network Security Groups (NSGs) Setup
1. Create a single Network Security Group named `nsg-backend` and associate it with the **entire BackendSubnet**.
2. Add **Inbound Security Rules**:
   * **Rule 1**: Priority: `100` | Source: `IP Addresses` (Gateway subnet, e.g. `10.10.0.0/27`) | Destination Port: `80` | Action: `Allow`
   * **Rule 2**: Priority: `110` | Source: `IP Addresses` (Bastion subnet, e.g. `10.10.1.0/26`) | Destination Port: `22` | Action: `Allow`
   * **Rule 3**: Priority: `900` | Source: `Any` | Destination Port: `*` | Action: `Deny`
3. Add **Outbound Security Rules**:
   * **Rule 1**: Priority: `100` | Destination: `IP Addresses` (`192.16.0.0/16` AWS range) | Destination Port: `27017` | Action: `Allow`
   * **Rule 2**: Priority: `110` | Destination: `Internet` | Destination Port: `80, 443` | Action: `Allow`

---

### Phase 7: Azure Application Gateway Setup
1. Search **Application Gateways** -> click **Create**.
2. **Basics**: Name: `appgw-multicloud-prod` | Tier: `Standard V2` | Virtual Network: `vnet-azure-prod` | Subnet: `BackendSubnet`.
3. **Frontends**: Select **Public** -> Create new Public IP (`pip-app-gateway`).
4. **Backends**:
   * Add pool `autohub-pool` targeting `vm-autohub-backend` private IP.
   * Add pool `kitchenos-pool` targeting `vm-kitchenos-backend` private IP.
5. **Backend Settings**: Name: `http-setting-port-80` | Protocol: `HTTP` | Port: `80`.
6. **Listeners**:
   * **Listener 1**: Name: `listener-autohub-wildcard` | Type: `Multi site` | Hostname: `*.sathvikdevops.site` | Port: 80.
   * **Listener 2**: Name: `listener-kitchenos-wildcard` | Type: `Multi site` | Hostname: `*.sathvikdevops.online` | Port: 80.
7. **Routing Rules**:
   * **Rule 1**: Name: `rule-autohub` | Listener: `listener-autohub-wildcard` | Target: `autohub-pool` via `http-setting-port-80`.
   * **Rule 2**: Name: `rule-kitchenos` | Listener: `listener-kitchenos-wildcard` | Target: `kitchenos-pool` via `http-setting-port-80`.

---

### Phase 8: Code Deployment, Nginx & Services Running

#### 1. Setup the AutoHub (Python) Backend VM
1. Log in to `vm-autohub-backend` via Bastion.
2. Clone the code:
   ```bash
   git clone https://github.com/Sathvik307393/review-01.git
   cd review-01/autohub_python
   ```
3. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv nginx
   pip3 install pymongo
   ```
4. Set the environment database connection string:
   * Open `/etc/environment` (`sudo nano /etc/environment`) and append:
     ```bash
     MONGO_URI="mongodb://autohub_user:AutoHubPassword@192.16.0.101:27017/autohub?authSource=autohub"
     ```
   * Reload variables: `source /etc/environment`.
5. Deploy Nginx config:
   * Overwrite `/etc/nginx/nginx.conf` with the contents of `autohub_python/nginx.conf`.
   * Restart Nginx: `sudo systemctl restart nginx`.
6. Launch services: `python3 run_all.py` (to run persistently in the background, configure it as a systemd service).

#### 2. Setup the KitchenOS (Node.js) Backend VM
1. Log in to `vm-kitchenos-backend` via Bastion.
2. Clone the code:
   ```bash
   git clone https://github.com/Sathvik307393/review-01.git
   cd review-01/kitchenos_nodejs
   ```
3. Install Node.js 18, dependencies, and Nginx:
   ```bash
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt install -y nodejs nginx
   npm install
   ```
4. Set the environment database connection string:
   * Open `/etc/environment` (`sudo nano /etc/environment`) and append:
     ```bash
     MONGO_URI="mongodb://kitchenos_user:KitchenOSPassword@192.16.0.244:27017/kitchenos?authSource=kitchenos"
     ```
   * Reload variables: `source /etc/environment`.
5. Deploy Nginx config:
   * Overwrite `/etc/nginx/nginx.conf` with the contents of `kitchenos_nodejs/nginx.conf`.
   * Restart Nginx: `sudo systemctl restart nginx`.
6. Launch services: `node run_all.js` (configure as systemd service to run in the background).

---

### Phase 9: Domain Namespace & DNS Configuration
1. Retrieve the **Public IP** of your Azure Application Gateway (`pip-app-gateway`).
2. Log into your domain registrar (GoDaddy, Route53, Namecheap, etc.) and add the following records:
   * **For `sathvikdevops.site` (Python Platform)**:
     * **A Record**: Host `autohub` pointing to the **Application Gateway Public IP**.
     * **A Record**: Host `*` (wildcard) pointing to the **Application Gateway Public IP**.
   * **For `sathvikdevops.online` (Node.js Platform)**:
     * **A Record**: Host `kitchenos` pointing to the **Application Gateway Public IP**.
     * **A Record**: Host `*` (wildcard) pointing to the **Application Gateway Public IP**.
