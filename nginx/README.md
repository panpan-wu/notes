# nginx

## nginx 常用配置

### proxy\_params

/etc/nginx/proxy\_params

```
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
```

### keepalive

/etc/nginx/conf.d/default.conf

```
upstream upstream_sample {
    server 127.0.0.1:8000;
    keepalive 100;
}

server {
    listen       80;

    location / {
        include proxy_params;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_pass http://upstream_sample;
    }
}
```

### 域名转发

/etc/nginx/nginx.conf

```
http {
    # dns 服务器地址及缓存时间
    # 地址可以用 cat /etc/resolv.conf 命令查询到
    # 缓存时间视情况合理配置
    resolver 127.0.0.53 valid=3s;
}
```

/etc/nginx/conf.d/default.conf

```
server {
    listen       80;

    # 这样可以让强制 nginx 做 dns 查询，防止 nginx 无限期缓存已经失效的 ip
    set $dn "your_domain";

    location / {
        include proxy_params;
        proxy_pass http://$dn;
    }

    location =/ {
        add_header Content-Type text/plain;
        return 200 "it works";
    }
}
```

#### nginx.conf

```
user  nginx;
worker_processes  auto;

error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;


events {
    worker_connections  8192;
}


http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    vhost_traffic_status_zone;
    client_max_body_size 100m;
    client_body_buffer_size 1024k;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for" '
                      '"$host" '
                      '$request_time $upstream_response_time $upstream_connect_time $upstream_header_time';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    # client_header_timeout 65;
    # client_body_timeout 65;
    keepalive_timeout  65;

    #gzip  on;

    include /etc/nginx/conf.d/*.conf;
}
```
