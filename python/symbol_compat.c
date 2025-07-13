#include <stdlib.h>
#include <errno.h>
#include <limits.h>

// Wrapper functions to provide older symbol versions
// These will be linked instead of the newer glibc versions

long __wrap_strtol(const char *nptr, char **endptr, int base) {
    // Call the real strtol function
    extern long __real_strtol(const char *nptr, char **endptr, int base);
    return __real_strtol(nptr, endptr, base);
}

long long __wrap_strtoll(const char *nptr, char **endptr, int base) {
    // Call the real strtoll function
    extern long long __real_strtoll(const char *nptr, char **endptr, int base);
    return __real_strtoll(nptr, endptr, base);
}
