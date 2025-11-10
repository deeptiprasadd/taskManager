// Use compat in service worker for simplicity
importScripts('https://www.gstatic.com/firebasejs/10.14.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.14.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAdh_iiHbCIDIFG9mpo3-RR6gVYUJGMiYI",
  authDomain: "taskplanner-daily.firebaseapp.com",
  projectId: "taskplanner-daily",
  storageBucket: "taskplanner-daily.firebasestorage.app",
  messagingSenderId: "521965388557",
  appId: "1:521965388557:web:9fc9878603ab27d9366644",
  measurementId: "G-WTSHVWJMCS"
});

const messaging = firebase.messaging();

// Optional: show a custom notification when a push arrives in background
messaging.onBackgroundMessage((payload) => {
  const title = payload?.notification?.title || 'Task Planner';
  const options = {
    body: payload?.notification?.body || 'You have an update.',
    icon: '/icons/icon-192.png',
    badge: '/icons/icon-192.png'
  };
  self.registration.showNotification(title, options);
});
