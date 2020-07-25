# 文件描述符限制调整

这篇文章讲的很详细：

https://www.linuxtechi.com/set-ulimit-file-descriptors-limit-linux-servers/

下面是用 ubuntu18 进行的实验，不保证其它系统可用。

## 调整系统级别限制

/etc/sysctl.conf

```
fs.file-max=262144
```

用下列命令让更改生效（不需要重启）：

```
sysctl -p
```

下列命令会立即更改 file-max 大小（重启后会失效）：

```
sysctl -w fs.file-max=262144
```

/etc/sysctl.conf 是系统级别的限制，即整个系统打开的文件描述符总数不能超过这个值。

用下列命令查看调整是否生效：

```
cat /proc/sys/fs/file-max
```

## 调整 systemd 服务限制

/etc/systemd/system.conf

```
DefaultLimitNOFILE=131072
```

/etc/systemd/user.conf

```
DefaultLimitNOFILE=131072
```

调整后需要重启系统。

这个调整会影响 systemd 管理的服务，比如 syslog、nginx、supervisor 等。要查看 nginx 是否生效，我们可以重启 nginx，然后用下列命令查看：

```
cat /proc/{nginx_master_pid}/limits
cat /proc/{nginx_worker_pid}/limits
```

其它服务可以用类似方式进行查看。

## 查看调整是否生效的命令总结

下列命令查看系统级别限制：

```
cat /proc/sys/fs/file-max
```

下列命令查看某个进程的限制：

```
cat /proc/{pid}/limits
```

下列命令查看当前所有的系统参数：

```
sysctl -a
```

## 调整针对用户（或用户组）的限制

/etc/security/limits.conf

```
* hard nofile 131072
* soft nofile 131072
root hard nofile 131072
root soft nofile 131072
```

目前发现这个调整只有登录时才生效，比如 ssh 连接到远程机器的时候。对于 /etc/init.d 里的服务，这个更改没有效果。网上有些地方说要加下列配置，但是这些配置的效果是什么还需要进一步验证。

/etc/pam.d/common-session

```
session required pam_limits.so
```

/etc/pam.d/common-session-noninteractive

```
session required pam_limits.so
```
