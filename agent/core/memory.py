import json
import sqlite3
from pathlib import Path
from time import time

class Memory:
    """Three-level memory with explicit RAM and persistent storage budgets."""
    SHORT_LIMIT = 2048
    # Keep durable organism memory bounded. At 16 GiB RAM this reserves roughly
    # a quarter of the machine for persistent G.A.I. memory while leaving the OS,
    # sensory organs and compute stack room to breathe.
    PERSISTENT_LIMIT_BYTES = 4 * 1024 * 1024 * 1024
    SHORT_EVENT_LIMIT = 8192
    RECALL_SCAN_LIMIT = 500
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, ts REAL NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, ts REAL NOT NULL, tier TEXT NOT NULL, key TEXT, kind TEXT NOT NULL, data TEXT NOT NULL, strength REAL NOT NULL DEFAULT 0.5, visits INTEGER NOT NULL DEFAULT 1, last_seen REAL NOT NULL)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_mem_tier ON memories(tier)")
        self.db.execute("CREATE INDEX IF NOT EXISTS idx_mem_key ON memories(tier,key)")
        self.db.commit()

    def remember(self, kind, data):
        self.store("short", kind, data)
        self.db.execute('INSERT INTO events(ts, kind, data) VALUES (?, ?, ?)', (time(), kind, json.dumps(data)))
        self.db.execute("DELETE FROM events WHERE id NOT IN (SELECT id FROM events ORDER BY id DESC LIMIT ?)", (self.SHORT_LIMIT * 4,))
        self.db.commit()

    def store(self, tier, kind, data, key=None, strength=0.5):
        tier = str(tier).lower()
        if tier not in {"short", "long", "constant"}:
            raise ValueError("invalid memory tier")
        now=time(); payload=json.dumps(data, sort_keys=True)
        if key:
            row=self.db.execute("SELECT id, strength, visits FROM memories WHERE tier=? AND key=?", (tier,str(key))).fetchone()
            if row:
                new_strength=min(1.0, float(row[1])*.75+float(strength)*.25+.05)
                self.db.execute("UPDATE memories SET ts=?,kind=?,data=?,strength=?,visits=?,last_seen=? WHERE id=?", (now,kind,payload,new_strength,row[2]+1,now,row[0]))
            else:
                self.db.execute("INSERT INTO memories(ts,tier,key,kind,data,strength,visits,last_seen) VALUES(?,?,?,?,?,?,?,?)", (now,tier,str(key),kind,payload,float(strength),1,now))
        else:
            self.db.execute("INSERT INTO memories(ts,tier,key,kind,data,strength,visits,last_seen) VALUES(?,?,?,?,?,?,?,?)", (now,tier,None,kind,payload,float(strength),1,now))
        if tier == "short":
            self.db.execute("DELETE FROM memories WHERE tier='short' AND id NOT IN (SELECT id FROM memories WHERE tier='short' ORDER BY last_seen DESC LIMIT ?)", (self.SHORT_LIMIT,))
        self.db.commit()
        self.enforce_budget()

    def enforce_budget(self):
        """Bound persistent memory by forgetting the weakest non-constant traces."""
        try:
            size = Path(self.path).stat().st_size
        except OSError:
            return
        if size <= self.PERSISTENT_LIMIT_BYTES:
            return
        # Never automatically delete constants. Long-term memories are trimmed
        # by weakest strength/oldest recency first; short memory is the final
        # pressure-release tier.
        while size > self.PERSISTENT_LIMIT_BYTES:
            row = self.db.execute(
                "SELECT id FROM memories WHERE tier='long' ORDER BY strength ASC,last_seen ASC LIMIT 1"
            ).fetchone()
            if row is None:
                row = self.db.execute(
                    "SELECT id FROM memories WHERE tier='short' ORDER BY strength ASC,last_seen ASC LIMIT 1"
                ).fetchone()
            if row is None:
                break
            self.db.execute("DELETE FROM memories WHERE id=?", (row[0],))
            self.db.commit()
            try: size = Path(self.path).stat().st_size
            except OSError: break

    def budget_snapshot(self):
        try:
            payload = int(self.db.execute("SELECT COALESCE(SUM(length(data)),0) FROM memories").fetchone()[0] or 0)
            events = int(self.db.execute("SELECT COALESCE(SUM(length(data)),0) FROM events").fetchone()[0] or 0)
            size = payload + events
        except Exception:
            try: size = Path(self.path).stat().st_size
            except OSError: size = 0
        return {"bytes": int(size), "limit_bytes": self.PERSISTENT_LIMIT_BYTES,
                "usage": round(min(1.0, size / max(1, self.PERSISTENT_LIMIT_BYTES)), 6),
                "short_limit": self.SHORT_LIMIT}

    def recall(self, tier=None, limit=20, kind=None):
        q="SELECT id,ts,tier,key,kind,data,strength,visits,last_seen FROM memories"
        clauses=[]; args=[]
        if tier: clauses.append("tier=?"); args.append(str(tier).lower())
        if kind: clauses.append("kind=?"); args.append(str(kind))
        if clauses: q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY strength DESC, last_seen DESC LIMIT ?"; args.append(int(limit))
        rows=self.db.execute(q,args).fetchall()
        return [dict(id=r[0],ts=r[1],tier=r[2],key=r[3],kind=r[4],data=json.loads(r[5]),strength=r[6],visits=r[7],last_seen=r[8]) for r in rows]

    def promote(self, memory_id, target="long", boost=0.15):
        row=self.db.execute("SELECT kind,data,key,strength,visits,tier FROM memories WHERE id=?",(int(memory_id),)).fetchone()
        if not row or row[5] != "short": return False
        tier=str(target).lower()
        self.store(tier,row[0],json.loads(row[1]),key=row[2],strength=min(1.0,row[3]+boost))
        return True

    def consolidate(self, short_limit=100, promote_strength=0.72, promote_visits=2):
        rows=self.db.execute("SELECT id,key,kind,data,strength,visits FROM memories WHERE tier='short' ORDER BY last_seen DESC LIMIT ?",(int(short_limit),)).fetchall()
        promoted=0; decayed=0
        for mid,key,kind,data,strength,visits in rows:
            if float(strength)>=promote_strength or int(visits)>=promote_visits:
                self.store('long',kind,json.loads(data),key=key,strength=float(strength)); promoted+=1
            else:
                self.db.execute("UPDATE memories SET strength=? WHERE id=?",(max(0.0,float(strength)*.995),mid)); decayed+=1
        self.db.commit()
        return {"promoted":promoted,"decayed":decayed}

    def recall_relevant(self, query, limit=8):
        """Unified recall across working/short/long/constant memory.

        Matching is deliberately lightweight and inspectable: token overlap plus
        memory strength/recency. Long-term memories therefore become usable by
        cognition without making the CC depend on the storage implementation.
        """
        terms = {str(x).lower() for x in (query or []) if str(x).strip()}
        if not terms:
            return []
        rows = self.db.execute(
            "SELECT id,ts,tier,key,kind,data,strength,visits,last_seen FROM memories "
            "WHERE tier IN ('short','long','constant') ORDER BY last_seen DESC LIMIT ?",
            (self.RECALL_SCAN_LIMIT,),
        ).fetchall()
        scored=[]
        now=time()
        for r in rows:
            try: data=json.loads(r[5])
            except Exception: continue
            text=json.dumps(data,sort_keys=True,default=str).lower()
            overlap=sum(1 for term in terms if term in text)
            if not overlap: continue
            recency=max(0.0,1.0-(now-float(r[8]))/86400.0)
            score=min(1.0,0.50*min(1.0,overlap/max(1,len(terms))) + 0.30*float(r[6]) + 0.20*recency)
            scored.append((score,r,data))
        scored.sort(key=lambda x:x[0],reverse=True)
        hits=[]
        for score,r,data in scored[:int(limit)]:
            hits.append(dict(id=r[0],ts=r[1],tier=r[2],key=r[3],kind=r[4],data=data,
                             strength=r[6],visits=r[7],last_seen=r[8],relevance=score))
        return hits

    def reinforce_relevant(self, query, limit=3, boost=0.05):
        """Reinforce memories that were actually recalled for a current context."""
        hits=self.recall_relevant(query,limit=limit)
        for hit in hits:
            self.db.execute("UPDATE memories SET strength=?,visits=?,last_seen=? WHERE id=?",
                            (min(1.0,float(hit['strength'])+float(boost)), int(hit['visits'])+1, time(), int(hit['id'])))
        self.db.commit()
        return hits

    def snapshot(self):
        return {tier: self.recall(tier=tier,limit=20) for tier in ("short","long","constant")}
