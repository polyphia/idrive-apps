"""Linux x86-64 bounded hardware-breakpoint destination reader.

No target code/data writes. Uses ptrace stops, debug registers and resume flag.
The caller must already have permission to trace the process. No policy changes.
"""
import argparse,ctypes,errno,hashlib,json,os,pathlib,signal,struct,sys,time

STOP_REQUESTED=False
PROFILE={'sha256':'7eda610dd0831377b8224733cd88ae3e46fedf136fcbe3b465308a5b00f3129f',
 'site':0x2c9d29,'code_start':0x2c9d21,'code':bytes.fromhex('488b7c24304c89fee852131f00')}
libc=ctypes.CDLL(None,use_errno=True)
libc.ptrace.restype=ctypes.c_long
libc.ptrace.argtypes=[ctypes.c_uint,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p]
PEEKUSER,POKEUSER,CONT,GETREGS,SETREGS,DETACH=3,6,7,12,13,17
SEIZE,INTERRUPT=0x4206,0x4207
WALL=0x40000000
DR=848  # offsetof(struct user, u_debugreg), Linux x86-64 ABI
class Regs(ctypes.Structure):
    _fields_=[(n,ctypes.c_ulonglong) for n in 'r15 r14 r13 r12 rbp rbx r11 r10 r9 r8 rax rcx rdx rsi rdi orig_rax rip cs eflags rsp ss fs_base gs_base ds es fs gs'.split()]
def trace(op,tid,addr=0,data=0):
    ctypes.set_errno(0)
    v=libc.ptrace(op,tid,ctypes.c_void_p(addr),ctypes.cast(data,ctypes.c_void_p) if not isinstance(data,int) else ctypes.c_void_p(data))
    e=ctypes.get_errno()
    if v==-1 and e:raise OSError(e,os.strerror(e))
    return v
def exact(read,addr,n):
    if n<0 or n>65536 or addr<4096 or addr+n>=1<<47:raise ValueError('Invalid memory range')
    b=read(addr,n)
    if len(b)!=n:raise ValueError('Short memory read')
    return b
def snapshot(read,state):
    begin,end,cap=struct.unpack('<QQQ',exact(read,state+0x18,24))
    if not (begin<=end<=cap) or (end-begin)%32 or (cap-begin)%32 or (end-begin)//32>16 or cap-begin>65536:raise ValueError('Invalid address vector')
    if not begin and (end or cap):raise ValueError('Invalid null vector')
    result=[];total=0
    for i in range((end-begin)//32):
        p,n=struct.unpack('<QQ',exact(read,begin+i*32,16))
        total+=n
        if n>4096 or total>65536:raise ValueError('Address exceeds bounds')
        text=exact(read,p,n).decode('utf-8','strict') if n else ''
        if '\0' in text:raise ValueError('Embedded NUL in address')
        result.append(text)
    return result
def identity(pid):
    # comm may contain spaces or parentheses; field 22 is starttime.
    stat=pathlib.Path('/proc/%d/stat'%pid).read_text()
    return stat[stat.rfind(')')+2:].split()[19]
def profile_target(pid,profile):
    binary=pathlib.Path('/proc/%d/exe'%pid).read_bytes()
    if hashlib.sha256(binary).hexdigest()!=profile['sha256']:raise ValueError('Unsupported executable hash')
    if binary[:6]!=b'\x7fELF\x02\x01' or struct.unpack_from('<H',binary,18)[0]!=62:raise ValueError('Requires little-endian x86-64 ELF')
    phoff=struct.unpack_from('<Q',binary,32)[0];size,count=struct.unpack_from('<HH',binary,54)
    loads=[struct.unpack_from('<IIQQQQQQ',binary,phoff+i*size) for i in range(count)]
    zero=next(s for s in loads if s[0]==1 and s[2]==0)
    st=os.stat('/proc/%d/exe'%pid);maps=[]
    for line in pathlib.Path('/proc/%d/maps'%pid).read_text().splitlines():
        fields=line.split();dev=fields[3].split(':')
        if int(fields[4])==st.st_ino and (int(dev[0],16),int(dev[1],16))==(os.major(st.st_dev),os.minor(st.st_dev)):
            a,b=[int(v,16) for v in fields[0].split('-')];maps.append((a,b,fields[1],int(fields[2],16)))
    row=next(r for r in maps if r[3]==0);bias=row[0]-(zero[3]&~4095)
    site=bias+profile['site']
    if not any(a<=site<b and 'x' in perm for a,b,perm,off in maps):raise ValueError('Callback is not executable')
    return bias
def tids(pid):return {int(p.name) for p in pathlib.Path('/proc/%d/task'%pid).iterdir()}
def find_aapd():
    matches=[]
    for entry in pathlib.Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            if (entry/'comm').read_text().strip()=='aapd':matches.append(int(entry.name))
        except (FileNotFoundError,PermissionError):pass
    if len(matches)!=1:raise ValueError('Expected exactly one aapd process; use --pid to identify the target')
    return matches[0]
class Tap:
    def __init__(self,pid,profile=PROFILE):
        self.pid=pid;self.profile=profile;self.tasks={};self.mem=None;self.events=[];self.start=identity(pid)
        self.bias=profile_target(pid,profile);self.site=self.bias+profile['site']
    def read(self,addr,n):return os.pread(self.mem,n,addr)
    def wait_stop(self,tid,timeout=2):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            got,status=os.waitpid(tid,os.WNOHANG|WALL)
            if got:
                if not os.WIFSTOPPED(status):raise RuntimeError('Target thread exited')
                self.tasks[tid]['stopped']=True
                # Preserve genuine delivery signals on detach. PTRACE_INTERRUPT is event 128.
                if status>>16!=128:
                    sig=os.WSTOPSIG(status);owned=False
                    if sig==signal.SIGTRAP and self.tasks[tid]['saved'] is not None and not status>>16:
                        regs=Regs();trace(GETREGS,tid,0,ctypes.byref(regs))
                        owned=regs.rip==self.site and trace(PEEKUSER,tid,DR+6*8)&1
                    self.tasks[tid]['signal']=0 if owned else sig
                return status
            time.sleep(.002)
        raise TimeoutError('Thread stop timed out')
    def arm(self):
        known=tids(self.pid)
        if not known or len(known)>128:raise ValueError('Unsupported thread count')
        for tid in sorted(known):
            trace(SEIZE,tid);self.tasks[tid]={'stopped':False,'saved':None,'signal':0}
            trace(INTERRUPT,tid);self.wait_stop(tid)
        if tids(self.pid)!=known or identity(self.pid)!=self.start:raise RuntimeError('Process changed during attach')
        self.mem=os.open('/proc/%d/mem'%self.pid,os.O_RDONLY)
        p=self.profile
        if exact(self.read,self.bias+p['code_start'],len(p['code']))!=p['code']:raise ValueError('Runtime callback bytes differ')
        for tid,item in self.tasks.items():
            saved=[trace(PEEKUSER,tid,DR+i*8)&((1<<64)-1) for i in (0,6,7)]
            if saved[2]&255:raise RuntimeError('Existing hardware breakpoints; refusing to replace')
            item['saved']=saved
            trace(POKEUSER,tid,DR,self.site);trace(POKEUSER,tid,DR+6*8,0);trace(POKEUSER,tid,DR+7*8,1)
        for tid in self.tasks:self.resume(tid)
    def resume(self,tid):
        item=self.tasks[tid];trace(CONT,tid,0,item['signal']);item['signal']=0;item['stopped']=False
    def collect(self,seconds=10,max_events=16):
        if not 0<seconds<=30 or not 1<=max_events<=100:raise ValueError('Capture limits exceeded')
        try:
            self.arm();deadline=time.monotonic()+seconds
            while time.monotonic()<deadline and len(self.events)<max_events and not STOP_REQUESTED:
                if identity(self.pid)!=self.start or tids(self.pid)!=set(self.tasks):raise RuntimeError('Process/thread topology changed; restart capture')
                for tid,item in self.tasks.items():
                    got,status=os.waitpid(tid,os.WNOHANG|WALL)
                    if not got:continue
                    if not os.WIFSTOPPED(status):raise RuntimeError('Target thread exited')
                    item['stopped']=True;sig=os.WSTOPSIG(status)
                    regs=Regs();trace(GETREGS,tid,0,ctypes.byref(regs))
                    dr6=trace(PEEKUSER,tid,DR+6*8)
                    if sig!=signal.SIGTRAP or status>>16 or regs.rip!=self.site or not dr6&1:
                        item['signal']=sig if not status>>16 else 0
                        raise RuntimeError('Unexpected target stop; capture aborted')
                    item['signal']=0
                    if regs.rsi!=regs.r15:raise ValueError('Unexpected callback registers')
                    p=self.profile
                    if exact(self.read,self.bias+p['code_start'],len(p['code']))!=p['code']:raise ValueError('Callback changed during capture')
                    observed=time.monotonic();addresses=snapshot(self.read,regs.rsi)
                    # RF prevents trapping again at the same execution breakpoint.
                    regs.eflags|=1<<16;trace(SETREGS,tid,0,ctypes.byref(regs));trace(POKEUSER,tid,DR+6*8,0)
                    self.resume(tid)  # Resume before serializing/outputting any address.
                    self.events.append({'schema':'aapd-address-snapshot-v1','sequence':len(self.events),'observed_monotonic_s':observed,'observed_wall_ms':round(time.time()*1000),'pid':self.pid,'process_start_ticks':self.start,'firmware_sha256':p['sha256'],'addresses':addresses})
                    if len(self.events)>=max_events:break
                time.sleep(.002)
            return self.events
        finally:self.close()
    def close(self):
        errors=[]
        for tid,item in self.tasks.items():
            try:
                if not item['stopped']:trace(INTERRUPT,tid);self.wait_stop(tid)
                if item['saved'] is not None:
                    for i,v in zip((0,6,7),item['saved']):trace(POKEUSER,tid,DR+i*8,v)
                trace(DETACH,tid,0,item['signal'])
            except (OSError,ChildProcessError) as e:
                if isinstance(e,OSError) and e.errno not in (errno.ESRCH,errno.ECHILD):errors.append(str(e))
            except Exception as e:errors.append(str(e))
        self.tasks.clear()
        if self.mem is not None:os.close(self.mem);self.mem=None
        if errors:raise RuntimeError('Detach incomplete: '+'; '.join(errors))
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pid',type=int);parser.add_argument('--seconds',type=float,default=10);parser.add_argument('--max-events',type=int,default=16);args=parser.parse_args()
    if os.uname().machine!='x86_64':raise ValueError('Only x86-64 supported')
    def interrupted(signum,frame):
        global STOP_REQUESTED
        STOP_REQUESTED=True
    signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
    events=Tap(args.pid if args.pid is not None else find_aapd()).collect(args.seconds,args.max_events)
    address=None
    for event in reversed(events):
        address=next((x.strip()[:2048] for x in event['addresses'] if isinstance(x,str) and x.strip()),None)
        if address:break
    # One bounded IPC result after clean detach, never a diagnostic file.
    print(json.dumps({'address':address,'detached':True},ensure_ascii=False))
if __name__=='__main__':
    try:main()
    except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(1)
