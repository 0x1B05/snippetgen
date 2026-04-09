#include "xs_snippet.h"

int xsrt_run_snippet(xsrt_env_t *env, const xsrt_snippet_desc_t *snippet) {
  int rc;

  if (env == 0 || snippet == 0) {
    return -1;
  }

  if (snippet->init != 0) {
    rc = snippet->init(env);
    if (rc != 0) {
      if (snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (snippet->run != 0) {
    rc = snippet->run(env);
    if (rc != 0) {
      if (snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (snippet->check != 0) {
    rc = snippet->check(env);
    if (rc != 0) {
      if (snippet->fini != 0) {
        snippet->fini(env);
      }
      return rc;
    }
  }

  if (snippet->fini != 0) {
    snippet->fini(env);
  }

  return 0;
}
