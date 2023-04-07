- [LPB](#lpb)
  - [使用帮助](#使用帮助)
  - [全局配置文件](#全局配置文件)
  - [使用指南](#使用指南)


# LPB
LPB(local package builder)是一个本地包构建辅助工具
* 可以作为 CI 的本地执行器
* 也可以用于本地编译源码的辅助工具; 如果你使用的是c/c++, 并且也总是喜欢从源码开始编译, 以及想要清晰的管理本地代码和库文件, 而不是当需要依赖某个库时使用 `apt install` 或 `vcpkg.exe install` 来搞定依赖库, 那么相信 `lpb` 会是一个趁手的工具

## 使用帮助
可以使用 `lpb -h` 来查看帮助, 当前 `lpb` 支持下面几个子命令  
* build: 用于解析 yaml 文件, 进行构建流程

而每个子命令, 也可以使用 `lpb [command] -h` 来查看帮助信息

## 全局配置文件
默认情况下, `lpb` 会读取以下目录中的 settings.xml 文件, 并依次加载文件中的设置信息 (如 制品搜索目录, 日志输出等级设置等)
* 用户目录: `~/.lpb/settings.xml`
* 用户 local 目录: `~/.local/share/lpb/settings.xml`
* 系统目录: `/etc/lpb/settings.xml`

具体的 `settings.xml` 配置, 可参考 [settings.xml](./etc/settings.xml)

## 使用指南
用户可以通过 [使用指南](./doc/cn/user_guide.md), 来一步一步的逐渐了解如何使用 `lpb` 进行简单的构建任务.  
如果想要将 `lpb` 作为 CI 的本地执行器使用, 可以参考一下 [作为 CI 执行器使用](./doc/cn/as_ci_executor.md) 文档.  
最后, 如果想要将 `lpb` 作为管理本地代码和库文件的辅助工具, 那么可以看一下 [本地库管理](./doc/cn/local_lib_manager.md) 文档.  
