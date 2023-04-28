- [HPB 使用指南](#hpb-使用指南)
  - [概览](#概览)
    - [示例01: Hello World](#示例01-hello-world)
    - [示例02: var](#示例02-var)

# HPB 使用指南
在开始阅读本指南时, 请先确认 `hpb` 已正确安装, 如果尚未安装, 可以跳转至 [安装](../../README_cn.md#安装) 文档查看  

## 概览
本使用指南是一个实操型指南, 通过从一个简单的例子开始, 一步一步的扩展为一个较为复杂的工程. 所用的示例都可以在 [examples](../../examples/) 目录中找到  

### 示例01: Hello World
不能免俗的, 让我们从一个打印 `hello world` 的程序开始吧.  

[example01](../../examples/example01)
```
example01
├── build.yml
└── hello.c
```

hello.c
```c {.line-numbers}
#include <stdio.h>

int main()
{
    printf("hello, world\n");
    return 0;
}
```

build.yml
```yaml {.line-numbers}
name: hello
jobs:
  build:
    steps:
      - run: gcc hello.c -o hello
```

当前目录结果如上所示, 仅有一个 `hello.c` 和 `build.yml`. 这个例子十分简单, 而且并不通用(比如在 Windows 下, 用户没有安装 MinGW 之类的工具, 这个命令是执行不了的), 在开始运行之前, 让我们先看一下 `build.yml`  
* 第 1 行: `name: hello` 指定了 yaml 的名称
* 第 2 行: `jobs` 是 `hpb` 任务的开始, 它的子节点是一系列的任务
* 第 3 行: `build` 是单个任务的名称, `hpb` 当中任务名称并没有限制, 你可以让任务叫做 `build`, `package`, `upload`, 也可以叫做 `foo`, `bar` 或 `baz`, 但是能表达任务所进行的工作显然是更好的
* 第 4 行: `steps` 表示从这里开始, 是此任务的步骤, 它的子节点们应该是列表
* 第 5 行: `- run: gcc hello.c -o hello`
  * 这里要注意, 本行开头的第一个字符为 `-`, 表示它是 yaml 列表中的一个元素
  * 这个 `run` 表示要执行的命令
  * `gcc hello.c -o hello` 执行生成任务, 生成名为 hello 的可执行文件

现在, 让我们进入目录并执行命令 `hpb build -c`, 可以看到当前生成了一个名为 hello 的可执行文件(没有 gcc 命令的环境会执行失败)

### 示例02: var