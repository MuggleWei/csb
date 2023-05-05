#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "zlib.h"

int32_t file_size(const char *filepath)
{
	FILE *fp = fopen(filepath, "rb");
	if (fp == NULL) {
		return -1;
	}

	fseek(fp, 0, SEEK_END);
	unsigned long len = ftell(fp);
	fclose(fp);

	return (int32_t)len;
}

int compress_one_file(const char *input_filepath, const char *output_filepath)
{
	FILE *input_fp = NULL;
	gzFile output_fp = NULL;

	input_fp = fopen(input_filepath, "rb");
	if (input_fp == NULL) {
		fprintf(stderr, "failed open input file: %s", input_filepath);
		goto compress_one_file_except;
	}

	output_fp = gzopen(output_filepath, "wb");
	if (output_fp == NULL) {
		fprintf(stderr, "failed open output file: %s", output_filepath);
		goto compress_one_file_except;
	}

	char buf[128];
	int num_read = 0, num_write = 0;
	uint32_t total_read = 0;
	while ((num_read = (int)fread(buf, 1, sizeof(buf), input_fp)) > 0) {
		total_read += (uint32_t)num_read;
		num_write = gzwrite(output_fp, buf, num_read);
		if (num_write != num_read) {
			fprintf(stderr, "failed write!");
			goto compress_one_file_except;
		}
	}

	fclose(input_fp);
	gzclose(output_fp);

	int32_t total_write = file_size(output_filepath);
	fprintf(stdout,
		"read %lu bytes, write %lu bytes, compression factor %4.2f%%",
		(unsigned long)total_read, (unsigned long)total_write,
		(1.0 - (double)total_write / (double)total_read) * 100.0);

	return 0;

compress_one_file_except:
	if (input_fp) {
		fclose(input_fp);
		input_fp = NULL;
	}

	if (output_fp) {
		gzclose(output_fp);
		output_fp = NULL;
	}

	return -1;
}

int decompress_one_file(const char *input_filepath, const char *output_filepath)
{
	gzFile input_fp = NULL;
	FILE *output_fp = NULL;

	input_fp = gzopen(input_filepath, "rb");
	if (input_fp == NULL) {
		fprintf(stderr, "failed open input file: %s", input_filepath);
		goto decompress_one_file_except;
	}

	output_fp = fopen(output_filepath, "wb");
	if (output_fp == NULL) {
		fprintf(stderr, "failed open output file: %s", output_filepath);
		goto decompress_one_file_except;
	}

	char buf[128];
	int num_read = 0;
	while ((num_read = (int)gzread(input_fp, buf, sizeof(buf))) > 0) {
		fwrite(buf, 1, num_read, output_fp);
	}

	gzclose(input_fp);
	fclose(output_fp);

	return 0;

decompress_one_file_except:
	if (input_fp) {
		gzclose(input_fp);
		input_fp = NULL;
	}

	if (output_fp) {
		fclose(output_fp);
		output_fp = NULL;
	}

	return -1;
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
