// PyStudio – Apps Script test
// Checks two things: (1) Python and the debugger work inside an Apps Script page,
// and (2) the page can tell which school account is signed in.

function doGet() {
  return HtmlService.createHtmlOutputFromFile('index')
    .setTitle('PyStudio')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

function whoAmI() {
  return Session.getActiveUser().getEmail();
}
