* [readme EN](./README.md)
* [readme 中文](./README_cn.md)

# LPB
LPB(local package builder) is an auxiliary tools for local pacakge building, which can be used as a local executor for CI, or an auxiliary tool for locally compiling source code.

## help
Use `lpb -h` to show help doc, currently `lpb` supports the following subcommands
* build: parse yaml file and do build process

Every subcommands can use `lpb [command] -h` to show help information

## lpb build

### lpb build - usage
Use `lpb build -h` to show `build` command's doc
```
  -c, --config string     [REQUIRED] build config file
    , --task-name string  [OPTIONAL] build task name, if empty, use config file without suffix as task-name
    , --task-id string    [OPTIONAL] build task id, if empty, set 'yyyymmddHHMMSSxxxx' as task-id
    , --work-dir string   [OPTIONAL] working directory(by default, use current working directory)
    , --art-dir list      [OPTIONAL] artifacts search directory, e.g. --art-dir=~/.local/
  -p, --param list        [OPTIONAL] build parameters, e.g. --params foo=123 -p bar=456
  -o, --output-dir string [OPTIONAL] output directory
```
* -c, --config: Specify yaml file for current build
* --task-name: Specify the task name of current build. When not set, use config file without suffix as task-name
* --task-id: Specify the task id of current build. When not set, use the `yyyymmddHHMMSSxxxx` format of the current time as the task id. If the caller wants to specify the id by himself, we recommend that the caller ensure that under the same task name, the task id should be unique
* --work-dir: Specify the working directory of this task, the default is the current working directory
* --art-dir: Artifacts search directory, by default `lpb` will read [default settings file](#default settings file), and add `artifacts/path` in the file to the artifacts search directory in turn
* -p, --param: Set build arguments
* -o, --output-dir: Specify the output directory, if not set, use `{task_directory}/output` as the output directory by default

### lpb build - config file
`lpb build` use yaml file as config file, basic structure as following
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
If you are familiar with github action or gitlab ci, it should be easy to understand the above file  
For `lpb`, the hierarchical relationship is `workflow > job > step > action`
* Each configuration file contains a workflow, which has two parameters
	* name: workflow's name
	* jobs: workflow job list
* The name of each job can be chosen at will, but do not repeat, job contains the following parameters
	* needs: dependency job list
	* steps: step list to perform in this job
* Each step represent some action
	* name: step's name
	* run: action list in this step
* Each action is a command

### lpb build - varaible
As mentioned in the use of the build subcommand, `-p` or `--param` can be used to pass parameters to the configuration file. Let’s take building `googletest` as an example to illustrate
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
Exec: `lpb build -c googletest.yml -p GIT_TAG=v1.13.0 -p BUILD_TYPE=release -o ./_artifacts`  
As you can see, we passed the variable `GIT_TAG` and `BUILD_TYPE` to the configuration file through `-p`  

In addition, you can also see some variables starting with `LPB_`, which are the variables that come with `lpb`, including the following
| 名称 | 描述 |
| ---- | ---- |
| LPB_ROOT_DIR | workflow init working directory |
| LPB_TASK_DIR | the directory assigned to this workflow, used for log output, workflow command execution flow output, etc |
| LPB_OUTPUT_DIR | The recommended output directory, the one specified by `lpb build -o` |
| LPB_FILE_DIR | The directory where the configuration files are located |
| LPB_TASK_NAME | task name, specify by `lpb build --task-name` |
| LPB_TASK_ID | task id, specify by `lpb build --task-id` |
| LPB_GIT_REF | if LPB_ROOT_DIR is subdir of git, then LBP_GIT_REF will be set follow the priority: git tag > git commit_id |
| LPB_GIT_TAG | if LPB_ROOT_DIR is subdir of git, LBP_GIT_TAG will be set current git tag |
| LPB_GIT_COMMIT_ID | if LPB_ROOT_DIR is subdir of git, LPB_GIT_COMMIT_ID will be set current git commit id |
| LPB_GIT_BRANCH | if LPB_ROOT_DIR is subdir of git, LPB_GIT_BRANCH will be set current git branch |

## default settings file
By default, `lpb` will search settings.xml file in following directory, and append settings info one by one
* User directory: `~/.lpb/settings.xml`
* User local directory: `~/.local/share/lpb/settings.xml`
* System directory: `/etc/lpb/settings.xml`
