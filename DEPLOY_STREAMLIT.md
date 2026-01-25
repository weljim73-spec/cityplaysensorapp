# Mia Training Tracker - Streamlit Web App Deployment Guide

## 🎯 Quick Start - Run Locally

### 1. Install Dependencies
```bash
pip install -r requirements_streamlit.txt
```

### 2. Install Tesseract OCR
**Mac:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 3. Run the App
```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

---

## ☁️ Deploy to Streamlit Cloud (FREE - Recommended for iPhone Access)

### Step 1: Create GitHub Repository
1. Go to https://github.com/new
2. Create a new repository (e.g., "mia-training-tracker")
3. Upload these files:
   - `streamlit_app.py`
   - `requirements_streamlit.txt`

### Step 2: Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Click "New app"
3. Connect your GitHub account
4. Select your repository
5. Set:
   - **Main file path:** `streamlit_app.py`
   - **Python version:** 3.10
6. Click "Deploy"!

### Step 3: Configure Tesseract (IMPORTANT!)
Since Streamlit Cloud doesn't have Tesseract installed by default, add a `packages.txt` file to your repo:

**Create `packages.txt`:**
```
tesseract-ocr
tesseract-ocr-eng
```

Redeploy after adding this file.

### Step 4: Access from iPhone
Once deployed, you'll get a URL like:
```
https://yourapp.streamlit.app
```

Open this URL on your iPhone Safari - it works perfectly on mobile!

---

## 📱 Mobile Usage Tips

### On iPhone:
1. **Upload Photos:** Tap the file uploader → Take Photo or Choose from Library
2. **Extract Data:** Scroll down and tap "Extract Data from All Images"
3. **Review Charts:** Swipe through tabs at the top
4. **Download Excel:** Use sidebar to download updated data

### Best Practices:
- Take clear, well-lit photos of CityPlay screenshots
- Hold phone horizontally for better screenshot capture
- Multiple screenshots per session work great!

---

## 🚀 Alternative Deployment Options

### Option 2: Deploy to Heroku
1. Create `Procfile`:
```
web: streamlit run streamlit_app.py --server.port=$PORT
```

2. Create `runtime.txt`:
```
python-3.10.12
```

3. Add Tesseract buildpack:
```bash
heroku buildpacks:add --index 1 https://github.com/heroku/heroku-buildpack-apt
```

4. Create `Aptfile`:
```
tesseract-ocr
tesseract-ocr-eng
```

5. Deploy:
```bash
git push heroku main
```

### Option 3: Deploy to Railway
1. Go to https://railway.app
2. "New Project" → "Deploy from GitHub"
3. Select your repository
4. Railway will auto-detect Streamlit
5. Add environment variables if needed

---

## 🔧 Troubleshooting

### OCR Not Working
**Error:** `TesseractNotFoundError`

**Solution:** Make sure Tesseract is installed:
- **Streamlit Cloud:** Add `packages.txt` with tesseract-ocr
- **Local Mac:** `brew install tesseract`
- **Local Windows:** Install from GitHub releases

### Charts Not Showing
**Error:** `ModuleNotFoundError: No module named 'matplotlib'`

**Solution:**
```bash
pip install -r requirements_streamlit.txt
```

### Can't Upload Files on Mobile
**Issue:** File uploader not working on iPhone

**Solution:**
- Use Safari (not Chrome) on iPhone
- Allow camera/photo access in Safari settings
- Try "Take Photo" instead of "Choose File"

---

## 📊 Features Included

✅ **Upload & Extract** - OCR from CityPlay screenshots (mobile camera supported)
✅ **Analytics** - 6 interactive charts
✅ **Agility Tab** - Detailed agility metrics
✅ **Ball Work Tab** - Technical skills tracking
✅ **Personal Records** - All-time bests with dates
✅ **AI Insights** - Performance analysis
✅ **Excel Import/Export** - Full data management
✅ **Mobile Responsive** - Works perfectly on iPhone

---

## 🎨 Customization

### Change Theme
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Add More Charts
Edit `streamlit_app.py` around line 459 to add new chart options.

### Modify OCR Patterns
Edit the `parse_ocr_text()` function around line 137 to adjust OCR extraction patterns.

---

## 💡 Tips for Best Experience

1. **Take Clear Photos:** Good lighting = better OCR accuracy
2. **Multiple Angles:** Upload 2-4 screenshots per session for complete data
3. **Review Extracted Data:** Always check OCR results before saving
4. **Regular Backups:** Download your Excel file weekly
5. **iPhone Home Screen:** Add to home screen for app-like experience

---

## 📞 Support

If you encounter issues:
1. Check Tesseract is installed correctly
2. Verify all dependencies in `requirements_streamlit.txt`
3. Test locally before deploying to cloud
4. Check Streamlit Cloud logs for deployment errors

---

**Built with Streamlit** | Accessible from any browser | iPhone-optimized ⚽
