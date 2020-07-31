# ALB ELB\_5XXs 排查

## ALB 状态码说明

- HTTP 5XXs 是 target group 返回的 5XX
- HTTP 4XXs 是 target group 返回的 4XX
- ELB 5XXs 表示请求并未完成（可能原因：1. 未能成功和 target group 建立连接 2. target group 提前关闭了连接），这个状态码是 ELB 记录的状态码
- ELB 4XXs 表示请求并未完成（可能原因：客户端的请求有问题，ALB 直接返回了错误，并没有向 target group 转发请求），这个状态码是 ELB 记录的状态码
- HTTP 500s + HTTP 502s + HTTP 503s + HTTP 504s = ELB 5XXs

AWS 文档：https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html

## ALB 开启 access logs 的方法

https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-logging-bucket-permissions

## ALB access logs 分析

分析各个状态码数量：

```
gzcat *.gz | awk '{print $9}' | sort | uniq -c
```

结果：

```
1841798 200
5416 400
  29 401
  34 404
 115 405
 218 408
 229 460
 168 502
```

将异常请求保存到文件：

```
gzcat *.gz | awk '{if($9=="400"){print $0}}' > 400.txt
gzcat *.gz | awk '{if($9=="401"){print $0}}' > 401.txt
gzcat *.gz | awk '{if($9=="404"){print $0}}' > 404.txt
gzcat *.gz | awk '{if($9=="405"){print $0}}' > 405.txt
gzcat *.gz | awk '{if($9=="408"){print $0}}' > 408.txt
gzcat *.gz | awk '{if($9=="460"){print $0}}' > 460.txt
gzcat *.gz | awk '{if($9=="502"){print $0}}' > 502.txt
```

## nginx 状态码

log 格式:

```
    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent $request_length "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for" '
                      '"$http_x_amzn_trace_id" $http_content_length '
                      '"$host" '
                      '$request_time $upstream_response_time $upstream_connect_time $upstream_header_time';
```

其中 http\_x\_amzn\_trace\_id 是 ALB 添加的唯一 log 标识，用这个字段可以将 ALB logs 与 nginx logs 对应起来。

log 分析：

```
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c
```

```
8828760 200
  33809 400
      6 403
     29 404
      7 405
   1134 408
    391 499
      8 500
```

将异常请求保存到文件：

```
awk '{if($9=="408"){print $0}}' /var/log/nginx/access.log > logs/408.txt
awk '{if($9=="499"){print $0}}' /var/log/nginx/access.log > logs/499.txt
awk '{if($9=="500"){print $0}}' /var/log/nginx/access.log > logs/500.txt
```

为了探究 nginx 状态码的触发条件，写了一个简单的 http 服务：

```python
import time

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    print('start sleep')
    time.sleep(100)
    print('end sleep')
    return 'Hello, World!'


if __name__ == "__main__":
    app.run(debug=True)
```

nginx 配置: /etc/nginx/conf.d/default.conf

```
server {
    listen       80;

    #charset koi8-r;
    #access_log  /var/log/nginx/host.access.log  main;

    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:5000;
    }
}
```

408 触发条件：telnet localhost 80 然后输入 POST / HTTP/1.1 等待即可，最终 nginx 会记录一条 408 的 log。

```
127.0.0.1 - - [30/Jul/2020:03:48:16 +0000] "POST / HTTP/1.1" 408 0 "-" "-" "-" "" 48.815 - - -
```

499 触发条件：curl localhost，然后 ctrl + c 中断 curl，nginx 报了一条 499 的 log。

```
127.0.0.1 - - [30/Jul/2020:02:42:28 +0000] "GET / HTTP/1.1" 499 0 "-" "curl/7.58.0" "-"
```

502 触发条件：curl localhost 然后关闭 web 服务，nginx 记录了 502 的 log。

```
127.0.0.1 - - [30/Jul/2020:02:46:40 +0000] "GET / HTTP/1.1" 502 157 "-" "curl/7.58.0" "-"
```

504 触发条件：curl localhost 然后等待自然超时，nginx 记录了 504 的 log。

```
127.0.0.1 - - [30/Jul/2020:02:44:46 +0000] "GET / HTTP/1.1" 504 167 "-" "curl/7.58.0" "-"
```

简单总结一下：

- 408：客户端在规定时间内未能传输完整的 http header 或 http body。这个规定时间由 nginx 的 client\_header\_timeout、client\_body\_timeout 参数控制。
- 499：在请求尚未完成时客户端主动关闭了连接。
- 502: 后端服务在请求尚未完成时关闭了连接。
- 504：后端服务在规定时间内未能返回 response。这个规定时间由 nginx 的 keepalive\_timeout 参数控制。

## ALB HTTP502 与 nginx 状态码对应关系

ALB 状态码 AWS 官方说明：https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html

对 502 的说明摘录如下：

```
HTTP 502: Bad gateway
Possible causes:

The load balancer received a TCP RST from the target when attempting to establish a connection.

The load balancer received an unexpected response from the target, such as "ICMP Destination unreachable (Host unreachable)", when attempting to establish a connection. Check whether traffic is allowed from the load balancer subnets to the targets on the target port.

The target closed the connection with a TCP RST or a TCP FIN while the load balancer had an outstanding request to the target. Check whether the keep-alive duration of the target is shorter than the idle timeout value of the load balancer.

The target response is malformed or contains HTTP headers that are not valid.

The load balancer encountered an SSL handshake error or SSL handshake timeout (10 seconds) when connecting to a target.

The deregistration delay period elapsed for a request being handled by a target that was deregistered. Increase the delay period so that lengthy operations can complete.

The target is a Lambda function and the response body exceeds 1 MB.

The target is a Lambda function that did not respond before its configured timeout was reached.
```

在我们的场景里，ALB 502 是由 nginx 408 导致的：客户端在规定时间未能传输完 http header 或 http body，然后 nginx 主动关了连接，这时 ALB 就会记录一个 502。解决办法：将 nginx 的 client\_header\_timeout、client\_body\_timeout 和 keepalive\_timeout 设为 300（需要大于 ALB idle timeout，idle timeout 默认是 60s），这样连接会由 ALB 关闭，nginx 会报 499，ALB 会报 408。这样只是转移了 5XX 错误（从 502 变成了 408），要真正解决问题还需要看客户端为什么会超时（可能是网不好）。

关于 timeout 设为 300 的说明：设为 80 发现 nginx 仍然有可能会报 408，这时 ALB 报 502，所以设了一个比 60 大的多的值。
