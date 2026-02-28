#!/usr/bin/env bash
# =============================================================================
# setup_alb.sh  –  Create an ALB in front of occ-api-service (ECS)
# Run once. The ALB DNS never changes across ECS deployments.
#
# Prerequisites: aws cli v2 installed and configured (aws configure)
# Usage: bash scripts/setup_alb.sh
# =============================================================================
set -euo pipefail

# ── Force real AWS (unset LocalStack override if present) ────────────────────
unset AWS_ENDPOINT_URL
unset LOCALSTACK_HOST

# ── Config (matches ci.yml) ──────────────────────────────────────────────────
REGION="us-east-1"
CLUSTER="occ-code-quality"
SERVICE="occ-api-service"
APP_PORT=8000
ALB_NAME="occ-code-quality-alb"
TG_NAME="occ-api-tg"
SG_ALB_NAME="occ-alb-sg"
SG_ECS_NAME="occ-api-sg"   # existing SG attached to your ECS tasks

# ── 1. Discover VPC & subnets used by the ECS service ───────────────────────
echo "==> Fetching VPC and subnets from ECS service..."

TASK_ARN=$(aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --region "$REGION" \
  --query "taskArns[0]" \
  --output text)

if [ "$TASK_ARN" = "None" ] || [ -z "$TASK_ARN" ]; then
  echo "ERROR: No running tasks found in service $SERVICE. Deploy at least once first."
  exit 1
fi

ENI_ID=$(aws ecs describe-tasks \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN" \
  --region "$REGION" \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" \
  --output text)

VPC_ID=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$ENI_ID" \
  --region "$REGION" \
  --query "NetworkInterfaces[0].VpcId" \
  --output text)

echo "    VPC: $VPC_ID"

# Get all public subnets in the VPC (ALB needs at least 2 AZs)
SUBNET_IDS=$(aws ec2 describe-subnets \
  --filters \
    "Name=vpc-id,Values=$VPC_ID" \
    "Name=map-public-ip-on-launch,Values=true" \
  --region "$REGION" \
  --query "Subnets[*].SubnetId" \
  --output text | tr '\t' ',')

echo "    Public Subnets: $SUBNET_IDS"

if [ -z "$SUBNET_IDS" ]; then
  echo "ERROR: No public subnets found. An ALB requires at least 2 public subnets."
  exit 1
fi

# ── 2. Create Security Group for ALB ────────────────────────────────────────
echo "==> Creating ALB security group..."

ALB_SG_ID=$(aws ec2 create-security-group \
  --group-name "$SG_ALB_NAME" \
  --description "Allow HTTP/HTTPS inbound to ALB" \
  --vpc-id "$VPC_ID" \
  --region "$REGION" \
  --query "GroupId" \
  --output text 2>/dev/null || \
  aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=$SG_ALB_NAME" "Name=vpc-id,Values=$VPC_ID" \
    --region "$REGION" \
    --query "SecurityGroups[0].GroupId" \
    --output text)

echo "    ALB SG: $ALB_SG_ID"

# Allow HTTP 80 from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id "$ALB_SG_ID" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 \
  --region "$REGION" 2>/dev/null || echo "    (HTTP rule already exists)"

# Allow HTTPS 443 from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id "$ALB_SG_ID" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 \
  --region "$REGION" 2>/dev/null || echo "    (HTTPS rule already exists)"

# ── 3. Allow ALB → ECS on app port ──────────────────────────────────────────
echo "==> Allowing ALB SG → ECS on port $APP_PORT..."

ECS_SG_ID=$(aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=$SG_ECS_NAME" "Name=vpc-id,Values=$VPC_ID" \
  --region "$REGION" \
  --query "SecurityGroups[0].GroupId" \
  --output text 2>/dev/null || echo "")

if [ -n "$ECS_SG_ID" ] && [ "$ECS_SG_ID" != "None" ]; then
  aws ec2 authorize-security-group-ingress \
    --group-id "$ECS_SG_ID" \
    --protocol tcp \
    --port "$APP_PORT" \
    --source-group "$ALB_SG_ID" \
    --region "$REGION" 2>/dev/null || echo "    (rule already exists)"
  echo "    ECS SG $ECS_SG_ID updated."
else
  echo "    WARNING: Could not find ECS SG '$SG_ECS_NAME'. Add inbound rule manually:"
  echo "      Source: $ALB_SG_ID  Protocol: TCP  Port: $APP_PORT"
fi

# ── 4. Create Target Group (type=ip for awsvpc ECS tasks) ───────────────────
echo "==> Creating Target Group..."

TG_ARN=$(aws elbv2 create-target-group \
  --name "$TG_NAME" \
  --protocol HTTP \
  --port "$APP_PORT" \
  --vpc-id "$VPC_ID" \
  --target-type ip \
  --health-check-path "/health" \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region "$REGION" \
  --query "TargetGroups[0].TargetGroupArn" \
  --output text 2>/dev/null || \
  aws elbv2 describe-target-groups \
    --names "$TG_NAME" \
    --region "$REGION" \
    --query "TargetGroups[0].TargetGroupArn" \
    --output text)

echo "    Target Group ARN: $TG_ARN"

# ── 5. Create the ALB ────────────────────────────────────────────────────────
echo "==> Creating Application Load Balancer..."

# Convert comma-separated subnets to space-separated for CLI
SUBNET_LIST=$(echo "$SUBNET_IDS" | tr ',' ' ')

ALB_ARN=$(aws elbv2 create-load-balancer \
  --name "$ALB_NAME" \
  --subnets $SUBNET_LIST \
  --security-groups "$ALB_SG_ID" \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --region "$REGION" \
  --query "LoadBalancers[0].LoadBalancerArn" \
  --output text 2>/dev/null || \
  aws elbv2 describe-load-balancers \
    --names "$ALB_NAME" \
    --region "$REGION" \
    --query "LoadBalancers[0].LoadBalancerArn" \
    --output text)

echo "    ALB ARN: $ALB_ARN"

# ── 6. Create HTTP Listener → forward to Target Group ───────────────────────
echo "==> Creating HTTP listener (port 80)..."

aws elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTP \
  --port 80 \
  --default-actions "Type=forward,TargetGroupArn=$TG_ARN" \
  --region "$REGION" \
  --output text > /dev/null 2>/dev/null || echo "    (listener already exists)"

# ── 7. Attach ALB to ECS Service ─────────────────────────────────────────────
echo "==> Updating ECS service to use the Target Group..."

# Get current task definition
TASK_DEF=$(aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$SERVICE" \
  --region "$REGION" \
  --query "services[0].taskDefinition" \
  --output text)

# Get the container name and port from the task definition
CONTAINER_NAME=$(aws ecs describe-task-definition \
  --task-definition "$TASK_DEF" \
  --region "$REGION" \
  --query "taskDefinition.containerDefinitions[0].name" \
  --output text)

aws ecs update-service \
  --cluster "$CLUSTER" \
  --service "$SERVICE" \
  --load-balancers "targetGroupArn=$TG_ARN,containerName=$CONTAINER_NAME,containerPort=$APP_PORT" \
  --region "$REGION" \
  --output text > /dev/null

echo "    ECS service updated."

# ── 8. Get the stable ALB DNS name ───────────────────────────────────────────
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --load-balancer-arns "$ALB_ARN" \
  --region "$REGION" \
  --query "LoadBalancers[0].DNSName" \
  --output text)

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  ALB is ready. This DNS name NEVER changes:"
echo ""
echo "    http://${ALB_DNS}"
echo ""
echo "  Set this as your GitHub secret BACKEND_URL:"
echo ""
echo "    gh secret set BACKEND_URL --body \"http://${ALB_DNS}\""
echo ""
echo "  Then never touch it again — ECS deployments rotate task"
echo "  IPs automatically; the ALB handles it."
echo "============================================================"
