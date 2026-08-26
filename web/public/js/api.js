/* Data layer. Two backends behind one interface:
   - Firebase (auth + Firestore + Storage + callable compare)
   - Demo (bundled JSON, read-only) when firebase-init has no config.

   Interface:
     signIn(), signOut(), onUser(cb)
     listSessions() -> [{id, performer, venue, date, status, metrics, qc}]
     getSession(id) -> full session JSON (laughstack Session.to_dict shape)
     createUpload(file, meta, onProgress) -> sessionId
     compare(aId, bId) -> {rows, matched}
*/

import { firebase, isConfigured } from "./firebase-init.js";

export const demoMode = !isConfigured;

// ---------------------------------------------------------------- demo ----
const demo = {
  async listSessions() {
    const idx = await fetch("demo/index.json").then(r => r.json());
    return idx.sessions;
  },
  async getSession(id) {
    return fetch(`demo/${id}.json`).then(r => r.json());
  },
  async compare(a, b) {
    return fetch("demo/comparison.json").then(r => r.json());
  },
  signIn() { alert("Demo mode — add your Firebase config in js/firebase-init.js"); },
  signOut() {},
  onUser(cb) { cb({ uid: "demo", displayName: "Demo mode" }); },
  async createUpload() {
    throw new Error("Uploads are disabled in demo mode. Configure Firebase first.");
  },
};

// ------------------------------------------------------------- firebase ----
const fb = {
  _mods: null,
  async mods() {
    if (this._mods) return this._mods;
    const app = await firebase();
    const [auth, fs, st, fn] = await Promise.all([
      import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js"),
      import("https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js"),
      import("https://www.gstatic.com/firebasejs/10.12.2/firebase-storage.js"),
      import("https://www.gstatic.com/firebasejs/10.12.2/firebase-functions.js"),
    ]);
    this._mods = { app, auth, fs, st, fn,
      authInst: auth.getAuth(app), db: fs.getFirestore(app),
      storage: st.getStorage(app), functions: fn.getFunctions(app) };
    return this._mods;
  },
  async signIn() {
    const m = await this.mods();
    await m.auth.signInWithPopup(m.authInst, new m.auth.GoogleAuthProvider());
  },
  async signOut() {
    const m = await this.mods();
    await m.auth.signOut(m.authInst);
  },
  async onUser(cb) {
    const m = await this.mods();
    m.auth.onAuthStateChanged(m.authInst, cb);
  },
  async listSessions() {
    const m = await this.mods();
    const u = m.authInst.currentUser;
    if (!u) return [];
    const q = m.fs.query(
      m.fs.collection(m.db, "sessions"),
      m.fs.where("owner", "==", u.uid),
      m.fs.orderBy("createdAt", "desc"),
      m.fs.limit(100));
    const snap = await m.fs.getDocs(q);
    return snap.docs.map(d => ({ id: d.id, ...d.data() }));
  },
  async getSession(id) {
    const m = await this.mods();
    const doc = await m.fs.getDoc(m.fs.doc(m.db, "sessions", id));
    if (!doc.exists()) throw new Error("session not found");
    const d = doc.data();
    if (d.status !== "complete" || !d.resultPath) return { _pending: d };
    const url = await m.st.getDownloadURL(m.st.ref(m.storage, d.resultPath));
    return fetch(url).then(r => r.json());
  },
  async createUpload(file, meta, onProgress) {
    const m = await this.mods();
    const u = m.authInst.currentUser;
    if (!u) throw new Error("sign in first");
    const sessionId = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    await m.fs.setDoc(m.fs.doc(m.db, "sessions", sessionId), {
      owner: u.uid, status: "queued",
      performer: meta.performer || "", venue: meta.venue || "",
      date: meta.date || "", sourceType: meta.sourceType || "upload",
      createdAt: m.fs.serverTimestamp(),
    });
    const ext = (file.name.match(/\.[A-Za-z0-9]+$/) || [".wav"])[0].toLowerCase();
    const ref = m.st.ref(m.storage, `uploads/${u.uid}/${sessionId}/original${ext}`);
    await new Promise((resolve, reject) => {
      const task = m.st.uploadBytesResumable(ref, file);
      task.on("state_changed",
        s => onProgress?.(s.bytesTransferred / s.totalBytes),
        reject, resolve);
    });
    return sessionId;
  },
  async compare(a, b) {
    const m = await this.mods();
    const call = m.fn.httpsCallable(m.functions, "compare_sessions");
    const res = await call({ a, b });
    return res.data;
  },
};

const impl = demoMode ? demo : fb;
export const signIn = (...a) => impl.signIn(...a);
export const signOut = (...a) => impl.signOut(...a);
export const onUser = (...a) => impl.onUser(...a);
export const listSessions = (...a) => impl.listSessions(...a);
export const getSession = (...a) => impl.getSession(...a);
export const createUpload = (...a) => impl.createUpload(...a);
export const compare = (...a) => impl.compare(...a);
