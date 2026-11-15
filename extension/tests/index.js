// Directory entry point keeps `node --test extension/tests/` portable.
Promise.all([import('./detector.test.mjs'), import('./policies.test.mjs')]).catch(() => {
  process.exitCode = 1;
});
