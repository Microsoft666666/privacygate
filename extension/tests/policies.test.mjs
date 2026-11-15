import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const read=name=>fs.readFileSync(new URL('../'+name,import.meta.url),'utf8');
for(const name of ['patterns.js','detector.js','policies.js'])vm.runInThisContext(read(name));
const data=JSON.parse(read('policies.json'));
test('every emitted category has metadata and three policies',()=>{
 assert.deepEqual(data,globalThis.PrivacyGatePolicy);
 for(const category of globalThis.PrivacyGateDetector.categories){
  assert.ok(data.categories[category].placeholder);
  for(const rules of Object.values(data.policies))assert.ok(['ALLOW','WARN','BLOCK'].includes(rules[category]));
 }
});
test('manifest is restricted to three sites and settings storage',()=>{
 const manifest=JSON.parse(read('manifest.json'));
 assert.equal(manifest.manifest_version,3);
 assert.deepEqual(manifest.permissions,['storage']);
 assert.equal(manifest.host_permissions,undefined);
 assert.deepEqual(manifest.content_scripts[0].matches,['https://chatgpt.com/*','https://claude.ai/*','https://gemini.google.com/*']);
 for(const name of manifest.content_scripts[0].js){
  const code=read(name);
  assert.doesNotMatch(code,/\b(?:fetch|XMLHttpRequest|WebSocket)\s*\(/);
  assert.doesNotMatch(code,/console\.(?:log|debug|info)\s*\(/);
 }
});
