/* Local pattern/checksum engine. No language model, network, or text storage. */
(() => {
  'use strict';
  const {patterns:p, secrets, priority} = globalThis.PrivacyGatePatterns;
  const categories = ['EMAIL','US_PHONE','INTL_PHONE','SSN','PAYMENT_CARD','IPV4','PARTIAL_DETAIL','BANK_ACCOUNT','SECRET','STREET_ADDRESS','NATIONAL_ID','DATE_OF_BIRTH'];
  const matches = (source,text,flags='g') => [...text.matchAll(new RegExp(source,flags))];
  const digits = value => value.replace(/[ -]/g,'');
  const luhn = value => {
    const d=digits(value); if(!/^\d{13,19}$/.test(d)||new Set(d).size===1) return false;
    return [...d].reverse().reduce((sum,c,i)=>{let n=+c;if(i%2){n*=2;if(n>9)n-=9;}return sum+n;},0)%10===0;
  };
  const aba = d => /^\d{9}$/.test(d)&&new Set(d).size>1&&[...d].reduce((s,c,i)=>s+(+c)*[3,7,1][i%3],0)%10===0;
  const iban = value => {
    const v=value.replace(/ /g,'');if(!/^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$/.test(v)||v.length>34)return false;
    const decimal=(v.slice(4)+v.slice(0,4)).replace(/[A-Z]/g,c=>String(c.charCodeAt(0)-55));
    return BigInt(decimal)%97n===1n;
  };
  const nationalId = value => '10X98765432'[[...value.slice(0,17)].reduce((s,c,i)=>s+(+c)*[7,9,10,5,8,4,2,1,6,3,7,9,10,5,8,4,2][i],0)%11]===value.slice(-1).toUpperCase();
  const validDate = value => {
    let y,m,d,a;
    if((a=/^(\d{4})-(\d{2})-(\d{2})$/.exec(value))) [,y,m,d]=a;
    else if((a=/^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/.exec(value))){[,m,d,y]=a;if(y.length===2)y=+y+(+y<=68?2000:1900);}
    else {
      const months=['january','february','march','april','may','june','july','august','september','october','november','december'];
      if((a=/^(\w+) (\d{1,2}), (\d{4})$/.exec(value))){m=months.indexOf(a[1].toLowerCase())+1;d=a[2];y=a[3];}
      else if((a=/^(\d{1,2}) (\w+) (\d{4})$/.exec(value))){d=a[1];m=months.indexOf(a[2].toLowerCase())+1;y=a[3];}
      else return false;
    }
    const date=new Date(0);date.setUTCFullYear(+y,+m-1,+d);
    return +y>0&&date.getUTCFullYear()===+y&&date.getUTCMonth()===+m-1&&date.getUTCDate()===+d;
  };
  function detect(text){
    const found=[];
    const add=(category,m,group=0,value=m[group])=>{
      const start=m.indices ? m.indices[group][0] : m.index;
      found.push({category,start,end:start+value.length,matched_text:value,reason:'Local pattern or checksum match; check it yourself.',confidence:'pattern-based'});
    };
    const runs=matches(p.NUMERIC_RUN,text);
    for(const [category,pattern] of [['EMAIL',p.EMAIL],['US_PHONE',p.PHONE],['SSN',p.SSN]]){
      for(const m of matches(pattern,text)){
        if(category!=='EMAIL'&&runs.some(r=>m.index<r.index+r[0].length&&r.index<m.index+m[0].length))continue;
        add(category,m);
      }
    }
    for(const m of runs)if(luhn(m[0]))add('PAYMENT_CARD',m);
    for(const m of matches(p.IPV4,text)){
      const prefix=text.slice(Math.max(0,m.index-96),m.index);
      const version=/\b(?:version|release|build|v)\s*[:=]?\s*$/i.test(prefix);
      const network=/\b(?:ipv?4?|gateway|router|network\s+address|host\s+address|visit)\b[^.!?\n]{0,48}$/i.test(prefix);
      if(version&&!network)continue;
      if(m[0].split('.').every(n=>+n<=255&&(n==='0'||!n.startsWith('0'))))add('IPV4',m);
    }
    for(const m of matches(p.PARTIAL,text))add('PARTIAL_DETAIL',m);
    // Browser phone checks are deliberately shape-only, unlike Python phonenumbers.
    for(const m of matches(String.raw`(?<![\dA-Za-z])\+(?!1(?:\D|$))[2-9]\d{0,2}[ .-]?(?:\d[ .-]?){6,13}\d(?!\d)`,text)){
      const count=m[0].replace(/\D/g,'').length;if(count>=8&&count<=15)add('INTL_PHONE',m);
    }
    for(const m of matches(String.raw`(?<!\d)1[3-9]\d(?:[ -]?\d{4}){2}(?!\d)`,text))add('INTL_PHONE',m);
    const near=(m,keyword,distance,both=false)=>new RegExp(keyword,'i').test(text.slice(Math.max(0,m.index-distance),m.index))||(both&&new RegExp(keyword,'i').test(text.slice(m.index+m[0].length,m.index+m[0].length+distance)));
    for(const m of matches(String.raw`(?<![\dA-Za-z])\d{6,17}(?![\dA-Za-z])`,text)){
      const v=m[0];
      if(v.length===9&&near(m,String.raw`\b(?:ssn|social security(?: number| no\.?)?)\b`,32)&&!['000','666'].includes(v.slice(0,3))&&!v.startsWith('9')&&v.slice(3,5)!=='00'&&v.slice(5)!=='0000')add('SSN',m);
      if(near(m,String.raw`\b(?:routing|aba|rtn)\b`,40,true)&&aba(v))add('BANK_ACCOUNT',m);
      if(near(m,String.raw`\b(?:account|acct|a/c|checking|savings)\b`,40,true)&&!luhn(v))add('BANK_ACCOUNT',m);
    }
    for(const m of matches(String.raw`\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,30}\b`,text))if(iban(m[0]))add('BANK_ACCOUNT',m);
    for(const m of matches(p.DATE,text,'gi'))if(near(m,String.raw`\b(?:born|birthday|dob|date of birth|b\.)`,30)&&validDate(m[0]))add('DATE_OF_BIRTH',m);
    for(const [pattern,group] of secrets){
      for(const m of matches(pattern.replace('(?i)',''),text,pattern.includes('(?i)')?'gdi':'gd')){
        let value=m[group];if(pattern.includes('password|passwd'))value=value.replace(/[.,;!?)"']+$/g,'');
        if(value)add('SECRET',m,group,value);
      }
    }
    for(const m of matches(p.ADDRESS,text))add('STREET_ADDRESS',m);
    for(const m of matches(p.NATIONAL_ID,text))if(nationalId(m[0]))add('NATIONAL_ID',m);
    const accepted=[];
    found.sort((a,b)=>(priority[b.category]||0)-(priority[a.category]||0)||(b.end-b.start)-(a.end-a.start)||a.start-b.start||a.category.localeCompare(b.category));
    for(const f of found)if(!accepted.some(a=>f.start<a.end&&a.start<f.end))accepted.push(f);
    return accepted.sort((a,b)=>a.start-b.start||a.end-b.end||a.category.localeCompare(b.category));
  }
  globalThis.PrivacyGateDetector={detect,categories,luhn,aba,iban,nationalId,validDate};
})();
