- [HPB](#hpb)
  - [使用帮助](#使用帮助)
  - [安装](#安装)
    - [从源码安装](#从源码安装)
      - [Unix类系统](#unix类系统)
      - [Windows系统](#windows系统)
  - [使用指南](#使用指南)
  - [全局配置文件](#全局配置文件)


# HPB
HPB(Happy Package Builder)是一个包构建辅助工具
* 最基础的方面, 它可以作为 CI 的本地执行器
* 更有趣的, 它也可以用于本地源码和制品库管理的工具; 如果你使用的是c/c++, 总是喜欢自己从源码开始编译, 并且想要清晰的管理本地代码和库文件, 而不是当需要某个库时使用平台特定的 `apt install` 或 `pacman -S` 来搞定依赖库, 那么相信 `hpb` 会是一个趁手的工具  

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
首先确保 python 已安装, 并且 python-pip 和 python-venv 可以正常使用, 通过下面命令来检查是否已经正确安装
```
python --verion
python -m pip --version
python -m venv -h
```

接着, 根据不同的操作系统, 执行对应的安装脚本

#### Unix类系统
确保 `~/.local/bin` 在 PATH 中, 接着执行项目根目录中的脚本 `install.sh`  

#### Windows系统
执行 `install.bat`, 接着将 `dist/hpb/hpb.exe` 文件任意放入一个目录, 将此目录加入环境变量 Path 当中

## 使用指南
当你已经成功完成了安装工作, 可以通过 [入门指南](./doc/cn/user_guide.md), 来一步一步的逐渐了解如何使用 `hpb`, 本指南将会让你学到 `hpb` 的一些基本概念和用法.  
当你已经完成了 [入门指南](./doc/cn/user_guide.md) 的阅读, 并且想要使用 `hpb` 来管理本地的制品库以及编译源码 c/c++ 时自动引入依赖, 那么可以看一下 [使用 hpb 来辅助开发](./doc/cn/dev_with_hpb.md)

## 全局配置文件
默认情况下, `hpb` 会读取以下目录中的 settings.xml 文件, 并依次加载文件中的设置信息 (如 制品搜索目录, 日志输出等级设置等)
* 用户目录: `~/.hpb/settings.xml`
* 用户 local 目录: `~/.local/share/hpb/settings.xml`
* 系统目录: `/etc/hpb/settings.xml`

具体的 `settings.xml` 配置, 可参考 [settings.xml](./etc/settings.xml)
