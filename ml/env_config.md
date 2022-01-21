# install docker

```
curl https://get.docker.com | sh \
  && sudo systemctl --now enable docker
```

# nvidia

```
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
   && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
   && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
```

```
sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
sudo docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

# 修改 docker 源

/etc/docker/daemon.json

```
{
  "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]
}
```

```
sudo systemctl restart docker
```

- Docker 官方中国区: https://registry.docker-cn.com
- 网易: http://hub-mirror.c.163.com
- 中国科学技术大学: https://docker.mirrors.ustc.edu.cn
- 阿里云: https://<你的ID>.mirror.aliyuncs.com

# ubuntu 源

```
sed -i s@/archive.ubuntu.com/@/mirrors.tuna.tsinghua.edu.cn/@g /etc/apt/sources.list
```

# python 源

```
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

# conda 源

```
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/ \
    && conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/ \
    && conda config --set show_channel_urls yes
```

# pytorch

```
docker pull pytorch/pytorch:1.10.0-cuda11.3-cudnn8-runtime
```

# mac docker

mac docker 默认分配的内存较小，有可能会导致构建 image 时失败，可以点击 docker 图标 -> 设置 -> Resources 进行调整。

# docker save load

save

```
docker image save wenet:2021-11-09 -o ~/Data/docker_images/wenet:2021-11-09.tar
```

load

```
docker image load -i ~/Data/docker_images/wenet:2021-11-09.tar
```
