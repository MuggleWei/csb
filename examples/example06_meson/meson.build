project('hello', 'c')

dep_foo = dependency('foo')
executable('hello', 'src/hello.c',
  dependencies: dep_foo,
  install : true,
  install_rpath: '$ORIGIN/../lib')
