- [HPB 使用指南](#hpb-使用指南)
  - [概览](#概览)
    - [示例01: Hello World](#示例01-hello-world)
    - [示例02: built-in variables](#示例02-built-in-variables)
      - [示例解析](#示例解析)
    - [示例03: variables](#示例03-variables)
      - [示例解析](#示例解析-1)
    - [示例04: 依赖包](#示例04-依赖包)
    - [示例05: 构建自己的包](#示例05-构建自己的包)
      - [示例解析](#示例解析-2)
    - [示例06: Fat 包](#示例06-fat-包)
  - [附录1-内建变量列表](#附录1-内建变量列表)

# HPB 使用指南
在开始阅读本指南时, 请先确认 `hpb` 已正确安装, 如果尚未安装, 可以跳转至 [安装](../../README_cn.md#安装) 文档查看  

## 概览
本指南是一个实操型指南, 通过从一个简单的例子开始, 一步一步的扩展为一个较为复杂的工程. 所用的示例都可以在 [examples](../../examples/) 目录中找到  

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

当前目录结果如上所示, 仅有 `hello.c` 和 `build.yml`. 这个例子十分简单, 而且并不通用(比如在 Windows 下, 如果用户没有安装 MinGW 之类的工具, 这个命令是执行不了的), 在开始运行之前, 让我们先看一下 `build.yml`  
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

[build.yml](../../examples/example02_cmake/build.yml)
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

[build.yml](../../examples/example02_meson/build.yml)
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

### 示例03: variables
截至目前, 通过 CMake/Meson, 我们的 `hello, world` 已经可以运行在各个平台上了, 但是有一个问题: 我们在配置文件中, 直接将 build_type 设置为了 release, 这实在太不灵活了, 让我们继续改进上面的 `build.yml` 文件  

<div>
<details>
<summary>Example03 CMake</summary>

[build.yml](../../examples/example03_cmake/build.yml)
```yaml {.line-numbers}
name: hello
variables:
  - build_type: release
jobs:
  build:
    steps:
      - run: >
          cmake \
            -S ${HPB_SOURCE_PATH} \
            -B ${HPB_BUILD_DIR} \
            -DCMAKE_INSTALL_PREFIX=${HPB_OUTPUT_DIR}
            -DCMAKE_BUILD_TYPE=${build_type};
          cmake --build ${HPB_BUILD_DIR} --config ${build_type};
          cmake --build ${HPB_BUILD_DIR} --config ${build_type} --target install;
```
 
</detail>
</div>

<div>
<details>
<summary>Example03 Meson</summary>

[build.yml](../../examples/example03_cmake/build.yml)
```yaml {.line-numbers}
name: hello
variables:
  - build_type: release
jobs:
  build:
    steps:
      - run: >
          meson setup ${HPB_BUILD_DIR} \
            --prefix ${HPB_OUTPUT_DIR} \
            --buildtype ${build_type};
          meson compile -C ${HPB_BUILD_DIR};
          meson install -C ${HPB_BUILD_DIR};
```
 
</detail>
</div>

#### 示例解析
在此示例中, 我们添加了 `variables`, 它的子节点为变量列表. 当前将 `build_type` 的默认值设置为 `release`. 当我们没有额外提供任何选项时, 它的值将保持配置文件中的默认值.  
现在进入对应的目录, 运行 `hpb build -c build.yml -p build_type=debug`, 将编译 `debug` 版本. 我们通过 `build -p build_type=debug` 覆盖了文件中 `build_type` 的默认值

### 示例04: 依赖包
本节继续扩展我们的工程, 实现一个依赖 zlib 库, 用于压缩/解压单个文件的程序   
[hello.c](../../examples/example04_cmake/src/hello.c)
```c {.line-numbers}
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "zlib.h"

int compress_one_file(const char *input_filepath, const char *output_filepath)
{
	......
}

int decompress_one_file(const char *input_filepath, const char *output_filepath)
{
	......
}

int main(int argc, char *argv[])
{
	if (argc < 4) {
		fprintf(stderr,
			"Usage: %s <c|d> <in> <out>\n"
			"e.g\n"
			"\t%s c hello.c hello.c.gz\n",
			argv[0], argv[0]);
		exit(EXIT_FAILURE);
	}

	if (strcmp(argv[1], "c") == 0) {
		compress_one_file(argv[2], argv[3]);
	} else if (strcmp(argv[1], "d") == 0) {
		decompress_one_file(argv[2], argv[3]);
	} else {
		fprintf(stderr, "Unrecognized compress/decompress flag: %s\n",
			argv[1]);
		exit(EXIT_FAILURE);
	}

	return 0;
}
```
这个程序很简单, 通过第 2 个输入参数来判断是压缩或解压. 其中 `compress_one_file` 和 `decompress_one_file` 使用 zlib 实现压缩/解压文件的功能.  
接着我们更改 `hpb` 的配置文件, 增加对 zlib 的依赖  

```yaml {.line-numbers}
name: hello
variables:
  - build_type: release
deps:
  - name: zlib
    maintainer: madler
    tag: v1.2.13
jobs:
  ......
```
`deps` 是依赖项目列表, 其中每一个依赖都由 `name`, `maintainer` 和 `tag` 这三个字段唯一确定  

接着根据所使用的构建工具, 添加包搜索路径
<div>
<details>
<summary>Example04 CMake</summary>

[build.yml](../../examples/example04_cmake/build.yml)
```yaml {.line-numbers}
......
jobs:
  build:
    steps:
      - run: >
          cmake \
            -S ${HPB_SOURCE_PATH} \
            -B ${HPB_BUILD_DIR} \
            -DCMAKE_PREFIX_PATH=${HPB_DEPS_DIR} \
            -DCMAKE_INSTALL_PREFIX=${HPB_OUTPUT_DIR} \
            -DCMAKE_BUILD_TYPE=${build_type};
          cmake --build ${HPB_BUILD_DIR} --config ${build_type};
          cmake --build ${HPB_BUILD_DIR} --config ${build_type} --target install;
```
 
</detail>
</div>

此时在示例目录中运行 `hpb build -c build.yml`, 会看到错误提示:  
> failed find dep:  
> {  
> &nbsp;&nbsp;&nbsp;&nbsp;"maintainer": "madler",  
> &nbsp;&nbsp;&nbsp;&nbsp;"name": "zlib",  
> &nbsp;&nbsp;&nbsp;&nbsp;"tag": "v1.2.13"  
> }  
> failed search dependencies

这是因为在默认情况下, 当前配置文件并没有配置远程包管理库, 而本地包管理库中也没有 zlib. 所以当前有两个选择
* 本地生成 zlib 包, 并上传至本地包管理库当中
* 配置有 zlib 的远程包管理库 (暂未实现)

让我们先选择使用第一种方法: 生成本地 zlib 包.  
`hpb` 默认会安装一些较为常见的包编译的配置文件, 可以直接生成 zlib 包并上传至本地包管理库中
```
hpb build -m task -c ~/.hpb/share/modules/zlib/zlib.yml
```
在任意目录执行上述命令, 成功执行后, zlib 包将会被上传至本地包管理库当中. 执行 `hpb search -n zlib` 来查看 zlib 包是否成功被上传至本地包管理库当中
```
zlib
└── madler/zlib
```

此时回到示例目录中, 执行 `hpb build -c build.yml`, 便能成功生成程序

### 示例05: 构建自己的包
在上一小节当中, 我们已经在程序中添加了包的依赖, 使用 zlib 用于压缩/解压一个文件. 本节, 让我们将上一小节的函数放到自己的库当中, 当需要再次使用时, 我们只需依赖自己的包即可.  

1. 将 [example05](../../examples/example05_cmake) 拷贝至任意文件夹并重命名为 foo
2. 进入 foo, 执行
```
git init
git add .
git commit -m "init foo"
git tag v1.0.0
hpb build -c build.yml
```
3. 查看 foo 是否正确的被上传至了本地包管理库中
```
# 搜索名为 foo 的库
hpb search -n foo

# 搜索名为 foo, 维护者为 mugglewei 的库
hpb search -n foo -m mugglewei

# 搜索名为 foo, 维护者为 mugglewei 并且 tag 信息为 v1.0.0 的库
hpb search -n foo -m mugglewei -v v1.0.0
```

#### 示例解析
[build.yml](../../examples/example05_cmake/build.yml)
```
name: foo
variables:
  - build_type: release
source:
  name: foo
  maintainer: mugglewei
deps:
  - name: zlib
    maintainer: madler
    tag: v1.2.13
jobs:
  build:
    steps:
      - run: >
        ......
  package:
    needs: [build]
    steps:
      - run: >
          cd ${HPB_TASK_DIR};
          hpb pack;
  upload:
    needs: [package]
    steps:
      - run: >
          hpb push;
```
* 当前的 `hpb` 配置文件中, 在根节点中增加了一个 `source` 节点, 表明了当前包的名称以及维护者.
* 在 foo 目录中执行了 `git tag v1.0.0`, `hpb` 默认会读取目录的 git 信息, 来作为包的 tag
* 在配置文件中, `jobs` 节点下增加了 `package` 和 `upload` 步骤, 用于打包和上传包至配置文件指定的包管理库中
* 在 `package` 和 `upload` 步骤中, 有 `needs` 节点, 它声明了此任务的依赖任务

### 示例06: Fat 包
上一小节生成并上传了 foo 包, 现在让我们来使用它  

<div>
<details>
<summary>Example06 CMake</summary>

[build.yml](../../examples/example06_cmake/build.yml)
```yaml {.line-numbers}
name: hello
variables:
  - build_type: release
source:
  name: hello
  maintainer: mugglewei
deps:
  - name: foo
    maintainer: mugglewei
    tag: v1.0.0
jobs:
  build:
    steps:
      - run: >
          cmake \
            -S ${HPB_SOURCE_PATH} \
            -B ${HPB_BUILD_DIR} \
            -DCMAKE_PREFIX_PATH=${HPB_DEPS_DIR} \
            -DCMAKE_INSTALL_PREFIX=${HPB_OUTPUT_DIR} \
            -DCMAKE_BUILD_TYPE=${build_type};
          cmake --build ${HPB_BUILD_DIR} --config ${build_type};
          cmake --build ${HPB_BUILD_DIR} --config ${build_type} --target install;
  package:
    needs: [build]
    steps:
      - run: >
          cd ${HPB_TASK_DIR};
          hpb pack --copy-to ${HPB_ROOT_DIR}/_packages/;
```
 
</detail>
</div>

<div>
<details>
<summary>Example06 Meson</summary>

[build.yml](../../examples/example06_meson/build.yml)
```yaml {.line-numbers}
name: hello
variables:
  - build_type: release
source:
  name: hello
  maintainer: mugglewei
deps:
  - name: foo
    maintainer: mugglewei
    tag: v1.0.0
jobs:
  build:
    steps:
      - run: >
          meson setup ${HPB_BUILD_DIR} \
            --pkg-config-path ${HPB_DEPS_DIR}/lib/pkgconfig \
            --prefix ${HPB_OUTPUT_DIR} \
            --buildtype ${build_type};
          meson compile -C ${HPB_BUILD_DIR};
          meson install -C ${HPB_BUILD_DIR};
  package:
    needs: [build]
    steps:
      - run: >
          cd ${HPB_TASK_DIR};
          hpb pack --copy-to ${HPB_ROOT_DIR}/_packages/;
```
 
</detail>
</div>

在示例 06 中, 只需要添加依赖项 foo, 构建之后便会自动下载依赖的依赖. 本节并未将生成的包上传至本地包管理库中, 而是在 `hpb pack` 中, 将其拷贝至了示例目录的 `_packages` 文件夹中. 现在进入 `_packages` 目录, 解压 tar.gz 包, 将会发现其中只有 bin 目录, 这符合包的预期.  
但是如果你想要部署一个服务, 也许你希望得到一个 Fat 包(包中包含了其所有的依赖). 我们只需要稍微修改一下 yaml 文件即可.  
```
......
source:
  name: hello
  maintainer: mugglewei
deps:
  - name: foo
    maintainer: mugglewei
    tag: v1.0.0
build:
  fat_pkg: true
jobs:
  build:
......
```
在 yaml 文件中, 增加一个 `build` 节点, 并设置其子节点的 `fat_pkg` 为 `true`, 那么在打包时, 会自动将依赖及依赖的依赖全部打入包中

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
