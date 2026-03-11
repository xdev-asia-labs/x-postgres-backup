# 🐘 x-postgres-backup

Hệ thống quản lý backup/restore PostgreSQL HA Cluster (Patroni) với Web Dashboard và Job Scheduler.

## 📋 Mục lục

- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Yêu cầu hệ thống](#-yêu-cầu-hệ-thống)
- [Cài đặt](#-cài-đặt)
- [Cấu hình](#-cấu-hình)
- [Sử dụng](#-sử-dụng)
- [API Endpoints](#-api-endpoints)
- [Deployment](#-deployment)
- [CI/CD & Release](#-cicd--release)
- [Troubleshooting](#-troubleshooting)

## 📖 Giới thiệu

`x-postgres-backup` là một công cụ toàn diện để quản lý backup và restore cho PostgreSQL High Availability Cluster (sử dụng Patroni). Hệ thống cung cấp giao diện web thân thiện, lập lịch tự động, và thông báo realtime cho các hoạt động backup/restore.

### Tính năng chính

✅ **Dashboard trực quan**: Giám sát cluster, lịch sử backup, disk usage  
✅ **Backup Management**: Hỗ trợ `pg_basebackup` và `pg_dump` với lập lịch tự động  
✅ **Restore Management**: Restore từ backup với UI trực quan, dễ sử dụng  
✅ **Job Scheduler**: Cấu hình lịch backup/cleanup/verify qua web interface  
✅ **Cluster Monitoring**: Theo dõi trạng thái cluster realtime qua Patroni REST API  
✅ **Backup Verification**: Tự động kiểm tra tính toàn vẹn của backup  
✅ **Smart Notifications**: Thông báo qua Telegram và Email khi có sự kiện quan trọng  
✅ **Retention Management**: Tự động dọn dẹp backup cũ theo chính sách  

## 🛠️ Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **Dashboard** | Tổng quan trạng thái cluster, backup history, disk usage |
| **Backup Management** | Chạy backup thủ công hoặc theo lịch (pg_basebackup, pg_dump) |
| **Restore Management** | Restore từ backup với UI trực quan |
| **Job Scheduler** | Cấu hình lịch backup/cleanup/verify qua web |
| **Cluster Monitoring** | Realtime cluster status từ Patroni REST API |
| **Verification** | Tự động kiểm tra tính toàn vẹn backup |
| **Notifications** | Thông báo qua Telegram và Email khi backup/restore thành công hoặc thất bại |

## 💻 Yêu cầu hệ thống

### Phần mềm bắt buộc

- **Python**: 3.11 hoặc cao hơn
- **PostgreSQL Client Tools**: `pg_basebackup`, `pg_dump`, `pg_restore`, `psql`
  - Debian/Ubuntu: `sudo apt install postgresql-client-16`
  - RHEL/CentOS: `sudo yum install postgresql16`
  - macOS: `brew install postgresql@16`
- **PostgreSQL HA Cluster**: Patroni 3.x hoặc 4.x với etcd
- **Disk Space**: Đủ không gian để lưu trữ backup (khuyến nghị >= 2x kích thước database)

### Tùy chọn (cho deployment)

- **Docker & Docker Compose**: Cho containerized deployment
- **Systemd**: Cho production deployment trên Linux

## 🚀 Cài đặt

### Cài đặt với Python Virtual Environment (Development)

#### Bước 1: Clone repository

```bash
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup
```

#### Bước 2: Tạo và kích hoạt Virtual Environment

```bash
# Tạo virtual environment
python3 -m venv venv

# Kích hoạt virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

#### Bước 3: Cài đặt dependencies

```bash
# Nâng cấp pip
pip install --upgrade pip

# Cài đặt các package cần thiết
pip install -r requirements.txt
```

#### Bước 4: Tạo file cấu hình

```bash
# Copy file mẫu
cp .env.example .env

# Tạo thư mục data cho SQLite
mkdir -p data

# Tạo thư mục backup (tùy chỉnh theo nhu cầu)
mkdir -p /var/backups/postgresql
```

#### Bước 5: Cấu hình kết nối

Mở file `.env` và cập nhật các thông tin sau:

```bash
# Kết nối Patroni
PATRONI_NODES=10.10.10.11:8008,10.10.10.12:8008,10.10.10.13:8008

# Thông tin PostgreSQL
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_postgres_password
PG_BIN_DIR=/usr/lib/postgresql/16/bin  # Đường dẫn đến PostgreSQL binaries

# Replication user cho pg_basebackup
PG_REPLICATION_USER=replicator
PG_REPLICATION_PASSWORD=your_replicator_password

# Thư mục backup
BACKUP_DIR=/var/backups/postgresql
```

#### Bước 6: Khởi động ứng dụng

```bash
# Development mode với auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Bước 7: Truy cập Dashboard

Mở trình duyệt và truy cập:

```
http://localhost:8000
```

### Cài đặt với Docker Compose (Production)

### Cài đặt với Docker Compose (Production)

```bash
# 1. Clone repository
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup

# 2. Cấu hình
cp .env.example .env
nano .env  # Chỉnh sửa cấu hình

# 3. Khởi động container
docker compose up -d

# 4. Kiểm tra logs
docker compose logs -f

# 5. Truy cập dashboard
open http://localhost:8000
```

## ⚙️ Cấu hình

### Cấu hình cơ bản

Tất cả cấu hình được thực hiện qua environment variables trong file `.env`.

#### Cấu hình Application

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `APP_NAME` | x-postgres-backup | Tên ứng dụng |
| `APP_HOST` | 0.0.0.0 | Địa chỉ listen |
| `APP_PORT` | 8000 | Port listen |
| `APP_LOG_LEVEL` | info | Log level (debug, info, warning, error) |
| `APP_SECRET_KEY` | change-me | Secret key cho session (phải thay đổi) |

#### Cấu hình Cluster

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `PATRONI_NODES` | 10.10.10.11:8008 | Danh sách Patroni REST API endpoints (ngăn cách bởi dấu phẩy) |
| `PATRONI_AUTH_ENABLED` | false | Bật xác thực cho Patroni API |
| `PATRONI_AUTH_USERNAME` | | Username cho Patroni API |
| `PATRONI_AUTH_PASSWORD` | | Password cho Patroni API |

#### Cấu hình PostgreSQL

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `PG_PORT` | 5432 | PostgreSQL port |
| `PG_USER` | postgres | PostgreSQL superuser |
| `PG_PASSWORD` | | PostgreSQL password |
| `PG_BIN_DIR` | /usr/lib/postgresql/18/bin | Đường dẫn đến PostgreSQL binaries |
| `PG_REPLICATION_USER` | replicator | User để chạy pg_basebackup |
| `PG_REPLICATION_PASSWORD` | | Password của replication user |

#### Cấu hình Backup

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `BACKUP_DIR` | /var/backups/postgresql | Thư mục lưu backup |
| `BACKUP_RETENTION_DAYS` | 7 | Số ngày giữ backup |
| `BACKUP_RETENTION_COPIES` | 7 | Số lượng backup tối thiểu giữ lại |
| `BACKUP_COMPRESSION` | gzip | Phương thức nén (gzip, lz4, zstd) |

#### Cấu hình Scheduler (Cron)

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `SCHEDULE_BASEBACKUP` | 0 2 ** * | Lịch chạy pg_basebackup (2:00 AM mỗi ngày) |
| `SCHEDULE_PGDUMP` | 0 3 ** * | Lịch chạy pg_dump (3:00 AM mỗi ngày) |
| `SCHEDULE_VERIFY` | 0 4 ** * | Lịch verify backup (4:00 AM mỗi ngày) |
| `SCHEDULE_CLEANUP` | 0 6 ** * | Lịch cleanup backup cũ (6:00 AM mỗi ngày) |

**Định dạng Cron**: `minute hour day month day_of_week`

Ví dụ:

- `0 2 * * *` - 2:00 AM mỗi ngày
- `0 */6 * * *` - Mỗi 6 giờ
- `0 0 * * 0` - 12:00 AM mỗi Chủ nhật
- `30 3 * * 1-5` - 3:30 AM từ thứ 2 đến thứ 6

### Cấu hình Thông báo (Notifications)

#### Telegram Notifications

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `TELEGRAM_ENABLED` | false | Bật/tắt thông báo Telegram |
| `TELEGRAM_BOT_TOKEN` | | Token của Telegram Bot |
| `TELEGRAM_CHAT_ID` | | Chat ID nhận thông báo |

##### Hướng dẫn tạo Telegram Bot

1. **Tạo bot mới**:
   - Mở Telegram và tìm [@BotFather](https://t.me/BotFather)
   - Gửi lệnh `/newbot`
   - Đặt tên và username cho bot
   - Lưu lại **Bot Token** nhận được

2. **Lấy Chat ID**:
   - Tìm và nhắn tin cho bot vừa tạo
   - Truy cập URL: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Tìm giá trị `"chat":{"id":123456789}` trong JSON response
   - Lưu lại **Chat ID**

3. **Cập nhật `.env`**:

   ```bash
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_CHAT_ID=123456789
   ```

#### Email Notifications

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `EMAIL_ENABLED` | false | Bật/tắt thông báo Email |
| `EMAIL_SMTP_HOST` | smtp.gmail.com | SMTP server hostname |
| `EMAIL_SMTP_PORT` | 587 | SMTP server port |
| `EMAIL_SMTP_USER` | | SMTP username/email |
| `EMAIL_SMTP_PASSWORD` | | SMTP password (App Password cho Gmail) |
| `EMAIL_FROM` | | Email người gửi |
| `EMAIL_TO` | | Danh sách email nhận (ngăn cách bởi dấu phẩy) |
| `EMAIL_USE_TLS` | true | Sử dụng TLS/STARTTLS |

##### Hướng dẫn cấu hình Gmail

1. **Tạo App Password**:
   - Truy cập [Google Account Security](https://myaccount.google.com/security)
   - Bật **2-Step Verification** (nếu chưa bật)
   - Truy cập [App Passwords](https://myaccount.google.com/apppasswords)
   - Chọn "Mail" và thiết bị của bạn
   - Lưu lại mật khẩu 16 ký tự (ví dụ: `xxxx xxxx xxxx xxxx`)

2. **Cập nhật `.env`**:

   ```bash
   EMAIL_ENABLED=true
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_SMTP_USER=your_email@gmail.com
   EMAIL_SMTP_PASSWORD=xxxx xxxx xxxx xxxx
   EMAIL_FROM=your_email@gmail.com
   EMAIL_TO=admin1@example.com,admin2@example.com
   EMAIL_USE_TLS=true
   ```

##### Cấu hình SMTP Server khác

**Office 365 / Outlook:**

```bash
EMAIL_SMTP_HOST=smtp.office365.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
```

**Yahoo Mail:**

```bash
EMAIL_SMTP_HOST=smtp.mail.yahoo.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
```

**Custom SMTP:**

```bash
EMAIL_SMTP_HOST=mail.yourdomain.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
```

### Cấu hình Authentication & Authorization

#### Bật/Tắt Authentication

```bash
# Bật authentication (mặc định)
AUTH_ENABLED=true

# Tắt authentication (không yêu cầu login - chỉ dùng cho development)
AUTH_ENABLED=false
```

#### JWT & Session Settings

| Variable | Mặc định | Mô tả |
|----------|----------|-------|
| `JWT_SECRET_KEY` | change-me | Secret key cho JWT tokens (PHẢI thay đổi trong production) |
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | Thời gian hết hạn access token (24 giờ) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Thời gian hết hạn refresh token (30 ngày) |
| `SESSION_SECRET_KEY` | change-me | Secret key cho session cookie |
| `SESSION_COOKIE_NAME` | xpb_session | Tên session cookie |
| `SESSION_MAX_AGE` | 86400 | Thời gian sống của session (24 giờ) |

#### Default Admin Account

Khi khởi động lần đầu, hệ thống tự động tạo một admin account:

```bash
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=admin123
```

**⚠️ QUAN TRỌNG**: Thay đổi password ngay sau khi đăng nhập lần đầu!

#### User Management Settings

```bash
# Cho phép user tự đăng ký tài khoản
ALLOW_REGISTRATION=true

# Yêu cầu xác thực email (chưa implement)
REQUIRE_EMAIL_VERIFICATION=false
```

#### Single Sign-On (SSO) - Google

1. **Tạo OAuth 2.0 credentials:**
   - Truy cập [Google Cloud Console](https://console.cloud.google.com/)
   - Tạo project mới hoặc chọn project có sẵn
   - Vào **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **OAuth 2.0 Client ID**
   - Chọn **Web application**
   - Thêm Authorized redirect URIs:
     - Development: `http://localhost:8000/auth/google/callback`
     - Production: `https://yourdomain.com/auth/google/callback`
   - Lưu **Client ID** và **Client Secret**

2. **Cấu hình `.env`:**

```bash
GOOGLE_CLIENT_ID=123456789-abc123xyz.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz789
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

#### Single Sign-On (SSO) - Microsoft

1. **Đăng ký app trên Azure:**
   - Truy cập [Azure Portal](https://portal.azure.com/)
   - Vào **Azure Active Directory** > **App registrations**
   - Click **New registration**
   - Nhập tên app và chọn account type
   - Thêm Redirect URI (Web):
     - Development: `http://localhost:8000/auth/microsoft/callback`
     - Production: `https://yourdomain.com/auth/microsoft/callback`
   - Sau khi tạo, vào **Certificates & secrets** > **New client secret**
   - Lưu **Application (client) ID**, **Directory (tenant) ID**, và **Client Secret**

2. **Cấu hình `.env`:**

```bash
MICROSOFT_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MICROSOFT_CLIENT_SECRET=abc123~xyz789.def456
MICROSOFT_TENANT_ID=common
MICROSOFT_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback
```

**Tenant ID:**

- `common` - Cho phép tất cả Microsoft accounts (personal + organizational)
- `organizations` - Chỉ organizational accounts
- `consumers` - Chỉ personal Microsoft accounts
- `{tenant-id}` - Chỉ một organization cụ thể

#### API Authentication

**Với Bearer Token (JWT):**

```bash
# Get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }

# Use token in API requests
curl http://localhost:8000/api/backups \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Refresh Token:**

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

## 📖 Sử dụng

### Đăng nhập

1. **Truy cập trang login**: `http://localhost:8000/login`

2. **Đăng nhập với tài khoản mặc định**:
   - Email: `admin@example.com`
   - Password: `admin123`

3. **SSO Login**:
   - Click **Google** hoặc **Microsoft** button
   - Đăng nhập với tài khoản SSO
   - Tự động tạo user mới nếu chưa tồn tại

4. **Đăng ký tài khoản mới** (nếu `ALLOW_REGISTRATION=true`):
   - Click **Sign up** link
   - Nhập email, password, tên đầy đủ
   - Click **Create Account**

### Dashboard Overview

Sau khi đăng nhập, truy cập dashboard chính:

- **Cluster Status**: Hiển thị trạng thái các node (Leader, Replica, lag)
- **Recent Backups**: Danh sách backup gần đây với trạng thái
- **Disk Usage**: Theo dõi dung lượng backup đã sử dụng
- **Quick Actions**: Chạy backup/restore nhanh

### Quản lý Backup

#### Chạy Backup thủ công

1. Truy cập tab **Backups**
2. Chọn loại backup:
   - **Base Backup** (`pg_basebackup`): Full physical backup
   - **Logical Backup** (`pg_dump`): Logical backup theo database
3. Chọn database (nếu chạy pg_dump)
4. Click **Run Backup**

#### Xem lịch sử Backup

- Tab **Backups** hiển thị tất cả backup đã chạy
- Thông tin: Thời gian, kích thước, trạng thái, thời gian chạy
- Lọc theo loại backup, database, trạng thái

### Restore Database

#### Restore từ pg_dump

1. Truy cập tab **Restore**
2. Chọn file backup từ danh sách
3. Nhập tên database đích
4. Chọn các tùy chọn:
   - **Drop existing**: Xóa database cũ trước khi restore
   - **Target host**: Node để restore (mặc định: Leader)
5. Click **Start Restore**

#### Restore từ pg_basebackup

Base backup dùng để restore toàn bộ cluster, cần thực hiện manual trên server:

```bash
# Stop PostgreSQL
systemctl stop postgresql

# Restore data directory
rm -rf /var/lib/postgresql/16/main/*
tar -xzf /var/backups/postgresql/basebackup_2024-01-15_020000/base.tar.gz \
    -C /var/lib/postgresql/16/main/

# Set permissions
chown -R postgres:postgres /var/lib/postgresql/16/main

# Start PostgreSQL
systemctl start postgresql
```

### Cấu hình Job Scheduler

1. Truy cập tab **Jobs**
2. Xem danh sách scheduled jobs hiện tại
3. Chỉnh sửa cron expression để thay đổi lịch
4. Tắt job bằng cách bỏ tick "Enabled"
5. Chạy thủ công job bất kỳ với nút **Run Now**

### Xem Job History

Tab **Jobs** > **History** hiển thị:

- Lịch sử chạy tất cả jobs
- Trạng thái (success/failed)
- Thời gian bắt đầu/kết thúc
- Log details

## 🔌 API Endpoints

Hệ thống cung cấp REST API cho tích hợp và automation.

### Web UI Routes

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/` | GET | Dashboard tổng quan |
| `/login` | GET | Trang login |
| `/backups` | GET | Trang quản lý backup |
| `/restore` | GET | Trang quản lý restore |
| `/jobs` | GET | Trang quản lý job scheduler |
| `/settings` | GET | Trang cấu hình |

### Authentication APIs

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/auth/register` | POST | Đăng ký tài khoản mới |
| `/auth/login` | POST | Đăng nhập với email/password |
| `/auth/logout` | POST | Đăng xuất |
| `/auth/refresh` | POST | Refresh access token |
| `/auth/me` | GET | Thông tin user hiện tại |
| `/auth/google/login` | GET | Đăng nhập với Google SSO |
| `/auth/google/callback` | GET | Google OAuth callback |
| `/auth/microsoft/login` | GET | Đăng nhập với Microsoft SSO |
| `/auth/microsoft/callback` | GET | Microsoft OAuth callback |
| `/auth/users` | GET | Danh sách users (admin only) |
| `/auth/users/{id}` | DELETE | Xóa user (admin only) |

### Cluster APIs

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/cluster/status` | GET | Trạng thái cluster từ Patroni |
| `/api/cluster/databases` | GET | Danh sách databases |

### Backup APIs

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/backups` | GET | Danh sách backup records |
| `/api/backups/run` | POST | Chạy backup mới |
| `/api/backups/disk` | GET | Danh sách backup trên disk |
| `/api/verify` | GET | Verify tất cả backup |

**Example - Chạy pg_dump:**

```bash
curl -X POST http://localhost:8000/api/backups/run \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "pgdump",
    "database": "mydb"
  }'
```

**Example - Chạy pg_basebackup:**

```bash
curl -X POST http://localhost:8000/api/backups/run \
  -H "Content-Type: application/json" \
  -d '{
    "backup_type": "basebackup"
  }'
```

### Restore APIs

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/restore/available` | GET | Danh sách backup có thể restore |
| `/api/restore/run` | POST | Chạy restore operation |

**Example - Restore database:**

```bash
curl -X POST http://localhost:8000/api/restore/run \
  -H "Content-Type: application/json" \
  -d '{
    "dump_file": "/var/backups/postgresql/pg_dump/2024-01-15_030000/mydb_backup_2024-01-15_030000.dump",
    "target_database": "mydb_restored",
    "drop_existing": false
  }'
```

### Job APIs

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/jobs/schedules` | GET | Danh sách job schedules |
| `/api/jobs/schedules/{id}` | PUT | Cập nhật job schedule |
| `/api/jobs/run/{name}` | POST | Chạy job thủ công |
| `/api/jobs/history` | GET | Lịch sử chạy jobs |

**Example - Chạy cleanup job:**

```bash
curl -X POST http://localhost:8000/api/jobs/run/cleanup
```

### Disk APIs

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/api/disk` | GET | Thông tin disk usage |
| `/api/cleanup` | POST | Xóa backup cũ theo retention policy |

## 🚢 Deployment

### Ansible Deployment (Khuyến nghị cho Production)

Ansible role được cung cấp trong `deploy/ansible/` để tự động hóa deployment.

#### Bước 1: Copy role vào Ansible project

```bash
cp -r deploy/ansible/ /path/to/your/ansible/roles/x-postgres-backup/
```

#### Bước 2: Tạo inventory

```yaml
# inventory/production.yml
backup_servers:
  hosts:
    backup01:
      ansible_host: 10.10.10.50
      ansible_user: root
```

#### Bước 3: Tạo playbook

```yaml
# playbooks/deploy-backup.yml
---
- name: Deploy x-postgres-backup
  hosts: backup_servers
  become: yes
  roles:
    - role: x-postgres-backup
      vars:
        app_version: "latest"
        patroni_nodes: "10.10.10.11:8008,10.10.10.12:8008,10.10.10.13:8008"
        pg_password: "{{ vault_pg_password }}"
        pg_replication_password: "{{ vault_pg_replication_password }}"
        backup_dir: "/var/backups/postgresql"
        telegram_enabled: true
        telegram_bot_token: "{{ vault_telegram_bot_token }}"
        telegram_chat_id: "{{ vault_telegram_chat_id }}"
```

#### Bước 4: Chạy deployment

```bash
ansible-playbook -i inventory/production.yml playbooks/deploy-backup.yml
```

### Systemd Service (Linux Production)

#### Bước 1: Tạo systemd service file

```bash
sudo cp deploy/systemd/x-postgres-backup.service /etc/systemd/system/
sudo nano /etc/systemd/system/x-postgres-backup.service
```

#### Bước 2: Reload và start service

```bash
# Reload systemd daemon
sudo systemctl daemon-reload

# Enable service để tự khởi động
sudo systemctl enable x-postgres-backup

# Start service
sudo systemctl start x-postgres-backup

# Kiểm tra status
sudo systemctl status x-postgres-backup

# Xem logs
sudo journalctl -u x-postgres-backup -f
```

### Docker Deployment

#### Docker Compose (Đơn giản nhất)

```bash
# Clone và cấu hình
git clone https://github.com/xdev-asia-labs/x-postgres-backup.git
cd x-postgres-backup
cp .env.example .env
nano .env

# Start containers
docker compose up -d

# Xem logs
docker compose logs -f

# Stop containers
docker compose down
```

#### Docker Standalone

```bash
# Build image
docker build -t x-postgres-backup:latest .

# Run container
docker run -d \
  --name x-postgres-backup \
  -p 8000:8000 \
  -v /var/backups/postgresql:/var/backups/postgresql \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  x-postgres-backup:latest

# Xem logs
docker logs -f x-postgres-backup
```

## 🏗️ Architecture

### Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Frontend**: Jinja2 + HTMX + Tailwind CSS (CDN)
- **Scheduler**: APScheduler (cron-like scheduling)
- **Database**: SQLite (local state tracking)
- **HTTP Client**: httpx (async Patroni API calls)
- **Notifications**: aiosmtplib (Email), httpx (Telegram)

### Project Structure

```
x-postgres-backup/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration loader
│   ├── database.py          # SQLAlchemy setup + session management
│   ├── models.py            # Database models (BackupRecord, JobHistory, JobSchedule)
│   ├── scheduler.py         # APScheduler integration + job definitions
│   │
│   ├── routers/
│   │   ├── api.py           # REST API endpoints
│   │   └── dashboard.py     # HTML dashboard routes (SSR)
│   │
│   ├── services/
│   │   ├── backup.py        # pg_basebackup + pg_dump operations
│   │   ├── restore.py       # pg_restore operations
│   │   ├── cluster.py       # Patroni REST API client
│   │   ├── verify.py        # Backup integrity verification
│   │   └── notification.py  # Telegram & Email notification service
│   │
│   ├── static/
│   │   └── css/
│   │       └── style.css    # Custom CSS (extends Tailwind)
│   │
│   └── templates/           # Jinja2 HTML templates
│       ├── base.html        # Base template layout
│       ├── dashboard.html   # Dashboard overview
│       ├── backups.html     # Backup management
│       ├── restore.html     # Restore management
│       ├── jobs.html        # Job scheduler
│       └── settings.html    # Settings page
│
├── deploy/
│   ├── ansible/             # Ansible role cho automated deployment
│   │   ├── defaults/
│   │   │   └── main.yml      # Default variables
│   │   ├── handlers/
│   │   │   └── main.yml      # Service handlers
│   │   ├── tasks/
│   │   │   └── main.yml      # Deployment tasks
│   │   └── templates/
│   │       ├── env.j2        # .env template
│   │       └── x-postgres-backup.service.j2  # Systemd service
│   │
│   └── systemd/
│       └── x-postgres-backup.service  # Systemd unit file
│
├── data/                    # SQLite database directory (created at runtime)
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore
├── LICENSE
└── README.md
```

## � CI/CD & Release

### GitHub Actions Workflows

Project sử dụng 3 workflow tự động:

| Workflow | Trigger | Chức năng |
|----------|---------|----------|
| **CI** | Push/PR → `main` | Lint (Ruff), test, build Docker image |
| **Build & Push** | Push → `main`, tag `v*` | Build multi-arch (amd64/arm64) và push lên Docker Hub + GHCR |
| **Release** | Push → `main` | Semantic versioning tự động, tạo GitHub Release, push release image |

### Semantic Versioning

Version được tạo tự động dựa trên [Conventional Commits](https://www.conventionalcommits.org/):

| Commit prefix | Release type | Ví dụ |
|---------------|-------------|-------|
| `feat:` | Minor (0.**1**.0) | `feat: add SSO login` |
| `fix:` | Patch (0.0.**1**) | `fix: bcrypt compatibility` |
| `perf:` | Patch | `perf: optimize backup query` |
| `feat!:` hoặc `BREAKING CHANGE:` | Major (**1**.0.0) | `feat!: new API schema` |

Các commit `docs:`, `style:`, `chore:`, `ci:`, `test:` **không** tạo release mới.

### Cấu hình Secrets

Thêm vào **Settings → Secrets and variables → Actions** của GitHub repo:

**Secrets:**

| Secret | Mô tả |
|--------|--------|
| `DOCKERHUB_TOKEN` | Docker Hub Access Token |

**Variables:**

| Variable | Mô tả |
|----------|--------|
| `DOCKERHUB_USERNAME` | Docker Hub username |

> `GITHUB_TOKEN` được cung cấp tự động bởi GitHub Actions, không cần cấu hình.

### Docker Images

Sau khi push lên `main`, image sẽ được publish tại:

```bash
# Docker Hub
docker pull <dockerhub-username>/x-postgres-backup:latest
docker pull <dockerhub-username>/x-postgres-backup:1.2.3

# GitHub Container Registry
docker pull ghcr.io/xdev-asia-labs/x-postgres-backup:latest
docker pull ghcr.io/xdev-asia-labs/x-postgres-backup:1.2.3
```

### Quy trình Release

```
git commit -m "feat: add backup encryption"   →  v1.1.0 (minor)
git commit -m "fix: restore timeout issue"     →  v1.1.1 (patch)
git commit -m "feat!: new REST API v2"          →  v2.0.0 (major)
git commit -m "docs: update README"             →  no release
```

## �🐛 Troubleshooting

### Server không khởi động được

**Lỗi: `ModuleNotFoundError: No module named 'app'`**

```bash
# Đảm bảo bạn đang ở thư mục root của project
cd /path/to/x-postgres-backup

# Và virtual environment đã được activate
source venv/bin/activate
```

**Lỗi: `Permission denied` khi tạo backup**

```bash
# Kiểm tra quyền truy cập thư mục backup
ls -la /var/backups/postgresql

# Cấp quyền cho user đang chạy service
sudo chown -R $USER:$USER /var/backups/postgresql
sudo chmod -R 755 /var/backups/postgresql
```

### Không kết nối được với Patroni

**Lỗi: `No cluster leader found`**

1. Kiểm tra Patroni nodes có đang chạy:

   ```bash
   curl http://10.10.10.11:8008/patroni
   ```

2. Kiểm tra cấu hình `PATRONI_NODES` trong `.env`:

   ```bash
   PATRONI_NODES=10.10.10.11:8008,10.10.10.12:8008,10.10.10.13:8008
   ```

3. Nếu Patroni có authentication, bật và cấu hình:

   ```bash
   PATRONI_AUTH_ENABLED=true
   PATRONI_AUTH_USERNAME=your_username
   PATRONI_AUTH_PASSWORD=your_password
   ```

### pg_basebackup thất bại

**Lỗi: `FATAL: no pg_hba.conf entry for replication`**

Cần thêm entry trong `pg_hba.conf` của PostgreSQL:

```bash
# Thêm vào pg_hba.conf
host    replication    replicator    <backup_server_ip>/32    md5

# Reload PostgreSQL
sudo systemctl reload postgresql
```

**Lỗi: `pg_basebackup: command not found`**

```bash
# Kiểm tra PostgreSQL client tools đã được cài:
which pg_basebackup

# Nếu chưa có, cài đặt:
# Ubuntu/Debian:
sudo apt install postgresql-client-16

# RHEL/CentOS:
sudo yum install postgresql16

# Cập nhật PG_BIN_DIR trong .env
PG_BIN_DIR=/usr/bin  # hoặc đường dẫn chính xác
```

### Notification không hoạt động

**Telegram không nhận được thông báo:**

1. Kiểm tra bot token và chat ID:

   ```bash
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
   ```

2. Test gửi message:

   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>&text=Test message"
   ```

**Email không gửi được:**

1. Test SMTP connection:

   ```bash
   telnet smtp.gmail.com 587
   ```

2. Với Gmail, đảm bảo:
   - Đã bật 2-Step Verification
   - Sử dụng App Password (không phải mật khẩu Gmail thường)
   - Allow less secure apps (nếu cần)

3. Kiểm tra logs:

   ```bash
   # Docker
   docker compose logs -f | grep -i "email\|smtp"
   
   # Systemd
   sudo journalctl -u x-postgres-backup -f | grep -i "email\|smtp"
   ```

### Database SQLite bị lock

**Lỗi: `database is locked`**

```bash
# Stop service
sudo systemctl stop x-postgres-backup

# Xóa lock file
rm -f data/backup_manager.db-wal data/backup_manager.db-shm

# Start service
sudo systemctl start x-postgres-backup
```

### Disk đầy do backup

```bash
# Kiểm tra disk usage
df -h /var/backups/postgresql

# Chạy cleanup thủ công
curl -X POST http://localhost:8000/api/cleanup

# Hoặc xóa backup cũ thủ công
find /var/backups/postgresql -type f -mtime +7 -delete
```

## 📊 Monitoring & Logs

### Xem Logs

**Development (venv):**

```bash
# Logs hiển thị trực tiếp trên terminal
# hoặc redirect vào file
uvicorn app.main:app --log-config logging.yaml > logs/app.log 2>&1
```

**Docker:**

```bash
# Real-time logs
docker compose logs -f

# Logs của một service cụ thể
docker compose logs -f x-postgres-backup

# Lọc logs
docker compose logs | grep -i "error\|backup"
```

**Systemd:**

```bash
# Real-time logs
sudo journalctl -u x-postgres-backup -f

# Logs từ thời điểm cụ thể
sudo journalctl -u x-postgres-backup --since "2024-01-15 10:00:00"

# Lọc theo mức độ
sudo journalctl -u x-postgres-backup -p err
```

### Metrics & Monitoring

Kết hợp với monitoring tools:

**Prometheus:**

- Expose metrics endpoint (có thể mở rộng)
- Scrape từ `/metrics`

**Grafana:**

- Import dashboard template
- Visualize backup trends, success rate, duration

**Nagios/Icinga:**

- Check API endpoint health
- Alert on backup failures

## 🤝 Contributing

Contributions are welcome! Vui lòng:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📝 License

MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

## 🔗 Links

- **Repository**: <https://github.com/xdev-asia-labs/x-postgres-backup>
- **Issues**: <https://github.com/xdev-asia-labs/x-postgres-backup/issues>
- **Patroni Documentation**: <https://patroni.readthedocs.io/>
- **PostgreSQL Documentation**: <https://www.postgresql.org/docs/>

## ✨ Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [HTMX](https://htmx.org/) - High power tools for HTML
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [Patroni](https://github.com/patroni/patroni) - PostgreSQL HA solution

---

Made with ❤️ by [xdev.asia](https://xdev.asia)
