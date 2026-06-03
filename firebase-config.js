// firebase-config.js
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

// !!! استبدلي القيم التالية ببيانات مشروعك من Firebase Console !!!
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_AUTH_DOMAIN",
    projectId: "project-graduation2026",
    storageBucket: "YOUR_STORAGE_BUCKET",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// تهيئة التطبيق
const app = initializeApp(firebaseConfig);

// تصدير قاعدة البيانات لاستخدامها في ملفات أخرى
export const db = getFirestore(app);