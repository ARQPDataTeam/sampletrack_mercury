# SampleTrack - Passive Mercury

This Dash application is used for entering, editing, and managing passive mercury sampling tracking information before uploading it to a database.


## Using the App

### Creating a New Entry

1. Click the **New** button.
2. Enter one or more Sampler IDs. They must follow the format `ECCC####`.
   - A new row appears automatically once a valid ID is entered.
   - If scanning with a barcode scanner, the new textbox will automatically be selected (allowing for consecutive scans without needing to click with the keyboard/mouse)
3. Select "Sample" or "Blank" for each entry.
4. Enter the Kit ID in the format `EC-####`.
5. Click **Done**.
6. The entries will be shown in the table with auto-generated `sampleid` values in the format `EC-####_ECCC####`.

### Updating Existing Entries

1. Click the **Update** button.
2. Choose one of three options to search by: **Kit ID**, **Sampler ID**, **Location Shipped**
3. For **Kit ID** or **Sampler ID**, enter an existing ID (e.g., `EC-1234`). If the ID exists, matching rows will be loaded into the table (note when using **Sampler ID**, only entries for the most recent kit containing the entered **Sampler ID** will be shown).
4. For **Location Shipped**, select from a dropdown that displays all unique locations stored in the database. All entries with this location will be displayed
5. Make any edits directly in the table.
6. You may then upload the updated data.

### Editing Table Entries

- All columns except `sampleid` are editable.
- You can click into any cell to change:
  - Dates (e.g., `shipped_date`, `return_date`)
  - Location
  - Notes
  - Sample type (via dropdown)
- **PRESS ENTER AFTER EDITING ANY CELL TO SAVE THAT ENTRY. A FEEDBACK MESSAGE BELOW THE TABLE WILL CONFIRM YOUR EDIT WAS SAVED**
- If you change `kitid` or `samplerid`, the `sampleid` will update automatically.

### Uploading to Database

- Once you are satisfied with the data, click **Upload Data to Database**.
- The app will:
  - Check for duplicate sample IDs in the database.
  - If duplicates exist, a modal will appear asking if you want to overwrite them.
    - Clicking **Yes, Overwrite** will remove existing rows and upload the new ones.
    - Clicking **Cancel** will skip the upload.
- A confirmation message appears below the table after upload.

## Data Validation

- Kit ID must match: `EC-####`
- Sampler ID must match: `ECCC####`
- Datetimes must be in `YYYY-MM-DD HH:MM:SS`

## Resetting Input Fields

- Refresh the browser to reset the app
