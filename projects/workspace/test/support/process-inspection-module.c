/* A real OS-loaded image with no WebGPU or N-API dependency. The loader calls
 * this standard N-API entry point; opaque pointers pass through unchanged. */
#if defined(_WIN32)
#define PROBE_EXPORT __declspec(dllexport)
#else
#define PROBE_EXPORT __attribute__((visibility("default")))
#endif

PROBE_EXPORT void *napi_register_module_v1(void *environment, void *exports) {
    (void)environment;
    return exports;
}
