#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "foo/foo.h"

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
