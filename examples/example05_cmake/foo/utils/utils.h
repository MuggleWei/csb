#ifndef FOO_UTILS_H_
#define FOO_UTILS_H_

#include "foo/foo_macro.h"

#ifdef __cplusplus
extern "C" {
#endif

FOO_EXPORT
int compress_one_file(const char *input_filepath, const char *output_filepath);

FOO_EXPORT
int decompress_one_file(const char *input_filepath,
			const char *output_filepath);

#ifdef __cplusplus
} // extern "C"
#endif

#endif // !FOO_UTILS_H_
