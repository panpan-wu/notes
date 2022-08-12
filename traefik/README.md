# traefik + docker swarm + rsyslog

对中小公司来说，traefik + docker swarm + rsyslog 或许是一种不错的部署方案。

## docker swarm 集群搭建

待补充

## 启动 traefik

配置文件见：traefik/docker-compose.yaml

7000 端口用来提供项目服务，7001 端口是 traefik 的监控服务。要改监控服务的密码，修改这下列行：

```
traefik.http.middlewares.api-basic-auth.basicauth.users=asr:$$apr1$$4PGVT4gZ$$F1.SBl9/BMDntDZf9M3UN/
```

用下列命令启动服务：

```bash
docker stack deploy traefik -c docker-compose.yaml
```

## 启动项目

示例配置文件见：demo/docker-compose.yaml

这个只是示例配置，无法启动。

labels 部分演示了如何将服务暴露给 traefik，在这个例子中，访问 http://127.0.0.1:7000/demo/submit_task 就能访问到服务，注意 7000 端口是 traefik 暴露的端口，见 traefik/docker-compose.yaml 文件。

logging 部分演示了如何把 log 写入到 rsyslog 服务，一般来说系统已经安装了 rsyslog。

## rsyslog 配置

/etc/rsyslog.conf

```
# provides TCP syslog reception
module(load="imtcp")
input(type="imtcp" port="514")

# Filter duplicated messages 这里我们不过滤重复消息
$RepeatedMsgReduction off
```

/etc/rsyslog.d/10-default.conf

```
# 这个 APP-NAME 就是 docker logging 中设置的 tag
template(name="outpath_default" type="string"
         string="/var/log/projs/%APP-NAME%.log")

template(name="outfmt" type="list" option.jsonf="on") {
    property(outname="@timestamp" name="timereported" dateformat="rfc3339" format="jsonf")
    property(outname="app_name" name="app-name" format="jsonf")
    property(outname="hostname" name="hostname" format="jsonf")
    property(outname="message" name="msg" format="jsonf")
}

if ($syslogfacility-text == 'local0') then {
    action(type="omfile" dynaFile="outpath_default" template="outfmt")
    stop
}
```

创建 projs 目录

```
makedir /var/log/projs
chown syslog:adm /var/log/projs
```

log 滚动更新

/etc/logrotate.d/rsyslog_projs

```
/var/log/projs/*.log
{
        rotate 7
        daily
        missingok
        notifempty
        delaycompress
        compress
        postrotate
                /usr/lib/rsyslog/rsyslog-rotate
        endscript
}
```
