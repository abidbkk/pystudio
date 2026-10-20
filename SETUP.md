# Turning on student sign-in (Firebase)

This is a one-time setup and takes about 10 minutes. Firebase's free "Spark" plan is
enough for a school: 1 GB of storage, 20,000 saves and 50,000 file loads per day.

Do it while signed in to the Google account that should own the project. Using your
school account keeps it under the school's control.

## 1. Create the project
1. Go to https://console.firebase.google.com and click **Create a project**.
2. Name it, for example `pystudio`. You can turn Google Analytics **off**.

## 2. Turn on Google sign-in
1. In the left menu: **Build → Authentication → Get started**.
2. On the **Sign-in method** tab, choose **Google**, switch it **on**, pick a support email and click **Save**.
3. On the **Settings** tab, open **Authorized domains** and click **Add domain**: `abidbkk.github.io`
   (`localhost` is already allowed, for testing).

## 3. Create the database
1. **Build → Firestore Database → Create database**.
2. Choose a location close to you, for example `europe-west` / `eur3`. You can't change it later.
3. Choose **Start in production mode**.
4. Open the **Rules** tab, replace everything with the contents of
   [`firestore.rules`](firestore.rules), and click **Publish**.

## 4. Connect PyStudio to the project
1. Go to **Project settings** (the gear icon) → **General**. Under **Your apps**, click the **web** icon `</>`.
2. Give it a nickname (`pystudio`), leave Hosting unticked, and click **Register app**.
3. Copy the `firebaseConfig = { ... }` values into [`firebase-config.js`](firebase-config.js):

```js
window.PYSTUDIO_CONFIG = {
  firebase: {
    apiKey: "…",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "…",
    appId: "…",
  },
  allowedDomains: ["ics.edu.jo"],
};
```

4. Commit and push. The site updates within a couple of minutes.

## Notes
- **Which accounts can sign in:** accounts at `ics.edu.jo` or any subdomain, such as
  `students.ics.edu.jo`. To use a different domain, change it in **both** `firebase-config.js`
  and `firestore.rules`, then publish the rules again.
- **Where files are stored:** Firestore at `users/{uid}/files/{fileId}`. Each student can read and write only their own files.
  Under `users/{uid}`, the app also saves the student's email, name and last time they signed in.
- **Shared computers:** files aren't kept in the browser after a student signs out.
  Students should click **Sign out** when they finish.
- **Use without signing in:** still available. Those files are saved only in that browser.
- If your Google Workspace admin restricts third-party apps, they may need to allow the Firebase project.
