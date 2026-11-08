const assert=require('assert'),EventEmitter=require('events'),path=require('path');
const {DestinationCapture}=require('../destination_capture');
function run(payload,code,signal){let received=null,args,child=new EventEmitter();child.stdout=new EventEmitter();child.stderr=new EventEmitter();child.kill=()=>{};const reader=new DestinationCapture({spawn:(exe,a)=>{args=a;return child;},onAddress:a=>{received=a;}});assert(reader.start());assert(!args.includes('--output'));child.stdout.emit('data',payload);child.emit('close',code,signal);return {received,reader};}
assert.equal(run(JSON.stringify({detached:true,address:'Example destination'}),0,null).received,'Example destination');
assert.equal(run(JSON.stringify({detached:false,address:'Example destination'}),0,null).received,null);
assert.equal(run(JSON.stringify({detached:true,address:'Example destination'}),1,null).received,null);
assert.equal(run('invalid',0,null).received,null);
assert.equal(run('x'.repeat(17000),0,null).received,null);
assert(run('{}',null,'SIGKILL').reader.locked);
console.log('PASS destination-only IPC: clean handoff, invalid/error/overflow rejection, detach lockout, no output-file argument');
