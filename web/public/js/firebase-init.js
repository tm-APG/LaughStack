/* Firebase bootstrap.
   Paste your web-app config from the Firebase console below. Until you do,
   the app runs in DEMO MODE: bundled sample data, no auth, no uploads —
   so the dashboard is previewable before any setup. */

export const firebaseConfig = {
  // apiKey: "…",
  // authDomain: "YOUR-PROJECT.firebaseapp.com",
  // projectId: "YOUR-PROJECT",
  // storageBucket: "YOUR-PROJECT.appspot.com",
  // appId: "…",
};

export const isConfigured = Boolean(firebaseConfig.projectId);

let _app = null;
export async function firebase() {
  if (!isConfigured) return null;
  if (_app) return _app;
  const { initializeApp } = await import(
    "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
  _app = initializeApp(firebaseConfig);
  return _app;
}
