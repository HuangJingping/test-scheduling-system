# 部署文档

## 部署概述

测试调度系统支持多种部署方式，从简单的单机部署到复杂的容器化分布式部署。本文档详细介绍各种部署场景和最佳实践。

## 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **磁盘**: 10GB可用空间
- **操作系统**: Windows 10/Linux Ubuntu 18.04+/macOS 10.15+
- **Python**: 3.8+

### 推荐配置
- **CPU**: 4核心+
- **内存**: 8GB+ RAM
- **磁盘**: 50GB+ SSD
- **操作系统**: Linux Ubuntu 20.04 LTS
- **Python**: 3.9+

### 大规模部署配置
- **CPU**: 8核心+
- **内存**: 16GB+ RAM
- **磁盘**: 100GB+ NVMe SSD
- **网络**: 千兆以太网
- **负载均衡**: Nginx/HAProxy

## 单机部署

### 1. 直接部署

#### 环境准备
```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3.9 python3.9-pip python3.9-venv -y

# 安装Git
sudo apt install git -y
```

#### 项目部署
```bash
# 创建部署目录
sudo mkdir -p /opt/test-scheduler
cd /opt/test-scheduler

# 克隆项目
git clone https://github.com/HuangJingping/test-scheduling-system.git .

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 配置权限
sudo chown -R $USER:$USER /opt/test-scheduler
chmod +x scripts/*.py
```

#### 配置文件设置
```bash
# 复制配置模板
cp config/scheduler_config.json.example config/scheduler_config.json
cp config/test_data.json.example config/test_data.json

# 编辑配置文件
nano config/scheduler_config.json
```

#### 验证部署
```bash
# 运行测试
python basic_test.py

# 运行演示
python demo_video_fixed.py

# 检查日志
tail -f logs/scheduler.log
```

### 2. 使用systemd服务

#### 创建服务文件
```bash
sudo nano /etc/systemd/system/test-scheduler.service
```

```ini
[Unit]
Description=Test Scheduling System
After=network.target

[Service]
Type=simple
User=scheduler
Group=scheduler
WorkingDirectory=/opt/test-scheduler
Environment=PATH=/opt/test-scheduler/venv/bin
ExecStart=/opt/test-scheduler/venv/bin/python -m src.api_server
Restart=always
RestartSec=10

# 日志配置
StandardOutput=journal
StandardError=journal
SyslogIdentifier=test-scheduler

# 安全配置
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/test-scheduler/logs /opt/test-scheduler/output

[Install]
WantedBy=multi-user.target
```

#### 启动服务
```bash
# 创建专用用户
sudo useradd --system --shell /bin/false scheduler

# 设置权限
sudo chown -R scheduler:scheduler /opt/test-scheduler

# 启用和启动服务
sudo systemctl daemon-reload
sudo systemctl enable test-scheduler
sudo systemctl start test-scheduler

# 检查状态
sudo systemctl status test-scheduler
```

## 容器化部署

### 1. Docker部署

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY . .

# 创建非root用户
RUN groupadd -r scheduler && useradd -r -g scheduler scheduler
RUN chown -R scheduler:scheduler /app

# 切换到非root用户
USER scheduler

# 暴露端口
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python scripts/health_check.py

# 启动命令
CMD ["python", "-m", "src.api_server"]
```

#### 构建和运行
```bash
# 构建镜像
docker build -t test-scheduler:latest .

# 运行容器
docker run -d \
    --name test-scheduler \
    -p 8080:8080 \
    -v $(pwd)/config:/app/config:ro \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/output:/app/output \
    --restart unless-stopped \
    test-scheduler:latest

# 查看日志
docker logs -f test-scheduler
```

### 2. Docker Compose部署

#### docker-compose.yml
```yaml
version: '3.8'

services:
  test-scheduler:
    build: .
    container_name: test-scheduler
    ports:
      - "8080:8080"
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./output:/app/output
      - ./data:/app/data
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - MAX_WORKERS=4
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "scripts/health_check.py"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: test-scheduler-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - test-scheduler
    restart: unless-stopped

  redis:
    image: redis:alpine
    container_name: test-scheduler-redis
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### Nginx配置
```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream test_scheduler {
        server test-scheduler:8080;
    }

    server {
        listen 80;
        server_name localhost;

        location / {
            proxy_pass http://test_scheduler;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            proxy_pass http://test_scheduler/health;
            access_log off;
        }
    }
}
```

#### 启动服务
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f test-scheduler
```

## Kubernetes部署

### 1. 命名空间和配置

#### namespace.yaml
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: test-scheduler
```

#### configmap.yaml
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: test-scheduler-config
  namespace: test-scheduler
data:
  scheduler_config.json: |
    {
      "scheduling": {
        "max_parallel": 3,
        "max_parallel_per_phase": 3
      },
      "working_time": {
        "hours_per_day": 8,
        "rest_day_cycle": 7
      },
      "priority_weights": {
        "dependency": 10,
        "duration": 2,
        "resource": 5,
        "phase": 20,
        "continuity": 50
      }
    }
```

### 2. 部署配置

#### deployment.yaml
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-scheduler
  namespace: test-scheduler
  labels:
    app: test-scheduler
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test-scheduler
  template:
    metadata:
      labels:
        app: test-scheduler
    spec:
      containers:
      - name: test-scheduler
        image: test-scheduler:latest
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: test-scheduler-config
      - name: logs
        emptyDir: {}
```

#### service.yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: test-scheduler-service
  namespace: test-scheduler
spec:
  selector:
    app: test-scheduler
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

#### ingress.yaml
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-scheduler-ingress
  namespace: test-scheduler
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: scheduler.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: test-scheduler-service
            port:
              number: 80
```

### 3. 部署命令
```bash
# 应用所有配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n test-scheduler
kubectl get services -n test-scheduler
kubectl get ingress -n test-scheduler

# 查看日志
kubectl logs -f deployment/test-scheduler -n test-scheduler
```

## 云平台部署

### 1. AWS部署

#### 使用ECS Fargate
```json
{
  "family": "test-scheduler",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "test-scheduler",
      "image": "your-account.dkr.ecr.region.amazonaws.com/test-scheduler:latest",
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/test-scheduler",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 使用Lambda
```python
import json
import boto3
from test_scheduler_refactored import TestScheduler

def lambda_handler(event, context):
    try:
        # 从S3获取测试数据
        s3 = boto3.client('s3')
        bucket = event['bucket']
        key = event['key']
        
        # 下载数据文件
        response = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(response['Body'].read())
        
        # 执行调度
        scheduler = TestScheduler()
        scheduler.load_data_from_dict(data)
        result = scheduler.solve_schedule()
        
        # 上传结果到S3
        output_key = f"results/{key.replace('.json', '_result.json')}"
        s3.put_object(
            Bucket=bucket,
            Key=output_key,
            Body=json.dumps(result.__dict__, default=str)
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': '调度完成',
                'result_location': f's3://{bucket}/{output_key}'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### 2. Azure部署

#### 使用Container Instances
```yaml
apiVersion: 2019-12-01
location: eastus
name: test-scheduler-container-group
properties:
  containers:
  - name: test-scheduler
    properties:
      image: your-registry.azurecr.io/test-scheduler:latest
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
      ports:
      - port: 8080
        protocol: TCP
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 8080
  restartPolicy: Always
```

### 3. Google Cloud部署

#### 使用Cloud Run
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: test-scheduler
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/cpu-throttling: "false"
        run.googleapis.com/memory: "1Gi"
    spec:
      containerConcurrency: 10
      containers:
      - image: gcr.io/PROJECT-ID/test-scheduler
        ports:
        - containerPort: 8080
        env:
        - name: ENVIRONMENT
          value: production
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
```

## 监控和日志

### 1. 应用监控

#### Prometheus配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'test-scheduler'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

#### 应用指标
```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 定义指标
schedule_requests_total = Counter('schedule_requests_total', '调度请求总数')
schedule_duration_seconds = Histogram('schedule_duration_seconds', '调度耗时')
active_schedules = Gauge('active_schedules', '当前活跃调度数')

def monitor_scheduling():
    schedule_requests_total.inc()
    start_time = time.time()
    
    try:
        active_schedules.inc()
        # 执行调度逻辑
        result = perform_scheduling()
        return result
    finally:
        schedule_duration_seconds.observe(time.time() - start_time)
        active_schedules.dec()
```

### 2. 日志聚合

#### ELK Stack配置
```yaml
# docker-compose.elk.yml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:7.17.0
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:7.17.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

#### Logstash配置
```ruby
# logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "test-scheduler" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{WORD:level} - %{GREEDYDATA:msg}" }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "test-scheduler-%{+YYYY.MM.dd}"
  }
}
```

### 3. 健康检查

#### 健康检查脚本
```python
#!/usr/bin/env python3
import sys
import requests
import json

def health_check():
    try:
        # 检查API响应
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code != 200:
            print(f"API健康检查失败: {response.status_code}")
            return False
        
        health_data = response.json()
        
        # 检查关键组件
        if not health_data.get('database_connected', False):
            print("数据库连接失败")
            return False
        
        if not health_data.get('scheduler_ready', False):
            print("调度器未准备就绪")
            return False
        
        # 检查资源使用
        memory_usage = health_data.get('memory_usage_percent', 0)
        if memory_usage > 90:
            print(f"内存使用率过高: {memory_usage}%")
            return False
        
        print("健康检查通过")
        return True
        
    except Exception as e:
        print(f"健康检查异常: {str(e)}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)
```

## 安全配置

### 1. 网络安全

#### 防火墙配置
```bash
# UFW配置
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允许SSH
sudo ufw allow 22/tcp

# 允许HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 允许应用端口（仅内网）
sudo ufw allow from 10.0.0.0/8 to any port 8080
```

#### SSL/TLS配置
```nginx
server {
    listen 443 ssl http2;
    server_name scheduler.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 应用安全

#### 环境变量配置
```bash
# .env文件
DATABASE_URL=postgresql://user:pass@localhost:5432/scheduler
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here
ENCRYPTION_KEY=your-encryption-key-here

# JWT配置
JWT_SECRET=your-jwt-secret
JWT_EXPIRATION=3600

# 安全配置
ALLOWED_HOSTS=localhost,scheduler.example.com
CORS_ORIGINS=https://frontend.example.com
```

#### 访问控制
```python
from functools import wraps
import jwt

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': '缺少认证令牌'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=['HS256'])
            current_user = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效令牌'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated_function
```

## 备份和恢复

### 1. 数据备份

#### 定时备份脚本
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/test-scheduler"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="scheduler_backup_${DATE}.tar.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份应用数据
tar -czf "${BACKUP_DIR}/${BACKUP_FILE}" \
    /opt/test-scheduler/config \
    /opt/test-scheduler/data \
    /opt/test-scheduler/logs

# 上传到云存储（可选）
aws s3 cp "${BACKUP_DIR}/${BACKUP_FILE}" s3://your-backup-bucket/

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "scheduler_backup_*.tar.gz" -mtime +7 -delete

echo "备份完成: ${BACKUP_FILE}"
```

#### 定时任务配置
```bash
# 添加到crontab
crontab -e

# 每天凌晨2点执行备份
0 2 * * * /opt/test-scheduler/scripts/backup.sh
```

### 2. 灾难恢复

#### 恢复脚本
```bash
#!/bin/bash
# restore.sh

if [ $# -ne 1 ]; then
    echo "用法: $0 <backup_file>"
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR="/opt/test-scheduler"

# 停止服务
sudo systemctl stop test-scheduler

# 备份当前数据
mv $RESTORE_DIR "${RESTORE_DIR}.$(date +%Y%m%d_%H%M%S)"

# 恢复数据
mkdir -p $RESTORE_DIR
tar -xzf $BACKUP_FILE -C /

# 恢复权限
sudo chown -R scheduler:scheduler $RESTORE_DIR

# 启动服务
sudo systemctl start test-scheduler

echo "恢复完成"
```

## 性能调优

### 1. 系统级优化

#### 内核参数调优
```bash
# /etc/sysctl.conf
# 网络优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# 文件描述符限制
fs.file-max = 65536

# 应用生效
sudo sysctl -p
```

#### 文件描述符限制
```bash
# /etc/security/limits.conf
scheduler soft nofile 65536
scheduler hard nofile 65536
```

### 2. 应用级优化

#### 连接池配置
```python
import asyncio
import aiohttp
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage

async def create_app():
    app = aiohttp.web.Application()
    
    # 配置连接池
    connector = aiohttp.TCPConnector(
        limit=100,              # 最大连接数
        limit_per_host=30,      # 单主机最大连接数
        ttl_dns_cache=300,      # DNS缓存时间
        use_dns_cache=True,
    )
    
    # 配置Redis会话存储
    redis_pool = aioredis.ConnectionPool.from_url(
        "redis://localhost:6379",
        max_connections=20
    )
    
    setup(app, RedisStorage(redis_pool))
    
    return app
```

#### 缓存策略
```python
import redis
import pickle
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=3600):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return pickle.loads(cached_result)
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                expiration, 
                pickle.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

## 故障排除

### 常见问题

#### 1. 内存不足
**症状**: 应用频繁重启，响应缓慢
**解决方案**:
```bash
# 检查内存使用
free -h
top -p $(pgrep -f test-scheduler)

# 调整Python内存限制
export PYTHONMALLOC=malloc
ulimit -v 2097152  # 限制虚拟内存为2GB
```

#### 2. 端口冲突
**症状**: 应用启动失败，端口被占用
**解决方案**:
```bash
# 查找占用端口的进程
sudo lsof -i :8080
sudo netstat -tlnp | grep :8080

# 终止进程
sudo kill -9 <PID>
```

#### 3. 文件权限问题
**症状**: 无法读写配置文件或日志文件
**解决方案**:
```bash
# 检查文件权限
ls -la /opt/test-scheduler/

# 修复权限
sudo chown -R scheduler:scheduler /opt/test-scheduler/
sudo chmod -R 755 /opt/test-scheduler/
sudo chmod -R 644 /opt/test-scheduler/config/*.json
```

### 日志分析

#### 常见错误模式
```bash
# 查找错误日志
grep -i error /opt/test-scheduler/logs/*.log

# 分析内存相关错误
grep -i "memory\|oom" /var/log/syslog

# 查找依赖关系错误
grep -i "circular\|dependency" /opt/test-scheduler/logs/*.log

# 分析性能问题
grep -i "timeout\|slow" /opt/test-scheduler/logs/*.log
```

## 维护指南

### 定期维护任务

#### 每日检查
- [ ] 检查服务状态
- [ ] 查看错误日志
- [ ] 监控资源使用
- [ ] 验证备份完成

#### 每周维护
- [ ] 更新系统安全补丁
- [ ] 清理临时文件和日志
- [ ] 检查磁盘空间
- [ ] 审查性能指标

#### 每月维护
- [ ] 更新应用依赖包
- [ ] 测试灾难恢复流程
- [ ] 优化数据库性能
- [ ] 审查安全配置

### 升级指南

#### 滚动升级流程
```bash
# 1. 备份当前版本
./scripts/backup.sh

# 2. 下载新版本
git fetch origin
git checkout v2.0.0

# 3. 更新依赖
pip install -r requirements.txt

# 4. 运行数据库迁移（如果需要）
python scripts/migrate.py

# 5. 重启服务
sudo systemctl restart test-scheduler

# 6. 验证升级
python scripts/health_check.py
```

---

这份部署文档涵盖了从简单单机部署到复杂云原生部署的各种场景，为不同规模和需求的部署提供了详细指导。