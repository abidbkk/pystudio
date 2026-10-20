# Setting up classes and online saving (Google Apps Script)

PyStudio runs on GitHub Pages. A small Apps Script project in **your** school Google account adds:

- **Sign-in:** students are recognised by their school Google account. There are no passwords or codes.
- **Saving:** each person's files go into a folder in **your** Google Drive.
- **Class lists:** you edit a Google Sheet listing classes, students and teachers.

Students use the Apps Script link (it ends in `/exec`). The plain GitHub link still works, but
files are then saved only in that browser.

## 1. Put the code in your Apps Script project
1. Open your **PyStudio** project at https://script.google.com.
2. In **`Code.gs`**, replace everything with the contents of [`apps-script/Code.gs`](apps-script/Code.gs).
3. In **`index.html`**, replace everything with the contents of [`apps-script/index.html`](apps-script/index.html).
4. Press **Ctrl+S**.

## 2. Run the one-time setup
1. In the toolbar's function menu (next to **Debug**), pick **`setup`**, then click **Run**.
2. Google asks for permission to use Drive and Sheets. Click **Review permissions** and choose your account.
   If you see "Google hasn't verified this app", click **Advanced → Go to PyStudio**. It's your own script.
3. The **Execution log** at the bottom shows two links:
   - **Class list**: the spreadsheet *PyStudio – Classes*
   - **Student files folder**: *PyStudio files* in your Drive

   Both are in your Drive, so you can find them again there.

## 3. Fill in the class list
In the **Students** tab, add one row per student:

| Class | Student name | Email | Last active (automatic) |
|---|---|---|---|
| 9A | Sara Ahmad | sara.ahmad@ics.edu.jo | |

- Delete the example row.
- To add other teachers, put their emails in the **Teachers** tab. You're always a teacher.
- Changes reach PyStudio within about a minute.

## 4. Publish the new version
1. Click **Deploy → Manage deployments**, then the pencil ✏️.
2. Set **Version** to **New version** and click **Deploy**.
   The `/exec` link stays the same.
3. Give that link to your students. A short link or QR code makes it easier to share.

## How it works for you
- You open the same link. You get **My files**, plus a **Classes** panel at the bottom left.
- Pick a class, then click a student to open their files. You can run and debug them.
  While you watch, their changes appear every few seconds.
- You can also edit their files. Your edits save into the student's file, and they see them within about 20 seconds.
  If you both change the same file at the same moment, nothing is lost: the second person's version is saved as `name-mine.py`.
- You can also browse everyone's work directly in the *PyStudio files* folder in Drive, organised as Class → Student.
- Deleted files go to **your** Drive trash, so you can restore them for 30 days.

## Good to know
- **Shared computers:** PyStudio uses whichever Google account the browser is signed in to.
  Students should sign out of Google at the end of the lesson.
- **Not on the list:** if a student isn't in the sheet yet, PyStudio tells them so and saves
  only on that computer until you add them.
- **Quotas:** Apps Script's free limits are well above what one class needs. Saves happen at most every
  few seconds while someone types.
- **Updating PyStudio:** changes to the editor are published on GitHub and appear straight away.
  You only redo steps 1 and 4 when `apps-script/Code.gs` or `apps-script/index.html` changes.
