# TODO

TODO: 完整的用于本地库管理的 workflow 结构
```
name: mugglec
variables:
  - git_url: https://github.com/MuggleWei/mugglec.git
  - repo_name: mugglec
  - GIT_TAG: v1.0.0
  - BUILD_TYPE: release
  - pkg_name: mugglec-${GIT_TAG}-${BUILD_TYPE}
source:
  owner: mugglewei
  name: ${repo_name}
  tag: ${GIT_TAG}
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
      - name: build
        run: >
          cd ${HPB_TASK_DIR};
          mkdir -p build;
          mkdir -p usr;
          cmake \
            -S ${HPB_SOURCE_PATH} -B build \
            -DCMAKE_BUILD_TYPE=${BUILD_TYPE} \
            -DBUILD_SHARED_LIBS=ON \
            -DCMAKE_PREFIX_PATH=${HPB_TEST_DEPS_DIR};${HPB_DEPS_DIR} \
            -DCMAKE_INSTALL_PREFIX=./usr;
      - name: test
        run: >
          cmake --build ./build --target test;
      - name: install
        run: >
          cmake --build ./build --target install;
  package:
    needs: [build]
    steps:
      - name: package
        run: >
          cd ${HPB_TASK_DIR}/usr;
          tar -czvf ${pkg_name}.tar.gz ./*;
          hpb push \
            --owner ${HPB_ART_OWNER} \
            --name ${HPB_ART_NAME} \
            --tag ${HPB_ART_TAG} \
            --pkg ${pkg_name}.tar.gz;
```
