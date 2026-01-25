# 📝 Google Sheets Setup Guide - Step by Step

## ✅ What You'll Get After Setup

- 📊 **Auto-load data** - App loads data from Google Sheets on startup
- 💾 **Auto-save** - New sessions automatically save to cloud
- 🔄 **Refresh Data button** - One-click sync from Google Sheets
- 📱 **Edit anywhere** - Update Google Sheet from any device
- 👥 **Share with coaches** - Give them view or edit access
- 🔄 **Always in sync** - Main app and coach view use same data

**Setup Time: 10-15 minutes**

---

## 📋 Overview

You'll need to:
1. Create a Google Sheet with your training data
2. Set up a Google Cloud service account
3. Share the sheet with the service account
4. Add credentials to Streamlit

Let's do it step by step!

---

## STEP 1: Create Your Google Sheet

### 1.1 Create the Spreadsheet

1. Go to https://sheets.google.com
2. Click "Blank" to create a new spreadsheet
3. Name it: **"Mia Training Data"**

### 1.2 Add Column Headers

**IMPORTANT:** If you already imported your Excel file to Google Sheets, SKIP THIS STEP! Your headers are already correct.

If creating a new sheet from scratch, use these exact column names in the first row:

```
Date
Session_Name
Coach
Location
Surface
With_Ball
Training_Type
Duration_min
Intensity
Ball_Touches
Total_Distance_mi
Sprint_Distance_yd
Accl_Decl
Kicking_Power_mph
Top_Speed_mph
Sprints
Left_Touches
Right_Touches
Left_Foot_Pct
Left_Releases
Right_Releases
Left_Kicking_Power_mph
Right_Kicking_Power_mph
Left_Turns
Back_Turns
Right_Turns
Intense_Turns
Avg_Turn_Entry_Speed_mph
Avg_Turn_Exit_Speed_mph
Total_Turns
Position
Goals
Assists
Work_Rate
Ball_Possessions
```

**Total: 35 columns**

**Note:** Several fields are auto-calculated by the app:
- `Total_Turns` = Left_Turns + Right_Turns + Back_Turns
- `Ball_Touches` = Left_Touches + Right_Touches
- `Left_Foot_Pct` = (Left_Touches / Ball_Touches) × 100
- `Kicking_Power_mph` = max(Left_Kicking_Power_mph, Right_Kicking_Power_mph)
- `Work_Rate` = (Total_Distance_mi × 1760) / Duration_min (yards per minute)

### 1.3 Add Your Existing Data (Optional)

If you have existing Excel data:
1. Open your Excel file
2. Copy all rows (including headers)
3. Paste into the Google Sheet
4. Make sure column names match exactly

### 1.4 Copy the Sheet URL

1. Look at your browser address bar
2. Copy the entire URL (e.g., `https://docs.google.com/spreadsheets/d/1abc123xyz.../edit`)
3. Save this URL - you'll need it later!

✅ **Step 1 Complete!** You now have a Google Sheet ready.

---

## STEP 2: Create Google Cloud Service Account

### 2.1 Go to Google Cloud Console

1. Open https://console.cloud.google.com/
2. Sign in with your Google account (same one that owns the sheet)

### 2.2 Create a New Project

1. Click the project dropdown at the top
2. Click "New Project"
3. Name it: **"Mia Training Tracker"**
4. Click "Create"
5. Wait 10-15 seconds for it to be created
6. Select the new project from the dropdown

### 2.3 Enable Google Sheets API

1. In the search bar at top, type: **"Google Sheets API"**
2. Click on "Google Sheets API"
3. Click the blue "Enable" button
4. Wait for it to enable (about 5 seconds)

### 2.4 Enable Google Drive API

1. In the search bar, type: **"Google Drive API"**
2. Click on "Google Drive API"
3. Click the blue "Enable" button
4. Wait for it to enable

### 2.5 Create Service Account

1. In the left menu, click "Credentials"
2. Click "Create Credentials" at the top
3. Select "Service Account"
4. Fill in:
   - **Service account name:** `mia-tracker`
   - **Service account ID:** (auto-fills, leave it)
   - **Description:** `Service account for Mia Training Tracker`
5. Click "Create and Continue"
6. Skip "Grant this service account access" - Click "Continue"
7. Skip "Grant users access" - Click "Done"

### 2.6 Create Service Account Key

1. You'll see your service account listed
2. Click on the service account email (looks like: `mia-tracker@...iam.gserviceaccount.com`)
3. Click the "Keys" tab at the top
4. Click "Add Key" → "Create new key"
5. Select "JSON"
6. Click "Create"
7. A JSON file will download to your computer
8. **IMPORTANT:** Keep this file safe! You'll need it in the next step

✅ **Step 2 Complete!** You have a service account with credentials.

---

## STEP 3: Share Google Sheet with Service Account

### 3.1 Get Service Account Email

1. Open the JSON file you just downloaded (in a text editor or just double-click)
2. Look for `"client_email"` - it looks like:
   ```json
   "client_email": "mia-tracker@project-name-123456.iam.gserviceaccount.com"
   ```
3. Copy this entire email address

### 3.2 Share the Sheet

1. Go back to your Google Sheet (the "Mia Training Data" spreadsheet)
2. Click the "Share" button (top right)
3. Paste the service account email in the "Add people" field
4. Make sure it's set to "Editor" (not Viewer)
5. **UNCHECK** "Notify people" (service accounts don't need emails)
6. Click "Share"

✅ **Step 3 Complete!** The service account can now access your sheet.

---

## STEP 4: Add Credentials to Streamlit

### 4.1 Go to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Find your "Mia Training Tracker" app
3. Click the ⋮ menu (three dots)
4. Select "Settings"

### 4.2 Add Secrets

1. Click on the "Secrets" section (left sidebar)
2. You'll see a text editor

### 4.3 Format Your Credentials

Open the JSON file you downloaded earlier. It looks something like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMII...\n-----END PRIVATE KEY-----\n",
  "client_email": "mia-tracker@...iam.gserviceaccount.com",
  ...
}
```

### 4.4 Paste Credentials in Streamlit Secrets

In the Streamlit Secrets editor, paste exactly this format:

```toml
google_sheets_url = "YOUR_GOOGLE_SHEET_URL"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-PRIVATE-KEY-HERE\n-----END PRIVATE KEY-----\n"
client_email = "mia-tracker@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/YOUR-SERVICE-ACCOUNT-EMAIL"
```

**IMPORTANT STEPS:**

1. **Replace `YOUR_GOOGLE_SHEET_URL`** with the URL you copied in Step 1.4
   - Example: `google_sheets_url = "https://docs.google.com/spreadsheets/d/1abc123xyz.../edit"`

2. **Copy values from your JSON file** into the corresponding fields:
   - `project_id` - from JSON
   - `private_key_id` - from JSON
   - `private_key` - from JSON (keep the quotes and `\n` characters!)
   - `client_email` - from JSON
   - `client_id` - from JSON
   - `client_x509_cert_url` - from JSON

3. **Click "Save"** at the bottom

### 4.5 Example Secrets File

Here's what it should look like (with fake data):

```toml
google_sheets_url = "https://docs.google.com/spreadsheets/d/1abcXYZ123/edit"

[gcp_service_account]
type = "service_account"
project_id = "mia-tracker-456789"
private_key_id = "abc123def456"
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASC...\n-----END PRIVATE KEY-----\n"
client_email = "mia-tracker@mia-tracker-456789.iam.gserviceaccount.com"
client_id = "123456789012345"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/mia-tracker%40mia-tracker-456789.iam.gserviceaccount.com"
```

✅ **Step 4 Complete!** Credentials are configured.

---

## STEP 5: Deploy Updated App

### 5.1 Upload Files to GitHub

Upload these 7 essential files to your GitHub repository:

1. **`streamlit_app.py`** - Main app with Google Sheets integration
2. **`coach_view.py`** - Coach read-only view
3. **`requirements.txt`** - Includes Google Sheets libraries
4. **`packages.txt`** - System dependencies for OCR
5. **`apt-packages.txt`** - Additional system packages
6. **`preview.png`** - Social media preview image
7. **`.streamlit/config.toml`** - App configuration

### 5.2 Deploy Main App

1. Go to https://share.streamlit.io/
2. Connect your GitHub repository
3. Select `streamlit_app.py` as the main file
4. Wait 2-3 minutes for deployment

### 5.3 Deploy Coach View (Optional)

1. Create a second app on Streamlit Cloud
2. Same repository, but select `coach_view.py` as main file
3. Use the same Google Sheets credentials
4. Wait for deployment

### 5.4 Test It!

**Main App:**
1. Open your app
2. Data should auto-load from Google Sheets on startup!
3. Try the "🔄 Refresh Data" button to manually sync
4. Add a test session - it should auto-save to Google Sheets!
5. Check the "Upload & Extract" tab - no sidebar clutter!

**Coach View:**
1. Open the coach view app
2. Data should auto-load from Google Sheets
3. All tabs available (except Upload & Extract)
4. Read-only - no editing capabilities
5. Manual refresh button for latest data

✅ **Step 5 Complete!** Google Sheets integration is working!

---

## 🎉 You're Done! How to Use

### Auto-Load (Happens Automatically)
- Open main app → Data loads from Google Sheets on startup
- Open coach view → Data loads from Google Sheets on startup
- No manual upload needed!

### Add New Sessions
1. Go to "Upload & Extract" tab in main app
2. Select training type (Speed/Agility, Ball Work, or Match types)
3. Upload training screenshot (optional, OCR extracts data)
4. Fill in form fields
5. Click "Add to Data File"
6. Confirm with "Yes"
7. Data automatically saves to Google Sheets!
8. Form resets for next entry

### Manual Refresh
- **Main App:** Click "🔄 Refresh Data" button (centered above tabs)
- **Coach View:** Click "🔄 Refresh Data" button in header
- Both apps reload latest data from Google Sheets

### Edit From Anywhere
- Open Google Sheet on your phone or computer
- Edit directly in the sheet
- Click "🔄 Refresh Data" in app to reload changes

### Share with Coaches
- Open Google Sheet
- Click "Share"
- Add coach's email with "Viewer" or "Editor" access
- Share the coach view app URL with them
- They can view all analytics without editing capabilities in the app

---

## 🔧 Troubleshooting

### Error: "Google Sheets credentials not configured"

**Fix:** Make sure you completed Step 4 and saved the secrets.

### Error: "Permission denied"

**Fix:** Make sure you shared the Google Sheet with the service account email (Step 3).

### Error: "Invalid credentials"

**Fix:** Double-check that you copied the credentials correctly from the JSON file. Pay special attention to the `private_key` - it should include `\n` characters.

### Data doesn't load

**Fix:**
1. Check that the Google Sheet URL in secrets is correct
2. Make sure the sheet has column headers in row 1
3. Try clicking "🔄 Sync from Cloud"

### App won't deploy

**Fix:** Make sure `requirements.txt` includes these libraries:
```
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0,<3.9.0
seaborn>=0.12.0
openpyxl>=3.1.0
pytesseract>=0.3.10
Pillow>=10.0.0
gspread>=5.11.0
google-auth>=2.23.0
```

**Fix:** Make sure `packages.txt` includes:
```
tesseract-ocr
tesseract-ocr-eng
libtesseract-dev
```

**Fix:** Make sure `apt-packages.txt` includes:
```
tesseract-ocr
```

---

## 🔐 Security Notes

### Is This Safe?

✅ **Yes!** Here's why:

1. **Service account credentials** are stored in Streamlit Secrets (encrypted)
2. **Only your app** can access the credentials
3. **Only you and the service account** can access the Google Sheet
4. **Google Cloud** uses industry-standard security

### Best Practices

- ✅ **Never** share your service account JSON file
- ✅ **Don't** commit credentials to GitHub
- ✅ **Do** use Streamlit Secrets for all credentials
- ✅ **Keep** the Google Sheet private (don't make it public)

---

## 💡 Tips & Tricks

### Tip 1: Create a Backup Sheet
- Make a copy of your Google Sheet monthly
- File → Make a copy
- Archive old data

### Tip 2: Use Google Sheets for Quick Edits
- On your phone, open Google Sheets app
- Make quick corrections to data
- Sync in the app to see updates

### Tip 3: Share Read-Only with Coaches
- Share with "Viewer" access (not Editor)
- They can see data but not modify
- You maintain full control

### Tip 4: Export for Offline Use
- Use "📥 Download Excel" in sidebar
- Keeps a local backup
- Can work offline if needed

---

## 🆘 Need Help?

If you get stuck:

1. **Check the error message** - It usually tells you what's wrong
2. **Review the troubleshooting section** above
3. **Verify each step** was completed correctly
4. **Check deployment logs** in Streamlit Cloud

Common issues:
- Forgot to share sheet with service account
- Wrong Google Sheet URL in secrets
- Missing `\n` characters in private_key
- Typo in column headers

---

## 🎯 Quick Reference

### Files to Upload (All 7):
1. `streamlit_app.py` - Main application
2. `coach_view.py` - Coach read-only view
3. `requirements.txt` - Python dependencies
4. `packages.txt` - System dependencies (OCR)
5. `apt-packages.txt` - Additional packages
6. `preview.png` - Social media preview
7. `.streamlit/config.toml` - App configuration

### Secrets Format (Same for Both Apps):
```toml
google_sheets_url = "YOUR_SHEET_URL"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

### Sheet Column Headers (35 total):
```
Date, Session_Name, Coach, Location, Surface, With_Ball, Training_Type, Duration_min, Intensity, Ball_Touches, Total_Distance_mi, Sprint_Distance_yd, Accl_Decl, Kicking_Power_mph, Top_Speed_mph, Sprints, Left_Touches, Right_Touches, Left_Foot_Pct, Left_Releases, Right_Releases, Left_Kicking_Power_mph, Right_Kicking_Power_mph, Left_Turns, Back_Turns, Right_Turns, Intense_Turns, Avg_Turn_Entry_Speed_mph, Avg_Turn_Exit_Speed_mph, Total_Turns, Position, Goals, Assists, Work_Rate, Ball_Possessions
```

### Calculated Fields (Auto-computed):
- **Total_Turns** = Left_Turns + Right_Turns + Back_Turns
- **Ball_Touches** = Left_Touches + Right_Touches
- **Left_Foot_Pct** = (Left_Touches / Ball_Touches) × 100
- **Kicking_Power_mph** = max(Left_Kicking_Power_mph, Right_Kicking_Power_mph)
- **Work_Rate** = (Total_Distance_mi × 1760) / Duration_min (yards per minute)

---

**Setup Complete!** 🎉 Enjoy your cloud-connected training tracker! ⚽📊
