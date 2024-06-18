# 违章监管系统

违章监管系统旨在通过软件设计和多线程技术，提供高效、实时的违章行为监控和管理解决方案。本系统基于PyQt5框架，结合UDP通信协议，实现数据的高速传输和处理。系统主要功能模块包括：数据接收与处理、数据存储、界面显示、边缘设备控制及视频流处理。

## 主要功能模块

1. **数据接收与处理**：通过多线程技术，实现对多种违章信息的并发接收。接收到的信息包括person_ID、违章类别、违章图像等。
2. **数据存储**：使用MySQL数据库存储和管理违章信息，确保数据的持久化和安全性。
3. **界面显示**：利用Qt Designer设计用户界面，提供直观的违章记录和图像查看功能。
4. **边缘设备控制**：用户可以通过界面控制边缘设备，例如开关灯光，发送控制指令。
5. **视频流处理**：独立线程接收边缘设备传输的视频流，确保视频处理的实时性和流畅性。

## 系统设计

- **多线程技术**：提高系统的并发处理能力。
- **UDP通信协议**：实现数据的高速传输。
- **PyQt5框架**：提供图形用户界面设计。
- **MySQL数据库**：存储和管理违章信息。

## 安装说明

### 环境配置

确保已安装Python 3.8以上版本，并安装以下依赖包：

```bash
pip install -r requirements.txt
```

`requirements.txt` 文件内容如下：

```
PyQt5==5.15.4
openpyxl==3.0.7
numpy==1.19.5
requests==2.25.1
opencv-python==4.5.1.48
```

### 项目结构

```
yolov8_edge/
│
├── main.py                     # 主程序入口
├── db.py                       # 数据库操作模块
├── utils/
│   ├── datasets.py             # 数据集加载模块
│   └── CustomMessageBox.py     # 自定义消息框
├── dialog/
│   └── rtsp_win.py             # RTSP 地址输入窗口
├── main_win/
│   └── win5.py                 # 主窗口 UI
├── config/
│   └── ip.json                 # 存放 RTSP 地址的配置文件
├── requirements.txt            # 项目依赖文件
└── README.md                   # 项目说明文件

```

## 配置数据库

确保已安装 MySQL，并创建相应的数据库和表。运行以下命令创建数据库：

```sql
CREATE DATABASE record;
USE record;

CREATE TABLE records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    time DATETIME NOT NULL,
    person_count INT NOT NULL,
    classes VARCHAR(255) NOT NULL,
    image VARCHAR(255) NOT NULL
);

CREATE TABLE records_svn (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(255) NOT NULL,
    class_num INT NOT NULL
);

CREATE TABLE records_sum (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sv INT NOT NULL,
    sh INT NOT NULL,
    svh INT NOT NULL
);
```

## 配置数据库连接

在 `db.py` 文件中设置数据库连接参数：

```python
host = "localhost"
user = "root"
password = "123456789"
database = "record"
```

## 配置IP地址和端口

在 `main.py` 文件中设置你的IP地址和端口：

```python
# 替换为你的本地 IP 地址和目标端口
ip = 'http://192.168.1.101:8000/'
target_ip = "192.168.1.101"
target_port = 11451
```

## 使用说明

1. 确保MySQL数据库服务已启动，并已创建所需的数据库和表。
2. 启动主程序：

```bash
python main.py
```

3. 使用界面查看违章记录、控制设备、查看视频流等。

---

这个README文档提供了详细的安装、配置和使用说明，帮助用户快速上手您的违章监管系统项目。
