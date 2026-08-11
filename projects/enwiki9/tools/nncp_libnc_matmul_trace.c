#define _GNU_SOURCE
#include <dlfcn.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>

typedef void (*MatMulFunction)(
    uintptr_t, uintptr_t, uintptr_t, uintptr_t, uintptr_t, uintptr_t,
    float, uintptr_t, uintptr_t, uintptr_t, uintptr_t, uintptr_t, uintptr_t,
    uintptr_t);

void mat_mul(uintptr_t a1, uintptr_t a2, uintptr_t a3, uintptr_t a4,
             uintptr_t a5, uintptr_t a6, float scale, uintptr_t a7,
             uintptr_t a8, uintptr_t a9, uintptr_t a10, uintptr_t a11,
             uintptr_t a12, uintptr_t a13)
{
    static MatMulFunction next;
    if (next == NULL)
        next = (MatMulFunction)dlsym(RTLD_NEXT, "mat_mul");
    fprintf(stderr,
            "gamma_mat_mul a1=%#" PRIxPTR " a2=%#" PRIxPTR
            " a3=%#" PRIxPTR " a4=%#" PRIxPTR " a5=%#" PRIxPTR
            " a6=%#" PRIxPTR " scale=%a a7=%#" PRIxPTR
            " a8=%#" PRIxPTR " a9=%#" PRIxPTR " a10=%#" PRIxPTR
            " a11=%#" PRIxPTR " a12=%#" PRIxPTR " a13=%#" PRIxPTR "\n",
            a1, a2, a3, a4, a5, a6, scale, a7, a8, a9, a10, a11, a12, a13);
    next(a1, a2, a3, a4, a5, a6, scale,
         a7, a8, a9, a10, a11, a12, a13);
}
