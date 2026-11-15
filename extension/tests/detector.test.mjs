import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
for(const name of ['patterns.js','detector.js'])vm.runInThisContext(fs.readFileSync(new URL('../'+name,import.meta.url),'utf8'));
const detector=globalThis.PrivacyGateDetector;
const cases=JSON.parse(fs.readFileSync(new URL('../../fixtures/detector_cases.json',import.meta.url),'utf8'));
for(const c of cases.filter(c=>c.targets.includes('js'))){
 test(c.id,()=>{
  const text=c.text.replaceAll('{{GH_TOKEN}}','gh'+'p_'+'x'.repeat(36));
  assert.deepEqual(detector.detect(text).map(({category,start,end})=>({category,start,end})),c.expected);
 });
}
test('malformed dates and check digits are rejected',()=>{
 assert.equal(detector.validDate('02/30/2009'),false);
 assert.equal(detector.validDate('2000-02-29'),true);
 assert.equal(detector.validDate('1900-02-29'),false);
 assert.equal(detector.aba('123456789'),false);
 assert.equal(detector.iban('GB83 WEST 1234 5698 7654 32'),false);
});
test('secret group offsets refer to the value only',()=>{
 const text='password: '+'pw'.repeat(5)+'!';
 const result=detector.detect(text);
 assert.equal(result.length,1);
 assert.equal(result[0].start,10);
 assert.equal(result[0].matched_text,'pw'.repeat(5));
});
test('version context avoids an IPv4 false positive',()=>{
 assert.equal(detector.detect('version 1.2.3.4').length,0);
 assert.equal(detector.detect('router 1.2.3.4')[0].category,'IPV4');
});
