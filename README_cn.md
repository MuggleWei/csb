# LPB
LPB(local package builder)是一个本地包构建辅助工具, 可以作为 CI 的本地执行器, 也可以用于本地编译源码的辅助工具  

## 使用帮助
可以使用 `lpb -h` 来查看帮助, 当前 `lpb` 支持下面几个子命令  
* build: 用于解析 yaml 文件, 进行构建流程

而每个子命令, 也可以使用 `lpb [command] -h` 来查看帮助信息

## build 子命令

### build 子命令 - 使用
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

### build 子命令 - 配置文件
`lpb build` 使用 yaml 配置文件, 基本的结构如下
```
name: Hello
jobs:
  job0:
    needs: [job1]
    steps:
      - name: echo
        run: >
          echo "before echo";
          echo "0";
          echo "after echo";
  job1:
    steps:
      - name: echo
        run: >
          echo "before echo";
          echo "1";
          echo "after echo";
```
如果你熟悉 github action 亦或是 gitlab ci 应该就很容易理解上面的文件了  
对于 lpb 来说, 层级关系是 `workflow > job > step > action`  
* 每个配置文件包含一个 workflow, 它有两个参数
	* name: workflow 的名称
	* jobs: workflow 要执行的任务列表, 包含了一系列的 job
* 每个 job 的名称可以随意取, 但不要重复, job 包含了以下属性
	* needs: 本任务所依赖的任务列表
	* steps: 本任务要执行的步骤, 包含了一系列的 step
* 每个 step 代表了一个步骤, 包括了以下属性
	* name: 本步骤的名称
	* run: 本步骤要执行的 action
* 每个 action 代表了一个命令

### build 子命令 - 变量
在 build 子命令使用当中提到, 可以用过 `-p` 或 `--param` 来向配置文件传参, 我们以构建 `googletest` 作为例子来说明  
googletest.yml  
```
name: Local Build
jobs:
  build:
    steps:
      - name: download
        run: >
          cd ${LPB_TASK_DIR};
          git clone --depth=1 --branch=${GIT_TAG} https://github.com/google/googletest.git;
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
      - name: package
        run: >
          cd ${LPB_TASK_DIR}/googletest/usr;
          tar -czvf googletest-${GIT_TAG}-${BUILD_TYPE}.tar.gz ./*;
          mv googletest-${GIT_TAG}-${BUILD_TYPE}.tar.gz ${LPB_OUTPUT_DIR};
```
执行命令: `lpb build -c googletest.yml -p GIT_TAG=v1.13.0 -p BUILD_TYPE=release -o ./_artifacts`  
可以看到, 我们通过 `-p`, 向配置文件中传递了参数 `GIT_TAG` 和 `BUILD_TYPE`.   

除此之外, 还可以看见一些以 `LPB_` 开头的变量, 这是 `lpb` 自带的变量, 有以下这些
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


## 默认配置文件
默认情况下, `lpb` 会读取以下目录中的 settings.xml 文件, 并依次加载文件中的设置信息 (如制品搜索目录)
* 用户目录: `~/.lpb/settings.xml`
* 用户 local 目录: `~/.local/share/lpb/settings.xml`
* 系统目录: `/etc/lpb/settings.xml`
