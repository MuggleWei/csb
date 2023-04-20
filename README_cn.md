- [HPB](#hpb)
  - [使用帮助](#使用帮助)
  - [安装](#安装)
    - [从源码安装](#从源码安装)
      - [Unix类系统](#unix类系统)
      - [Windows系统](#windows系统)
  - [使用指南](#使用指南)
  - [全局配置文件](#全局配置文件)


# HPB
HPB(Happy Package Builder) 是一个包管理工具, 同时也可以作为一个 CI 本地执行器使用  

* 主要解决包的存储, 以及依赖包的获取问题, 和语言无关
* 不会侵入你的构建工具, 当你使用 c/c++ 时, 无论使用的是 CMake, Meson, Makefile 或 Ninja, 都可以轻松的使用 `hpb` 来管理依赖包
* 去中心化, 用户可以在没有服务器的情况下, 在本地管理自己的源码和包

## 使用帮助
可以使用 `hpb -h` 来查看帮助, 当前 `hpb` 支持下面几个子命令  
* build: 解析 yaml 配置文件, 进行构建流程
* pack: 打包库文件
* push: 上传库文件 (当前暂时只支持上传至本地的制品库目录)
* pull: 拉取库文件 (当前暂时只支持拉取本地的制品库)
* search: 搜索库文件

而每个子命令, 也可以使用 `hpb [command] -h` 来查看帮助信息

## 安装

### 从源码安装
首先确保 python 已安装, 并且 python-pip 可以正常使用, 通过下面命令来检查是否已经正确安装
```
python --verion
python -m pip --version
```

**Unix类系统**  
确保 `~/.local/bin` 在 PATH 中, 接着执行项目根目录中的脚本 `install.sh`  

**Windows系统**  
执行项目根目录中的脚本 `install.bat`  

执行完安装脚本之后, 通过以下命令检测是否安装成功
```
hpb -v
```

## 使用指南
当你已经成功完成了安装工作, 可以通过 [入门指南](./doc/cn/user_guide.md), 来一步一步的逐渐了解如何使用 `hpb`, 本指南将会让你学到 `hpb` 的一些基本概念和用法.  
当你已经完成了 [入门指南](./doc/cn/user_guide.md) 的阅读, 并且想要使用 `hpb` 来管理本地的制品库以及编译源码 c/c++ 时自动引入依赖, 那么可以看一下 [使用 hpb 来辅助开发](./doc/cn/dev_with_hpb.md)

## 全局配置文件
默认情况下, `hpb` 会读取以下目录中的 settings.xml 文件, 并依次加载文件中的设置信息 (如 制品搜索目录, 日志输出等级设置等)
* 用户目录: `~/.hpb/settings.xml`
* 用户 local 目录: `~/.local/share/hpb/settings.xml`
* 系统目录: `/etc/hpb/settings.xml`

具体的 `settings.xml` 配置, 可参考 [settings.xml](./etc/settings.xml)
