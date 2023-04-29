- [HPB 使用指南](#hpb-使用指南)
  - [概览](#概览)
    - [示例01: Hello World](#示例01-hello-world)
    - [示例02: built-in variables](#示例02-built-in-variables)
      - [示例解析](#示例解析)
  - [附录1-内建变量列表](#附录1-内建变量列表)

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

当前目录结果如上所示, 仅有一个 `hello.c` 和 `build.yml`. 这个例子十分简单, 而且并不通用(比如在 Windows 下, 如果用户没有安装 MinGW 之类的工具, 这个命令是执行不了的), 在开始运行之前, 让我们先看一下 `build.yml`  
* 第 1 行: `name: hello` 指定了 yaml 的名称
* 第 2 行: `jobs` 是 `hpb` 任务的开始, 它的子节点是一系列的任务
* 第 3 行: `build` 是单个任务的名称, `hpb` 当中任务名称并没有限制, 你可以让任务叫做 `build`, `package`, `upload`, 也可以叫做 `foo`, `bar` 或 `baz`, 但是能表达任务所进行的工作显然是更好的
* 第 4 行: `steps` 表示从这里开始, 是此任务的步骤, 它的子节点们应该是列表
* 第 5 行: `- run: gcc hello.c -o hello`
  * 这里要注意, 本行开头的第一个字符为 `-`, 表示它是 yaml 列表中的一个元素
  * 这个 `run` 表示要执行的命令
  * `gcc hello.c -o hello` 执行生成任务, 生成名为 hello 的可执行文件

现在, 让我们进入目录并执行命令 `hpb build -c`, 可以看到当前生成了一个名为 hello 的可执行文件(没有 gcc 命令的环境会执行失败)

### 示例02: built-in variables
现在让我们来扩展一下上一小节的示例, 为了让我们的程序可以在任何平台上运行, 这次我们使用 CMake 或 meson 来生成工程, 你可以在两者之中挑选一个你熟悉的工具继续进行  

<div>
<details>
<summary>Example02 CMake</summary>

[example02_cmake](../../examples/example02_cmake)
```
example02
├── src
│   └── hello.c
├── CMakeLists.txt
└── build.yml
```

这次, 我们调整了一下目录结构, 将 `hello.c` 放进了 src 当中, 增加了一个 `CMakeLists.txt` 文件, 接着我们更改一下 `build.yml`  

[build.yml](../../examples/example02/cmake_build.yml)
```yaml {.line-numbers}
...
- run: >
    cmake \
      -S ${HPB_SOURCE_PATH} \
      -B ${HPB_BUILD_DIR} \
      -DCMAKE_INSTALL_PREFIX=${HPB_OUTPUT_DIR}
      -DCMAKE_BUILD_TYPE=release;
    cmake --build ${HPB_BUILD_DIR} --config release;
    cmake --build ${HPB_BUILD_DIR} --config release --target install;
```

现在进入 [example02_cmake](../../examples/example02_cmake) 运行 `hpb build -c build.yml`, 编译结束之后, 可以在 `example02_cmake/build/_hpb/output/bin/` 中看到我们生成的结果 `hello`

 
</detail>
</div>

<div>
<details>
<summary>Example02 Meson</summary>

[example02_meson](../../examples/example02_meson)
```
example02
├── src
│   └── hello.c
│── meson.build
└── meson_build.yml
```

这次, 我们调整了一下目录结构, 将 `hello.c` 放进了 src 当中, 增加了一个 `meson.build` 文件, 接着我们更改一下 `build.yml`  

[build.yml](../../examples/example02/build.yml)
```yaml {.line-numbers}
...
- run: >
    meson setup ${HPB_BUILD_DIR} \
      --prefix ${HPB_OUTPUT_DIR} \
      --buildtype release;
    meson compile -C ${HPB_BUILD_DIR};
    meson install -C ${HPB_BUILD_DIR};
```

现在进入 [example02_meson](../../examples/example02_meson) 运行 `hpb build -c build.yml`, 编译结束之后, 可以在 `example02_meson/build/_hpb/output/bin/` 中看到我们生成的结果 `hello`
 
</detail>
</div>
  
#### 示例解析
在这个示例中, 使用 CMake/Meson 构建时, 指定目录过程中使用了 `${HPB_SOURCE_PATH}`, `${HPB_BUILD_DIR}` 和 `${HPB_OUTPUT_DIR}` 变量, 它们都是 `hpb` 的内建变量  
* `${HPB_SOURCE_PATH}`: 代表项目所在路径, 在本例是当前的工作目录 (之后还会看到, 可以通过配置源码信息, 使得 `${HPB_SOURCE_PATH}` 不为当前工作目录)
* `${HPB_BUILD_DIR}`: 推荐使用的编译路径, 默认会为用户自动生成 (当然用户也可以自己指定目录, 但是之后会了解到, `hpb build` 有两种模式, 使用 `${HPB_BUILD_DIR}` 是更加方便的做法)
* `HPB_OUTPUT_DIR`: 编译后本地输出路径, 强烈推荐将 `CMAKE_INSTALL_PREFIX` 设置为此路径(而不是直接安装到系统/用户目录当中), 方便之后的打包操作

**注意: 在 `hpb` 当中, 所有的变量均以 `${xxx}` 的形式来指定, `$xxx` 和 `$(xxx)` 在 `hpb` 中并不是一个变量, 它们会被认为是普通的字符串**  

除了这里展示几个变量之外, `hpb` 还有许多内建变量, 它们均以 `HPB_` 开头, 具体内建变量列表详见: [附录1-内建变量列表](#附录1-内建变量列表)  

## 附录1-内建变量列表
| 名称 | 描述 |
| ---- | ---- |
| HPB_ROOT_DIR | workflow 初始的工作目录 |
| HPB_TASK_DIR | 为本任务分配的目录. <br>当 mode=dev 时, 为 `${HPB_BUILD_DIR}/build/_hpb` <br>当 mode=task 时, 为 `${HPB_ROOT_DIR}/_hpb/生成的task目录`  |
| HPB_BUILD_DIR | 构建目录, 建议用户使用此目录作为构建目录 |
| HPB_PKG_DIR | 打包后放置的目录 |
| HPB_DEPS_DIR | 依赖库所在目录 <br>如果用户使用 cmake, 建议将此目录加入 CMAKE_PREFIX_PATH 当中 |
| HPB_TEST_DEPS_DIR | 测试使用的依赖库所在的目录 <br>如果用户使用 cmake, 建议将此目录加入 CMAKE_PREFIX_PATH 当中 |
| HPB_OUTPUT_DIR | 输出目录 <br>如果用户使用 cmake, 建议将 CMAKE_INSTALL_PREFIX 设置为此目录 |
| HPB_FILE_DIR | 被执行的配置文件所在目录 |
| HPB_FILE_NAME | 被执行的配置文件的名称 |
| HPB_FILE_PATH | 被执行的配置文件的路径 |
| HPB_TASK_NAME | 任务名称, 即 `hpb build --task-name` 所指定的名称 |
| HPB_TASK_ID | 任务 id, 即 `hpb build --task-id` 所指定的 id |
| HPB_PLATFORM_SYSTEM | 系统名称: linux, windows, darwin ... |
| HPB_PLATFORM_RELEASE | 平台的 release 信息 |
| HPB_PLATFORM_VERSION | 平台的版本信息 |
| HPB_PLATFORM_MACHINE | 机器机器类型: AMD64, x86_64 ... |
| HPB_PLATFORM_DISTR | 当为 linux 时, 为发行版信息 <br>当为 windows 时, 代表版本号 |
| HPB_PLATFORM_LIBC | 平台默认的 libc 信息 |
| HPB_SOURCE_PATH | source 所在路径 |
| HPB_GIT_REF | 若 HPB_ROOT_DIR 是 git 工程中的目录, 那么 HPB_GIT_REF 会按以下优先级被指定: git tag > git commit_id  |
| HPB_GIT_TAG | source 所在目录的 git tag |
| HPB_GIT_COMMIT_ID | source 所在目录的 git commit id |
| HPB_GIT_BRANCH | source 所在目录的 git branch 名称 |