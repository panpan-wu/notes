## install

- 下载 envoy，将 envoy 拷贝到 /usr/local/bin
- 下载 envoy_hot_restarter.py 并拷贝到 /usr/local/bin

/etc/systemd/system/envoy.service

```
[Unit]
Description=Envoy
Wants=network-online.target
After=network-online.target

[Service]
User=root
Group=root
Type=simple
ExecStart=/usr/local/bin/envoy_hot_restarter.py /usr/local/bin/envoy_start.sh
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

/etc/logrotate.d/envoy

```
/var/log/envoy/*.log {
	daily
	missingok
	rotate 14
	compress
	delaycompress
	notifempty
	nocreate
	sharedscripts
	postrotate
		systemctl reload envoy
	endscript
}
```
