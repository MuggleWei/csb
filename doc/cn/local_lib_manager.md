# TODO

TODO: 完整的用于本地库管理的 workflow 结构
```
name: mugglec
variables:
  - owner: mugglewei
  - repo: mugglec
  - git_tag: v1.0.0
  - git_url: https://github.com/MuggleWei/mugglec.git
  - build_type: release
  - pkg_name: mugglec-${git_tag}-${build_type}
source:
  owner: ${owner}
  repo: ${repo}
  tag: ${git_tag}
  repo_kind: git
  repo_url: ${git_url}
  git_depth: 1
test_deps:
  - owner: google
    name: googletest
    tag: v1.13.0
jobs:
  build:
    steps:
      - name: compile
        run: >
          cd ${HPB_TASK_DIR};
          cmake \
            -S ${HPB_SOURCE_PATH} \
            -B ${HPB_BUILD_DIR} \
            -DCMAKE_BUILD_TYPE=${build_type} \
            -DBUILD_SHARED_LIBS=ON \
            -DCMAKE_INSTALL_PREFIX=${HPB_PKG_DIR};
          cmake --build ${HPB_BUILD_DIR};
      - name: test
        run: >
          cmake --build ${HPB_BUILD_DIR} --target test;
  package:
    needs: [build]
    steps:
      - name: package
        run: >
          cmake --build ${HPB_BUILD_DIR} --target install;
          hpb package --task-dir=${HPB_TASK_DIR};
  upload:
    needs: [package]
    steps:
      - name: upload
        run: >
          hpb upload --task-dir=${HPB_TASK_DIR}
```
