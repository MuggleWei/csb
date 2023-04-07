- [LPB 使用指南](#lpb-使用指南)
  - [lpb build](#lpb-build)
    - [lpb build - 使用](#lpb-build---使用)
    - [lpb build - hello world](#lpb-build---hello-world)
    - [lpb build - 变量赋值](#lpb-build---变量赋值)
    - [lpb build - 变量值覆盖](#lpb-build---变量值覆盖)
    - [lpb build - 内建变量](#lpb-build---内建变量)
    - [lpb build - 多任务依赖](#lpb-build---多任务依赖)
    - [lpb build - workflow的结构](#lpb-build---workflow的结构)
    - [lpb build - 现实中的例子](#lpb-build---现实中的例子)
  - [更多](#更多)


# LPB 使用指南

## lpb build

### lpb build - 使用
通过 `lpb build -h` 可以查看 `build` 的子命令参数
```
  -c, --config string     [REQUIRED] build config file
    , --task-name string  [OPTIONAL] build task name, if empty, use config file without suffix as task-name
    , --task-id string    [OPTIONAL] build task id, if empty, set 'yyyymmddHHMMSSxxxx' as task-id
    , --work-dir string   [OPTIONAL] working directory(by default, use current working directory)
    , --art-dir list      [OPTIONAL] artifacts search directory, e.g. --art-dir=~/.local/
  -p, --param list        [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456
  -o, --output-dir string [OPTIONAL] output directory
```
* -c, --config: 用于指定构建使用的 yaml 文件
* --task-name: 指定本次构建的任务名称, 如果没有指定, 将会使用配置文件去掉后缀名作为任务名称
* --task-id: 指定本次构建的任务 id, 当没有设定时,使用当前时间的 `yyyymmddHHMMSSxxxx` 格式作为任务 id. 如果调用者想要自己指定 id, 我们建议调用者确保相同的任务名称下, 任务 id 应该是唯一的
* --work-dir: 指定本次任务的工作目录, 默认情况下是当前的工作目录
* --art-dir: 制品搜索目录, 默认情况下 `lpb` 会读取[默认配置文件](#默认配置文件), 并将文件中的 `artifacts/path` 依次加入制品搜索目录中
* -p, --param: 设置构建参数
* -o, --output-dir: 指定输出目录, 若没有设置, 默认情况下使用 `任务目录/output` 作为输出目录

### lpb build - hello world
让我们通过一个简单的例子来展示 `lpb build` 的使用  
下面是一个名为 `hello.yml` 的文件
```
name: hello
jobs:
  job1:
    steps:
      - name: step1
        run: >
          echo "hello world";
```
此时，在此文件的目录下运行: `lpb build -c hello.yml`, 会在屏幕上看到屏幕上打印出了一些日志
```
2023-04-07 22:38:11,769|root|INFO|builder.py:54 - lpb builder run task hello.20230407-223811-748754
2023-04-07 22:38:11,771|root|INFO|builder.py:168 - run command: echo "hello world"
hello world
```
* 第一行代表运行了名为 `hello.20230407-223811-748754` 的任务
* 第二行代表运行了命令 `echo "hello world"`
* 最后一行为命令的输出结果

同时, 当前目录下还多了一个 `_lpb` 目录, 在其中可以找到和上面任务同名的子目录, 这是 `lpb` 默认的用于执行任务生成的文件夹

### lpb build - 变量赋值
上一小节我们已经运行了一个简单的例子, 它仅仅执行一个输出 "hello world" 的命令, 现在让我们使用变量, 来根据每次运行的输入, 而输出不同的内容
下面是一个名为 `echo.yml` 的文件
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
我们在文件中增加了 `varables`, 并定义了变量 `foo`, 将其值设置为 `foo`. 此时, 我们直接运行 `lpb build -c echo.yml` 将会看到错误日志
```
2023-04-07 22:56:34,185|root|INFO|builder.py:168 - run command: echo "${foo}"
foo
2023-04-07 22:56:34,190|root|INFO|builder.py:168 - run command: echo "${bar}"
2023-04-07 22:56:34,190|root|ERROR|builder.py:297 - failed find variable value: bar
2023-04-07 22:56:34,190|root|ERROR|builder.py:171 - failed replace variable in: echo "${bar}"
```
这是由于我们使用了变量 `${bar}`, 当却没有给出定义.  
此时我们可以在 `variables` 当中增加 `bar` 的定义, 从而修复此错误. 或者我们可以直接通过命令传参来实现, 比如运行  
`lpb build -c echo.yml -p bar="hello bar"`  
可以看到日志正常输出, 这证明我们成功的指定了 `bar` 的值. 
```
2023-04-07 23:01:01,468|root|INFO|builder.py:168 - run command: echo "${foo}"
foo
2023-04-07 23:01:01,472|root|INFO|builder.py:168 - run command: echo "${bar}"
hello bar
```

### lpb build - 变量值覆盖
除了通过命令传参赋值之外, 我们还可以通过命令传参直接覆盖配置文件中变量的值. 比如我们通过命令参数设置 `foo` 的值  
`lpb build -c echo.yml -p foo="hello foo" -p bar="hello bar"`  
此时日志输出如下, 可以看到我们成功的通过命令传参覆盖了配置文件当中变量的值
```
2023-04-07 23:04:11,877|root|INFO|builder.py:168 - run command: echo "${foo}"
hello foo
2023-04-07 23:04:11,883|root|INFO|builder.py:168 - run command: echo "${bar}"
hello bar
```

### lpb build - 内建变量
除了用户定义的变量之外, 还有一些 `lpb` 内建的变量  
下面是一个名为 `inner_var.yml` 的文件
```
name: inner_var
jobs:
  job1:
    steps:
      - name: step1
        run: >
          echo "${LPB_ROOT_DIR}";
          echo "$(pwd)";
          echo "${LPB_TASK_DIR}";
          cd ${LPB_TASK_DIR};
          echo "$(pwd)";
```
运行 `lpb build -c inner_var.yml`, 我们将可以看到被打印出的目录信息, 以及当前目录(**注意, 这个例子中使用了 unix/linux 的命令 pwd, 所以在 windows 上直接运行是会报错的**)  

除了上面看到的两个内建变量, 还有许多内建变量, 它们都由 `LPB_` 开头, 具体的见下表
| 名称 | 描述 |
| ---- | ---- |
| LPB_ROOT_DIR | workflow 初始的工作目录 |
| LPB_TASK_DIR | 为本任务分配的目录, 用于日志输出, workflow 命令执行流输出等等 |
| LPB_OUTPUT_DIR | 建议使用的输出目录, 即 `lpb build -o` 所指定的目录 |
| LPB_FILE_DIR | 配置文件所在的目录 |
| LPB_TASK_NAME | 任务名称, 即 `lpb build --task-name` 所指定的名称 |
| LPB_TASK_ID | 任务 id, 即 `lpb build --task-id` 所指定的 id |
| LPB_GIT_REF | 若 LPB_ROOT_DIR 是 git 工程中的目录, 那么 LBP_GIT_REF 会按一下优先级被指定: git tag > git commit_id |
| LPB_GIT_TAG | 若 LPB_ROOT_DIR 是 git 工程中的目录, LBP_GIT_TAG 会被设置为当前的 git tag |
| LPB_GIT_COMMIT_ID | 若 LPB_ROOT_DIR 是 git 工程中的目录, LPB_GIT_COMMIT_ID 会被设置为当前的 git commit id |
| LPB_GIT_BRANCH | 若 LPB_ROOT_DIR 是 git 工程中的目录, LPB_GIT_BRANCH 会被设置为当前的 git branch 名称 |

当前的版本中, 用户可以强行覆盖内建变量的值, 但是极不建议这样做  

### lpb build - 多任务依赖
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
          mv hello.tar.gz ${LPB_OUTPUT_DIR};
  build:
    steps:
      - name: prepare
        run: >
          cd ${LPB_TASK_DIR};
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
现在让我们运行: `lpb build -c deps.yml -o ./_artifacts`  
可以看到如下的输出
```
2023-04-07 23:31:21,127|root|INFO|builder.py:129 - run job: build
2023-04-07 23:31:21,128|root|INFO|builder.py:168 - run command: cd ${LPB_TASK_DIR}
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
2023-04-07 23:31:21,178|root|INFO|builder.py:168 - run command: mv hello.tar.gz ${LPB_OUTPUT_DIR}
```
通过上面日志, 我们看到 `run job: build` 确实先于 `run job: package` 被执行. 在上面的命令中, 我么们还指定了 `./_artifacts` 为输出目录, 因此, 你可以在 `./_artifacts` 当中看到构建的结果 `hello.tar.gz`

### lpb build - workflow的结构
到现在为止, 我们已经看到了 `lpb build` 所使用的 `yaml` 大致的模样了. 如果你使用过 github action 亦或是 gitlab ci 应该就很容易理解这种类型的文件结构.  
对于 lpb 来说, 层级关系是 `workflow > job > step > action`  
* 每个配置文件包含一个 workflow, 它有下面几个属性
	* name: workflow 的名称
	* variables: 用于在配置文件中自定义变量
	* artifacts: 指定制品的基本信息
	* jobs: workflow 要执行的任务列表, 包含了一系列的 job
* 每个 job 的名称可以随意取, 但不要重复, job 包含了以下属性
	* needs: 本任务所依赖的任务列表
	* steps: 本任务要执行的步骤, 包含了一系列的 step
* 每个 step 代表了一个步骤, 包括了以下属性
	* name: 本步骤的名称
	* run: 本步骤要执行的 action
* 每个 action 代表了一个命令

### lpb build - 现实中的例子
下面我们使用 `lpb`, 来执行一下 `googletest` 的构建
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
          cd ${LPB_TASK_DIR};
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
          cd ${LPB_TASK_DIR}/googletest/usr;
          tar -czvf ${pkg_name}.tar.gz ./*;
          mv ${pkg_name}.tar.gz ${LPB_OUTPUT_DIR};
```
执行命令: `lpb build -c googletest.yml -p GIT_TAG=v1.13.0 -p BUILD_TYPE=release -o ./_artifacts`  
成功结束之后, 我们便可以在 `./_artifacts` 目录当中看到 `googletest-v1.13.0-release.tar.gz`

## 更多
如果想要更深入的了解 `lpb` 作为 CI 的本地执行器, 可以参考文档 [作为 CI 执行器使用](./as_ci_executor.md)  
如果想要将 `lpb` 作为管理本地代码和库文件的辅助工具, 那么可以参考文档 [本地库管理](./local_lib_manager.md)