/* Artifact-level probe: run a fixture tensor through the COMPILED Prism Q2_0
 * quantizer and dequantizer, so torch fake-quant can be compared against the
 * real fork math (not a Python reimplementation).
 *
 * It calls the fork's exported functions:
 *     quantize_row_q2_0_ref  (float -> block_q2_0)
 *     dequantize_row_q2_0    (block_q2_0 -> float)
 * Only the ABI (struct layout + prototypes) is declared here; the quantization
 * body is NOT copied — it is linked from libggml-base.
 *
 * Build (against the Prism fork build):
 *   gcc -O2 prism_q2_0_probe.c -o prism_q2_0_probe \
 *       -L<fork>/build-cpu/bin -lggml-base -Wl,-rpath,<fork>/build-cpu/bin
 *
 * Usage: prism_q2_0_probe <in_fp32.bin> <n_elements> <out_prefix>
 *   writes <out_prefix>.codes.i8   (int8 level per element, level = code-1)
 *          <out_prefix>.deq.f32    (float dequantized value per element)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#define QK2_0 128
typedef uint16_t ggml_half;
typedef struct { ggml_half d; uint8_t qs[QK2_0/4]; } block_q2_0;

/* linked from libggml-base (Prism fork) */
extern void quantize_row_q2_0_ref(const float *x, block_q2_0 *y, int64_t k);
extern void dequantize_row_q2_0(const block_q2_0 *x, float *y, int64_t k);

int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "usage: %s in.bin n out\n", argv[0]); return 2; }
    const char *in = argv[1];
    long n = atol(argv[2]);
    const char *prefix = argv[3];
    if (n <= 0 || n % QK2_0 != 0) { fprintf(stderr, "n must be a positive multiple of %d\n", QK2_0); return 2; }

    float *x = (float*)malloc(sizeof(float) * n);
    FILE *f = fopen(in, "rb");
    if (!f) { perror("open in"); return 1; }
    if ((long)fread(x, sizeof(float), n, f) != n) { fprintf(stderr, "short read\n"); return 1; }
    fclose(f);

    long nb = n / QK2_0;
    block_q2_0 *blocks = (block_q2_0*)malloc(sizeof(block_q2_0) * nb);
    float *deq = (float*)malloc(sizeof(float) * n);

    quantize_row_q2_0_ref(x, blocks, n);   /* compiled Prism quantizer */
    dequantize_row_q2_0(blocks, deq, n);   /* compiled Prism dequantizer */

    /* extract 2-bit codes -> signed levels (code-1) */
    int8_t *levels = (int8_t*)malloc(n);
    for (long b = 0; b < nb; ++b) {
        for (int j = 0; j < QK2_0; ++j) {
            uint8_t code = (blocks[b].qs[j/4] >> ((j%4)*2)) & 0x3;
            levels[b*QK2_0 + j] = (int8_t)code - 1;
        }
    }

    char path[1024];
    snprintf(path, sizeof(path), "%s.codes.i8", prefix);
    FILE *fc = fopen(path, "wb"); fwrite(levels, 1, n, fc); fclose(fc);
    snprintf(path, sizeof(path), "%s.deq.f32", prefix);
    FILE *fd = fopen(path, "wb"); fwrite(deq, sizeof(float), n, fd); fclose(fd);

    fprintf(stderr, "probe ok: n=%ld blocks=%ld\n", n, nb);
    free(x); free(blocks); free(deq); free(levels);
    return 0;
}
