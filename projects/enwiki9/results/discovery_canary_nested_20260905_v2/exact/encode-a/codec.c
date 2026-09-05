/* SPDX-License-Identifier: MIT
 * Synthetic release canary: streaming run-length pairs, no corpus knowledge. */
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    int decode, c, previous, count, i;
    FILE *input, *output;
    if (argc != 4 || (strcmp(argv[1], "c") && strcmp(argv[1], "d"))) return 2;
    decode = !strcmp(argv[1], "d");
    input = fopen(argv[2], "rb");
    if (!input) return 3;
    output = fopen(argv[3], "wb");
    if (!output) { fclose(input); return 3; }
    if (decode) {
        if (fgetc(input) != 'R' || fgetc(input) != '1') return 4;
        while ((count = fgetc(input)) != EOF) {
            c = fgetc(input);
            if (!count || c == EOF) return 4;
            for (i = 0; i < count; ++i) if (fputc(c, output) == EOF) return 5;
        }
    } else {
        fputc('R', output); fputc('1', output);
        previous = EOF; count = 0;
        while ((c = fgetc(input)) != EOF) {
            if (count && (c != previous || count == 255)) {
                fputc(count, output); fputc(previous, output); count = 0;
            }
            previous = c; ++count;
        }
        if (count) { fputc(count, output); fputc(previous, output); }
    }
    if (ferror(input) || ferror(output)) return 5;
    if (fclose(input) || fclose(output)) return 5;
    return 0;
}
