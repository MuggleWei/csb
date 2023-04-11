- [HPB](#hpb)
  - [使用帮助](#使用帮助)
  - [使用指南](#使用指南)
  - [全局配置文件](#全局配置文件)


# HPB
HPB(Happy Package Builder)是一个包构建辅助工具
* 可以作为 CI 的本地执行器
* 更有趣的, 它也可以用于本地源码编译和制品库管理的辅助工具; 如果你使用的是c/c++, 并且也总是喜欢从源码开始编译, 想要清晰的管理本地代码和库文件, 而不是当需要依赖某个库时使用 `apt install` 或 `vcpkg.exe install` 来搞定依赖库, 那么相信 `hpb` 会是一个趁手的工具

## 使用帮助
可以使用 `hpb -h` 来查看帮助, 当前 `hpb` 支持下面几个子命令  
* build: 解析 yaml 配置文件, 进行构建流程
* upload: 上传编译好的库
* search: 搜索库文件

而每个子命令, 也可以使用 `hpb [command] -h` 来查看帮助信息

## 使用指南
用户可以通过 [使用指南](./doc/cn/user_guide.md), 来一步一步的逐渐了解如何使用 `hpb` 进行简单的构建任务.  
如果想要将 `hpb` 作为 CI 的本地执行器使用, 可以参考一下 [作为 CI 执行器使用](./doc/cn/as_ci_executor.md) 文档.  
最后, 如果想要将 `hpb` 作为管理本地代码和库文件的辅助工具, 那么可以看一下 [本地库管理](./doc/cn/local_lib_manager.md) 文档.  

## 全局配置文件
默认情况下, `hpb` 会读取以下目录中的 settings.xml 文件, 并依次加载文件中的设置信息 (如 制品搜索目录, 日志输出等级设置等)
* 用户目录: `~/.hpb/settings.xml`
* 用户 local 目录: `~/.local/share/hpb/settings.xml`
* 系统目录: `/etc/hpb/settings.xml`

具体的 `settings.xml` 配置, 可参考 [settings.xml](./etc/settings.xml)
