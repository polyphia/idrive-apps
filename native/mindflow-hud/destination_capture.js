"use strict";
// Destination-only IPC. No GPS, guidance, session logs or USB exports.
const path=require('path'),cp=require('child_process');
class DestinationCapture {
 constructor(o){this.o=o||{};this.root=this.o.root||__dirname;this.child=null;this.locked=false;this.state={active:false,message:'Destination reader idle'};}
 start(){
  if(this.child||this.locked||this.closing)return false;
  const runtime=path.join(this.root,'adapter-runtime');
  const args=['--library-path',path.join(runtime,'lib')+':'+path.join(runtime,'usr/lib'),path.join(runtime,'usr/bin/python3.12'),'-B',path.join(this.root,'destination_reader.py'),'--seconds','30','--max-events','16'];
  let output='',errors='',overflow=false;
  try{
   const child=this.child=(this.o.spawn||cp.spawn)(path.join(runtime,'lib/ld-musl-x86_64.so.1'),args,{env:{PATH:'/usr/bin:/bin',LANG:'C.UTF-8',PYTHONHOME:path.join(runtime,'usr'),PYTHONDONTWRITEBYTECODE:'1',PYTHONNOUSERSITE:'1'},stdio:['ignore','pipe','pipe']});
   this.state={active:true,message:'Reading navigation destination'};
   child.stdout.on('data',d=>{if(output.length+d.length>16384){overflow=true;child.kill('SIGTERM');}else output+=String(d);});
   child.stderr.on('data',d=>{errors=(errors+String(d)).slice(-4096);});
   child.on('error',()=>{this.state.message='Destination reader could not start';});
   child.once('close',(code,signal)=>{
    clearTimeout(this.timer);this.child=null;
    this.locked=!!signal||/Detach incomplete/.test(errors);
    this.state={active:false,message:'Destination unavailable'};
    if(code===0&&!signal&&!overflow){
     try{const result=JSON.parse(output);
      if(result.detached===true&&typeof result.address==='string'&&result.address.trim()&&result.address.length<=2048&&!this.closing){
       this.state.message='Destination received; resolving route';
       if(this.o.onAddress)this.o.onAddress(result.address.trim());
      }
     }catch(e){this.state.message='Destination response invalid';}
    }
    output='';errors='';
    if(this.o.done&&!this.closing)this.o.done();
   });
   this.timer=setTimeout(()=>this.stop(),40000);this.timer.unref();return true;
  }catch(e){this.child=null;this.state={active:false,message:'Destination reader could not start'};return false;}
 }
 stop(){if(this.child)this.child.kill('SIGTERM');}
 async close(){this.closing=true;if(this.child){const child=this.child;await new Promise(r=>{child.once('close',r);this.stop();});}}
}
module.exports={DestinationCapture};
