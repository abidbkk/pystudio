// PyStudio settings.
//
// To turn on student sign-in and online saving, paste your Firebase web app config
// below (see SETUP.md). While `firebase` is null, PyStudio works without sign-in and
// saves files only in the browser.
//
// The Firebase web config is not a secret: it only identifies the project. Access to
// student files is protected by the rules in firestore.rules.
window.PYSTUDIO_CONFIG = {
  firebase: null,

  // Only Google accounts from these domains (or their subdomains) may sign in.
  // Keep this in step with the domain check in firestore.rules.
  allowedDomains: ["ics.edu.jo"],
};
