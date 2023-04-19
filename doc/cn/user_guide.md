- [HPB 使用指南](#hpb-使用指南)
  - [hpb build](#hpb-build)
    - [hpb build - 使用](#hpb-build---使用)
    - [hpb build - hello world](#hpb-build---hello-world)
    - [hpb build - 变量赋值](#hpb-build---变量赋值)
    - [hpb build - 变量值覆盖](#hpb-build---变量值覆盖)
    - [hpb build - 内建变量](#hpb-build---内建变量)
    - [hpb build - 多任务依赖](#hpb-build---多任务依赖)
    - [hpb build - workflow的结构](#hpb-build---workflow的结构)
    - [hpb build - 现实中的例子](#hpb-build---现实中的例子)
  - [更多](#更多)


# HPB 使用指南
在开始阅读本指南时, 请先确认 `hpb` 已正确安装, 如果尚未安装, 可以跳转至 [安装](../../README_cn.md#安装) 文档查看  

## hpb build

### hpb build - 使用
通过 `hpb build -h` 可以查看 `build` 的子命令参数
```
  -c, --config string     [REQUIRED] build config file
  -m, --mode string       [OPTIONAL] dev or task, use dev by default
    , --task-name string  [OPTIONAL] build task name, if empty, use config file without suffix as task-name
    , --task-id string    [OPTIONAL] build task id, if empty, set 'yyyymmddHHMMSSxxxx' as task-id
    , --work-dir string   [OPTIONAL] working directory(by default, use current working directory)
  -p, --param list        [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456
  -s, --settings string   [OPTIONAL] manual set settings.xml
```
* -c, --config: 用于指定构建使用的 yaml 文件
* -m, --mode: 指定当前的构建模式, 当前可选模式为 dev 或 task, 默认情况为 dev.  
  * 不同的模式本质是相同的, 只是生成的目录结构有所区别
  * 当使用 dev 模式时, 生成的 `hpb` 目录结构会全部在 `build/_hpb` 目录下
  * 当使用 task 模式时, 会为每次构建生成不同的目录
* --task-name: 指定本次构建的任务名称, 如果没有指定, 将会使用配置文件去掉后缀名作为任务名称. **此参数仅在 task 模式下生效**
* --task-id: 指定本次构建的任务 id, 当没有设定时,使用当前时间的 `yyyymmddHHMMSSxxxx` 格式作为任务 id. 如果调用者想要自己指定 id, 我们建议调用者确保相同的任务名称下, 任务 id 应该是唯一的. **此参数仅在 task 模式下生效**
* --work-dir: 指定本次任务的工作目录, 默认情况下是当前的工作目录
* -p, --param: 设置构建参数
* -s, --settings: 额外指定配置文件

### hpb build - hello world
看了上面的命令 `help` 之后, 是否觉得有些抽象呢？ 不用担心，让我们通过一个简单的例子来展示 `hpb build` 的使用  
例1: [example01_hello/hello.yml](../../examples/example01_hello/hello.yml)
```
name: hello
jobs:
  job1:
    steps:
      - name: step1
        run: >
          echo "hello, world";
```
此时，在此文件的目录下运行: `hpb build -c hello.yml`, 会在屏幕上看到屏幕上打印出了一些日志
```
2023-04-18 23:49:56,340|root|INFO|builder.py:44 - hpb builder run task hello.20230418-234956-331565
2023-04-18 23:49:56,448|root|INFO|workflow_handle.py:264 - run job: job1
2023-04-18 23:49:56,449|root|INFO|workflow_handle.py:309 - run command: echo "hello, world"
COMMAND|echo "hello, world"
REAL_COMMAND|echo "hello, world"
STDOUT|"hello, world"
```
* 第 1 行代表开始运行名为 `hello.20230418-233339-791253` 的任务
* 第 2 行 `run job: job1` 表示开始运行任务 `job1`
* 第 3 行 `run command: echo "hello, world"` 则代表了要运行的命令
* 第 4, 5 行代表真实的执行了命令
* 最后一行 `STDOUT` 表示此行为命令的输出结果 `"hello, world"`

此时, 当前目录下还会生成一个 `build/_hpb` 目录, 现在暂时无须了解它的内容, 之后我们将会再此遇见它  

### hpb build - 变量赋值
上一小节我们运行了一个简单的例子, 它仅仅执行一个输出 "hello world" 的命令, 现在让我们来使用变量, 输出一些不同的内容
例2: [example02_var/var.yml](../../examples/example02_var/var.yml)
```
name: echo
variables:
  - foo: foo
jobs:
  job1:
    steps:
      - name: step1
        run: >
          echo "${foo}";
          echo "${bar}";
```
我们在文件中增加了 `varables` 分节, 并定义了变量 `foo`, 将其值设置为 `foo`. 此时, 我们进入目录并运行 `hpb build -c var.yml` 将会看到错误日志
```
......
2023-04-18 23:50:30,037|root|INFO|workflow_handle.py:309 - run command: echo "${bar}"
COMMAND|echo "${bar}"
2023-04-18 23:50:30,039|root|ERROR|workflow_handle.py:313 - failed replace variable in: echo "${bar}"
```
这是由于我们使用了变量 `${bar}`, 当却没有给 `bar` 变量赋过值. 我们可以像对待变量 `foo` 一样, 通过在 `variables` 当中增加对 `bar` 的赋值从而修复此错误.  
除此之外, 还可以直接通过命令传参来实现: `hpb build -c echo.yml -p bar="hello bar"`. 此时将会得到类似下面的输出
```
2023-04-18 23:51:20,480|root|INFO|workflow_handle.py:264 - run job: job1
2023-04-18 23:51:20,481|root|INFO|workflow_handle.py:309 - run command: echo "${foo}"
COMMAND|echo "${foo}"
REAL_COMMAND|echo "foo"
STDOUT|"foo"
2023-04-18 23:51:20,494|root|INFO|workflow_handle.py:309 - run command: echo "${bar}"
COMMAND|echo "${bar}"
REAL_COMMAND|echo "hello bar"
STDOUT|"hello bar"
```

**需要注意的是**: 在 `hpb` 当中, 变量只支持使用 `${xxx}` 来表示变量, 而 `$(xxx)` 和 `$xxx` 都并不会被 `hpb` 在使用中作为变量

### hpb build - 变量值覆盖
当同时在配置文件的 `variables` 分节以及命令行输入中定义了相同的变量, 则命令行的输入的值将会覆盖 `varaibles` 当中的赋值.  
`hpb build -c echo.yml -p foo="hello foo" -p bar="hello bar"`  
```
2023-04-18 23:53:06,250|root|INFO|workflow_handle.py:309 - run command: echo "${foo}"
COMMAND|echo "${foo}"
REAL_COMMAND|echo "hello foo"
STDOUT|"hello foo"
2023-04-18 23:53:06,270|root|INFO|workflow_handle.py:309 - run command: echo "${bar}"
COMMAND|echo "${bar}"
REAL_COMMAND|echo "hello bar"
STDOUT|"hello bar"
```

### hpb build - 内建变量
除了用户定义的变量之外, 还有一些 `hpb` 内建的变量  
例3: [examples/example03_inner_val](../../examples/example03_inner_var/inner_var.yml)
```
name: inner_var
variables:
  - curdir:
      default: "$(pwd)"
      windows: "%cd%"
jobs:
  job1:
    steps:
      - name: step1
        run: >
          echo "${HPB_ROOT_DIR}";
          echo ${curdir};
          cd "${HPB_TASK_DIR}";
          echo ${curdir};
```
运行 `hpb build -c inner_var.yml`, 我们将可以看到被打印出的目录信息, 这个配置文件中有两点值得关注
1. 变量 `curdir` 的值并没有直接设置, 而是根据系统的不同而不同
   * `default` 表示当没有精确匹配的系统时, 将 `curdir` 设置为 `"$(pwd)"`
   * `windows` 表示当系统为 `windows` 时, 将 `curdir` 设置为 `"%cd%"`
2. 可以看到 `HPB_ROOT_DIR` 和 `HPB_TASK_DIR`, 它们是 `hpb` 的内建变量, 在 `hpb` 脚本当中, 内建变量全部以 `HPB_` 打头, 所以用户在使用过程中, 尽量避免 `HPB_` 开头的变量, 以防冲突

除了上面看到的两个内建变量, 还有许多内建变量, 具体的见下表
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

如果用户愿意, 也可以通过命令行入参强行覆盖内建变量的值  

### hpb build - 多任务依赖
TODO:
到目前为止, 我们已经运行了一些很简单的例子, 它们仅仅包含了一个 `job`, 而这个 `job` 当中只有一个 `step`. 现在让我们稍微扩展一下, 假设我们有两个 `job`, 分别名为 `build` 和 `package`, 而 `package` 依赖于 `build`  
下面是一个名为 `deps.yml` 的文件
```
name: deps
variables:
  - foo: hello foo
jobs:
  package:
    needs: [build]
    steps:
      -name: package
        run: >
          tar -czvf hello.tar.gz hello.sh;
          mv hello.tar.gz ${HPB_OUTPUT_DIR};
  build:
    steps:
      - name: prepare
        run: >
          cd ${HPB_TASK_DIR};
          echo "Downloading source code";
      - name: build
        run: >
          echo "start compile";
          echo "compiling ...";
          echo "#!/bin/bash" >> hello.sh;
          echo "echo ${foo}" >> hello.sh;
          chmod u+x hello.sh;
          echo "mission completed";
```
这里特地在书写顺序上调换了 `build` 和 `package` 的位置, 但是注意, 在 `package` 当中, 有一行 `needs: [build]`, 这说明了 `package` 任务依赖于 `build` 的完成.  
现在让我们运行: `hpb build -c deps.yml -o ./_artifacts`  
可以看到如下的输出
```
2023-04-07 23:31:21,127|root|INFO|builder.py:129 - run job: build
2023-04-07 23:31:21,128|root|INFO|builder.py:168 - run command: cd ${HPB_TASK_DIR}
2023-04-07 23:31:21,128|root|INFO|builder.py:168 - run command: echo "Downloading source code"
Downloading source code
2023-04-07 23:31:21,133|root|INFO|builder.py:168 - run command: echo "start compile"
start compile
2023-04-07 23:31:21,139|root|INFO|builder.py:168 - run command: echo "compiling ..."
compiling ...
2023-04-07 23:31:21,145|root|INFO|builder.py:168 - run command: echo "#!/bin/bash" >> hello.sh
2023-04-07 23:31:21,150|root|INFO|builder.py:168 - run command: echo "echo ${foo}" >> hello.sh
2023-04-07 23:31:21,155|root|INFO|builder.py:168 - run command: chmod u+x hello.sh
2023-04-07 23:31:21,161|root|INFO|builder.py:168 - run command: echo "mission completed"
mission completed
2023-04-07 23:31:21,165|root|INFO|builder.py:129 - run job: package
2023-04-07 23:31:21,166|root|INFO|builder.py:168 - run command: tar -czvf hello.tar.gz hello.sh
hello.sh
2023-04-07 23:31:21,178|root|INFO|builder.py:168 - run command: mv hello.tar.gz ${HPB_OUTPUT_DIR}
```
通过上面日志, 我们看到 `run job: build` 确实先于 `run job: package` 被执行. 在上面的命令中, 我么们还指定了 `./_artifacts` 为输出目录, 因此, 你可以在 `./_artifacts` 当中看到构建的结果 `hello.tar.gz`

### hpb build - workflow的结构
到现在为止, 我们已经看到了 `hpb build` 所使用的 `yaml` 大致的模样了. 如果你使用过 github action 亦或是 gitlab ci 应该就很容易理解这种类型的文件结构.  
对于 hpb 来说, 层级关系是 `workflow > job > step > action`  
* 每个配置文件包含一个 workflow, 它有下面几个属性
	* name: workflow 的名称
	* variables: 用于在配置文件中自定义变量
	* source: 指定源码信息
	* artifacts: 指定制品信息
	* jobs: workflow 要执行的任务列表, 包含了一系列的 job
* 每个 job 的名称可以随意取, 但不要重复, job 包含了以下属性
	* needs: 本任务所依赖的任务列表
	* steps: 本任务要执行的步骤, 包含了一系列的 step
* 每个 step 代表了一个步骤, 包括了以下属性
	* name: 本步骤的名称
	* run: 本步骤要执行的 action
* 每个 action 代表了一个命令

### hpb build - 现实中的例子
下面我们使用 `hpb`, 来执行一下 `googletest` 的构建
```
name: googletest
variables:
  - GIT_TAG: v1.13.0
  - BUILD_TYPE: release
  - git_url: https://github.com/google/googletest.git
  - pkg_name: googletest-${GIT_TAG}-${BUILD_TYPE}
jobs:
  prepare:
    steps:
      - name: prepare
        run: >
          cd ${HPB_TASK_DIR};
          git clone --depth=1 --branch=${GIT_TAG} ${git_url};
  build:
    needs: [prepare]
    steps:
      - name: build
        run: >
          cd googletest;
          mkdir -p build;
          mkdir -p usr;
          cmake \
            -S . -B build \
            -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
            -DBUILD_SHARED_LIBS=ON \
            -DCMAKE_INSTALL_PREFIX=./usr;
          cmake --build ./build --target install;
  package:
    needs: [build]
    steps:
      - name: package
        run: >
          cd ${HPB_TASK_DIR}/googletest/usr;
          tar -czvf ${pkg_name}.tar.gz ./*;
          mv ${pkg_name}.tar.gz ${HPB_OUTPUT_DIR};
```
执行命令: `hpb build -c googletest.yml -p GIT_TAG=v1.13.0 -p BUILD_TYPE=release -o ./_artifacts`  
成功结束之后, 我们便可以在 `./_artifacts` 目录当中看到 `googletest-v1.13.0-release.tar.gz`

## 更多
如果想要更深入的了解 `hpb` 作为 CI 的本地执行器, 可以参考文档 [作为 CI 执行器使用](./as_ci_executor.md)  
如果想要将 `hpb` 作为管理本地代码和库文件的辅助工具, 那么可以参考文档 [本地库管理](./local_lib_manager.md)
