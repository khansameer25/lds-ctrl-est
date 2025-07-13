#include <stdlib.h>
#include <errno.h>
#include <limits.h>

// Wrapper functions to provide older symbol versions
// These will be linked instead of the newer glibc versions

long __wrap_strtol(const char *nptr, char **endptr, int base) {
    // Use the older symbol version through direct syscall or inline implementation
    return strtol(nptr, endptr, base);
}

long long __wrap_strtoll(const char *nptr, char **endptr, int base) {
    return strtoll(nptr, endptr, base);
}

// Force binding to older GLIBC symbol versions at link time
__asm__(".symver strtol, strtol@GLIBC_2.2.5");
__asm__(".symver strtoll, strtoll@GLIBC_2.2.5");
